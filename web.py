from flask import Flask, render_template_string, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from uuid import uuid4
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'trocas-secret-key'
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
ITEMS_FOLDER = os.path.join(app.root_path, 'data', 'items')
USERS_FOLDER = os.path.join(app.root_path, 'data', 'users')
TRADES_FOLDER = os.path.join(app.root_path, 'data', 'trades')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

for folder in (UPLOAD_FOLDER, ITEMS_FOLDER, USERS_FOLDER, TRADES_FOLDER):
    os.makedirs(folder, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_user(username):
    path = os.path.join(USERS_FOLDER, f'{username}.json')
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            user = json.load(f)
            if 'saldo' not in user:
                user['saldo'] = 0
            if 'purchase_history' not in user:
                user['purchase_history'] = []
            if 'sales_history' not in user:
                user['sales_history'] = []
            return user
    except (json.JSONDecodeError, OSError):
        return None


def save_user(user):
    path = os.path.join(USERS_FOLDER, f'{user["username"]}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(user, f, ensure_ascii=False)


def load_items():
    loaded = []
    for filename in os.listdir(ITEMS_FOLDER):
        if not filename.endswith('.json'):
            continue
        path = os.path.join(ITEMS_FOLDER, filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                loaded.append(json.load(f))
        except (json.JSONDecodeError, OSError):
            continue
    return loaded

items = load_items()


def load_trades():
    loaded = []
    for filename in os.listdir(TRADES_FOLDER):
        if not filename.endswith('.json'):
            continue
        path = os.path.join(TRADES_FOLDER, filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                loaded.append(json.load(f))
        except (json.JSONDecodeError, OSError):
            continue
    return loaded


def save_trade(trade):
    path = os.path.join(TRADES_FOLDER, f'{trade["id"]}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(trade, f, ensure_ascii=False)


def delete_trade(trade_id):
    path = os.path.join(TRADES_FOLDER, f'{trade_id}.json')
    if os.path.exists(path):
        os.remove(path)


def get_user_items(username):
    return [item for item in items if item['seller'] == username]


def remove_item(item):
    if item in items:
        items.remove(item)
    json_path = os.path.join(ITEMS_FOLDER, f"{item['id']}.json")
    if os.path.exists(json_path):
        os.remove(json_path)
    photo_path = os.path.join(app.root_path, item['photo'].lstrip('/'))
    if os.path.exists(photo_path):
        os.remove(photo_path)


trades = load_trades()

TEMPLATE = '''
<!doctype html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Trocas Din Din</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css">
    <style>
        body { padding-top: 60px; background: #f8f9fa; }
        .card-img-top { object-fit: cover; height: 200px; }
    </style>
</head>
<body>
<nav class="navbar navbar-expand-lg navbar-dark bg-primary fixed-top">
    <a class="navbar-brand" href="{{ url_for('home') }}">Trocas Din Din</a>
    <div class="ml-auto text-white">
        {% if user %}
            <span>{{ user.username }}</span> | 
            <strong>💰 {{ user.saldo }} Din Din</strong> | 
            <a href="{{ url_for('logout') }}" class="text-white">Sair</a>
        {% else %}
            <a href="{{ url_for('login') }}" class="text-white">Login</a>
        {% endif %}
    </div>
</nav>
<div class="container">
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <div class="alert alert-info mt-3">
          {% for msg in messages %}{{ msg }}<br>{% endfor %}
        </div>
      {% endif %}
    {% endwith %}

    <div class="row">
        <div class="col-md-8">
            <h3 class="mb-3">Anúncios disponíveis</h3>
            <div class="row">
                {% for item in items %}
                <div class="col-md-6 mb-4">
                    <div class="card h-100">
                        <img src="{{ item.photo }}" class="card-img-top" alt="{{ item.title }}">
                        <div class="card-body d-flex flex-column">
                            <h5 class="card-title">{{ item.title }}</h5>
                            <p class="card-text">{{ item.description }}</p>
                            <p class="card-text font-weight-bold">Preço: {{ item.price }} Din Din</p>
                            <p class="card-text text-muted">Vendedor: {{ item.seller }}</p>
                            <p class="card-text">Contato: <a href="https://wa.me/{{ item.whatsapp }}" target="_blank">WhatsApp</a></p>
                            {% if user and user.username == item.seller %}
                            <div class="btn-group btn-block" role="group">
                                <form action="{{ url_for('delete_item', item_id=item.id) }}" method="post" style="flex: 1;">
                                    <button type="submit" class="btn btn-danger btn-block">Remover</button>
                                </form>
                            </div>
                            {% elif user and user.username != item.seller %}
                            <form action="{{ url_for('buy', item_id=item.id) }}" method="post" class="mt-auto">
                                <button type="submit" class="btn btn-success btn-block">Comprar</button>
                            </form>
                            {% if my_items %}
                            <form action="{{ url_for('request_trade', item_id=item.id) }}" method="post" class="mt-2">
                                <div class="form-group mb-2">
                                    <select name="offered_item_id" class="form-control" required>
                                        <option value="">Ofereça um item seu em troca</option>
                                        {% for my_item in my_items %}
                                        <option value="{{ my_item.id }}">{{ my_item.title }}</option>
                                        {% endfor %}
                                    </select>
                                </div>
                                <button type="submit" class="btn btn-outline-secondary btn-block">Pedir Troca</button>
                            </form>
                            {% else %}
                            <button class="btn btn-outline-secondary btn-block mt-2" disabled>Publique um item para oferecer em troca</button>
                            {% endif %}
                            {% else %}
                            <button class="btn btn-success btn-block" disabled>Faça login para comprar</button>
                            {% endif %}
                        </div>
                    </div>
                </div>
                {% else %}
                <div class="col-12">
                    <div class="alert alert-secondary">Nenhum item disponível no momento.</div>
                </div>
                {% endfor %}
            </div>
        </div>
        <div class="col-md-4">
            {% if user %}
            <h4 class="mb-3">Publicar item</h4>
            <form id="add-item-form" action="{{ url_for('add_item') }}" method="post" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="title">Título</label>
                    <input type="text" id="title" name="title" class="form-control" required>
                </div>
                <div class="form-group">
                    <label for="description">Descrição</label>
                    <textarea id="description" name="description" class="form-control" rows="3" required></textarea>
                </div>
                <div class="form-group">
                    <label for="price">Preço (Din Din)</label>
                    <input type="number" id="price" name="price" min="1" class="form-control" required>
                </div>
                <div class="form-group">
                    <label for="photo">Foto (JPG)</label>
                    <input type="file" id="photo" name="photo" accept="image/jpeg" class="form-control-file" required>
                </div>
                <div class="form-group">
                    <label for="whatsapp">WhatsApp</label>
                    <input type="text" id="whatsapp" name="whatsapp" class="form-control" placeholder="5511999999999" required>
                </div>
                <button type="submit" class="btn btn-primary btn-block">Publicar</button>
            </form>
            <hr>
            <h4 class="mb-3">Pedidos de Troca Recebidos</h4>
            {% if trade_requests %}
            <div class="list-group">
                {% for trade in trade_requests %}
                <div class="list-group-item">
                    <strong>{{ trade.buyer }}</strong> quer trocar <em>{{ trade.requested_title }}</em>
                    por <em>{{ trade.offered_title }}</em>.
                    <div class="mt-2">
                        <form action="{{ url_for('accept_trade', trade_id=trade.id) }}" method="post" style="display:inline-block;">
                            <button type="submit" class="btn btn-success btn-sm">Aceitar</button>
                        </form>
                        <form action="{{ url_for('reject_trade', trade_id=trade.id) }}" method="post" style="display:inline-block; margin-left: 8px;">
                            <button type="submit" class="btn btn-danger btn-sm">Recusar</button>
                        </form>
                    </div>
                </div>
                {% endfor %}
            </div>
            {% else %}
            <div class="alert alert-secondary">Nenhum pedido de troca recebido.</div>
            {% endif %}

            <hr>
            <h4 class="mb-3">Histórico de Compras</h4>
            {% if user.purchase_history %}
            <ul class="list-group mb-3">
                {% for entry in user.purchase_history %}
                <li class="list-group-item">
                    Comprou <strong>{{ entry.get('name', entry.get('title', '')) }}</strong> por <strong>{{ entry.get('price', '') }} Din Din</strong><br>
                    Contato: <a href="https://wa.me/{{ entry.get('zap', entry.get('whatsapp', '')) }}" target="_blank">{{ entry.get('zap', entry.get('whatsapp', '')) }}</a><br>
                    {{ entry.get('description', '') }}<br>
                    em {{ entry.get('date', '')[:19].replace('T', ' ') }}
                </li>
                {% endfor %}
            </ul>
            {% else %}
            <div class="alert alert-secondary">Nenhuma compra registrada.</div>
            {% endif %}

            <h4 class="mb-3">Histórico de Vendas</h4>
            {% if user.sales_history %}
            <ul class="list-group">
                {% for entry in user.sales_history %}
                <li class="list-group-item">
                    Vendeu <strong>{{ entry.title }}</strong> por <strong>{{ entry.price }} Din Din</strong>
                    para {{ entry.buyer }} em {{ entry.date[:19].replace('T', ' ') }}
                </li>
                {% endfor %}
            </ul>
            {% else %}
            <div class="alert alert-secondary">Nenhuma venda registrada.</div>
            {% endif %}
            {% else %}
            <div class="alert alert-info">Faça login para publicar anúncios</div>
            {% endif %}
        </div>
    </div>

</div>
<script>
document.addEventListener('DOMContentLoaded', function() {
    var form = document.getElementById('add-item-form');
    if (form) {
        form.addEventListener('keydown', function(event) {
            if (event.key === 'Enter' && event.target.tagName === 'INPUT') {
                event.preventDefault();
            }
        });
    }
});
</script>
<script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

LOGIN_TEMPLATE = '''
<!doctype html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Login - Trocas Din Din</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css">
    <style>
        body { padding-top: 60px; background: #f8f9fa; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
        .login-card { max-width: 400px; width: 100%; }
    </style>
</head>
<body>
<div class="login-card">
    <div class="card">
        <div class="card-body">
            <h3 class="card-title text-center mb-4">Trocas Din Din</h3>
            {% with messages = get_flashed_messages() %}
              {% if messages %}
                <div class="alert alert-danger">
                  {% for msg in messages %}{{ msg }}<br>{% endfor %}
                </div>
              {% endif %}
            {% endwith %}
            <form action="{{ url_for('login') }}" method="post">
                <div class="form-group">
                    <label for="username">Usuário</label>
                    <input type="text" id="username" name="username" class="form-control" required>
                </div>
                <div class="form-group">
                    <label for="password">Senha</label>
                    <input type="password" id="password" name="password" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-primary btn-block">Entrar</button>
            </form>
            <hr>
            <p class="text-center">Não tem conta? <a href="{{ url_for('register') }}">Registre-se aqui</a></p>
        </div>
    </div>
</div>
<script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

REGISTER_TEMPLATE = '''
<!doctype html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Registrar - Trocas Din Din</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css">
    <style>
        body { padding-top: 60px; background: #f8f9fa; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
        .register-card { max-width: 400px; width: 100%; }
    </style>
</head>
<body>
<div class="register-card">
    <div class="card">
        <div class="card-body">
            <h3 class="card-title text-center mb-4">Criar Conta</h3>
            {% with messages = get_flashed_messages() %}
              {% if messages %}
                <div class="alert alert-danger">
                  {% for msg in messages %}{{ msg }}<br>{% endfor %}
                </div>
              {% endif %}
            {% endwith %}
            <form action="{{ url_for('register') }}" method="post">
                <div class="form-group">
                    <label for="username">Usuário</label>
                    <input type="text" id="username" name="username" class="form-control" required>
                </div>
                <div class="form-group">
                    <label for="password">Senha</label>
                    <input type="password" id="password" name="password" class="form-control" required>
                </div>
                <div class="form-group">
                    <label for="confirm">Confirmar Senha</label>
                    <input type="password" id="confirm" name="confirm" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-success btn-block">Registrar</button>
            </form>
            <hr>
            <p class="text-center">Já tem conta? <a href="{{ url_for('login') }}">Faça login aqui</a></p>
        </div>
    </div>
</div>
<script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

@app.route('/')
def home():
    user = None
    my_items = []
    trade_requests = []
    if 'username' in session:
        user = get_user(session['username'])
        if user:
            my_items = get_user_items(user['username'])
            for trade in trades:
                if trade['seller'] == user['username']:
                    requested_item = next((i for i in items if i['id'] == trade['requested_item_id']), None)
                    offered_item = next((i for i in items if i['id'] == trade['offered_item_id']), None)
                    trade_requests.append({
                        'id': trade['id'],
                        'buyer': trade['buyer'],
                        'requested_title': requested_item['title'] if requested_item else 'Item não encontrado',
                        'offered_title': offered_item['title'] if offered_item else 'Item não encontrado'
                    })
    return render_template_string(TEMPLATE, items=items, user=user, my_items=my_items, trade_requests=trade_requests)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Preencha todos os campos.')
            return redirect(url_for('login'))

        user = get_user(username)
        if user is None or not check_password_hash(user['password'], password):
            flash('Usuário ou senha incorretos.')
            return redirect(url_for('login'))

        session['username'] = username
        flash(f'Bem-vindo, {username}!')
        return redirect(url_for('home'))

    return render_template_string(LOGIN_TEMPLATE)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm = request.form.get('confirm', '').strip()

        if not username or not password or not confirm:
            flash('Preencha todos os campos.')
            return redirect(url_for('register'))

        if password != confirm:
            flash('As senhas não combinam.')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('A senha deve ter no mínimo 6 caracteres.')
            return redirect(url_for('register'))

        if get_user(username) is not None:
            flash('Esse usuário já existe.')
            return redirect(url_for('register'))

        user = {
            'username': username,
            'password': generate_password_hash(password),
            'saldo': 30,
            'purchase_history': [],
            'sales_history': []
        }
        save_user(user)

        session['username'] = username
        flash(f'Conta criada com sucesso! Bem-vindo, {username}!')
        return redirect(url_for('home'))

    return render_template_string(REGISTER_TEMPLATE)


@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta.')
    return redirect(url_for('login'))


@app.route('/add', methods=['POST'])
def add_item():
    if 'username' not in session:
        flash('Faça login para publicar anúncios.')
        return redirect(url_for('login'))

    user = get_user(session['username'])
    if not user:
        session.clear()
        return redirect(url_for('login'))

    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    whatsapp = request.form.get('whatsapp', '').strip()
    try:
        price = int(request.form.get('price', 0))
    except ValueError:
        price = 0

    photo_file = request.files.get('photo')
    if photo_file is None or photo_file.filename == '':
        flash('Selecione um arquivo JPG para a foto.')
        return redirect(url_for('home'))

    if not allowed_file(photo_file.filename):
        flash('Só é permitido enviar imagens JPG.')
        return redirect(url_for('home'))

    if not title or not description or not whatsapp or price <= 0:
        flash('Preencha todos os campos corretamente para publicar o item.')
        return redirect(url_for('home'))

    item_id = str(uuid4())
    extension = photo_file.filename.rsplit('.', 1)[1].lower()
    photo_filename = f"{item_id}.{extension}"
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
    photo_file.save(save_path)
    photo_url = url_for('static', filename=f'uploads/{photo_filename}')

    item = {
        'id': item_id,
        'title': title,
        'description': description,
        'price': price,
        'photo': photo_url,
        'whatsapp': whatsapp,
        'seller': user['username']
    }

    items.append(item)
    with open(os.path.join(ITEMS_FOLDER, f'{item_id}.json'), 'w', encoding='utf-8') as f:
        json.dump(item, f, ensure_ascii=False)

    flash('Item publicado com sucesso!')
    return redirect(url_for('home'))


@app.route('/buy/<item_id>', methods=['POST'])
def buy(item_id):
    if 'username' not in session:
        flash('Faça login para comprar.')
        return redirect(url_for('login'))

    buyer = get_user(session['username'])
    if not buyer:
        session.clear()
        return redirect(url_for('login'))

    item = next((item for item in items if item['id'] == item_id), None)
    if item is None:
        flash('Item não encontrado.')
        return redirect(url_for('home'))

    if buyer['username'] == item['seller']:
        flash('Você não pode comprar seu próprio anúncio.')
        return redirect(url_for('home'))

    if item['price'] > buyer['saldo']:
        flash('Saldo insuficiente para comprar este item.')
        return redirect(url_for('home'))

    seller = get_user(item['seller'])
    if not seller:
        flash('Vendedor não encontrado.')
        return redirect(url_for('home'))

    buyer['saldo'] -= item['price']
    seller['saldo'] += item['price']

    buyer.setdefault('purchase_history', []).append({
        'name': item.get('title', ''),
        'zap': item.get('whatsapp', ''),
        'description': item.get('description', ''),
        'price': item['price'],
        'date': datetime.now().isoformat()
    })
    seller.setdefault('sales_history', []).append({
        'item_id': item['id'],
        'title': item['title'],
        'price': item['price'],
        'buyer': buyer['username'],
        'date': datetime.now().isoformat()
    })

    save_user(buyer)
    save_user(seller)

    items.remove(item)

    json_path = os.path.join(ITEMS_FOLDER, f'{item_id}.json')
    if os.path.exists(json_path):
        os.remove(json_path)

    photo_path = os.path.join(app.root_path, item['photo'].lstrip('/'))
    if os.path.exists(photo_path):
        os.remove(photo_path)

    flash(f"Compra realizada! Você gastou {item['price']} Din Din. {item['seller']} recebeu {item['price']} Din Din.")
    return redirect(url_for('home'))


@app.route('/trade/<item_id>', methods=['POST'])
def request_trade(item_id):
    if 'username' not in session:
        flash('Faça login para solicitar uma troca.')
        return redirect(url_for('login'))

    buyer = get_user(session['username'])
    if not buyer:
        session.clear()
        return redirect(url_for('login'))

    item = next((item for item in items if item['id'] == item_id), None)
    if item is None:
        flash('Item não encontrado.')
        return redirect(url_for('home'))

    if item['seller'] == buyer['username']:
        flash('Você não pode trocar com seu próprio anúncio.')
        return redirect(url_for('home'))

    offered_item_id = request.form.get('offered_item_id')
    offered_item = next((i for i in items if i['id'] == offered_item_id and i['seller'] == buyer['username']), None)
    if offered_item is None:
        flash('Selecione um item seu válido para oferecer em troca.')
        return redirect(url_for('home'))

    trade_id = str(uuid4())
    trade = {
        'id': trade_id,
        'buyer': buyer['username'],
        'seller': item['seller'],
        'requested_item_id': item['id'],
        'offered_item_id': offered_item['id'],
        'created_at': datetime.now().isoformat()
    }
    trades.append(trade)
    save_trade(trade)

    flash(f'Pedido de troca enviado para {item["seller"]}!')
    return redirect(url_for('home'))


@app.route('/trade/<trade_id>/accept', methods=['POST'])
def accept_trade(trade_id):
    if 'username' not in session:
        flash('Faça login para aceitar a troca.')
        return redirect(url_for('login'))

    user = get_user(session['username'])
    if not user:
        session.clear()
        return redirect(url_for('login'))

    trade = next((t for t in trades if t['id'] == trade_id), None)
    if trade is None:
        flash('Pedido de troca não encontrado.')
        return redirect(url_for('home'))

    if trade['seller'] != user['username']:
        flash('Apenas o vendedor pode aceitar este pedido de troca.')
        return redirect(url_for('home'))

    requested_item = next((i for i in items if i['id'] == trade['requested_item_id']), None)
    offered_item = next((i for i in items if i['id'] == trade['offered_item_id']), None)
    if not requested_item or not offered_item:
        flash('Um dos itens da troca não está mais disponível.')
        delete_trade(trade_id)
        trades.remove(trade)
        return redirect(url_for('home'))

    remove_item(requested_item)
    remove_item(offered_item)

    trades.remove(trade)
    delete_trade(trade_id)

    flash('Troca aceita! Os itens foram removidos da plataforma.')
    return redirect(url_for('home'))


@app.route('/trade/<trade_id>/reject', methods=['POST'])
def reject_trade(trade_id):
    if 'username' not in session:
        flash('Faça login para recusar a troca.')
        return redirect(url_for('login'))

    user = get_user(session['username'])
    if not user:
        session.clear()
        return redirect(url_for('login'))

    trade = next((t for t in trades if t['id'] == trade_id), None)
    if trade is None:
        flash('Pedido de troca não encontrado.')
        return redirect(url_for('home'))

    if trade['seller'] != user['username']:
        flash('Apenas o vendedor pode recusar este pedido de troca.')
        return redirect(url_for('home'))

    trades.remove(trade)
    delete_trade(trade_id)
    flash('Pedido de troca recusado.')
    return redirect(url_for('home'))


@app.route('/delete/<item_id>', methods=['POST'])
def delete_item(item_id):
    if 'username' not in session:
        flash('Faça login para remover anúncios.')
        return redirect(url_for('login'))

    user = get_user(session['username'])
    if not user:
        session.clear()
        return redirect(url_for('login'))

    item = next((item for item in items if item['id'] == item_id), None)
    if item is None:
        flash('Item não encontrado.')
        return redirect(url_for('home'))

    if user['username'] != item['seller']:
        flash('Você só pode remover seus próprios anúncios.')
        return redirect(url_for('home'))

    items.remove(item)

    json_path = os.path.join(ITEMS_FOLDER, f'{item_id}.json')
    if os.path.exists(json_path):
        os.remove(json_path)

    photo_path = os.path.join(app.root_path, item['photo'].lstrip('/'))
    if os.path.exists(photo_path):
        os.remove(photo_path)

    flash(f"Anúncio '{item['title']}' removido com sucesso!")
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
 