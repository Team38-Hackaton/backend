import os
import json
import sqlite3
from datetime import datetime, timedelta, timezone

from flask import Flask, request, g, jsonify
from flask_cors import CORS
# from config import Config
from flask_jwt_extended import create_access_token, JWTManager, get_jwt, get_jwt_identity, unset_jwt_cookies, \
    jwt_required
from werkzeug.security import generate_password_hash, check_password_hash

from DataBaseMethods import DataBase

DATABASE = '/tmp/flsite.db'
SECRET_KEY = 'Sample_Key'
DEBUG = False
MAX_CONTENT_LENGTH = 1024 * 1024 * 3

app = Flask(__name__)
jwt = JWTManager(app)
cors = CORS(app)
app.config["JWT_SECRET_KEY"] = "sample_key"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=8)
app.config.from_object(__name__)
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'flsite.db')))
app.config['CORS_HEADERS'] = 'Content-Type'


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
        target_timestamp = datetime.timestamp(now + timedelta(days=1))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            data = response.get_json()
            if type(data) is dict:
                data["access_token"] = access_token
                response.data = json.dumps(data)
        return response
    except (RuntimeError, KeyError):
        return response


@app.route('/', methods=["GET"])
@jwt_required()
def index():
    email = get_jwt_identity()
    user = dbase.get_user_by_email(email)

    response_body = {
        "email": email,
        "name": user["name"]
    }

    return response_body


@app.route('/login', methods=["POST"])
def login():
    user_email = request.json.get("email", None)
    user = dbase.get_user_by_email(user_email)
    if user and check_password_hash(user['psw'], request.json.get("psw", None)):
        access_token = create_access_token(identity=user_email)
        response = {"access_token": access_token,
                    "email": user_email,
                    "name": user["name"]
                    }, 200
        return response
    else:
        response = {"status": "неверный логин или пароль"}, 401
        return response


@app.route("/register", methods=["POST"])
def register():
    if request.method == "POST":
        user_login = request.json.get("name", None)
        user_mail = request.json.get("email", None)
        user_psw = request.json.get("psw", None)

        if len(user_login) > 1 and len(user_mail) > 4 and len(user_psw) > 4:
            psw_hash = generate_password_hash(user_psw)
            if dbase.add_new_user(user_login, user_mail, psw_hash):
                return {"status": "вы зарегистрировались"}, 200
            else:
                return {"status": "ошибка БД или пользователь уже есть"},
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
    email = get_jwt_identity()
    user = dbase.get_user_by_email(email)

    response_body = {
        "email": email,
        "name": user["name"]
    }

    return response_body


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)
