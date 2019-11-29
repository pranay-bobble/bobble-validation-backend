import datetime
import logging
import os
import random
import socket
import json
from sqlalchemy.sql import func

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy import not_, or_, and_
from sqlalchemy.orm import load_only
import sqlalchemy
from functools import wraps
import jwt
from datetime import datetime, timedelta

app = Flask(__name__)

# [START gae_flex_mysql_app]
# Environment variables are defined in app.yaml.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_DATABASE_URI']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
TASK_REVIEW_MAX_COUNT = 3
MIN_DAYS_BEFORE_FETCHING_TASK_FOR_REVIEW = 1
# Use BUCKET_NAME or the project default bucket.
BUCKET_NAME = os.environ['BUCKET_NAME']

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
            user_id = data['id']
        except:
            return jsonify({'message' : 'Token is invalid!'}), 401

        return f(user_id, *args, **kwargs)

    return decorated

class Tasks(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True, index=True)
    source_file = db.Column(db.String(255))
    num_reviews = db.Column(db.Integer, default='0')
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    overall_score = db.Column(db.DECIMAL(scale=5, precision=3), nullable=True)

    @hybrid_property
    def review_completed(self):
        if (self.overall_score is not None) and (self.num_reviews >= TASK_REVIEW_MAX_COUNT):
            return True
        return False

    @hybrid_method
    def has_completed_review(self):
        return (self.overall_score.isnot(None)) & (self.num_reviews >= TASK_REVIEW_MAX_COUNT)

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



class Reviews(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True, index=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    started_at = db.Column(db.DateTime(), nullable=False, server_default=func.now())
    completed_at = db.Column(db.DateTime(), nullable=True)
    score = db.Column(db.DECIMAL(scale=5, precision=3), nullable=True)

    @hybrid_method
    def is_complete(self):
        return self.score.isnot(None)

def get_existing_task_undergoing_review(user_id):
    review = Reviews.query.filter(
        Reviews.user_id == user_id,
        Reviews.score.is_(None)
    ).first()

    if review is None:
        return None
    
    task = Tasks.query.filter(
        Tasks.id == review.task_id,
    ).first()

    return task

def remove_duplicate_reviews(user_id, task_id):
    reviews = Reviews.query.filter(
        Reviews.user_id == user_id,
        Reviews.task_id == task_id,
        not_(Reviews.is_complete())
    ).all()

    if reviews is not None and len(reviews) > 0:
        for review in reviews:
            db.session.delete(review)

        db.session.commit()

def initialise_review(user_id, task_id):
    review = Reviews()
    review.task_id = task_id
    review.user_id = user_id
    db.session.add(review)
    db.session.commit()

def get_task_for_review(user_id):
    existing_task = get_existing_task_undergoing_review(user_id)
    if existing_task is not None:
        if not existing_task.review_completed:
            return existing_task
        remove_duplicate_reviews(user_id, existing_task.id)

    tasks_reviewed = db.session.query(Reviews.task_id).distinct().filter(
        Reviews.user_id == user_id,
        Reviews.is_complete()
    ).subquery('tasks_reviewed')

    tasks_undergoing_review = db.session.query(Reviews.task_id).distinct().filter(
        not_(Reviews.is_complete()),
        Reviews.started_at > (datetime.now() - timedelta(days=MIN_DAYS_BEFORE_FETCHING_TASK_FOR_REVIEW))
    ).subquery('tasks_undergoing_review')

    task_ids = Tasks.query.options(load_only(*['id'])).filter(
        not_(Tasks.has_completed_review()),
        not_(Tasks.id.in_(tasks_undergoing_review)),
        not_(Tasks.id.in_(tasks_reviewed)),
    ).all()

    task_id = random.choice(task_ids).id

    task = Tasks.query.filter_by(id=task_id).first()

    if task is not None:
        initialise_review(user_id, task.id)

    return task


@app.route('/get_tasks', methods=['GET'])
@token_required
def get_tasks(user_id):

    task = get_task_for_review(user_id)
    input_file_path = "https://storage.googleapis.com/{}/image-segmentation/images/input/{}".format(BUCKET_NAME, task.source_file)
    output_file_path = "https://storage.googleapis.com/{}/image-segmentation/images/output/{}".format(BUCKET_NAME, task.source_file)
    return jsonify({'task_id':task.id, "input_url":input_file_path, "output_url":output_file_path})

if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
