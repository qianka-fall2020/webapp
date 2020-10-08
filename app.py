import json

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import Schema, fields

import uuid
import time
import MySQLdb
from flask_httpauth import HTTPBasicAuth
import bcrypt
import pickle
from datetime import datetime

# def password_validator(passw):
#     if len(passw) < 9:#length >=8
#         return False
#     if not bool(re.search(r'\d', passw)):#contains digits
#         return False
#     if not bool(re.search(r'[a-zA-Z]', passw)):#conatins letters
#         return False
#     return True
from helper import password_validator
from sqlalchemy import JSON
from sqlalchemy.orm import relationship, backref

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost/assign1'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Init db
db = SQLAlchemy(app)
# Init ma
ma = Marshmallow(app)

auth = HTTPBasicAuth()
salt = bcrypt.gensalt()
pw = ""


@auth.verify_password
def verify_password(username, password):
    global pw
    user = User.query.filter_by(username=username).first()
    if user and bcrypt.checkpw(password.encode('utf8'), user.password.encode('utf8')):
        return username


# User Class/Model
class User(db.Model):
    id = db.Column(db.String(200), primary_key=True)
    first_name = db.Column(db.String(200))
    last_name = db.Column(db.String(200))
    username = db.Column(db.String(200))
    password = db.Column(db.String(200))
    account_created = db.Column(db.String(200))
    account_updated = db.Column(db.String(200))

    def __init__(self, first_name, last_name, username, password, account_created, account_updated):
        self.id = uuid.uuid4()
        self.first_name = first_name
        self.last_name = last_name
        self.password = password
        self.username = username
        self.account_created = account_created
        self.account_updated = account_updated


# User Schema
class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'username', 'account_created', 'account_updated')


# Init schema
user_schema = UserSchema()

questcat = db.Table('questcat',
                    db.Column('question', db.String(200), db.ForeignKey('question.question_id'), primary_key=True),
                    db.Column('category', db.String(200), db.ForeignKey('category.category_id'), primary_key=True)
                    # db.Column('answer', db.String(200), db.ForeignKey('answer.answer_id'), primary_key=True)
                    )

questans = db.Table('questans',
                    db.Column('question', db.String(200), db.ForeignKey('question.question_id'), primary_key=True),
                    db.Column('answer', db.String(200), db.ForeignKey('answer.answer_id'), primary_key=True)
                    )


# Answer Class/Model
class Answer(db.Model):
    answer_id = db.Column(db.String(200), primary_key=True)
    question_id = db.Column(db.String(200))
    created_timestamp = db.Column(db.String(200))
    updated_timestamp = db.Column(db.String(200))
    user_id = db.Column(db.String(200), db.ForeignKey('user.id'))
    # user = relationship("User", backref=backref("user", lazy="dynamic"))
    answer_text = db.Column(db.String(200))

    def __init__(self, question_id, created_timestamp, updated_timestamp, user_id, answer_text):
        self.answer_id = uuid.uuid4()
        self.question_id = question_id
        self.created_timestamp = created_timestamp
        self.updated_timestamp = updated_timestamp
        self.user_id = user_id
        self.answer_text = answer_text


# Answer Schema
class AnswerSchema(ma.Schema):
    class Meta:
        fields = ('answer_id', 'question_id', 'created_timestamp', 'updated_timestamp', 'user_id', 'answer_text')


# Init schema
answer_schema = AnswerSchema()


# Category Class/Model
class Category(db.Model):
    category_id = db.Column(db.String(200), primary_key=True)
    category = db.Column(db.String(400))

    def __init__(self, category):
        self.category_id = uuid.uuid4()
        self.category = category


# Category Schema
class CategorySchema(ma.Schema):
    class Meta:
        fields = ('category_id', 'category')


# Init schema
Category_schema = CategorySchema()


# Question Class/Model
class Question(db.Model):
    question_id = db.Column(db.String(200), primary_key=True)
    created_timestamp = db.Column(db.String(200))
    updated_timestamp = db.Column(db.String(200))
    user_id = db.Column(db.String(200), db.ForeignKey('user.id'))
    # user = relationship("User", backref=backref("user", uselist=False))
    question_text = db.Column(db.String(200))
    categories = db.relationship("Category", secondary=questcat,
                                 backref="questions", cascade='all, delete')
    answers = db.relationship("Answer", secondary=questans,
                              backref="questions", cascade='all, delete')

    def __init__(self, created_timestamp, updated_timestamp, user_id, question_text):
        self.question_id = uuid.uuid4()
        self.created_timestamp = created_timestamp
        self.updated_timestamp = updated_timestamp
        self.user_id = user_id
        self.question_text = question_text

    def serialize(self):
        return {"question_id": self.question_id,
                "created_timestamp": self.created_timestamp,
                "updated_timestamp": self.updated_timestamp,
                "user_id": self.user_id,
                "question_text": self.question_text,
                "categories": self.categories,
                "answer": self.answers}


# Question Schema
class QuestionSchema(ma.Schema):
    class Meta:
        fields = ('question_id', 'created_timestamp', 'updated_timestamp', 'user_id', 'question_text', 'categories')

    categories = fields.Nested('CategorySchema', default=[], many=True)
    answers = fields.Nested('AnswerSchema', default=[], many=True)


# Init schema
question_schema = QuestionSchema()

# db.drop_all()
db.create_all()
"""

User section

"""


# create a User
@app.route("/User", methods=["post"])
def createuser():
    # id = uuid.uuid4()
    first_name = request.json['first_name']
    last_name = request.json['last_name']
    username = request.json['username']
    password = request.json['password']
    if not password_validator(password):
        resp = jsonify("Your password must contains numbers and length >8")
        resp.status_code = 400
        return resp
    password = bcrypt.hashpw(password.encode('utf8'), salt)
    account_created = time.strftime('%Y-%m-%d %H:%M:%S')
    account_updated = time.strftime('%Y-%m-%d %H:%M:%S')
    user = User.query.filter_by(username=username).first()
    if user:
        resp = jsonify("Your email has already been registered")
        resp.status_code = 400
        return resp
    new_user = User(first_name, last_name, username, password, account_created, account_updated)
    db.session.add(new_user)
    db.session.commit()
    return user_schema.jsonify(new_user)


# get user with auth
@app.route("/User", methods=["get"])
@auth.login_required()
def getuser():
    user = User.query.filter_by(username=auth.username()).first()
    return user_schema.jsonify(user)


# get user with auth and id
@app.route("/User/<id>", methods=["get"])
def getuserById(id):
    user = User.query.filter_by(id=id).first()
    if user:
        return user_schema.jsonify(user)
    else:
        res = jsonify("Not Found")
        res.status_code = 404
        return res


# update a user
@app.route("/User", methods=["put"])
@auth.login_required()
def updateuser():
    # id = uuid.uuid4()
    first_name = request.json['first_name']
    last_name = request.json['last_name']
    username = request.json['username']
    if username != auth.username():
        resp = jsonify("You can't change your email")
        resp.status_code = 400
        return resp
    password = request.json['password']
    if not password_validator(password):
        resp = jsonify("Your password must contains numbers and length >8")
        resp.status_code = 400
        return resp
    password = bcrypt.hashpw(password.encode('utf8'), salt)
    account_updated = time.strftime('%Y-%m-%d %H:%M:%S')
    user = User.query.filter_by(username=username).first()
    user.first_name = first_name
    user.last_name = last_name
    user.password = password
    user.account_updated = account_updated
    db.session.commit()
    return user_schema.jsonify(user)


"""

Question section

"""


# get a question
@app.route("/Question/<id>", methods=["get"])
def getAQuestion(id):
    question = Question.query.filter_by(question_id=id).first()
    return question_schema.jsonify(question)


# get all questions
@app.route("/Questions", methods=["get"])
def getAllQuestions():
    questions = Question.query.all()
    result = question_schema.dump(questions)
    return jsonify(result.keys())

# Update a Question
@app.route('/Question/<id>', methods=['put'])
@auth.login_required()
def updatequestion(id):
    updated_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    user = User.query.filter_by(username=auth.username()).first()
    user_id = user.id
    temp = Question.query.filter_by(user_id=user_id).first()
    if not temp:
        res = jsonify("You are not authorized to update or delete this question!")
        res.status_code = 401
        return res
    question = Question.query.filter_by(question_id=id).first()
    if not question:
        res = jsonify("Can't find the question")
        res.status_code = 404
        return res
    question.question_text = request.json['question_text']
    categories = request.json['categories'][0]
    categories = categories.get('category')
    new_category = Category(categories)
    if not Category.query.filter_by(category=categories).first():
        db.session.commit()
    question.categories.append(new_category)
    question.updated_timestamp = updated_timestamp
    db.session.commit()
    return question_schema.jsonify(question)

# Delete a Question
@app.route('/Question/<id>', methods=['delete'])
@auth.login_required()
def deletequestion(id):
    user = User.query.filter_by(username=auth.username()).first()
    user_id = user.id
    temp = Question.query.filter_by(user_id=user_id).first()
    if not temp:
        res = jsonify("You are not authorized to update or delete this question!")
        res.status_code = 401
        return res
    question = Question.query.filter_by(question_id=id).first()
    if not question:
        res = jsonify("Can't find the question")
        res.status_code = 404
        return res
    db.session.delete(question)
    question.categories.clear()
    question.answers.clear()
    db.session.commit()
    return jsonify("question has been deleted")


# Create a Question
@app.route('/Question', methods=['POST'])
@auth.login_required()
def add_question():
    created_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    updated_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    user = User.query.filter_by(username=auth.username()).first()
    user_id = user.id
    question_text = request.json['question_text']
    categories = request.json['categories'][0]
    categories = categories.get('category')
    new_category = Category(categories)
    if not Category.query.filter_by(category=categories).first():
        db.session.commit()
    new_question = Question(created_timestamp, updated_timestamp, user_id, question_text)
    new_question.categories.append(new_category)
    db.session.add(new_question)
    db.session.commit()
    return question_schema.jsonify(new_question)

"""

Answer section

"""

# delete a Answer
@app.route('/Question/<string_id>/answer/<id>', methods=['delete'])
@auth.login_required()
def delete_question(string_id, id):
    user = User.query.filter_by(username=auth.username()).first()
    user_id = user.id
    answer = Answer.query.filter_by(question_id=string_id, answer_id=id, user_id=user_id).first()
    if not answer:
        res = jsonify("You are not authorized to update or delete this answer!")
        res.status_code = 401
        return res
    db.session.delete(answer)
    db.session.commit()
    return jsonify("question has been deleted")

# update a Answer
@app.route('/Question/<string_id>/answer/<id>', methods=['put'])
@auth.login_required()
def update_question(string_id, id):

    updated_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    user = User.query.filter_by(username=auth.username()).first()
    user_id = user.id
    answer = Answer.query.filter_by(question_id=string_id, answer_id=id, user_id=user_id).first()
    if not answer:
        res = jsonify("You are not authorized to update or delete this answer!")
        res.status_code = 401
        return res
    answer.answer_text = request.json['answer_text']
    answer.updated_timestamp= updated_timestamp
    db.session.commit()
    return answer_schema.jsonify(answer)

# Answer a Answer
@app.route('/Question/<string_id>/answer', methods=['POST'])
@auth.login_required()
def answer_question(string_id):
    created_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    updated_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    user = User.query.filter_by(username=auth.username()).first()
    user_id = user.id
    answer_text = request.json['answer_text']

    new_answer = Answer(string_id, created_timestamp, updated_timestamp, user_id, answer_text)

    db.session.add(new_answer)
    db.session.commit()
    return answer_schema.jsonify(new_answer)


# Get a Question's Answer
@app.route('/Question/<string_id>/answer/<id>', methods=['get'])
def getquestionsanswer(string_id, id):
    answer = Answer.query.filter_by(question_id=string_id, answer_id=id).first()
    return answer_schema.jsonify(answer)


if __name__ == "__main__":
    app.run(host="localhost", port=3000, debug=True)
