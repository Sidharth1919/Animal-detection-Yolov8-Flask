from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from flask_pymongo import PyMongo
from werkzeug.security import check_password_hash, generate_password_hash
from bson import ObjectId
from flask import Blueprint

auth_bp = Blueprint('auth', __name__)
app = Flask(__name__)
app.config['SECRET_KEY'] = '10101'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/farmdb'

mongo = PyMongo(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

class User(UserMixin):
    def __init__(self, user_id, email):
        self.id = str(user_id)
        self.email = email

    @staticmethod
    def get(user_id):
        if not ObjectId.is_valid(user_id):
            return None
        user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)}, {'email': 1})
        if user_data:
            return User(user_data['_id'], user_data['email'])
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_document = mongo.db.users.find_one({'email': email})

        if user_document and check_password_hash(user_document['password'], password):
            user = User(user_document['_id'], user_document['email'])
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid email/password combination')

    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        existing_user = mongo.db.users.find_one({'email': email})

        if existing_user is None:
            hashed_password = generate_password_hash(password)
            mongo.db.users.insert_one({'email': email, 'password': hashed_password})
            return redirect(url_for('auth.login'))
        else:
            flash('Email already exists')

    return render_template('signup.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))