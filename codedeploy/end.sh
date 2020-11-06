#! /bin/bash

if [ -n $(pgrep -f 'python3 app.py') ]; then
	sudo kill echo $(pgrep -f 'python3 app.py')
fi
