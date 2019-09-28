#!/usr/bin/env python
import time
import datetime
import os
import json

from lifxlan import Light, Group, WorkflowException
from retrying import retry

# Discover all lights on LAN and create a LifxLAN object
# lifx = LifxLAN()
## Get all devices, a list of Device objects
#devices = lifx.get_devices()
#
#for i in devices:
#    print(i)

# Create all the objects
p = json.loads(os.environ['PARENT'])
parent_light = Light(p['mac'], p['ip'])

c1 = json.loads(os.environ['CHILD1'])
child1_light = Light(c1['mac'], c1['ip'])

c2 = json.loads(os.environ['CHILD2'])
child2_light = Light(c2['mac'], c2['ip'])

# create the groups
g = Group([child1_light, child2_light])
full_group = Group([parent_light, child1_light, child2_light])

def get_power_state(l):
    state = "off" # default
    try:
        if l.get_power() > 0:
            state = "on"
    except WorkflowException: # the light is powered off
        state = "off"
    except OSError: # ignore a timeout
        state = "off"
    return(state)

@retry(wait_random_min=100, wait_random_max=200)
def modify_brightness(group):
    # if between 5am and 5pm then set brightness to 100%, if otherwise, set
    # brightness to 20%
    now = datetime.datetime.now()
    # Use the retrying library to automatically retry. The problem is that, when
    # lights are powered on, they do not respond to get_() for a few seconds, so
    # instead of adding a random sleep or complicated retry behavior, just use
    # the retry library to retry until this function returns
    # When a light doesn't respond, a WorkflowException is raised
    if 5 <= now.hour <= 17:
        group.set_brightness(65535)
    else:
        group.set_brightness(13107)
    # TODO: This is a jarring transition, use the HTTP API to set brightness
    # prior to turning on!

# This is the initial state when the script starts
power_state = {"state": get_power_state(parent_light), "times_seen": 0}

while True:
    print("Starting beginning of loop at: "+ str(datetime.datetime.now()))
    print(power_state)
    new_power_state = get_power_state(parent_light)

    if power_state['state'] != new_power_state:
        print("There is a transition!")
        # increment the times_seen
        power_state['times_seen'] = power_state['times_seen'] + 1
        # Wait for 2 times_seen before modifying power
        if power_state['times_seen'] > 1:
            g.set_power(new_power_state)
            if new_power_state == "on":
                modify_brightness(full_group)
            power_state['state'] = new_power_state
            # reset times_seen
            power_state['times_seen'] = 0

    if power_state['state'] == new_power_state:
        # The power state is the same so reset the times_seen
        # This is the part that catches "blips" in UDP packet timeouts
        if power_state['times_seen'] != 0:
            print("Blip detected, resetting times_seen")
            power_state['times_seen'] = 0

    # Sleep timer controls the loop iteration
    time.sleep(.4)
