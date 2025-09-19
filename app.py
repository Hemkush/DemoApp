from flask import Flask
from flask import Flask, request, jsonify
from flask_mysqldb import MySQL, MySQLdb
from flask import Flask, request, jsonify, render_template, abort, redirect
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import mysql.connector

app = Flask(__name__)
# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'your_password' #replace with actual DB password
app.config['MYSQL_DB'] = 'budt_748'
mysql = MySQL(app)

# app = Flask(__name__) 
app.secret_key = 'ueierfhufiqiuh4ruhrekj' # required for session cookies

# --- Flask-Login Config --- 
login_manager = LoginManager() 
login_manager.init_app(app) 
login_manager.login_view = 'login'

# --- Role Helpers --- 
def is_admin(): 
    return current_user.role in ['Admin']
 
def role_required(*roles): 
    def wrapper(fn): 
        @wraps(fn) 
        def decorated_view(*args, **kwargs): 
            if not current_user.is_authenticated or current_user.role not in roles: 
                return abort(403) 
            return fn(*args, **kwargs) 
        return decorated_view 
    return wrapper

# --- User Loader Class --- 
class User(UserMixin): 
    def __init__(self, id, name, email, password, role): 
        self.id = id 
        self.name = name 
        self.email = email 
        self.password = password 
        self.role = role 
        
@login_manager.user_loader 
def load_user(user_id): 
    cur = mysql.connection.cursor() 
    cur.execute("SELECT * FROM users WHERE uid = %s", (user_id,)) 
    user_data = cur.fetchone() 
    cur.close() 
    if user_data: 
        return User(*user_data)
    return None

first_name = "Hemant"
last_name = "Kushwaha"
# @app.route('/')
# def home():
#     return render_template('home.html')

# ======================== # ROUTES # ======================== 
# --- Login --- 
@app.route('/login', methods=['GET', 'POST']) 
def login(): 
    if request.method == 'POST': 
        email = request.form['email'] 
        password = request.form['password'] 
        cur = mysql.connection.cursor() 
        cur.execute("SELECT * FROM users WHERE email = %s", (email,)) 
        user_data = cur.fetchone() 
        cur.close() 
        if user_data and check_password_hash(user_data[3], password): 
            user = User(*user_data) 
            login_user(user) 
            return redirect('/') 
        else: 
            return render_template('login.html', error="Invalid credentials") 
    return render_template('login.html')

# --- Logout --- 
@app.route('/logout') 
@login_required 
def logout(): 
    logout_user() 
    return redirect('/login')

# --- Home Page --- 
@app.route('/') 
@login_required 
def home(): 
    return render_template('home.html')

# --- Add User (Admin Only) --- 
@app.route('/user', methods=['POST']) 
@login_required 
@role_required('Admin') 
def add_user(): 
    if request.is_json: 
        data = request.get_json() 
        uid = data['uid']
        name = data['name'] 
        email = data['email'] 
        role = data.get('role', 'Admin') 
        password = generate_password_hash(data.get('password', 'test123')) 
        cur = mysql.connection.cursor() 
        sql = "INSERT INTO users (uid, name, email, password, role) VALUES (%s, %s, %s, %s, %s)" 
        cur.execute(sql, (uid, name, email, password, role)) 
        mysql.connection.commit() 
        cur.close() 
        return jsonify(message="User added successfully"), 201 
    return jsonify(error="Invalid submission"), 400

# --- View Users (All Logged-In Users) --- 
@app.route('/users', methods=['GET']) 
@login_required 
def get_users(): 
    cur = mysql.connection.cursor() 
    cur.execute("SELECT uid, name, email, role FROM users") 
    users = cur.fetchall() 
    cur.close() 
    user_dicts = [] 
    for user in users: 
        user_data = { 
            'uid': user[0], 
            'name': user[1], 
            'role': user[3] 
            } 
        # Admins can view emails, customers can't 
        if is_admin(): 
            user_data['email'] = user[2] 
        user_dicts.append(user_data) 
    return jsonify(user_dicts)

# --- Delete User (Admin Only) --- 
@app.route('/user/<int:uid>', methods=['DELETE']) 
@login_required 
@role_required('Admin') 
def delete_user(uid): 
    cur = mysql.connection.cursor() 
    cur.execute("DELETE FROM users WHERE uid = %s", [uid]) 
    mysql.connection.commit() 
    cur.close() 
    return jsonify(message="User deleted successfully")

# @app.route('/user', methods=['POST'])
# def add_user():
#     if request.is_json:
#         data = request.get_json()  # Get data as JSON
#         uid = data['uid']
#         name = data['name']
#         email = data['email']
#         db = mysql.connection
        
#         # Create a cursor from the database connection
#         cur = db.cursor()
#         # SQL query string
#         sql = "INSERT INTO users (uid, name, email) VALUES (%s, %s, %s)"
#         # Execute the SQL command
#         cur.execute(sql, (uid, name, email))
#         # Commit the changes in the database
#         db.commit()
#         # Close the cursor
#         cur.close()
#         # Insert into database or process data here
#         return jsonify(message="User added successfully"), 201
#     else:
#         return jsonify(error="Error in submission"), 400
    
# @app.route('/users', methods=['GET'])
# def get_users():
#     cur = mysql.connection.cursor()
#     cur.execute("SELECT uid, name, email FROM users")
#     users = cur.fetchall()
#     cur.close()

#     user_dicts = [
#         {'uid': user[0], 'name': user[1], 'email': user[2]}
#         for user in users
#     ]
#     return jsonify(user_dicts), 200

# @app.route('/user/<int:uid>', methods=['DELETE'])
# def delete_user(uid):
#     cur = mysql.connection.cursor()
#     cur.execute("DELETE FROM users WHERE uid = %s", (uid,))
#     mysql.connection.commit()
#     cur.close()

#     return jsonify(message="User deleted successfully")

if __name__ == '__main__':
 app.run(debug=True)