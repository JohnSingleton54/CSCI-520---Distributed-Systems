# Notes for Mac

## Using Scripts

[Accessing Instances Linux](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AccessingInstancesLinux.html)

### Sending files

```bash
./sendFile <path to PEM> <Public DNS (IPv4)> <File>
```

Example:

```bash
./sendFile.sh ~/Desktop/pems/class.pem ec2-54-1A7-145-25H.us-west-2.compute.amazonaws.com ./echoConnection2.py
```

### Connection to Server

```bash
./connect.sh <path to PEM> <Public DNS (IPv4)>
```

Example:

```bash
./connect.sh ~/Desktop/pems/class.pem ec2-54-1A7-145-25H.us-west-2.compute.amazonaws.com
```
