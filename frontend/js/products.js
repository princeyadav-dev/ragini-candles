// Product data is fetched from the backend API; there is no second browser-side catalogue.
window.RaginiProducts = {
  async list() {
    const res = await fetch(`${window.RAGINI_CONFIG.API_BASE_URL}/api/products`);
    if (!res.ok) throw new Error("Could not load products");
    return res.json();
  },
  async get(id) {
    const res = await fetch(`${window.RAGINI_CONFIG.API_BASE_URL}/api/products/${encodeURIComponent(id)}`);
    if (!res.ok) throw new Error("Product not found");
    return res.json();
  }
};
