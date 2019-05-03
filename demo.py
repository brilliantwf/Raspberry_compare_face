from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import sys
import logging
import time
import getopt
from datetime import datetime
import RPi.GPIO as GPIO
import picamera
import os
import tinys3
import json
import MFRC522
 
# Create an object of the class MFRC522
MIFAREReader = MFRC522.MFRC522()

# Usage
usageInfo = """Usage:

Use certificate based mutual authentication:
python rpi_rfid_rekognition.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath>

Type "python rpi_rfid_rekognition.py -h" for available options.
"""
# Help info
helpInfo = """-e, --endpoint
	Your AWS IoT custom endpoint
-r, --rootCA
	Root CA file path
-c, --cert
	Certificate file path
-k, --key
	Private key file path
-h, --help
	Help information
"""

# Read in command-line parameters
host = ""
rootCAPath = ""
certificatePath = ""
privateKeyPath = ""
try:
	opts, args = getopt.getopt(sys.argv[1:], "hwe:k:c:r:", ["help", "endpoint=", "key=","cert=","rootCA="])
	if len(opts) == 0:
		raise getopt.GetoptError("No input parameters!")
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			print(helpInfo)
			exit(0)
		if opt in ("-e", "--endpoint"):
			host = arg
		if opt in ("-r", "--rootCA"):
			rootCAPath = arg
		if opt in ("-c", "--cert"):
			certificatePath = arg
		if opt in ("-k", "--key"):
			privateKeyPath = arg
except getopt.GetoptError:
	print(usageInfo)
	exit(1)

# Missing configuration notification
missingConfiguration = False
if not host:
	print("Missing '-e' or '--endpoint'")
	missingConfiguration = True
if not rootCAPath:
	print("Missing '-r' or '--rootCA'")
	missingConfiguration = True
if not certificatePath:
    print("Missing '-c' or '--cert'")
    missingConfiguration = True
if not privateKeyPath:
    print("Missing '-k' or '--key'")
    missingConfiguration = True
if missingConfiguration:
	exit(2)

# photo properties
image_width = 800
image_height = 600
file_extension = '.jpg'

# AWS S3 properties
access_key_id = 'your-ak'
secret_access_key = 'your-sk'
bucket_name = 'yourbucketname'

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = None

myAWSIoTMQTTClient = AWSIoTMQTTClient("basicPubSub")
myAWSIoTMQTTClient.configureEndpoint(host, 8883)
myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

# camera setup
camera = picamera.PiCamera()
camera.resolution = (image_width, image_height)
camera.awb_mode = 'auto'

def waitForRFIDScan():
    #print("Looking for cards")
    #print("Press Ctrl-C to stop.")
    # This loop checks for chips. If one is near it will get the UID
    done = False
    try:      
      while not done:    
        # Scan for cards
        (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)    
        # Get the UID of the card
        (status,uid) = MIFAREReader.MFRC522_Anticoll()    
        # If we have the UID, continue
        if status == MIFAREReader.MI_OK:     
          # Print UID
          print("UID: "+str(uid[0])+","+str(uid[1])+","+str(uid[2])+","+str(uid[3]))
          ss = str(uid[0])+str(uid[1])+str(uid[2])+str(uid[3])
          done = True    
          #time.sleep(2)
    except KeyboardInterrupt:
        GPIO.cleanup()
    return ss

def uploadToS3(file_name):
    filepath = file_name + file_extension
    camera.capture(filepath)
    conn = tinys3.Connection(access_key_id, secret_access_key)
    f = open(filepath, 'rb')
    conn.upload(filepath, f, bucket_name,
               headers={
               'x-amz-meta-cache-control': 'max-age=60'
               })
    if os.path.exists(filepath):
        os.remove(filepath)
   # camera.close()


# Custom MQTT message callback
def photoVerificationCallback(client, userdata, message):
    print("Received a new message: ")
    data = json.loads(message.payload)
    try:
        similarity = data[1][0]['Similarity']
        print("Received similarity: " + str(similarity))
        if(similarity >= 90):
            print("Access allowed, opening doors.")
            print("Thank you!")
	else :
            print "you are not allow pass"
    except:
        pass
    print("Finished processing event.")

def checkRFIDNumber(rfidnumber):
    return rfidnumber == '732916299'

# Connect and subscribe to AWS IoT
myAWSIoTMQTTClient.connect()
myAWSIoTMQTTClient.subscribe("rekognition/result", 1, photoVerificationCallback)
time.sleep(2)


# Publish to the same topic in a loop forever
while True:
    print("waiting for scan RFID Card")
    scan = waitForRFIDScan()
    print(scan)
    if(checkRFIDNumber(scan)):
        print("RFID correct, taking photo...")
        uploadToS3(scan)
    else:
        print("Bad RFID - Access Denied")
