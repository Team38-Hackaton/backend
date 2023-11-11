from flask import Flask, request, g
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from flask_jwt_extended import create_access_token, JWTManager
import sqlite3
import os
from DataBaseMethods import DataBase
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

DATABASE = '/tmp/flsite.db'
SECRET_KEY = 'fefevergerttert3454534t6erge'
DEBUG = True
MAX_CONTENT_LENGTH = 1024 * 1024 * 3


app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "sample_key"
app.config.from_object(__name__)
app.config.from_object(Config)
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'flsite.db')))
jwt = JWTManager(app)
login_manager = LoginManager(app)


def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def create_db():
    db = connect_db()
    with app.open_resource('sq_db.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    db.close()

def get_db():
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    return g.link_db


dbase = None
@app.before_request
def before_request():
    global dbase
    db = get_db()
    dbase = DataBase(db)

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'link_db'):
        g.link_db.close()

@app.route('/')
def index():
    response_body = {
        "hello": "World",
        "test": "success"
    }

    return response_body


@app.route('/login', methods=["POST"])
def login():
    if request.method == "POST":
        user = dbase.get_user_by_email(request.json.get("email", None))
        if user and user['psw'] == request.json.get("psw", None):
            return {"status": "вы вошли"}
        else:
            return {"status": "неверный логин или пароль"}

@app.route("/register", methods=["POST"])
def register():
    if request.method == "POST":
        user_login = request.json.get("login", None)
        user_mail = request.json.get("email", None)
        user_psw = request.json.get("psw", None)
        user_psw2 = request.json.get("psw2", None)
        if len(user_login) > 4 and len(user_mail) > 4 and len(user_psw) > 4 and user_psw == user_psw2:
            if dbase.add_new_user(user_login, user_mail, user_psw):
                return {"status": "вы зарегались"}
            else:
                return {"status": "ошибка БД или пользователь уже есть"}
        else:
            return {"status": "неверно заполнены поля"}


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
