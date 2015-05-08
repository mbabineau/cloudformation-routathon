CloudFormation templates for a [Routathon](https://github.com/QubitProducts/routathon) stack proxying requests to a [Mesos](http://mesos.apache.org)+[Marathon](https://github.com/mesosphere/marathon) cluster.

Prerequisites:
* A Mesos cluster running the Marathon framework, such as provided by [mbabineau/cloudformation-mesos](https://github.com/mbabineau/cloudformation-mesos)

## Overview

This template bootstraps a routing/load balancing stack for Marathon.

Rouathon servers are launched from public AMIs running Ubuntu 14.04 LTS and pre-loaded with Docker and Runit. If you wish to use your own image, simply modify `RegionMap` in `routathon.json`.

To adjust cluster capacity, simply increment or decrement `InstanceCount` in the CloudFormation stack. Node addition/removal will be handled transparently by the auto scaling group.

Note that this template must be used with Amazon VPC. New AWS accounts automatically use VPC, but if you have an old account and are still using EC2-Classic, you'll need to modify this template or make the switch.

## Usage

### 1. Clone the repository
```bash
git clone https://github.com/mbabineau/cloudformation-routathon.git
```

### 2. Create an Admin security group
This is a VPC security group containing access rules for cluster administration, and should be locked down to your IP range, a bastion host, or similar. This security group will be associated with the Mesos servers.

Inbound rules are at your discretion, but you may want to include access to:
* `22 [tcp]` - SSH port
* `80 [tcp]` - Proxied HTTP
* `8000 [tcp]` - Routathon admin HTTP

### 3. Set up Mesos+Marathon
You can use the instructions and template at [mbabineau/cloudformation-mesos](https://github.com/mbabineau/cloudformation-mesos), or you can use an existing cluster.

We'll need:
* A URL associated with Marathon
* A security group associated with the Marathon servers (or LB)
* A security group associated with the Mesos slaves

### 4. Launch the stack
Launch the stack via the AWS console, a script, or [aws-cli](https://github.com/aws/aws-cli).

See `routathon.json` for the full list of parameters, descriptions, and default values.

Of note:
`ProxyRules` should be a JSON array of (app name, protocol, app port, HAProxy port) tuples (e.g., `[["myapp", "tcp", 8081, 80]]`)

Example using `aws-cli`:
```bash
aws cloudformation create-stack \
    --template-body file://routathon.json \
    --stack-name <stack> \
    --capabilities CAPABILITY_IAM \
    --parameters \
        ParameterKey=KeyName,ParameterValue=<key> \
        ParameterKey=MarathonUrl,ParameterValue=<url> \
        ParameterKey=MarathonSecurityGroup,ParameterValue=<sg_id> \
        ParameterKey=MesosSlaveSecurityGroup,ParameterValue=<sg_id> \
        ParameterKey=ProxyRules,ParameterValue=<rules> \
        ParameterKey=VpcId,ParameterValue=<vpc_id> \
        ParameterKey=Subnets,ParameterValue='<subnet_id_1>\,<subnet_id_2>' \
        ParameterKey=AdminSecurityGroup,ParameterValue=<sg_id> \
```
