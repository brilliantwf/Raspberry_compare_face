# Access control using AWS Rekognition, IOT and Raspberry
Access Control use 2step verification system, which after successful authentication with RFID card/key, compare if the owner of the card is the same person as the one using that card at the moment of authentication. 
## The following equipment was used.
1. Raspberry 3B+
2. RFID-RC522
3. Raspberry Camera Rev1.3
## The following is the processing flow:
![](https://github.com/brilliantwf/Raspberry_compare_face/blob/master/rfid.jpg)
1. User touches the RFID reader with the RFID card
2. When the RFID event is detected and the number read is valid, the RPi Camera takes the photo of the person staying close to the RFID reader.
3. The photo is passed to the S3 Service
4. AWS Lambda function is triggered when the new photo gets uploaded to the specific S3 bucket and passes that data to AWS Rekognition service.
5. Rekognition service replies to the Lambda, giving the probability value that the person on the given image is the same person as the one on the reference photo,If the images match, put the image into the mach directory of S3, otherwise put it into the unmatch directory..
6. The Lambda function publishes the data received from Rekognition to the IoT topic
7. Raspberry Pi listens for the events on the IoT topic and once the data is received it decides if it should allow access (or perform any other action).
## install guide
1. Register Raspberry as thing and download the certificate on AWS IOTcore
2. Copy awsclilayer.zip to lambda as a layer for lambda.
3. import lambda_function.py as your lambda code,edit s3 path.
4. copy demo.py to your raspberry
5. pip install picamera,tinys3 and other dependencies
6. run command python demo.py -e IOTEndpoint.amazonaws.com -r "/Rootkey path/root-CA.crt" -k "/Privatekey path/HomePi.private.key" -c "/CertPath/HomePi.cert.pem"

