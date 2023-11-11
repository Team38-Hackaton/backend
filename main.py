from flask import Flask, request, g
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
    email = request.json.get("email", None)
    password = request.json.get("password", None)
    if email != "test" or password != "test":
        return {"msg": "Wrong email or password"}, 401

    access_token = create_access_token(identity=email)
    response = {"access_token": access_token}
    return response



if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
