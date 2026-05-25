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
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
  <title>Trocas Din Din — Publicações</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css">
  <style>
    body { padding-top: 60px; background: #f8f9fa; }
    .card-img-top { object-fit: cover; height: 200px; }
  </style>
</head>
<body>
<nav class="navbar navbar-expand-lg navbar-dark bg-primary fixed-top">
    <a class="navbar-brand" href="index.html">Trocas Din Din — Publicações</a>
    <div class="ml-auto text-white">
      <span id="nav-user">Convidado</span> |
      <button id="login-btn" class="btn btn-sm btn-light">Login</button>
      <button id="logout-btn" class="btn btn-sm btn-secondary" style="display:inline-block; margin-left:8px;">Logout</button>
      <button id="publish-btn" class="btn btn-sm btn-success" style="margin-left:8px;">Publicar</button>
      <button id="history-btn" class="btn btn-sm btn-info" style="margin-left:8px;">Histórico</button>
    </div>
</nav>
<div class="container" style="padding-top: 80px">
  <h1 class="mb-4">Anúncios disponíveis</h1>
    <div class="row">
        <div id="items-container"></div>
'''

HTML_TEMPLATE_FOOT = '''
  </div>
  <div class="row mt-4">
    <div class="col-md-6">
      <h3>Pedidos de Troca</h3>
      <div id="trade-requests"></div>
    </div>
    <div class="col-md-6">
      <h3>Meu Histórico</h3>
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
                        <p class="card-text text-muted">Publicado: {display_date}</p>
                        <p class="card-text font-weight-bold">Preço: {price} Din Din</p>
                        <p class="card-text text-muted">Vendedor: {seller}</p>
                        <p class="card-text">Contato: <a href="https://wa.me/{whatsapp}" target="_blank">WhatsApp</a></p>
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
  if(navUser){ navUser.textContent = user ? user : 'Convidado'; }
  const container = document.getElementById('items-container');
  if(!container) return;
  container.innerHTML = '';
  store.items.forEach(it=>{
    const col = document.createElement('div'); col.className='col-md-6 mb-4';
    const card = document.createElement('div'); card.className='card h-100';
    const img = document.createElement('img'); img.className='card-img-top'; img.src = it.photo ? ('uploads/'+it.photo.split('/').pop()) : '';
    img.alt = it.title || '';
    const body = document.createElement('div'); body.className='card-body d-flex flex-column';
    body.innerHTML = `<h5 class="card-title">${it.title}</h5><p class="card-text">${it.description}</p><p class="card-text text-muted">Publicado: ${it.date||it.created_at||it.source_mtime||''}</p><p class="card-text font-weight-bold">Preço: ${it.price} Din Din</p><p class="card-text text-muted">Vendedor: ${it.seller}</p><p class="card-text">Contato: <a href=\"https://wa.me/${it.whatsapp}\" target=\"_blank\">WhatsApp</a></p>`;
    const btn = document.createElement('button'); btn.className='btn btn-success btn-block mt-auto'; btn.textContent='Comprar';
    btn.onclick = ()=>{ buyItem(it.id); };
    body.appendChild(btn);
    const tradeBtn = document.createElement('button'); tradeBtn.className='btn btn-outline-secondary btn-block mt-2'; tradeBtn.textContent='Pedir Troca';
    tradeBtn.onclick = ()=>{ requestTradePrompt(it.id); };
    body.appendChild(tradeBtn);
    card.appendChild(img); card.appendChild(body); col.appendChild(card); container.appendChild(col);
  });
}

function loginPrompt(){
  const name = prompt('Usuário (apenas nome):'); if(!name) return;
  let store = loadStore(); let user = store.users.find(u=>u.username===name);
  if(!user){ user = { username: name, saldo: 30, purchase_history: [], sales_history: [] }; store.users.push(user); saveStore(store); }
  localStorage.setItem('currentUser', name); render(); alert('Logado como '+name);
}

function logout(){ localStorage.removeItem('currentUser'); render(); }

function buyItem(itemId){
  const current = localStorage.getItem('currentUser'); if(!current){ alert('Faça login para comprar'); return; }
  const store = loadStore(); const buyer = store.users.find(u=>u.username===current);
  const item = store.items.find(i=>i.id===itemId); if(!item){ alert('Item não encontrado'); return; }
  if(item.seller===buyer.username){ alert('Você não pode comprar seu próprio item'); return; }
  if(buyer.saldo < item.price){ alert('Saldo insuficiente'); return; }
  const seller = store.users.find(u=>u.username===item.seller) || { username: item.seller, saldo:0, purchase_history:[], sales_history:[] };
  buyer.saldo -= item.price; seller.saldo = (seller.saldo||0) + item.price;
  buyer.purchase_history.push({ title: item.title, price: item.price, date: new Date().toISOString(), whatsapp: item.whatsapp, description: item.description });
  seller.sales_history = seller.sales_history || []; seller.sales_history.push({ title: item.title, price: item.price, buyer: buyer.username, date: new Date().toISOString() });
  store.items = store.items.filter(i=>i.id!==itemId);
  if(!store.users.find(u=>u.username===seller.username)) store.users.push(seller);
  saveStore(store); render(); alert('Compra realizada com sucesso!');
}

function requestTradePrompt(itemId){
  const current = localStorage.getItem('currentUser'); if(!current){ alert('Faça login para pedir trocas'); return; }
  const store = loadStore(); const myItems = store.items.filter(i=>i.seller===current);
  if(myItems.length===0){ alert('Você precisa ter um item publicado para oferecer em troca'); return; }
  const offered = prompt('Escolha o ID do seu item para oferecer:\\n' + myItems.map(i=>i.id+': '+i.title).join('\\n'));
  if(!offered) return; const trade = { id: 't-'+Date.now(), buyer: current, seller: store.items.find(i=>i.id===itemId).seller, requested_item_id: itemId, offered_item_id: offered, created_at: new Date().toISOString() };
  store.trades.push(trade); saveStore(store); alert('Pedido de troca enviado!'); render();
}

function renderTradeRequests(){
  const current = localStorage.getItem('currentUser'); const container = document.getElementById('trade-requests'); if(!container) return;
  const store = loadStore(); container.innerHTML = '';
  if(!current) { container.innerHTML = '<div class="alert alert-secondary">Faça login para ver pedidos</div>'; return; }
  const myRequests = store.trades.filter(t=>t.seller===current);
  if(myRequests.length===0) { container.innerHTML = '<div class="alert alert-secondary">Nenhum pedido de troca recebido.</div>'; return; }
  myRequests.forEach(t=>{
    const el = document.createElement('div'); el.className='list-group-item';
    el.innerHTML = `<strong>${t.buyer}</strong> quer trocar ${t.requested_item_id} por ${t.offered_item_id}.`;
    const accept = document.createElement('button'); accept.className='btn btn-success btn-sm'; accept.textContent='Aceitar'; accept.onclick=()=>{ acceptTrade(t.id); };
    const reject = document.createElement('button'); reject.className='btn btn-danger btn-sm'; reject.style.marginLeft='8px'; reject.textContent='Recusar'; reject.onclick=()=>{ rejectTrade(t.id); };
    el.appendChild(document.createElement('div')).appendChild(accept);
    el.appendChild(reject);
    container.appendChild(el);
  });
}

function acceptTrade(tradeId){ const store = loadStore(); const t = store.trades.find(x=>x.id===tradeId); if(!t) return alert('Trade não encontrado'); const req = store.items.find(i=>i.id===t.requested_item_id); const off = store.items.find(i=>i.id===t.offered_item_id); if(!req || !off) { alert('Um dos itens não está mais disponível'); store.trades = store.trades.filter(x=>x.id!==tradeId); saveStore(store); render(); return; } store.items = store.items.filter(i=>i.id!==req.id && i.id!==off.id); store.trades = store.trades.filter(x=>x.id!==tradeId); saveStore(store); render(); renderTradeRequests(); alert('Troca aceita — itens removidos'); }

function rejectTrade(tradeId){ const store = loadStore(); store.trades = store.trades.filter(x=>x.id!==tradeId); saveStore(store); render(); renderTradeRequests(); alert('Pedido recusado'); }

function publishItemPrompt(){
  const current = localStorage.getItem('currentUser'); if(!current){ alert('Faça login para publicar um item'); return; }
  const title = prompt('Título do item:'); if(!title) return;
  const description = prompt('Descrição:') || '';
  const priceStr = prompt('Preço (somente números):') || '0'; const price = parseFloat(priceStr) || 0;
  const whatsapp = prompt('WhatsApp (apenas números, ex: 5511999999999):') || '';
  const photo = prompt('Nome do arquivo em uploads (ex: foto.jpg) — deixe vazio se não tiver:') || '';
  const id = 'i-'+Date.now();
  const item = { id: id, title: title, description: description, price: price, photo: photo ? ('/static/uploads/'+photo) : '', whatsapp: whatsapp, seller: current, date: new Date().toISOString() };
  const store = loadStore(); store.items.push(item); saveStore(store); render(); alert('Item publicado com sucesso!');
}

function renderHistory(){
  const current = localStorage.getItem('currentUser'); const container = document.getElementById('history-container'); if(!container) return;
  if(!current){ container.innerHTML = '<div class="alert alert-secondary">Faça login para ver histórico</div>'; return; }
  const store = loadStore(); const user = store.users.find(u=>u.username===current) || { purchase_history: [], sales_history: [] };
  let html = '<h5>Compras</h5>';
  if(user.purchase_history && user.purchase_history.length){ html += '<ul class="list-group mb-3">' + user.purchase_history.map(p=>`<li class="list-group-item">${p.title} — ${p.price} Din Din — ${p.date}</li>`).join('') + '</ul>'; } else { html += '<div class="text-muted">Nenhuma compra registrada.</div>'; }
  html += '<h5>Vendas</h5>';
  if(user.sales_history && user.sales_history.length){ html += '<ul class="list-group">' + user.sales_history.map(s=>`<li class="list-group-item">${s.title} — ${s.price} Din Din — ${s.date} — Comprador: ${s.buyer||s.buyer}</li>`).join('') + '</ul>'; } else { html += '<div class="text-muted">Nenhuma venda registrada.</div>'; }
  container.innerHTML = html;
}

document.addEventListener('DOMContentLoaded', function(){
  const loginBtn = document.getElementById('login-btn'); if(loginBtn) loginBtn.onclick=loginPrompt;
  const logoutBtn = document.getElementById('logout-btn'); if(logoutBtn) logoutBtn.onclick=logout;
  const publishBtn = document.getElementById('publish-btn'); if(publishBtn) publishBtn.onclick=publishItemPrompt;
  const historyBtn = document.getElementById('history-btn'); if(historyBtn) historyBtn.onclick=renderHistory;
  render(); renderTradeRequests();
});
'''

        data_script = "<script>\nconst ITEMS = " + items_json + ";\nconst USERS = " + users_json + ";\nconst TRADES = " + trades_json + ";\n" + js_body + "\n</script>"
        out.write(data_script)
        out.write(HTML_TEMPLATE_END)


if __name__ == '__main__':
    build()
