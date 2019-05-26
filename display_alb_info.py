#!/bin/python
# Input parameter: stackname and the aws environment
# Output: all the ALB names and its instance name within the stack
# liz 26-05-2019 initial version


import os
import sys
import boto3
import botocore.session


session=""


def get_elb_arn(stackname):


    client = session.client('resourcegroupstaggingapi')
    response = client.get_resources(
        PaginationToken='',
        TagFilters=[
            {
                'Key': "Stackname",
                'Values': [stackname]
            }
        ],
        ResourcesPerPage=50,
        ResourceTypeFilters=['elasticloadbalancing:loadbalancer']
    )
    #print response
    elb_arn_list = []
    for d in response['ResourceTagMappingList']:
        for key,value in d.iteritems():
            if key == "ResourceARN" :
                elb_arn_list.append(value)
    return elb_arn_list




def get_tg_arn(elb_arn_list):
# for each elb arn, build a dictionary which holds the elb_arn as the key and the target_group_arn as the value


    client = session.client('elbv2')
    arns_dict = {}
    for elb in elb_arn_list:
        arns_dict[elb] = ""
        response = client.describe_listeners(
            LoadBalancerArn = elb,
            PageSize = 50
        )
        listen_values = response['Listeners']
        for d in listen_values:
            if "DefaultActions" in d:
                for d2 in d["DefaultActions"]:
                    if "TargetGroupArn" in d2:
                       arns_dict[elb] = d2["TargetGroupArn"]
    #print arns_dict
    return arns_dict


def get_instance_name(arns_dict):


    client = session.client('elbv2')
    instance_dict = {}
    for elb_arn, tg_arn in arns_dict.iteritems():
        response = client.describe_target_health(TargetGroupArn = tg_arn)
        for d in response["TargetHealthDescriptions"]:
           elb_name = convert_elb_arn_to_elb_name(elb_arn)
           instance_dict[elb_name] = d["Target"]["Id"]
    return instance_dict




def convert_elb_arn_to_elb_name(elb_arn):


    return elb_arn.split("/")[-2]




def print_report(stackname,instance_dict):


    print "Stack name is {}".format(stackname)
    for k,v in instance_dict.iteritems():
        print "ALB name is {} Instance Name is {}".format(k,v)




def main(stackname, env):


    global session
    session = boto3.session.Session(profile_name = env)
    #session = boto3.session.Session(profile_name='nonprod')


    elb_arn_list = get_elb_arn(stackname)
    arns_dict = get_tg_arn(elb_arn_list)
    instance_dict = get_instance_name(arns_dict)
    print_report(stackname,instance_dict)




if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
