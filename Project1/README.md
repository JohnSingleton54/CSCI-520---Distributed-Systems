# Distributed Log

## Links

- [EC2 Main Page](https://aws.amazon.com/ec2/)
- [Deploy a Python Web App](https://aws.amazon.com/getting-started/projects/deploy-python-application/)
- [Launch a (PHP) Application](https://aws.amazon.com/getting-started/tutorials/launch-an-app/)
- [Launch a Linux Virtual Machine](https://aws.amazon.com/getting-started/tutorials/launch-a-virtual-machine/?nc2=type_a)
- [EC2 Console](https://us-west-2.console.aws.amazon.com/ec2/v2/home?region=us-west-2#Instances:sort=instanceId)
- [Python 2 Sockets](https://docs.python.org/2/library/socket.html#example)

## Setting up the EC2 instances

1. Goto [EC2 Instances](https://us-west-2.console.aws.amazon.com/ec2/v2/home?region=us-west-2#Instances:sort=desc:dnsName)
2. Click Security Group ([Following this](https://stackoverflow.com/questions/53174079/how-to-socket-communication-between-2-different-amazon-ec2))
3. Add Inbound Rule, custom 8080

## Mac/Linux Commands

[Accessing Instances Linux](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AccessingInstancesLinux.html)

### Sending files

```bash
scp -i <path to PEM> <File> ec2-user@<Public DNS (IPv4)>:<File>
```

Example:

```bash
scp -i ~/Desktop/pems/class.pem ./echoConnection2.py ec2-user@ec2-54-1A7-145-25H.us-west-2.compute.amazonaws.com:./echoConnection2.py  
```

### Connection to Server

```bash
ssh -i <path to PEM> ec2-user@<Public DNS (IPv4)>
```

Example:

```bash
ssh -i ~/Desktop/pems/class.pem ec2-user@ec2-54-1A7-145-25H.us-west-2.compute.amazonaws.com
```
