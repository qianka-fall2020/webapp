#! /bin/bash
id = $(pgrep -f 'python3 app.py')
if [-n "$(id)"]; then
   kill $(pgrep -f 'python3 app.py')
fi

