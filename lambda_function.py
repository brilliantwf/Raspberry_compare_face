import commands
import json
import os
from cStringIO import StringIO
import re
import boto3
iot = boto3.client('iot-data')
print('Loading function')
def aws(cmd):
    return commands.getoutput(cmd)
def lambda_handler(event, context):
    print(event)
    bucket=event[u"Records"][0][u"s3"][u"bucket"][u"arn"]
    bucket_name=bucket.split(':::')[1]
    item=event[u"Records"][0][u"s3"][u"object"][u"key"]
    path=bucket+"/"+item
    image='{"S3Object":{"Bucket":"'+bucket_name+'","Name":"'+item+'"}}'
    result=aws("/opt/aws rekognition compare-faces --source-image '{\"S3Object\":{\"Bucket\":\"facebucket\",\"Name\":\"source/sourcepage.jpg\"}}' --target-image '"+image+"' --similarity-threshold 0.0 --region us-east-1")
    findsimil=result.find("Similarity")
    simil=float(result[(findsimil+13):(findsimil+18)])
    mypayload = json.dumps(((eval(result))['SourceImageFace'],(eval(result))['FaceMatches']))
    iotResponse = iot.publish(topic="rekognition/result",qos=1,payload=mypayload)
    
    print(simil)
    if simil > 80:
        print(aws("/opt/aws s3 mv s3://"+bucket_name+"/"+item+" s3://"+bucket_name+"/match/"))
    else:
        print(aws("/opt/aws s3 mv s3://"+bucket_name+"/"+item+" s3://"+bucket_name+"/unmatch/"))
    return iotResponse
