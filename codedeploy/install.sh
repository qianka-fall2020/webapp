#! /bin/bash
sudo apt-get update
sudo apt-get -y install python3.8
sudo apt-get remove python-pip-whl
sudo apt-get -y install python3-pip
sudo pip3 install flask
sudo pip3 install marshmallow
sudo pip3 install uuid
sudo pip3 install flask_httpauth
sudo pip3 install bcrypt
sudo pip3 install flask_sqlalchemy
sudo pip3 install flask_marshmallow
sudo pip3 install boto3
sudo apt-get install -y python3-mysqldb
sudo pip3 install marshmallow-sqlalchemy
sudo apt-get install unzip
curl "https://s3.amazonaws.com/aws-cli/awscli-bundle.zip" -o "awscli-bundle.zip"
unzip awscli-bundle.zip
sudo python3 awscli-bundle/install -i /usr/local/aws -b /usr/local/bin/aws
