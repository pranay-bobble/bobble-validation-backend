import datetime
import logging
import os
import socket
from sqlalchemy.sql import func

from flask import Flask, request, jsonify, make_response
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy

app = Flask(__name__)

# [START gae_flex_mysql_app]
# Environment variables are defined in app.yaml.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_DATABASE_URI']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, index=True)
    username = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    full_name = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime(), nullable=False, server_default=func.now())
    deactivated = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(self, username, password, full_name):
        self.username = username
        self.password = password
        self.full_name = full_name

@app.route('/log_in', methods=['POST'])
def log_in():
    data = request.get_json()
    if not data or not data['username'] or not data['password']:
        return make_response('Details not fulfilled', 401, {'WWW-Authenticate' : 'Basic realm="Details required!"'})

    user = User.query.filter_by(username=data['username']).first()

    if not user:
        return make_response('Invalid user', 401, {'WWW-Authenticate' : 'Basic realm="Invalid user!"'})

    if (user.deactivated):
        return make_response('User disabled', 401, {'WWW-Authenticate' : 'Basic realm="User disabled!"'})

    if check_password_hash(user.password, data['password']):
        token = jwt.encode({'username' : user.username, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
        return jsonify({'token':token.decode('UTF-8')})
    return make_response('Wrong password', 401, {'WWW-Authenticate' : 'Basic realm="Wrong password!"'})


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)

