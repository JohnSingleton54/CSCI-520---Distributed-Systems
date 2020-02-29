#!/bin/bash

scp -i $1 $3 ec2-user@$2:$3
