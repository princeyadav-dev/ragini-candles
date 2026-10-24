(() => {
  const money = n => new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",maximumFractionDigits:0}).format(n);
  window.money = money;
  window.cartStore = {
    read(){ try{return JSON.parse(localStorage.getItem("ragini-cart")||"[]")}catch{return []} },
    write(items){localStorage.setItem("ragini-cart",JSON.stringify(items)); window.dispatchEvent(new Event("ragini-cart-change"))},
    count(){return this.read().reduce((s,x)=>s+x.qty,0)}
  };
  function updateCount(){document.querySelectorAll("[data-cart-count]").forEach(e=>e.textContent=window.cartStore.count())}
  document.addEventListener("DOMContentLoaded", async()=>{
    updateCount(); window.addEventListener("ragini-cart-change",updateCount);
    document.querySelectorAll("[data-year]").forEach(e=>e.textContent=new Date().getFullYear());
    const grid=document.querySelector("[data-featured-grid]");
    if(grid){
      try{
        const products=await window.RaginiProducts.list();
        const featured=products.filter(p=>p.featured).slice(0,4);
        grid.innerHTML=featured.map(card).join("") || '<p class="muted">Our featured collection is being prepared. Please visit the shop soon.</p>';
        bindAdd(grid);
      }catch{grid.innerHTML='<p class="muted">The collection is temporarily unavailable. Please try again shortly.</p>'}
    }
    document.querySelectorAll("[data-wa]").forEach(a=>{
      const n=window.RAGINI_CONFIG.WHATSAPP_NUMBER;
      if(n && /^\d{8,15}$/.test(n)){a.href=`https://wa.me/${n}`;a.hidden=false}
      else {a.hidden=true}
    });
    document.querySelectorAll("[data-faq-button]").forEach(btn=>btn.addEventListener("click",()=>{const panel=btn.nextElementSibling; const open=btn.getAttribute("aria-expanded")==="true";btn.setAttribute("aria-expanded",String(!open));panel.hidden=open;}));
  });
  function card(p){return `<article class="product-card"><a class="product-image" href="product.html?id=${encodeURIComponent(p.id)}"><img src="${escapeAttr(p.image)}" alt="${escapeAttr(p.name)}" loading="lazy" onerror="this.src='images/candle-placeholder.svg'"></a><div class="product-info"><p class="eyebrow">${escapeHtml(p.category)}</p><h3><a href="product.html?id=${encodeURIComponent(p.id)}">${escapeHtml(p.name)}</a></h3><p class="price">${money(p.price)}</p><button class="button button-small" data-add="${escapeAttr(p.id)}" ${p.stock<=0?"disabled":""}>${p.stock<=0?"Sold out":"Add to bag"}</button></div></article>`}
  function bindAdd(scope){scope.querySelectorAll("[data-add]").forEach(b=>b.addEventListener("click",async()=>{try{const p=await window.RaginiProducts.get(b.dataset.add);const items=window.cartStore.read();const row=items.find(x=>x.id===p.id);if(row)row.qty=Math.min(row.qty+1,p.stock);else items.push({id:p.id,qty:1});window.cartStore.write(items);const old=b.textContent;b.textContent="Added";setTimeout(()=>b.textContent=old,900)}catch{alert("This product could not be added right now.")}}))}
  window.renderProductCard=card;window.bindProductAdds=bindAdd;
  function escapeHtml(s){return String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
  function escapeAttr(s){return escapeHtml(s)}
})();
