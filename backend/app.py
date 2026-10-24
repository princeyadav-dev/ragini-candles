import os, re, secrets, logging
from datetime import timedelta
from functools import wraps
from urllib.parse import urlparse
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv
from groq import Groq

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "None" if os.getenv("COOKIE_SECURE", "false").lower() == "true" else "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("COOKIE_SECURE", "false").lower() == "true"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)
app.config["MAX_CONTENT_LENGTH"] = 1_100_000
db_url = os.getenv("DATABASE_URL", "").strip()
if db_url.startswith("postgres://"):
    db_url = "postgresql://" + db_url[len("postgres://"):]
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = db_url or "sqlite:///" + os.path.join(os.path.dirname(__file__), "local-dev.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

origin_text = os.getenv("FRONTEND_ORIGIN", "http://127.0.0.1:5500,http://localhost:5500")
allowed_origins = [x.strip().rstrip("/") for x in origin_text.split(",") if x.strip()]
CORS(app, supports_credentials=True, origins=allowed_origins, allow_headers=["Content-Type", "X-CSRF-Token"], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
limiter = Limiter(get_remote_address, app=app, default_limits=[], storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"))

class Product(db.Model):
    id = db.Column(db.String(40), primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(2000), nullable=False)
    category = db.Column(db.String(60), nullable=False)
    image = db.Column(db.String(500), nullable=False, default="images/candle-placeholder.svg")
    stock = db.Column(db.Integer, nullable=False, default=0)
    featured = db.Column(db.Boolean, nullable=False, default=False)
    fragrance = db.Column(db.String(100), nullable=False, default="")
    size = db.Column(db.String(100), nullable=False, default="")

def product_json(p):
    return {"id":p.id,"name":p.name,"price":p.price,"description":p.description,"category":p.category,"image":p.image,"stock":p.stock,"featured":p.featured,"fragrance":p.fragrance,"size":p.size}
def clean_text(value, field, max_len, required=False):
    if not isinstance(value, str): raise ValueError(f"{field} must be text")
    value=value.strip()
    if required and not value: raise ValueError(f"{field} is required")
    if len(value)>max_len: raise ValueError(f"{field} must be at most {max_len} characters")
    return value
def validate_product(data, existing=None):
    if not isinstance(data,dict): raise ValueError("Expected a JSON object")
    name=clean_text(data.get("name", existing.name if existing else ""), "Name",120,True)
    description=clean_text(data.get("description", existing.description if existing else ""), "Description",2000,True)
    category=clean_text(data.get("category", existing.category if existing else ""), "Category",60,True)
    image=clean_text(data.get("image", existing.image if existing else "images/candle-placeholder.svg"), "Image",500) or "images/candle-placeholder.svg"
    fragrance=clean_text(data.get("fragrance", existing.fragrance if existing else ""), "Fragrance",100)
    size=clean_text(data.get("size", existing.size if existing else ""), "Size",100)
    try: price=int(data.get("price", existing.price if existing else 0)); stock=int(data.get("stock", existing.stock if existing else 0))
    except (TypeError,ValueError): raise ValueError("Price and stock must be whole numbers")
    if price<1 or price>1000000: raise ValueError("Price must be between 1 and 1000000")
    if stock<0 or stock>100000: raise ValueError("Stock must be between 0 and 100000")
    featured=data.get("featured", existing.featured if existing else False)
    if not isinstance(featured,bool): raise ValueError("Featured must be true or false")
    if image.startswith("//") or re.match(r"(?i)^(javascript|data|file):",image): raise ValueError("Use a safe relative image path or HTTP(S) image URL")
    if image.startswith("http") and not image.startswith(("https://","http://")): raise ValueError("Invalid image URL")
    return dict(name=name,price=price,description=description,category=category,image=image,stock=stock,featured=featured,fragrance=fragrance,size=size)
def require_admin(fn):
    @wraps(fn)
    def wrapped(*args,**kwargs):
        if not session.get("admin"): return jsonify(error="Sign in required"),401
        return fn(*args,**kwargs)
    return wrapped
def csrf_ok():
    token=session.get("csrf")
    return bool(token and secrets.compare_digest(token,request.headers.get("X-CSRF-Token","")))
def require_csrf():
    if not csrf_ok(): return jsonify(error="Security token expired. Refresh the page and sign in again."),403
    return None

@app.after_request
def security_headers(resp):
    resp.headers["X-Content-Type-Options"]="nosniff"
    resp.headers["Referrer-Policy"]="strict-origin-when-cross-origin"
    resp.headers["X-Frame-Options"]="DENY"
    resp.headers["Cache-Control"]="no-store" if request.path.startswith("/api/admin") else "public, max-age=60"
    return resp

@app.get("/api/health")
def health():
    return jsonify(status="ok", service="ragini-candles-api")

@app.get("/api/products")
def products_list():
    return jsonify([product_json(p) for p in Product.query.order_by(Product.featured.desc(), Product.name.asc()).all()])
@app.get("/api/products/<product_id>")
def product_get(product_id):
    p=db.session.get(Product,product_id)
    if not p:return jsonify(error="Product not found"),404
    return jsonify(product_json(p))

@app.get("/api/admin/session")
def admin_session():
    return jsonify(authenticated=bool(session.get("admin")),csrf_token=session.get("csrf",""))
@app.post("/api/admin/login")
@limiter.limit("5 per minute")
def admin_login():
    data=request.get_json(silent=True) or {}
    email=os.getenv("ADMIN_EMAIL","").strip().lower()
    password=os.getenv("ADMIN_PASSWORD","")
    password_hash=os.getenv("ADMIN_PASSWORD_HASH","")
    if not email or (not password and not password_hash):
        return jsonify(error="Admin is not configured. Set ADMIN_EMAIL and ADMIN_PASSWORD (or ADMIN_PASSWORD_HASH) in backend environment variables."),503
    given_email=str(data.get("email","")).strip().lower()
    given_password=data.get("password","")
    valid=given_email==email and isinstance(given_password,str) and (check_password_hash(password_hash,given_password) if password_hash else secrets.compare_digest(given_password,password))
    if not valid:return jsonify(error="Email or password is incorrect"),401
    session.clear();session["admin"]=True;session["csrf"]=secrets.token_urlsafe(32);session.permanent=True
    return jsonify(authenticated=True,csrf_token=session["csrf"])
@app.post("/api/admin/logout")
@require_admin
def admin_logout():
    bad=require_csrf()
    if bad:return bad
    session.clear()
    return jsonify(ok=True)
@app.post("/api/admin/products")
@require_admin
def product_create():
    bad=require_csrf()
    if bad:return bad
    try:
        values=validate_product(request.get_json(silent=True))
        p=Product(id=secrets.token_urlsafe(9),**values);db.session.add(p);db.session.commit()
        return jsonify(product_json(p)),201
    except ValueError as e: db.session.rollback();return jsonify(error=str(e)),400
    except Exception: db.session.rollback();app.logger.exception("Product create failed");return jsonify(error="Could not save product"),500
@app.put("/api/admin/products/<product_id>")
@require_admin
def product_update(product_id):
    bad=require_csrf()
    if bad:return bad
    p=db.session.get(Product,product_id)
    if not p:return jsonify(error="Product not found"),404
    try:
        for k,v in validate_product(request.get_json(silent=True),p).items():setattr(p,k,v)
        db.session.commit();return jsonify(product_json(p))
    except ValueError as e:db.session.rollback();return jsonify(error=str(e)),400
    except Exception:db.session.rollback();app.logger.exception("Product update failed");return jsonify(error="Could not update product"),500
@app.delete("/api/admin/products/<product_id>")
@require_admin
def product_delete(product_id):
    bad=require_csrf()
    if bad:return bad
    p=db.session.get(Product,product_id)
    if not p:return jsonify(error="Product not found"),404
    db.session.delete(p);db.session.commit();return jsonify(ok=True)

@app.post("/api/chat")
@limiter.limit("10 per minute")
def chat():
    data=request.get_json(silent=True) or {}
    message=data.get("message")
    if not isinstance(message,str) or not message.strip():return jsonify(error="Please enter a message."),400
    message=message.strip()
    if len(message)>1000:return jsonify(error="Please keep messages under 1000 characters."),400
    key=os.getenv("GROQ_API_KEY","").strip()
    if not key:return jsonify(error="The AI assistant is not configured yet. Please browse the shop or contact the store directly."),503
    try:
        catalogue=[product_json(p) for p in Product.query.all()]
        model=os.getenv("GROQ_MODEL","llama-3.3-70b-versatile").strip()
        client=Groq(api_key=key,timeout=18.0,max_retries=1)
        system=("You are Ragini, the friendly bilingual (Hindi/English) assistant for Ragini Candles. "
          "Use only this catalogue and configured policy facts. Do not invent prices, stock, delivery times, fees, return policies, certifications, reviews, or guarantees. "
          "For order status, delivery/returns, or missing info, say the store must confirm. Suggest products only from the catalogue. "
          "General candle-care guidance is allowed. Keep replies concise and warm. Catalogue JSON: "+str(catalogue)+
          ". Delivery fee is not configured and must be confirmed. Return policy is not provided. Orders are enquiries until the store confirms.")
        result=client.chat.completions.create(model=model,messages=[{"role":"system","content":system},{"role":"user","content":message}],temperature=0.4,max_tokens=450)
        reply=result.choices[0].message.content or "I couldn't prepare a reply. Please try again."
        return jsonify(reply=reply)
    except Exception as e:
        # Do not log provider exception text; it can contain request metadata.
        app.logger.warning("Chat provider request failed (%s)",type(e).__name__)
        return jsonify(error="The assistant is temporarily unavailable. Please try again later."),503

def seed():
    if Product.query.count():return
    examples=[
      dict(id="vanilla-glow",name="Vanilla Glow Candle",price=299,description="A warm, comforting candle for slow evenings and cosy corners. Sample catalogue entry.",category="Scented candles",image="images/candle-placeholder.svg",stock=12,featured=True,fragrance="Vanilla",size="Sample size"),
      dict(id="golden-rose",name="Golden Rose Candle",price=399,description="A decorative rose-inspired candle for thoughtful gifting and soft styling. Sample catalogue entry.",category="Decorative candles",image="images/candle-placeholder.svg",stock=8,featured=True,fragrance="",size="Sample size")]
    for row in examples:db.session.add(Product(**row))
    db.session.commit()
with app.app_context():
    if not app.config["SECRET_KEY"] and os.getenv("FLASK_ENV")=="production":
        raise RuntimeError("FLASK_SECRET_KEY must be set in production")
    if not app.config["SECRET_KEY"]:
        app.config["SECRET_KEY"]=secrets.token_hex(32)
        app.logger.warning("Using an ephemeral development session key; set FLASK_SECRET_KEY for stable sessions.")
    db.create_all()
    seed()

if __name__=="__main__":
    app.run(host="127.0.0.1",port=int(os.getenv("PORT","5000")),debug=False)
