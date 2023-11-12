from flask import Flask, request, g, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from flask_jwt_extended import create_access_token, JWTManager, get_jwt, get_jwt_identity, unset_jwt_cookies, jwt_required, decode_token
import sqlite3
import os
import json
from DataBaseMethods import DataBase
from datetime import datetime, timedelta, timezone

DATABASE = '/tmp/flsite.db'
SECRET_KEY = 'fefevergerttert3454534t6erge'
DEBUG = True
MAX_CONTENT_LENGTH = 1024 * 1024 * 3


app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "sample_key"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config.from_object(__name__)
app.config.from_object(Config)
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'flsite.db')))
jwt = JWTManager(app)


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

@app.after_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            data = response.get_json()
            if type(data) is dict:
                data["access_token"] = access_token
                response.data = json.dumps(data)
        return response
    except (RuntimeError, KeyError):
        return response


@app.route('/')
def index():
    response_body = {
        "hello": "World",
        "test": "success"
    }

    return response_body


@app.route('/login', methods=["POST"])
def login():
    user_email = request.json.get("email", None)
    user = dbase.get_user_by_email(user_email)
    if user and check_password_hash(user['psw'], request.json.get("psw", None)):
        access_token = create_access_token(identity=user_email)
        response = {"access_token": access_token}
        return response
    else:
        response = {"status": "Неверный логин или пароль"}
        return response

@app.route("/register", methods=["POST"])
def register():
    if request.method == "POST":
        user_login = request.json.get("login", None)
        user_mail = request.json.get("email", None)
        user_psw = request.json.get("psw", None)
        user_psw2 = request.json.get("psw2", None)
        if len(user_login) > 4 and len(user_mail) > 4 and len(user_psw) > 4 and user_psw == user_psw2:
            psw_hash = generate_password_hash(user_psw)
            if dbase.add_new_user(user_login, user_mail, psw_hash):
                return {"status": "вы зарегались"}
            else:
                return {"status": "ошибка БД или пользователь уже есть"}
        else:
            return {"status": "неверно заполнены поля"}

@app.route("/logout", methods=["POST"])
def logout():
    response = jsonify({"status": "вы вышли из системы"})
    unset_jwt_cookies(response)
    return response


@app.route('/profile', methods=["POST"])
@jwt_required()
def my_profile():
    jwtr = request.headers.get('Authorization', None)
    jwtr = str.replace(str(jwtr), 'Bearer ', '')
    token = decode_token(jwtr)
    email = token["sub"]
    user = dbase.get_user_by_email(email)
    print(user)
    response_body = {
        "email": email,
        "login": user["name"]
    }

    return response_body



if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
