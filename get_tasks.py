import datetime
import logging
import os
import socket
from sqlalchemy.sql import func

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
from functools import wraps
import jwt

app = Flask(__name__)

# [START gae_flex_mysql_app]
# Environment variables are defined in app.yaml.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_DATABASE_URI']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

db = SQLAlchemy(app)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message' : 'Token is missing!'}), 401

        try: 
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user_id = data['id']
        except:
            return jsonify({'message' : 'Token is invalid!'}), 401

        return f(current_user_id, *args, **kwargs)

    return decorated

class Tasks(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True, index=True)
    source_file = db.Column(db.String(255))
    num_reviews = db.Column(db.Integer, default='0')
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    overall_score = db.Column(db.DECIMAL(scale=5, precision=3), nullable=True)

@app.route('/get_tasks', methods=['GET'])
@token_required
def get_tasks(current_user_id):
    tasks = Tasks.query.order_by(sqlalchemy.asc(Tasks.id)).limit(10)
    results = [
        'Id: {} Img_Name: {}'.format(x.id, x.source_file)
        for x in tasks]
    results.append("CURRENT USER ID {}".format(current_user_id))

    output = 'Last 10 visits:\n{}'.format('\n'.join(results))

    return output, 200, {'Content-Type': 'text/plain; charset=utf-8'}

if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
