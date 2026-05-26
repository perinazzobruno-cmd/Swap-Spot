import json
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent
DATA_DIR = ROOT / 'data'
ITEMS_DIR = DATA_DIR / 'items'
USERS_DIR = DATA_DIR / 'users'
TRADES_DIR = DATA_DIR / 'trades'
STATIC_DIR = ROOT / 'static'
UPLOADS_DIR = STATIC_DIR / 'uploads'

OUT_DIR = ROOT / 'docs'
OUT_UPLOADS = OUT_DIR / 'uploads'

HTML_TEMPLATE_HEAD = '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
  <title>Swap Spot: Trade, Save, Repeat!</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css">
  <style>
    body { padding-top: 60px; background: #f8f9fa; }
    .card-img-top { object-fit: cover; height: 200px; }
  </style>
</head>
<body>
<nav class="navbar navbar-expand-lg navbar-dark bg-primary fixed-top">
    <a class="navbar-brand" href="index.html">Swap Spot: Trade, Save, Repeat!</a>
    <div class="ml-auto text-white">
      <span id="nav-user">Guest</span> |
      <button id="login-btn" class="btn btn-sm btn-light">Login</button>
      <button id="logout-btn" class="btn btn-sm btn-secondary" style="display:inline-block; margin-left:8px;">Logout</button>
      <button id="publish-btn" class="btn btn-sm btn-success" style="margin-left:8px;">Publish</button>
      <button id="history-btn" class="btn btn-sm btn-info" style="margin-left:8px;">History</button>
    </div>
</nav>
<div class="container" style="padding-top: 80px">
  <h1 class="mb-4">Available Listings</h1>
    <div class="row">
        <div id="items-container"></div>
'''

HTML_TEMPLATE_FOOT = '''
  </div>
  <div id="publish-section" class="card mt-4 mb-4" style="display:none;">
    <div class="card-body">
      <h3>Post Item</h3>
      <form id="publish-form">
        <div class="form-group">
          <label for="publish-title">Title</label>
          <input type="text" id="publish-title" class="form-control" required>
        </div>
        <div class="form-group">
          <label for="publish-description">Description</label>
          <textarea id="publish-description" class="form-control" rows="3" required></textarea>
        </div>
        <div class="form-group">
          <label for="publish-price">Price (Coins)</label>
          <input type="number" id="publish-price" class="form-control" min="1" required>
        </div>
        <div class="form-group">
          <label for="publish-whatsapp">WhatsApp</label>
          <input type="text" id="publish-whatsapp" class="form-control" placeholder="5511999999999" required>
        </div>
        <div class="form-group">
          <label for="publish-photo">Photo (JPEG)</label>
          <input type="file" id="publish-photo" class="form-control-file" accept="image/jpeg" required>
        </div>
        <button type="submit" class="btn btn-success">Publish</button>
        <button type="button" id="cancel-publish-btn" class="btn btn-secondary ml-2">Cancel</button>
      </form>
    </div>
  </div>
  <div class="row mt-4">
    <div class="col-md-6">
      <h3>Swap Requests</h3>
      <div id="trade-requests"></div>
    </div>
    <div class="col-md-6">
      <h3>My History</h3>
      <div id="history-container"></div>
    </div>
  </div>
</div>
'''

HTML_TEMPLATE_END = '''
<script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''



def load_json_folder(folder: Path):
    objs = []
    if not folder.exists():
        return objs
    for p in sorted(folder.glob('*.json')):
        try:
            with open(p, 'r', encoding='utf-8') as fh:
                d = json.load(fh)
            try:
                m = datetime.fromtimestamp(p.stat().st_mtime).isoformat()
                d['source_mtime'] = m
            except Exception:
                pass
            objs.append(d)
        except Exception as e:
            print('failed to load', p, e)
    return objs


def build():
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # copy uploads
    if UPLOADS_DIR.exists():
        shutil.copytree(UPLOADS_DIR, OUT_UPLOADS)

    items = load_json_folder(ITEMS_DIR)
    users = load_json_folder(USERS_DIR)
    trades = load_json_folder(TRADES_DIR)

    index_path = OUT_DIR / 'index.html'
    with open(index_path, 'w', encoding='utf-8') as out:
        out.write(HTML_TEMPLATE_HEAD)

        for it in items:
            title = it.get('title') or it.get('name') or 'Sem título'
            desc = it.get('description') or it.get('desc') or ''
            price = it.get('price', 0)
            seller = it.get('seller', '')
            whatsapp = it.get('whatsapp', '')
            photo = it.get('photo') or it.get('image') or ''
            photo_path = ('uploads/' + photo.split('/')[-1]) if photo else ''
            display_date = it.get('source_mtime') or it.get('date') or ''
            card = f'''<div class="col-md-6 mb-4">
        <div class="card h-100">
                <img src="{photo_path}" class="card-img-top" alt="{title}">
                <div class="card-body d-flex flex-column">
                        <h5 class="card-title">{title}</h5>
                        <p class="card-text">{desc}</p>
                        <p class="card-text text-muted">Published: {display_date}</p>
                        <p class="card-text font-weight-bold">Price: {price} Coins</p>
                        <p class="card-text text-muted">Seller: {seller}</p>
                        <p class="card-text">Contact: <a href="https://wa.me/{whatsapp}" target="_blank">WhatsApp</a></p>
                </div>
        </div>
</div>'''
            out.write(card)

        out.write(HTML_TEMPLATE_FOOT)

        # embed data for client-side interactivity safely
        items_json = json.dumps(items, ensure_ascii=False)
        users_json = json.dumps(users, ensure_ascii=False)
        trades_json = json.dumps(trades, ensure_ascii=False)

        js_body = '''
// simple client-side store using localStorage
function loadStore(){
  const store = JSON.parse(localStorage.getItem('site_store') || '{}');
  store.items = store.items || ITEMS.slice();
  store.users = store.users || USERS.slice();
  store.trades = store.trades || TRADES.slice();
  return store;
}
function saveStore(store){
  localStorage.setItem('site_store', JSON.stringify(store));
}

function render(){
  const store = loadStore();
  const user = localStorage.getItem('currentUser');
  const navUser = document.getElementById('nav-user');
  const publishSection = document.getElementById('publish-section');
  const publishBtn = document.getElementById('publish-btn');
  if(navUser){ navUser.textContent = user ? user : 'Guest'; }
  if(publishBtn){ publishBtn.style.display = user ? 'inline-block' : 'none'; }
  if(publishSection){ publishSection.style.display = 'none'; }
  const container = document.getElementById('items-container');
  if(!container) return;
  container.innerHTML = '';
  store.items.forEach(it=>{
    const col = document.createElement('div'); col.className='col-md-6 mb-4';
    const card = document.createElement('div'); card.className='card h-100';
    const img = document.createElement('img'); img.className='card-img-top';
    let photoSrc = it.photo || '';
    if(photoSrc.startsWith('/static/')){ photoSrc = photoSrc.slice('/static/'.length); }
    img.src = photoSrc;
    img.alt = it.title || '';
    const body = document.createElement('div'); body.className='card-body d-flex flex-column';
    body.innerHTML = `<h5 class="card-title">${it.title}</h5><p class="card-text">${it.description}</p><p class="card-text text-muted">Published: ${it.date||it.created_at||it.source_mtime||''}</p><p class="card-text font-weight-bold">Price: ${it.price} Coins</p><p class="card-text text-muted">Seller: ${it.seller}</p><p class="card-text">Contact: <a href=\"https://wa.me/${it.whatsapp}\" target=\"_blank\">WhatsApp</a></p>`;
    const btn = document.createElement('button'); btn.className='btn btn-success btn-block mt-auto'; btn.textContent='Buy';
    btn.onclick = ()=>{ buyItem(it.id); };
    body.appendChild(btn);
    const tradeBtn = document.createElement('button'); tradeBtn.className='btn btn-outline-secondary btn-block mt-2'; tradeBtn.textContent='Request Swap';
    tradeBtn.onclick = ()=>{ requestTradePrompt(it.id); };
    body.appendChild(tradeBtn);
    card.appendChild(img); card.appendChild(body); col.appendChild(card); container.appendChild(col);
  });
}

function loginPrompt(){
  const name = prompt('Username (name only):'); if(!name) return;
  let store = loadStore(); let user = store.users.find(u=>u.username===name);
  if(!user){ user = { username: name, saldo: 30, purchase_history: [], sales_history: [] }; store.users.push(user); saveStore(store); }
  localStorage.setItem('currentUser', name); render(); alert('Logged in as '+name);
}

function logout(){ localStorage.removeItem('currentUser'); render(); }

function buyItem(itemId){
  const current = localStorage.getItem('currentUser'); if(!current){ alert('Please login to buy'); return; }
  const store = loadStore(); const buyer = store.users.find(u=>u.username===current);
  const item = store.items.find(i=>i.id===itemId); if(!item){ alert('Item not found'); return; }
  if(item.seller===buyer.username){ alert('You cannot buy your own item'); return; }
  if(buyer.saldo < item.price){ alert('Insufficient balance'); return; }
  const seller = store.users.find(u=>u.username===item.seller) || { username: item.seller, saldo:0, purchase_history:[], sales_history:[] };
  buyer.saldo -= item.price; seller.saldo = (seller.saldo||0) + item.price;
  buyer.purchase_history.push({ title: item.title, price: item.price, date: new Date().toISOString(), whatsapp: item.whatsapp, description: item.description });
  seller.sales_history = seller.sales_history || []; seller.sales_history.push({ title: item.title, price: item.price, buyer: buyer.username, date: new Date().toISOString() });
  store.items = store.items.filter(i=>i.id!==itemId);
  if(!store.users.find(u=>u.username===seller.username)) store.users.push(seller);
  saveStore(store); render(); alert('Purchase completed successfully!');
}

function requestTradePrompt(itemId){
  const current = localStorage.getItem('currentUser'); if(!current){ alert('Please login to request a swap'); return; }
  const store = loadStore(); const myItems = store.items.filter(i=>i.seller===current);
  if(myItems.length===0){ alert('You must post an item first to offer in swap'); return; }
  const offered = prompt('Choose the ID of your item to offer in swap:\\n' + myItems.map(i=>i.id+': '+i.title).join('\\n'));
  if(!offered) return; const trade = { id: 't-'+Date.now(), buyer: current, seller: store.items.find(i=>i.id===itemId).seller, requested_item_id: itemId, offered_item_id: offered, created_at: new Date().toISOString() };
  store.trades.push(trade); saveStore(store); alert('Swap request sent!'); render();
}

function renderTradeRequests(){
  const current = localStorage.getItem('currentUser'); const container = document.getElementById('trade-requests'); if(!container) return;
  const store = loadStore(); container.innerHTML = '';
  if(!current) { container.innerHTML = '<div class="alert alert-secondary">Please login to view swap requests</div>'; return; }
  const myRequests = store.trades.filter(t=>t.seller===current);
  if(myRequests.length===0) { container.innerHTML = '<div class="alert alert-secondary">No swap requests received.</div>'; return; }
  myRequests.forEach(t=>{
    const el = document.createElement('div'); el.className='list-group-item';
    el.innerHTML = `<strong>${t.buyer}</strong> wants to swap ${t.requested_item_id} for ${t.offered_item_id}.`;
    const accept = document.createElement('button'); accept.className='btn btn-success btn-sm'; accept.textContent='Accept'; accept.onclick=()=>{ acceptTrade(t.id); };
    const reject = document.createElement('button'); reject.className='btn btn-danger btn-sm'; reject.style.marginLeft='8px'; reject.textContent='Reject'; reject.onclick=()=>{ rejectTrade(t.id); };
    el.appendChild(document.createElement('div')).appendChild(accept);
    el.appendChild(reject);
    container.appendChild(el);
  });
}

function acceptTrade(tradeId){ const store = loadStore(); const t = store.trades.find(x=>x.id===tradeId); if(!t) return alert('Trade not found'); const req = store.items.find(i=>i.id===t.requested_item_id); const off = store.items.find(i=>i.id===t.offered_item_id); if(!req || !off) { alert('One of the items is no longer available'); store.trades = store.trades.filter(x=>x.id!==tradeId); saveStore(store); render(); return; } store.items = store.items.filter(i=>i.id!==req.id && i.id!==off.id); store.trades = store.trades.filter(x=>x.id!==tradeId); saveStore(store); render(); renderTradeRequests(); alert('Swap accepted — items removed'); }

function rejectTrade(tradeId){ const store = loadStore(); store.trades = store.trades.filter(x=>x.id!==tradeId); saveStore(store); render(); renderTradeRequests(); alert('Swap request rejected'); }

function togglePublishForm(){
  const current = localStorage.getItem('currentUser');
  if(!current){ alert('Please login to publish an item'); return; }
  const section = document.getElementById('publish-section');
  if(!section) return;
  section.style.display = section.style.display === 'block' ? 'none' : 'block';
}

function hidePublishForm(){
  const section = document.getElementById('publish-section');
  if(section){ section.style.display = 'none'; }
  const form = document.getElementById('publish-form');
  if(form){ form.reset(); }
}

function handlePublishSubmit(event){
  event.preventDefault();
  const current = localStorage.getItem('currentUser');
  if(!current){ alert('Please login to publish an item'); return; }
  const title = document.getElementById('publish-title').value.trim();
  const description = document.getElementById('publish-description').value.trim();
  const price = parseFloat(document.getElementById('publish-price').value) || 0;
  const whatsapp = document.getElementById('publish-whatsapp').value.trim();
  const photoInput = document.getElementById('publish-photo');
  if(!title || !description || price <= 0 || !whatsapp){ alert('Please fill in all required fields correctly.'); return; }
  if(photoInput.files.length === 0){ alert('Select a JPEG file.'); return; }
  const file = photoInput.files[0];
  if(file.type !== 'image/jpeg'){
    alert('Select a JPEG file.');
    return;
  }
  const reader = new FileReader();
  reader.onload = function(e){
    const photoData = e.target.result;
    const id = 'i-'+Date.now();
    const item = { id: id, title: title, description: description, price: price, whatsapp: whatsapp, seller: current, date: new Date().toISOString(), photo: photoData };
    const store = loadStore();
    store.items.push(item);
    saveStore(store);
    render();
    renderTradeRequests();
    hidePublishForm();
    alert('Item posted successfully!');
  };
  reader.readAsDataURL(file);
}

function renderHistory(){
  const current = localStorage.getItem('currentUser'); const container = document.getElementById('history-container'); if(!container) return;
  if(!current){ container.innerHTML = '<div class="alert alert-secondary">Please login to view history</div>'; return; }
  const store = loadStore(); const user = store.users.find(u=>u.username===current) || { purchase_history: [], sales_history: [] };
  let html = '<h5>Purchases</h5>';
  if(user.purchase_history && user.purchase_history.length){ html += '<ul class="list-group mb-3">' + user.purchase_history.map(p=>`<li class="list-group-item">${p.title} — ${p.price} Coins — ${p.date}</li>`).join('') + '</ul>'; } else { html += '<div class="text-muted">No purchases recorded.</div>'; }
  html += '<h5>Sales</h5>';
  if(user.sales_history && user.sales_history.length){ html += '<ul class="list-group">' + user.sales_history.map(s=>`<li class="list-group-item">${s.title} — ${s.price} Coins — ${s.date} — Buyer: ${s.buyer||s.buyer}</li>`).join('') + '</ul>'; } else { html += '<div class="text-muted">No sales recorded.</div>'; }
  container.innerHTML = html;
}

document.addEventListener('DOMContentLoaded', function(){
  const loginBtn = document.getElementById('login-btn'); if(loginBtn) loginBtn.onclick=loginPrompt;
  const logoutBtn = document.getElementById('logout-btn'); if(logoutBtn) logoutBtn.onclick=logout;
  const publishBtn = document.getElementById('publish-btn'); if(publishBtn) publishBtn.onclick=togglePublishForm;
  const publishForm = document.getElementById('publish-form'); if(publishForm) publishForm.addEventListener('submit', handlePublishSubmit);
  const cancelPublishBtn = document.getElementById('cancel-publish-btn'); if(cancelPublishBtn) cancelPublishBtn.onclick=hidePublishForm;
  const historyBtn = document.getElementById('history-btn'); if(historyBtn) historyBtn.onclick=renderHistory;
  render(); renderTradeRequests();
});
'''

        data_script = "<script>\nconst ITEMS = " + items_json + ";\nconst USERS = " + users_json + ";\nconst TRADES = " + trades_json + ";\n" + js_body + "\n</script>"
        out.write(data_script)
        out.write(HTML_TEMPLATE_END)


if __name__ == '__main__':
    build()
