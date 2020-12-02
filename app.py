from flask import Flask, request, jsonify, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import Schema, fields

import uuid
import time
from flask_httpauth import HTTPBasicAuth
import bcrypt
import logging
import boto3
import os
import statsd
import logging
from dotenv import load_dotenv,find_dotenv


from botocore.exceptions import ClientError

from helper import password_validator

load_dotenv(find_dotenv())

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Init db
db = SQLAlchemy(app)
# Init ma
ma = Marshmallow(app)
std = statsd.StatsClient('localhost', 8125)
logging.basicConfig(format='%(process)d-%(levelname)s-%(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='/opt/myapp.log',
                    filemode='w')
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
questfil = db.Table('questfil',
                    db.Column('question', db.String(200), db.ForeignKey('question.question_id'), primary_key=True),
                    db.Column('file', db.String(200), db.ForeignKey('file.file_id'), primary_key=True)
                    )

answerfil = db.Table('answerfil',
                     db.Column('answer', db.String(200), db.ForeignKey('answer.answer_id'), primary_key=True),
                     db.Column('file', db.String(200), db.ForeignKey('file.file_id'), primary_key=True)
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
    files = db.relationship("File", secondary=answerfil,
                            backref="answers", cascade='all, delete')

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
        fields = (
            'answer_id', 'question_id', 'created_timestamp', 'updated_timestamp', 'user_id', 'answer_text', 'files')

    files = fields.Nested('FileSchema', default=[], many=True)


# Init schema
answer_schema = AnswerSchema()


# File Class/Model
class File(db.Model):
    file_name = db.Column(db.String(200))
    s3_object_name = db.Column(db.String(200))
    file_id = db.Column(db.String(200), primary_key=True)
    created_date = db.Column(db.String(200))

    def __init__(self, file_name, s3_object_name, created_date):
        self.file_name = file_name
        self.s3_object_name = s3_object_name
        self.file_id = uuid.uuid4()
        self.created_date = created_date


# Answer Schema
class FileSchema(ma.Schema):
    class Meta:
        fields = ('file_name', 's3_object_name', 'file_id', 'created_date')


# Init schema
file_schema = FileSchema()


# Category Class/Model
class Category(db.Model):
    category_id = db.Column(db.String(200), primary_key=True)
    category = db.Column(db.String(400))

    def __init__(self, category):
        self.category_id = uuid.uuid4()
        self.category = category

    def serialize(self):
        return {"category_id": self.category_id,
                "category": self.category
                }


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
    files = db.relationship("File", secondary=questfil,
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
                "categories": self.categories.serialze(),
                "answer": self.answers}


# Question Schema
class QuestionSchema(ma.Schema):
    class Meta:
        fields = (
            'question_id', 'created_timestamp', 'updated_timestamp', 'user_id', 'question_text', 'categories',
            'answers',
            'files')

    categories = fields.Nested('CategorySchema', default=[], many=True)
    answers = fields.Nested('AnswerSchema', default=[], many=True)
    files = fields.Nested('FileSchema', default=[], many=True)


# Init schema
question_schema = QuestionSchema()

# db.drop_all()
db.create_all()
"""

User section

"""

@app.route("/", methods=["get"])
def default():
    std.incr('serviceCall')
    res = jsonify("it's working")
    res.status_code = 200
    return res


# create a User
@app.route("/User", methods=["post"])
def createuser():
    start = time.time()
    std.incr('serviceCall')
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
    query_time = time.time()
    user = User.query.filter_by(username=username).first()
    qtd = int((time.time() - query_time) * 1000)
    std.timing('Query Call', qtd)
    if user:
        resp = jsonify("Your email has already been registered")
        resp.status_code = 400
        return resp
    new_user = User(first_name, last_name, username, password, account_created, account_updated)
    db.session.add(new_user)
    db.session.commit()
    dt = int((time.time() - start) * 1000)
    std.timing('API Call', dt)
    logging.info('create user successfully')
    return user_schema.jsonify(new_user)


# get user with auth
@app.route("/User", methods=["get"])
@auth.login_required()
def getuser():
    std.incr('serviceCall')
    start = time.time()
    query_time = time.time()
    user = User.query.filter_by(username=auth.username()).first()
    qtd = int((time.time() - query_time) * 1000)
    std.timing('Query Call', qtd)
    dt = int((time.time() - start) * 1000)
    std.timing('API Call', dt)
    return user_schema.jsonify(user)


# get user with auth and id
@app.route("/User/<id>", methods=["get"])
def getuserById(id):
    std.incr('serviceCall')
    start = time.time()
    query_time = time.time()
    user = User.query.filter_by(id=id).first()
    qtd = int((time.time() - query_time) * 1000)
    std.timing('Query Call', qtd)
    dt = int((time.time() - start) * 1000)
    std.timing('API Call', dt)
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
    std.incr('serviceCall')
    # id = uuid.uuid4()
    start = time.time()
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
    query_time = time.time()
    user = User.query.filter_by(username=username).first()
    qtd = int((time.time() - query_time) * 1000)
    std.timing('Query Call', qtd)
    user.first_name = first_name
    user.last_name = last_name
    user.password = password
    user.account_updated = account_updated
    db.session.commit()
    dt = int((time.time() - start) * 1000)
    std.timing('API Call', dt)
    return user_schema.jsonify(user)


"""

Question section

"""


# get a question
@app.route("/Question/<id>", methods=["get"])
def getAQuestion(id):
    std.incr('serviceCall')
    start = time.time()
    query_time = time.time()
    question = Question.query.filter_by(question_id=id).first()
    qtd = int((time.time() - query_time) * 1000)
    std.timing('Query Call1', qtd)

    query_time1 = time.time()
    answer = Answer.query.filter_by(question_id=id).first()
    qtd1 = int((time.time() - query_time1) * 1000)
    std.timing('Query Call2', qtd1)

    if answer:
        question.answers.append(answer)
    db.session.commit()
    dt = int((time.time() - start) * 1000)
    std.timing('API Call', dt)
    return question_schema.jsonify(question)


# get all questions
@app.route("/Questions", methods=["get"])
def getAllQuestions():
    std.incr('serviceCall')
    start = time.time()
    query_time = time.time()
    questions = Question.query.order_by(Question.created_timestamp).all()
    qtd = int((time.time() - query_time) * 1000)
    std.timing('Query Call', qtd)
    dt = int((time.time() - start) * 1000)
    std.timing('API Call', dt)
    return question_schema.jsonify(questions[0])


# Update a Question with a file
@app.route('/Question/<id>/file', methods=['post'])
@auth.login_required()
def postfile(id):
    std.incr('serviceCall')
    start = time.time()
    f = request.files['file']
    # if f.filename.rsplit('.', 1)[1].lower() not in
    created_date = time.strftime('%Y-%m-%d %H:%M:%S')
    s3_time = time.time()
    s3_resource = boto3.resource('s3', aws_access_key_id=os.environ.get('ACCESS_KEY'),
                                 aws_secret_access_key=os.environ.get('SECRETE_KEY'))
    my_bucket = s3_resource.Bucket('webapp.kai.qian')
    my_bucket.Object(f.filename).put(Body=f)
    s3td = int((time.time() - s3_time) * 1000)
    std.timing('S3 Call', s3td)
    new_file = File(f.filename, f.filename, created_date)
    query_time = time.time()
    question = Question.query.filter_by(question_id=id).first()
    qtd = int((time.time() - query_time) * 1000)
    std.timing('Query Call', qtd)
    if question:
        question.files.append(new_file)
        db.session.commit()
    else:
        res = jsonify("Not found the question")
        res.status_code = 404
        return res

    dt = int((time.time() - start) * 1000)
    std.timing('API Call', dt)
    return file_schema.jsonify(new_file)


# Update a Question
@app.route('/Question/<id>', methods=['put'])
@auth.login_required()
def updatequestion(id):
    std.incr('serviceCall')
    start = time.time()
    updated_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    query_time = time.time()
    user = User.query.filter_by(username=auth.username()).first()
    qtd = int((time.time() - query_time) * 1000)
    std.timing('Query Call', qtd)
    user_id = user.id
    query_time1 = time.time()
    temp = Question.query.filter_by(user_id=user_id).first()
    qtd1 = int((time.time() - query_time1) * 1000)
    std.timing('Query Call1', qtd1)

    if not temp:
        res = jsonify("You are not authorized to update or delete this question!")
        res.status_code = 401
        return res
    query_time2 = time.time()
    question = Question.query.filter_by(question_id=id).first()
    qtd2 = int((time.time() - query_time2) * 1000)
    std.timing('Query Call2', qtd2)
    if not question:
        res = jsonify("Can't find the question")
        res.status_code = 404
        return res
    question.question_text = request.json['question_text']
    categories = request.json['categories'][0]
    categories = categories.get('category')
    new_category = Category(categories)
    query_time3 = time.time()
    if not Category.query.filter_by(category=categories).first():
        db.session.commit()
    qtd3 = int((time.time() - query_time3) * 1000)
    std.timing('Query Call3', qtd3)
    question.categories.append(new_category)
    question.updated_timestamp = updated_timestamp
    db.session.commit()
    dt = int((time.time() - start) * 1000)
    std.timing('API Call', dt)
    return question_schema.jsonify(question)


# Delete a Question's file
@app.route('/Question/<question_id>/file/<file_id>', methods=['delete'])
@auth.login_required()
def deletequestionfile(question_id, file_id):
    std.incr('serviceCall')
    start = time.time()
    query_time = time.time()
    user = User.query.filter_by(username=auth.username()).first()
    qtd = int((time.time() - query_time) * 1000)
    std.timing('Query Call', qtd)
    user_id = user.id
    query_time1 = time.time()
    temp = Question.query.filter_by(user_id=user_id).first()
    qtd1 = int((time.time() - query_time1) * 1000)
    std.timing('Query Call1', qtd1)

    if not temp:
        res = jsonify("You are not authorized to update or delete this file!")
        res.status_code = 401
        return res
    query_time2 = time.time()
    question = Question.query.filter_by(question_id=question_id).first()
    qtd2 = int((time.time() - query_time2) * 1000)
    std.timing('Query Call2', qtd2)
    if not question:
        res = jsonify("Can't find the question")
        res.status_code = 404
        return res
    query_time3 = time.time()
    file = File.query.filter_by(file_id=file_id).first()
    qtd3 = int((time.time() - query_time3) * 1000)
    std.timing('Query Call3', qtd3)
    if not file:
        return jsonify("Can't find the file")
    s3_time = time.time()
    s3_resource = boto3.resource('s3', aws_access_key_id=os.environ.get('ACCESS_KEY'),
                                 aws_secret_access_key=os.environ.get('SECRETE_KEY'))
    my_bucket = s3_resource.Bucket('webapp.kai.qian')
    my_bucket.Object(file.file_name).delete()
    s3td = int((time.time() - s3_time) * 1000)
    std.timing('S3 Call', s3td)
    question.files.clear()
    db.session.delete(file)
    db.session.commit()
    dt = int((time.time() - start) * 1000)
    std.timing('API Call', dt)
    return jsonify("file has been deleted")


# Delete a Question
@app.route('/Question/<id>', methods=['delete'])
@auth.login_required()
def deletequestion(id):
    std.incr('serviceCall')
    start = time.time()
    query_time = time.time()
    user = User.query.filter_by(username=auth.username()).first()
    qtd = int((time.time() - query_time) * 1000)
    std.timing('Query Call', qtd)
    user_id = user.id
    query_time1 = time.time()
    temp = Question.query.filter_by(user_id=user_id).first()
    qtd1 = int((time.time() - query_time1) * 1000)
    std.timing('Query Call1', qtd1)
    if not temp:
        res = jsonify("You are not authorized to update or delete this question!")
        res.status_code = 401
        return res
    query_time2 = time.time()
    question = Question.query.filter_by(question_id=id).first()
    qtd2 = int((time.time() - query_time2) * 1000)
    std.timing('Query Call2', qtd2)
    if not question:
        res = jsonify("Can't find the question")
        res.status_code = 404
        return res
    query_time3 = time.time()
    answer = Answer.query.filter_by(question_id=id).first()
    qtd3 = int((time.time() - query_time3) * 1000)
    std.timing('Query Call3', qtd3)
    if answer:
        res = jsonify("Can't delete this question")
        res.status_code = 404
        return res
    db.session.delete(question)
    question.categories.clear()
    question.answers.clear()
    db.session.commit()
    dt = int((time.time() - start) * 1000)
    std.timing('API Call', dt)
    return jsonify("question has been deleted")


# Create a Question
@app.route('/Question', methods=['POST'])
@auth.login_required()
def add_question():
    std.incr('serviceCall')
    start = time.time()
    created_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    updated_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    query_time = time.time()
    user = User.query.filter_by(username=auth.username()).first()
    qtd = int((time.time() - query_time) * 1000)
    std.timing('Query Call', qtd)
    user_id = user.id
    question_text = request.json['question_text']
    categories = request.json['categories'][0]
    categories = categories.get('category')
    categories = categories.lower()
    new_category = Category(categories)
    query_time1 = time.time()
    temp = Category.query.filter_by(category=categories).first()
    qtd1 = int((time.time() - query_time1) * 1000)
    std.timing('Query Call1', qtd1)
    # if temp:
    #     db.session.delete(temp)
    new_question = Question(created_timestamp, updated_timestamp, user_id, question_text)
    if temp:
        new_question.categories.append(temp)
    else:
        new_question.categories.append(new_category)
    # new_question.answers.append(Answer(uuid.uuid4(),created_timestamp, updated_timestamp,user_id, ""))
    db.session.add(new_question)
    db.session.commit()
    dt = int((time.time() - start) * 1000)
    std.timing('API Call', dt)
    return question_schema.jsonify(new_question)


"""

Answer section

"""


# Delete a Answer's file
@app.route('/Question/<question_id>/answer/<answer_id>/file/<file_id>', methods=['delete'])
@auth.login_required()
def deleteanswerfile(question_id, answer_id, file_id):
    std.incr('serviceCall')
    start = time.time()
    query_time = time.time()
    user = User.query.filter_by(username=auth.username()).first()
    qtd = int((time.time() - query_time) * 1000)
    std.timing('Query Call', qtd)
    user_id = user.id
    query_time1 = time.time()
    temp = Question.query.filter_by(user_id=user_id).first()
    qtd1 = int((time.time() - query_time1) * 1000)
    std.timing('Query Call1', qtd1)

    if not temp:
        res = jsonify("You are not authorized to update or delete this file!")
        res.status_code = 401
        return res
    query_time2 = time.time()
    question = Question.query.filter_by(question_id=question_id).first()
    qtd2 = int((time.time() - query_time2) * 1000)
    std.timing('Query Call2', qtd2)

    if not question:
        res = jsonify("Can't find the question")
        res.status_code = 404
        return res
    query_time3 = time.time()
    answer = Answer.query.filter_by(answer_id=answer_id).first()
    qtd3 = int((time.time() - query_time3) * 1000)
    std.timing('Query Call3', qtd3)

    if not answer:
        res = jsonify("Can't find the answer")
        res.status_code = 404
        return res
    query_time4 = time.time()
    file = File.query.filter_by(file_id=file_id).first()
    qtd4 = int((time.time() - query_time4) * 1000)
    std.timing('Query Call4', qtd4)

    if not file:
        return jsonify("Can't find the file")
    s3_time = time.time()
    s3_resource = boto3.resource('s3', aws_access_key_id=os.environ.get('ACCESS_KEY'),
                                 aws_secret_access_key=os.environ.get('SECRETE_KEY'))
    my_bucket = s3_resource.Bucket('webapp.kai.qian')
    my_bucket.Object(file.file_name).delete()
    s3td = int((time.time() - s3_time) * 1000)
    std.timing('S3 Call', s3td)
    question.files.clear()
    db.session.delete(file)
    db.session.commit()
    dt = int((time.time() - start) * 1000)
    std.timing('API Call', dt)
    return jsonify("file has been deleted")


# delete a Answer
@app.route('/Question/<string_id>/answer/<id>', methods=['delete'])
@auth.login_required()
def delete_question(string_id, id):
    std.incr('serviceCall')
    start = time.time()
    query_time = time.time()
    user = User.query.filter_by(username=auth.username()).first()
    qtd = int((time.time() - query_time) * 1000)
    std.timing('Query Call', qtd)
    user_id = user.id
    query_time1 = time.time()
    answer = Answer.query.filter_by(question_id=string_id, answer_id=id, user_id=user_id).first()
    qtd1 = int((time.time() - query_time1) * 1000)
    std.timing('Query Call1', qtd1)
    sns = boto3.client('sns', region_name='us-east-1')

    question_link = 'http://prod.kqlittleapp.com/Question/'+ string_id
    response = sns.publish(
        TopicArn='arn:aws:sns:us-east-1:516274383141:SNS_Topic',
        Message="recipient={}, question_id={}, answer_id={}, answer_text={}, question_link={}".format(
            auth.username(),
            str(string_id),
            ' ',
            'answer deleted',
            question_link)
    )
    if not answer:
        res = jsonify("You are not authorized to update or delete this answer!")
        res.status_code = 401
        return res
    db.session.delete(answer)
    db.session.commit()
    dt = int((time.time() - start) * 1000)
    std.timing('API Call', dt)

    return jsonify("question has been deleted")


# update a Answer
@app.route('/Question/<string_id>/answer/<id>', methods=['put'])
@auth.login_required()
def update_question(string_id, id):
    std.incr('serviceCall')
    start = time.time()

    updated_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    query_time = time.time()
    user = User.query.filter_by(username=auth.username()).first()
    qtd = int((time.time() - query_time) * 1000)
    std.timing('Query Call', qtd)
    user_id = user.id
    query_time1 = time.time()
    answer = Answer.query.filter_by(question_id=string_id, answer_id=id, user_id=user_id).first()
    qtd1 = int((time.time() - query_time1) * 1000)
    std.timing('Query Call1', qtd1)

    if not answer:
        res = jsonify("You are not authorized to update or delete this answer!")
        res.status_code = 401
        return res
    answer.answer_text = request.json['answer_text']
    answer.updated_timestamp = updated_timestamp
    sns = boto3.client('sns',region_name='us-east-1')

    link = 'http://prod.kqlittleapp.com/Question/'+ string_id +'/answer/' + id
    response = sns.publish(
        TopicArn='arn:aws:sns:us-east-1:516274383141:SNS_Topic',
        Message="recipient={}, question_id={}, answer_id={}, answer_text={}, link={}".format(
            auth.username(),
            str(string_id),
            str(answer.answer_id),
            answer.answer_text,
            link)
    )
    db.session.commit()
    dt = int((time.time() - start) * 1000)
    std.timing('API Call', dt)

    return answer_schema.jsonify(answer)


# Answer a Answer with file
@app.route('/Question/<question_id>/answer/<answer_id>/file', methods=['POST'])
@auth.login_required()
def answer_q_withfile(question_id, answer_id):
    std.incr('serviceCall')
    start = time.time()
    f = request.files['file']
    file_name = f.filename
    created_date = time.strftime('%Y-%m-%d %H:%M:%S')

    s3_time = time.time()
    s3_resource = boto3.resource('s3', aws_access_key_id=os.environ.get('ACCESS_KEY'),
                                 aws_secret_access_key=os.environ.get('SECRETE_KEY'))
    my_bucket = s3_resource.Bucket('webapp.kai.qian')
    my_bucket.Object(f.filename).put(Body=f)
    s3td = int((time.time() - s3_time) * 1000)
    std.timing('S3 Call', s3td)

    new_file = File(file_name, file_name, created_date)
    query_time = time.time()
    answer = Answer.query.filter_by(answer_id=answer_id).first()
    qtd = int((time.time() - query_time) * 1000)
    std.timing('Query Call', qtd)

    if answer:
        answer.files.append(new_file)
        db.session.commit()
    else:
        res = jsonify("Not found the question")
        res.status_code = 404
        return res
    dt = int((time.time() - start) * 1000)
    std.timing('API Call', dt)
    return file_schema.jsonify(new_file)


# Answer a Answer
@app.route('/Question/<string_id>/answer', methods=['POST'])
@auth.login_required()
def answer_question(string_id):
    std.incr('serviceCall')
    start = time.time()
    created_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    updated_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    query_time = time.time()
    user = User.query.filter_by(username=auth.username()).first()
    qtd = int((time.time() - query_time) * 1000)
    std.timing('Query Call', qtd)

    user_id = user.id
    answer_text = request.json['answer_text']
    sns = boto3.client('sns', region_name='us-east-1')

    new_answer = Answer(string_id, created_timestamp, updated_timestamp, user_id, answer_text)
    link = 'http://prod.kqlittleapp.com/Question/'+ string_id +'/answer/'+ str(new_answer.answer_id)
    response = sns.publish(
        TopicArn='arn:aws:sns:us-east-1:516274383141:SNS_Topic',
        Message="recipient={}, question_id={}, answer_id={}, answer_text={}, link={}".format(
            auth.username(),
            str(string_id),
            str(new_answer.answer_id),
            answer_text,
            link)
    )
    db.session.add(new_answer)
    db.session.commit()

    dt = int((time.time() - start) * 1000)
    std.timing('API Call', dt)
    return answer_schema.jsonify(new_answer)


# Get a Question's Answer
@app.route('/Question/<string_id>/answer/<id>', methods=['get'])
def getquestionsanswer(string_id, id):
    std.incr('serviceCall')
    start = time.time()
    query_time = time.time()
    answer = Answer.query.filter_by(question_id=string_id, answer_id=id).first()
    qtd = int((time.time() - query_time) * 1000)
    std.timing('Query Call', qtd)
    if not answer:
        res = jsonify("Not Found!")
        res.status_code = 401
        return res
    dt = int((time.time() - start) * 1000)
    std.timing('API Call', dt)
    return answer_schema.jsonify(answer)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)

