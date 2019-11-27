import datetime
import logging
import os
import socket
from sqlalchemy.sql import func

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy

app = Flask(__name__)

# [START gae_flex_mysql_app]
# Environment variables are defined in app.yaml.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_DATABASE_URI']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Tasks(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True, index=True)
    source_file = db.Column(db.String(255))
    num_reviews = db.Column(db.Integer, default='0')
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    overall_score = db.Column(db.DECIMAL(scale=5, precision=3), nullable=True)

@app.route('/get_tasks')
def get_tasks():
    tasks = Tasks.query.order_by(sqlalchemy.asc(Tasks.id)).limit(10)
    results = [
        'Id: {} Img_Name: {}'.format(x.id, x.source_file)
        for x in tasks]

    output = 'Last 10 visits:\n{}'.format('\n'.join(results))

    return output, 200, {'Content-Type': 'text/plain; charset=utf-8'}

if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
