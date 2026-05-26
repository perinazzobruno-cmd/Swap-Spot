from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
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
                        'requested_title': requested_item['title'] if requested_item else 'Item not found',
                        'offered_title': offered_item['title'] if offered_item else 'Item not found'
                    })
    return render_template('index.html', items=items, user=user, my_items=my_items, trade_requests=trade_requests)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Please fill in all fields.')
            return redirect(url_for('login'))

        user = get_user(username)
        if user is None or not check_password_hash(user['password'], password):
            flash('Invalid username or password.')
            return redirect(url_for('login'))

        session['username'] = username
        flash(f'Bem-vindo, {username}!')
        return redirect(url_for('home'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm = request.form.get('confirm', '').strip()

        if not username or not password or not confirm:
            flash('Please fill in all fields.')
            return redirect(url_for('register'))

        if password != confirm:
            flash('Passwords do not match.')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters.')
            return redirect(url_for('register'))

        if get_user(username) is not None:
            flash('This username is already taken.')
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
        flash(f'Account created successfully! Welcome, {username}!')
        return redirect(url_for('home'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))


@app.route('/add', methods=['POST'])
def add_item():
    if 'username' not in session:
        flash('Please login to post listings.')
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
        flash('Select a JPG file for the photo.')
        return redirect(url_for('home'))

    if not allowed_file(photo_file.filename):
        flash('Only JPG images are allowed.')
        return redirect(url_for('home'))

    if not title or not description or not whatsapp or price <= 0:
        flash('Please fill in all required fields correctly.')
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

    flash('Item posted successfully!')
    return redirect(url_for('home'))


@app.route('/buy/<item_id>', methods=['POST'])
def buy(item_id):
    if 'username' not in session:
        flash('Please login to buy.')
        return redirect(url_for('login'))

    buyer = get_user(session['username'])
    if not buyer:
        session.clear()
        return redirect(url_for('login'))

    item = next((item for item in items if item['id'] == item_id), None)
    if item is None:
        flash('Item not found.')
        return redirect(url_for('home'))

    if buyer['username'] == item['seller']:
        flash('You cannot buy your own listing.')
        return redirect(url_for('home'))

    if item['price'] > buyer['saldo']:
        flash('Insufficient balance to buy this item.')
        return redirect(url_for('home'))

    seller = get_user(item['seller'])
    if not seller:
        flash('Seller not found.')
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

    flash(f"Purchase completed! You spent {item['price']} Coins. {item['seller']} received {item['price']} Coins.")
    return redirect(url_for('home'))


@app.route('/trade/<item_id>', methods=['POST'])
def request_trade(item_id):
    if 'username' not in session:
        flash('Please login to request a swap.')
        return redirect(url_for('login'))

    buyer = get_user(session['username'])
    if not buyer:
        session.clear()
        return redirect(url_for('login'))

    item = next((item for item in items if item['id'] == item_id), None)
    if item is None:
        flash('Item not found.')
        return redirect(url_for('home'))

    if item['seller'] == buyer['username']:
        flash('You cannot swap with your own listing.')
        return redirect(url_for('home'))

    offered_item_id = request.form.get('offered_item_id')
    offered_item = next((i for i in items if i['id'] == offered_item_id and i['seller'] == buyer['username']), None)
    if offered_item is None:
        flash('Select a valid item of yours to offer in swap.')
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

    flash(f'Swap request sent to {item["seller"]}!')
    return redirect(url_for('home'))


@app.route('/trade/<trade_id>/accept', methods=['POST'])
def accept_trade(trade_id):
    if 'username' not in session:
        flash('Please login to accept the swap.')
        return redirect(url_for('login'))

    user = get_user(session['username'])
    if not user:
        session.clear()
        return redirect(url_for('login'))

    trade = next((t for t in trades if t['id'] == trade_id), None)
    if trade is None:
        flash('Swap request not found.')
        return redirect(url_for('home'))

    if trade['seller'] != user['username']:
        flash('Only the seller can accept this swap request.')
        return redirect(url_for('home'))

    requested_item = next((i for i in items if i['id'] == trade['requested_item_id']), None)
    offered_item = next((i for i in items if i['id'] == trade['offered_item_id']), None)
    if not requested_item or not offered_item:
        flash('One of the items in the swap is no longer available.')
        delete_trade(trade_id)
        trades.remove(trade)
        return redirect(url_for('home'))

    remove_item(requested_item)
    remove_item(offered_item)

    trades.remove(trade)
    delete_trade(trade_id)

    flash('Swap accepted! The items have been removed from the platform.')
    return redirect(url_for('home'))


@app.route('/trade/<trade_id>/reject', methods=['POST'])
def reject_trade(trade_id):
    if 'username' not in session:
        flash('Please login to reject the swap.')
        return redirect(url_for('login'))

    user = get_user(session['username'])
    if not user:
        session.clear()
        return redirect(url_for('login'))

    trade = next((t for t in trades if t['id'] == trade_id), None)
    if trade is None:
        flash('Swap request not found.')
        return redirect(url_for('home'))

    if trade['seller'] != user['username']:
        flash('Only the seller can reject this swap request.')
        return redirect(url_for('home'))

    trades.remove(trade)
    delete_trade(trade_id)
    flash('Swap request rejected.')
    return redirect(url_for('home'))


@app.route('/delete/<item_id>', methods=['POST'])
def delete_item(item_id):
    if 'username' not in session:
        flash('Please login to remove listings.')
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
        flash('You can only remove your own listings.')
        return redirect(url_for('home'))

    items.remove(item)

    json_path = os.path.join(ITEMS_FOLDER, f'{item_id}.json')
    if os.path.exists(json_path):
        os.remove(json_path)

    photo_path = os.path.join(app.root_path, item['photo'].lstrip('/'))
    if os.path.exists(photo_path):
        os.remove(photo_path)

    flash(f"Listing '{item['title']}' removed successfully!")
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
 
