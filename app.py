from flask import Flask
from flask import request
from flask import jsonify

import uuid
import time
import mysql.connector
from flask_httpauth import HTTPBasicAuth
import bcrypt


# def password_validator(passw):
#     if len(passw) < 9:#length >=8
#         return False
#     if not bool(re.search(r'\d', passw)):#contains digits
#         return False
#     if not bool(re.search(r'[a-zA-Z]', passw)):#conatins letters
#         return False
#     return True
from helper import password_validator

app = Flask(__name__)
db  = mysql.connector.connect(user='root', password='root',
                                 host='localhost',
                                 database='assign1',
                                auth_plugin='mysql_native_password')
MAIN_DB = db.cursor()
auth = HTTPBasicAuth()
salt = bcrypt.gensalt()
pw = ""


@auth.verify_password
def verify_password(username, password):
    global pw
    MAIN_DB.execute("select email, password from users")
    result = MAIN_DB.fetchall()
    for row in result:
        if username == row[0] and bcrypt.checkpw(password.encode('utf8'),row[1].encode('utf8')):
            pw = row[1]
            return username

@app.route("/User", methods=["get"])
@auth.login_required()
def getuser():
    MAIN_DB.execute("select id,first_name, last_name, email, account_created, account_updated from users where email = %s and password = %s", [auth.username(), pw])
    data = MAIN_DB.fetchall()
    row_headers = [x[0] for x in MAIN_DB.description]  # this will extract row headers
    json_data = []
    if data:
        for result in data:
            json_data.append(dict(zip(row_headers, result)))
            res = jsonify(json_data)
            res.status_code = 200
        return res

@app.route("/User", methods=["put"])
@auth.login_required()
def updateuser():
    # id = uuid.uuid4()
    first_name = request.json['first_name']
    last_name = request.json['last_name']
    email = request.json['email']
    password = request.json['password']
    if not password_validator(password):
        resp = jsonify("Your password must contains numbers and length >8")
        resp.status_code = 400
        return resp
    password = bcrypt.hashpw(password.encode('utf8'),salt)
    # account_created = time.strftime('%Y-%m-%d %H:%M:%S')
    account_updated = time.strftime('%Y-%m-%d %H:%M:%S')
    MAIN_DB.execute(
        "select id,first_name, last_name, email, account_created, account_updated from users where email = %s ",
        [email])
    data = MAIN_DB.fetchone()
    if data:
        resp = jsonify("Your email has already been registered")
        resp.status_code = 400
        return resp

    un = auth.username()
    MAIN_DB.execute("update users set first_name=%s, last_name=%s, email=%s, password=%s, account_updated=%s where email = %s", [first_name, last_name, email, password, account_updated, un])
    db.commit()
    MAIN_DB.execute(
        "select id,first_name, last_name, email, account_created, account_updated from users where email = %s and password = %s",
        [email, password])
    data = MAIN_DB.fetchone()
    row_headers = [x[0] for x in MAIN_DB.description]  # this will extract row headers
    json_data = []
    if data:
            json_data.append(dict(zip(row_headers, data)))
            res = jsonify(json_data)
            res.status_code = 200
            return res
    else :
        bad = jsonify("bad request")
        bad.status_code = 400
        return bad


@app.route("/User", methods=["post"])
def createuser():
    id = uuid.uuid4()
    first_name = request.json['first_name']
    last_name = request.json['last_name']
    email = request.json['email']
    password = request.json['password']
    if not password_validator(password):
        resp = jsonify("Your password must contains numbers and length >8")
        resp.status_code = 400
        return resp
    password = bcrypt.hashpw(password.encode('utf8'),salt)
    account_created = time.strftime('%Y-%m-%d %H:%M:%S')
    account_updated = time.strftime('%Y-%m-%d %H:%M:%S')
    MAIN_DB.execute(
        "select id,first_name, last_name, email, account_created, account_updated from users where email = %s ",
        [email])
    data = MAIN_DB.fetchone()
    if data:
        resp = jsonify("Your email has already been registered")
        resp.status_code = 400
        return resp

    sql = "INSERT INTO users (id, first_name, last_name, email, password, account_created, account_updated) values (%s,%s,%s,%s,%s,%s,%s)"
    MAIN_DB.execute(sql, (id, first_name, last_name, email, password, account_created, account_updated))
    db.commit()
    MAIN_DB.execute(
        "select id,first_name, last_name, email, account_created, account_updated from users where email = %s and password = %s",
        [email, password])
    data = MAIN_DB.fetchone()
    row_headers = [x[0] for x in MAIN_DB.description]  # this will extract row headers
    json_data = []
    if data:
            json_data.append(dict(zip(row_headers, data)))
            res = jsonify(json_data)
            res.status_code = 200
            return res
    else :
        bad = jsonify("bad request")
        bad.status_code = 400
        return bad

if __name__ == "__main__":
  app.run(host="localhost", port=3000, debug=True)