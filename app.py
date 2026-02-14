from xml.parsers.expat import errors
from flask import Flask, request, jsonify, render_template, send_from_directory, session, redirect, url_for, Response
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta
import os
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
load_dotenv()



DATABASE_URL = os.getenv("DATABASE_URL")

def get_postgres_connection():
    return psycopg2.connect(DATABASE_URL)

app = Flask(__name__)

def create_tables():
    conn = get_postgres_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100) NOT NULL,
        email VARCHAR(120) UNIQUE NOT NULL,
        password TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS pantry (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    product VARCHAR(200),
    expiry_date DATE,
    UNIQUE(user_id, product, expiry_date)
);

    """)

    conn.commit()
    cur.close()
    conn.close()


app.secret_key = "super_secret_key"

CORS(app)

DB = 'database.db'
print("DATABASE_URL:", DATABASE_URL)

def get_shelf_life(product, storage, opened):
    storage_map = {
        'room': 'room',
        'refrigerated': 'refrigerated',
        'frozen': 'frozen'
        }
    mapped_storage = storage_map.get(storage, 'room')
    column = f"shelf_life_{mapped_storage}_{'opened' if opened else 'closed'}"

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # --- START FIX ---
    # 1. Change the query to use LIKE for a partial match
    sql_query = f"SELECT {column} FROM products WHERE lower(name) LIKE ?"
    
    # 2. Create a search term with wildcards
    search_term = f'%{product.lower()}%'
    
    # 3. Execute with the new query and search term
    c.execute(sql_query, (search_term,))
    # --- END FIX ---

    result = c.fetchone()
    conn.close()

    return result[0] if result and result[0] is not None else None

#Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        conn = get_postgres_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                (username, email, password)
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            return "User already exists"
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('login'))

    return render_template("register.html")

#login route
from flask import flash

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_postgres_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, password FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user:
            flash("User not found. Please register.", "error")
            return render_template("login.html")
        from werkzeug.security import check_password_hash
        if not check_password_hash(user[2], password):
            flash("Incorrect password.", "error")
            return render_template("login.html")
    


        session['user_id'] = user[0]
        session['username'] = user[1]
        return redirect('/')

    return render_template("login.html")

# Guest Mode route
@app.route('/guest')
def guest():
    session['guest'] = True
    session['user_id'] = None
    session['username'] = "Guest"
    return redirect(url_for('home'))


# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Save to pantry route
@app.route('/save-to-pantry', methods=['POST'])
def save_to_pantry():

    if not session.get('user_id'):
        return jsonify({"status": "error", "message": "Login required."})

    data = request.json
    product = data.get("product")
    expiry_date = data.get("expiry_date")

    if not product or not expiry_date:
        return jsonify({"status": "error", "message": "Invalid data."})

    conn = get_postgres_connection()
    cur = conn.cursor()

    # Prevent duplicates
    cur.execute("""
        SELECT id FROM pantry
        WHERE user_id=%s AND product=%s AND expiry_date=%s
    """, (session['user_id'], product, expiry_date))

    existing = cur.fetchone()

    if existing:
        cur.close()
        conn.close()
        return jsonify({"status": "error", "message": "Item already saved."})

    cur.execute("""
        INSERT INTO pantry (user_id, product, expiry_date)
        VALUES (%s, %s, %s)
    """, (session['user_id'], product, expiry_date))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "success", "message": "Saved to pantry!"})

# Pantry route to display saved items and their expiry dates, sorted by nearest expiry first
@app.route('/pantry')
def pantry():

    if not session.get('user_id'):
        return redirect('/login')

    conn = get_postgres_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, product, expiry_date,
        (expiry_date - CURRENT_DATE) AS days_left
        FROM pantry
        WHERE user_id=%s
        ORDER BY expiry_date ASC
    """, (session['user_id'],))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    pantry_items = []

    for row in rows:
        pantry_items.append({
            "id": row[0],
            "product": row[1],
            "expiry_date": row[2],
            "days_left": row[3]
        })

    return render_template("pantry.html", items=pantry_items)

# Route to delete an item from the pantry
@app.route('/delete-from-pantry', methods=['POST'])
def delete_from_pantry():

    if not session.get('user_id'):
        return jsonify({"status": "error", "message": "Unauthorized"})

    data = request.json
    item_id = data.get("item_id")

    conn = get_postgres_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM pantry
        WHERE id=%s AND user_id=%s
    """, (item_id, session['user_id']))

    conn.commit()

    cur.close()
    conn.close()

    return jsonify({"status": "success"})


#pantry stats route to show number of expired and soon-to-expire items
@app.route('/pantry-stats')
def pantry_stats():
    if not session.get('user_id'):
        return jsonify({"expired":0,"soon":0,"safe":0,"total":0})

    conn = get_postgres_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT expiry_date FROM pantry
        WHERE user_id = %s
    """, (session['user_id'],))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    expired = soon = safe = 0
    today = datetime.now().date()

    for (expiry_date,) in rows:
        days = (expiry_date - today).days
        if days < 0:
            expired += 1
        elif days <= 3:
            soon += 1
        else:
            safe += 1

    return jsonify({
        "expired": expired,
        "soon": soon,
        "safe": safe,
        "total": expired + soon + safe
    })



# Route for robots.txt
@app.route('/robots.txt')
def serve_robots():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'robots.txt',
        mimetype='text/plain'
    )

# Route for sitemap.xml
@app.route('/sitemap.xml')
def sitemap_xml():
    return send_from_directory(app.static_folder, 'sitemap.xml')

@app.route('/get-product', methods=['POST'])
def get_product():
    data = request.json
    product = data.get('product', '').strip()
    storage = data.get('storage', 'room')
    opened = data.get('opened', False)
    manu_date = data.get('manufacturing_date')

    if not product:
        return jsonify({'status': 'error', 'message': 'Product name is required'}), 400

    shelf_life = get_shelf_life(product, storage, opened)
    if shelf_life is None:
        return jsonify({'status': 'error', 'message': 'Product not found or shelf life missing'}), 404

    if manu_date:
        try:
            if manu_date == "Invalid Date" or manu_date.strip() == "":
                raise ValueError
            mdate = datetime.strptime(manu_date, '%Y-%m-%d')
            expiry = mdate + timedelta(days=shelf_life)
            return jsonify({
                'status': 'success',
                'expiry_date': expiry.strftime('%Y-%m-%d'),
                'shelf_life': shelf_life
            })
        except:
            return jsonify({'status': 'error', 'message': 'Invalid date'}), 400

    return jsonify({
        'status': 'success',
        'shelf_life': shelf_life
    })


@app.route('/get-category-average', methods=['POST'])
def get_category_average():
    data = request.json
    category = data.get('category')
    if not category:
        return jsonify({'status': 'error', 'message': 'Category is required'}), 400

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    # --- START FIX ---
    # Remove the 'f' from f'''...'''
    c.execute('''
        SELECT AVG(
            shelf_life_room_closed + shelf_life_refrigerated_closed + shelf_life_frozen_closed
        ) / 3 FROM products WHERE lower(category) = ?
    ''', (category.lower(),))
    # --- END FIX ---
    
    avg = c.fetchone()[0]
    conn.close()

    if avg is None: # Changed 'if not avg' to 'if avg is None' to correctly handle 0
        return jsonify({'status': 'error', 'message': 'Category not found or no data'}), 404

    return jsonify({
        'status': 'success',
        'category': category,
        'average_shelf_life': round(avg)
    })


@app.route('/')
def home():
    return render_template("main.html")

# Debug route to check users in the database
@app.route('/debug-users')
def debug_users():
    conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, email FROM users")
    users = cur.fetchall()
    cur.close()
    conn.close()
    return str(users)


if __name__ == '__main__':
    create_tables()
    port = int(os.environ.get("PORT", 10000))
    app.run(debug=True, host='0.0.0.0', port=port)
