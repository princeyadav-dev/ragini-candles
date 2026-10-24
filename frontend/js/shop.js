document.addEventListener("DOMContentLoaded",async()=>{
 const grid=document.querySelector("#shop-grid"), search=document.querySelector("#search"), cat=document.querySelector("#category"), sort=document.querySelector("#sort"), status=document.querySelector("#shop-status");
 let all=[];
 try{all=await RaginiProducts.list();const cats=[...new Set(all.map(p=>p.category))];cats.forEach(c=>{const o=document.createElement("option");o.value=c;o.textContent=c;cat.append(o)});render()}
 catch{status.textContent="We couldn't load the catalogue. Check that the backend is running.";return}
 function render(){let list=all.filter(p=>(p.name+" "+p.description).toLowerCase().includes(search.value.toLowerCase())&&(!cat.value||p.category===cat.value));if(sort.value==="low")list.sort((a,b)=>a.price-b.price);if(sort.value==="high")list.sort((a,b)=>b.price-a.price);grid.innerHTML=list.map(renderProductCard).join("")||'<p class="muted">No candles match your search yet.</p>';bindProductAdds(grid);status.textContent=`${list.length} candle${list.length===1?"":"s"} found`}
 [search,cat,sort].forEach(el=>el.addEventListener(el===search?"input":"change",render));
});
