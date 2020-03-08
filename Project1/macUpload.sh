#!/bin/bash

upload() {
    scp -i $1 $3 ec2-user@$2:$3
}

upload $1 $2 ./connections.py
upload $1 $2 ./distributedLog.py
upload $1 $2 ./ourCalendar.py
upload $1 $2 ./main.py
