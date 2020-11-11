#! /bin/bash
cd /home/webapp
nohup python3 app.py > /dev/null 2>&1 &
echo $(pgrep -f 'python3 app.py')
ls -al
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -c file:cloudwatch.json \
    -s
