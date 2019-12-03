import datetime
import logging
import os
import socket
from sqlalchemy.sql import func

from flask import Flask, request, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy import not_, or_, and_
import sqlalchemy
from functools import wraps
from datetime import datetime, timedelta
import jwt

app = Flask(__name__)

# [START gae_flex_mysql_app]
# Environment variables are defined in app.yaml.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_DATABASE_URI']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PUBLIC_KEY'] = os.environ['PUBLIC_KEY'].replace('\\n', '\n')

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
            data = jwt.decode(token, app.config['PUBLIC_KEY'], algorithms='RS256')
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

    @hybrid_property
    def review_completed(self):
        if (self.overall_score is not None) and (self.num_reviews >= TASK_REVIEW_MAX_COUNT):
            return True
        return False

    @hybrid_method
    def has_completed_review(self):
        return (self.overall_score.isnot(None)) & (self.num_reviews >= TASK_REVIEW_MAX_COUNT)

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

def user_review_already_submitted(user_id, task_id):
    count = Reviews.query.filter(
        Reviews.user_id == user_id,
        Reviews.task_id == task_id,
        Reviews.is_complete()
    ).count()
    return count

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

def get_task_details(task_id):
    return Tasks.query.filter(Tasks.id == task_id).first()

def update_task_review(task_id, user_id, score):

    review = Reviews.query.filter(
        Reviews.user_id == user_id,
        Reviews.task_id == task_id,
    ).first()

    review.task_id = task_id
    review.user_id = user_id
    review.score = score
    review.completed_at = datetime.now()
    db.session.commit()

def update_overall_score(task_id, score):
    task = Tasks.query.filter(
        Tasks.id == task_id,
    ).first()
    if task.num_reviews == 0:
        task.overall_score = score
    else:
        task.overall_score = (task.overall_score + score)/2
    task.num_reviews += 1
    db.session.commit()

@app.route('/submit_review/<task_id>', methods=['PUT'])
@token_required
def submit_review(current_user_id, task_id):

    if user_review_already_submitted(current_user_id, task_id):
        remove_duplicate_reviews(current_user_id, task_id)
        return make_response(jsonify(status="error", errorDescription="reSubmission"), 400)

    task = get_task_details(task_id)

    request_data = request.get_json()
    review_score = request_data['review_score']
    if review_score not in range(0,11):
        return make_response(jsonify(status="error", errorDescription="incorrectData"), 400)


    update_task_review(task_id, current_user_id, review_score)

    update_overall_score(task_id, review_score)

    return make_response(jsonify(status="success"), 200)


# if __name__ == '__main__':
#     # This is used when running locally. Gunicorn is used to run the
#     # application on Google App Engine. See entrypoint in app.yaml.
#     app.run(host='127.0.0.1', port=8080, debug=True)

