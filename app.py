from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_from_directory
import sqlite3
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'food_app_secret_key'

DATABASE = os.path.join(os.path.dirname(__file__), 'food_app.db')

def get_db():
    conn = sqlite3.connect(DATABASE)
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT UNIQUE NOT NULL, password TEXT NOT NULL, name TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    cursor.execute('CREATE TABLE IF NOT EXISTS profiles (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT NOT NULL, phone TEXT NOT NULL, address TEXT, remark TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, profile_id INTEGER, order_items TEXT NOT NULL, total REAL NOT NULL, status TEXT DEFAULT "pending", delivery_time TEXT, create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(id), FOREIGN KEY (profile_id) REFERENCES profiles(id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS menu_items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT, price REAL NOT NULL, category TEXT NOT NULL, image_url TEXT, available INTEGER DEFAULT 1, sort_order INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    cursor.execute('CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    
    cursor.execute("SELECT COUNT(*) FROM admins WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO admins (username, password) VALUES ('admin', 'admin123')")
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE phone = '13800138000'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (phone, password, name) VALUES ('13800138000', '123456', '测试用户')")
    
    cursor.execute("SELECT COUNT(*) FROM menu_items")
    if cursor.fetchone()[0] == 0:
        menu_data = [
            ('宫保鸡丁', '经典川菜，鸡肉嫩滑', 38, 'recommend', 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=Kung%20Pao%20chicken%20with%20peanuts%20and%20dried%20chilies%20on%20white%20plate%20Chinese%20food&image_size=square', 1, 1),
            ('牛肉柿子', '牛肉软烂，汤汁浓郁', 42, 'recommend', 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=Beef%20noodles%20soup%20with%20meat%20chunks%20Chinese%20style&image_size=square', 1, 2),
            ('米饭', '优质香米，粒粒饱满', 3, 'staple', 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=Steamed%20white%20rice%20in%20bowl%20Asian%20food&image_size=square', 1, 3),
            ('麻婆豆腐', '麻辣鲜香，下饭神器', 28, 'hot', 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=Mapo%20tofu%20spicy%20Sichuan%20Chinese%20dish&image_size=square', 1, 4),
            ('糖醋里脊', '酸甜可口，外酥里嫩', 35, 'hot', 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=Sweet%20and%20sour%20pork%20Chinese%20dish&image_size=square', 1, 5),
            ('酸辣汤', '开胃爽口，酸辣适中', 18, 'drink', 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=Hot%20and%20sour%20soup%20Chinese%20style&image_size=square', 1, 6),
        ]
        cursor.executemany('''
            INSERT INTO menu_items (name, description, price, category, image_url, available, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', menu_data)
    
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/menu', methods=['GET'])
def get_menu():
    category = request.args.get('category')
    conn = get_db()
    cursor = conn.cursor()
    
    if category:
        cursor.execute('SELECT * FROM menu_items WHERE category = ? AND available = 1 ORDER BY sort_order', (category,))
    else:
        cursor.execute('SELECT * FROM menu_items WHERE available = 1 ORDER BY sort_order')
    
    items = []
    for row in cursor.fetchall():
        items.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'price': row[3],
            'category': row[4],
            'image_url': row[5],
            'available': row[6],
            'sort_order': row[7]
        })
    
    conn.close()
    return jsonify(items)

@app.route('/api/profile', methods=['POST'])
def save_profile():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM profiles WHERE phone = ?', (data['phone'],))
    row = cursor.fetchone()
    
    if row:
        cursor.execute('''
            UPDATE profiles SET name=?, address=?, remark=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (data['name'], data.get('address', ''), data.get('remark', ''), row[0]))
        profile_id = row[0]
    else:
        cursor.execute('''
            INSERT INTO profiles (name, phone, address, remark)
            VALUES (?, ?, ?, ?)
        ''', (data['name'], data['phone'], data.get('address', ''), data.get('remark', '')))
        profile_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'profile_id': profile_id})

@app.route('/api/profile/<phone>', methods=['GET'])
def get_profile(phone):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM profiles WHERE phone = ?', (phone,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return jsonify({
            'id': row[0],
            'name': row[1],
            'phone': row[2],
            'address': row[3],
            'remark': row[4],
            'created_at': row[5],
            'updated_at': row[6]
        })
    return jsonify(None)

@app.route('/api/register', methods=['POST'])
def user_register():
    data = request.json
    phone = data.get('phone')
    password = data.get('password')
    name = data.get('name', '')
    
    if not phone or not password:
        return jsonify({'success': False, 'message': '请输入手机号和密码'}), 400
    
    if len(password) < 4:
        return jsonify({'success': False, 'message': '密码至少4位'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE phone = ?', (phone,))
    if cursor.fetchone()[0] > 0:
        conn.close()
        return jsonify({'success': False, 'message': '该手机号已注册'}), 400
    
    cursor.execute('INSERT INTO users (phone, password, name) VALUES (?, ?, ?)', (phone, password, name))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'user': {
            'id': user_id,
            'phone': phone,
            'name': name
        }
    })

@app.route('/api/login', methods=['POST'])
def user_login():
    data = request.json
    phone = data.get('phone')
    password = data.get('password')
    
    if not phone or not password:
        return jsonify({'success': False, 'message': '请输入手机号和密码'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE phone = ? AND password = ?', (phone, password))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return jsonify({
            'success': True,
            'user': {
                'id': user[0],
                'phone': user[1],
                'name': user[3]
            }
        })
    
    return jsonify({'success': False, 'message': '手机号或密码错误'}), 401

@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.json
    
    conn = get_db()
    cursor = conn.cursor()
    
    profile_id = None
    if data.get('profile'):
        profile = data['profile']
        cursor.execute('SELECT id FROM profiles WHERE phone = ?', (profile['phone'],))
        row = cursor.fetchone()
        if row:
            profile_id = row[0]
        else:
            cursor.execute('''
                INSERT INTO profiles (name, phone, address, remark)
                VALUES (?, ?, ?, ?)
            ''', (profile['name'], profile['phone'], profile.get('address', ''), profile.get('remark', '')))
            profile_id = cursor.lastrowid
    
    order_items_json = json.dumps(data['items'], ensure_ascii=False)
    
    cursor.execute('''
        INSERT INTO orders (profile_id, order_items, total, status)
        VALUES (?, ?, ?, 'pending')
    ''', (profile_id, order_items_json, data['total']))
    
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'order_id': order_id})

@app.route('/api/orders', methods=['GET'])
def get_orders():
    status = request.args.get('status')
    phone = request.args.get('phone')
    conn = get_db()
    cursor = conn.cursor()
    
    profile_id = None
    if phone:
        cursor.execute('SELECT id FROM profiles WHERE phone = ?', (phone,))
        row = cursor.fetchone()
        if row:
            profile_id = row[0]
    
    if profile_id and status:
        cursor.execute('SELECT * FROM orders WHERE profile_id = ? AND status = ? ORDER BY create_time DESC', (profile_id, status))
    elif profile_id:
        cursor.execute('SELECT * FROM orders WHERE profile_id = ? ORDER BY create_time DESC', (profile_id,))
    elif status:
        cursor.execute('SELECT * FROM orders WHERE status = ? ORDER BY create_time DESC', (status,))
    else:
        cursor.execute('SELECT * FROM orders ORDER BY create_time DESC')
    
    orders = []
    for row in cursor.fetchall():
        order_id, order_profile_id, order_items_json, total, order_status, create_time = row
        try:
            order_items = json.loads(order_items_json) if isinstance(order_items_json, str) else []
        except:
            order_items = []
        
        order = {
            'id': order_id,
            'profile_id': order_profile_id,
            'order_items': order_items,
            'total': total,
            'status': order_status,
            'create_time': create_time
        }
        
        if order_profile_id:
            cursor.execute('SELECT * FROM profiles WHERE id = ?', (order_profile_id,))
            p_row = cursor.fetchone()
            if p_row:
                order['profile'] = {
                    'id': p_row[0],
                    'name': p_row[1],
                    'phone': p_row[2],
                    'address': p_row[3],
                    'remark': p_row[4]
                }
        orders.append(order)
    
    conn.close()
    return jsonify(orders)

@app.route('/api/orders/<order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    data = request.json
    new_status = data.get('status')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE orders SET status = ? WHERE id = ?', (new_status, order_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admins WHERE username = ? AND password = ?', (username, password))
        admin = cursor.fetchone()
        conn.close()
        
        if admin:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        
        return render_template('login.html', error='用户名或密码错误')
    
    return render_template('login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM orders')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM orders WHERE status = "pending"')
    pending = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM orders WHERE status = "confirmed"')
    confirmed = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM orders WHERE status = "completed"')
    completed = cursor.fetchone()[0]
    
    cursor.execute('SELECT * FROM orders ORDER BY create_time DESC LIMIT 10')
    recent_orders = []
    for row in cursor.fetchall():
        order_id, profile_id, order_items_json, total_price, status, create_time = row
        try:
            order_items = json.loads(order_items_json) if isinstance(order_items_json, str) else []
        except:
            order_items = []
        
        order = {
            'id': order_id,
            'profile_id': profile_id,
            'order_items': order_items,
            'total': total_price,
            'status': status,
            'create_time': create_time
        }
        
        if profile_id:
            cursor.execute('SELECT * FROM profiles WHERE id = ?', (profile_id,))
            p_row = cursor.fetchone()
            if p_row:
                order['profile'] = {
                    'id': p_row[0],
                    'name': p_row[1],
                    'phone': p_row[2],
                    'address': p_row[3],
                    'remark': p_row[4]
                }
        recent_orders.append(order)
    
    cursor.execute('SELECT * FROM menu_items ORDER BY sort_order')
    menu_items = []
    for row in cursor.fetchall():
        menu_items.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'price': row[3],
            'category': row[4],
            'image_url': row[5],
            'available': row[6],
            'sort_order': row[7]
        })
    
    conn.close()
    
    return render_template('dashboard.html', 
                           total=total, pending=pending, 
                           confirmed=confirmed, completed=completed,
                           orders=recent_orders,
                           menu_items=menu_items)

@app.route('/admin/orders')
def admin_orders():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    status = request.args.get('status')
    
    conn = get_db()
    cursor = conn.cursor()
    
    if status:
        cursor.execute('SELECT * FROM orders WHERE status = ? ORDER BY create_time DESC', (status,))
    else:
        cursor.execute('SELECT * FROM orders ORDER BY create_time DESC')
    
    orders = []
    for row in cursor.fetchall():
        order_id, profile_id, order_items_json, total_price, order_status, create_time = row
        try:
            order_items = json.loads(order_items_json) if isinstance(order_items_json, str) else []
        except:
            order_items = []
        
        order = {
            'id': order_id,
            'profile_id': profile_id,
            'order_items': order_items,
            'total': total_price,
            'status': order_status,
            'create_time': create_time
        }
        
        if profile_id:
            cursor.execute('SELECT * FROM profiles WHERE id = ?', (profile_id,))
            p_row = cursor.fetchone()
            if p_row:
                order['profile'] = {
                    'id': p_row[0],
                    'name': p_row[1],
                    'phone': p_row[2],
                    'address': p_row[3],
                    'remark': p_row[4]
                }
        orders.append(order)
    
    conn.close()
    
    return render_template('orders.html', orders=orders, status=status)

@app.route('/admin/update_status/<order_id>', methods=['POST'])
def admin_update_status(order_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    status = request.form['status']
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_orders'))

@app.route('/admin/profiles')
def admin_profiles():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM profiles ORDER BY created_at DESC')
    profiles = []
    for row in cursor.fetchall():
        profiles.append({
            'id': row[0],
            'name': row[1],
            'phone': row[2],
            'address': row[3],
            'remark': row[4],
            'created_at': row[5],
            'updated_at': row[6]
        })
    conn.close()
    
    return render_template('profiles.html', profiles=profiles)

@app.route('/admin/menu')
def admin_menu():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM menu_items ORDER BY sort_order')
    items = []
    for row in cursor.fetchall():
        items.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'price': row[3],
            'category': row[4],
            'image_url': row[5],
            'available': row[6],
            'sort_order': row[7]
        })
    conn.close()
    
    return render_template('menu.html', items=items)

@app.route('/admin/menu/add', methods=['POST'])
def admin_add_menu():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    name = request.form['name']
    description = request.form.get('description', '')
    price = float(request.form['price'])
    category = request.form['category']
    image_url = request.form.get('image_url', '')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO menu_items (name, description, price, category, image_url, available, sort_order)
        VALUES (?, ?, ?, ?, ?, 1, 0)
    ''', (name, description, price, category, image_url))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_menu'))

@app.route('/admin/menu/edit/<int:item_id>', methods=['POST'])
def admin_edit_menu(item_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    name = request.form['name']
    description = request.form.get('description', '')
    price = float(request.form['price'])
    category = request.form['category']
    image_url = request.form.get('image_url', '')
    available = 1 if request.form.get('available') else 0
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE menu_items SET name=?, description=?, price=?, category=?, image_url=?, available=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    ''', (name, description, price, category, image_url, available, item_id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_menu'))

@app.route('/admin/menu/delete/<int:item_id>')
def admin_delete_menu(item_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM menu_items WHERE id=?', (item_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_menu'))

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)