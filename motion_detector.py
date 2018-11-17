import time
import os
import sys

import RPi.GPIO as GPIO
import requests

GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.IN) #PIR sensor on pin 23

token = os.getenv('LIFX_TOKEN')
if not token:
    print("Please supply LIFX_TOKEN, exiting...")
    sys.exit(1)
headers = {"Authorization": "Bearer {}".format(token)}

# Try to get sleep time, default to 300
sleep = int(os.getenv('LIFX_WAKE_TIME', 300))

# this is just an easy way to build the payload
def build_payload(state):
    j = {}
    j['power'] = state
    j['color'] = "kelvin:3500 brightness:1"
    return j

# which light do we want? default to all
selector = os.getenv('LIFX_LIGHT', 'all')
# build the url
url = "https://api.lifx.com/v1/lights/{}".format(selector)

# check current state
def check_current_status(s):
    # not supported right now, assume off
    if s == "all":
        return "off"
    else:
        r = requests.get(url, headers=headers)
        # this is not perfect
        s = r.json()[0]['power']
        print('Current Status: {}'.format(s))
        return str(s)
try:
    state = check_current_status(selector)
    while True:
        if GPIO.input(23):
            if not state == "on":
                print("Motion Detected, turning light on")
                r = requests.put(url+'/state', data=build_payload('on'), headers=headers)
                state = "on"
                print("Sleeping {} seconds".format(sleep))
                time.sleep(sleep)
        else:
            if state == "on":
                print("Motion Not Detected, light is on so turning light off")
                r = requests.put(url+'/state', data=build_payload('off'), headers=headers)
                state = "off"
            else:
                print("Motion not detected, light is already off")
        time.sleep(.5)

except Exception as e:
    print(e)
    # cleanup is a safety function to reset any GPIO pins back to default
    GPIO.cleanup()
