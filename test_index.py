from app import app
from flask import request
from flask import json
import pytest
import requests


def test_login_valid(supply_url):
	url = supply_url + "/User"
	# data = {"first_name" : "testpost", "last_name":"testpost", "email":"testpost@gmail.com", "password": "Tears@628"}
	resp = requests.post(url)
	assert resp.status_code == 500

@pytest.mark.parametrize("username, password",[("test@gmail.com","Tears@628")])
def test_list_valid_user(supply_url,username, password):
	url = supply_url + "/User"
	resp = requests.get(url)
	assert resp.status_code == 401

# def test_list_invaliduser(supply_url):
# 	url = supply_url + "/User"
# 	resp = requests.get(url)
# 	assert resp.status_code == 400

# def test_postUser():
#     res = app.test_client().post(
#         '/User',
#
#     assert res.status_code == 200