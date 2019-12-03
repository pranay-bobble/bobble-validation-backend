import datetime
import logging
import os
import socket
from sqlalchemy.sql import func

from flask import Flask, request, jsonify, make_response
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
    username = db.Column(db.String(255), unique=True, index=True)
    password = db.Column(db.String(255))
    full_name = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime(), nullable=False, server_default=func.now())
    deactivated = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(self, username, password, full_name):
        self.username = username
        self.password = password
        self.full_name = full_name

@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.get_json()

    if not data or not data['username'] or not data['password'] or not data['full_name']:
        return make_response(jsonify(status="error", errorDescription="Details not fulfilled"), 400)

    user = User.query.filter_by(username=data['username']).first()

    if user:
        return make_response(jsonify(status="error", errorDescription="Please change username"), 400)

    hashed_password = generate_password_hash(data['password'], method='sha256')

    new_user = User(data['username'], hashed_password, data['full_name'])
    db.session.add(new_user)
    db.session.commit()

    return make_response(jsonify(status="success", message="New user created with username {}".format(data['username'])), 200)

# if __name__ == '__main__':
#     # This is used when running locally. Gunicorn is used to run the
#     # application on Google App Engine. See entrypoint in app.yaml.
#     app.run(host='127.0.0.1', port=8080, debug=True)