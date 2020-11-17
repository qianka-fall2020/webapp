#! /bin/bash
pwd
ls -al
cd /home/webapp
echo "DATABASE=mysql://csye6225fall2020:awsdb2020@csye6225-f20.cjtqoip7hsuk.us-east-1.rds.amazonaws.com/csye6225" >> .env
echo "SECRETE_KEY=b6GzRexMkTqtRpog84O3cscvDqzphD6JL0yVNn0s" >> .env
echo "ACCESS_KEY=AKIAJBIVTX6XNKEIIW3A" >> .env
cat .env
nohup sudo python3 app.py > /dev/null 2>&1 &
echo $(pgrep -f 'python3 app.py')
