from flask import Flask, request
from config import Config
from flask_jwt_extended import create_access_token, JWTManager


app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "sample_key"
app.config.from_object(__name__)
app.config.from_object(Config)
jwt = JWTManager(app)


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
