#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -*- mode: Python -*-

"""

OBS Studio coms
v0.1b

LICENCE : CC
by Sam Neurohack 
from /team/laser

Heavily based on samples in https://github.com/Elektordi/obs-websocket-py

Start()
goScene("live")
time.sleep(2)
goScene("MAXWELL only")
time.sleep(2)
goScene("black")
Stop()


"""

import sys
import time
import socket
from obswebsocket import obsws, requests 

obsIP = "localhost"
obsPORT = 4444
obsPWD = "secret"

obsretry = 1
obsdelay = 1
obstimeout = 2


def isOpen(ip, port):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		s.connect((ip, int(port)))
		s.shutdown(2)
		return True
	except:
		return False

def isconnected(obsIP = obsIP, obsPORT = obsPORT):

	ipup = False
	for i in range(obsretry):
		if isOpen(obsIP, obsPORT):
			ipup = True
			break
		else:
			time.sleep(obsdelay)
	return ipup


# Start as client only
def Start():
	global ws

	print("OBS Studio module...")
	ws = obsws(obsIP, obsPORT, obsPWD)
	ws.connect()

# Start as client and server to get event from OBS
def StartAll():
	global ws

	ws = obsws(obsIP, obsPORT, obsPWD)
	ws.register(on_event)
	ws.register(on_switch, events.SwitchScenes)
	ws.connect()


def goScene(name):

    print("Going to OBS scene :", name)
    ws.call(requests.SetCurrentScene(name))


def on_event(message):
    
    print(u"Got message: {}".format(message))


def on_switch(message):

    print(u"You changed the scene to {}".format(message.getSceneName()))


def Stop():

	print("OBS Studio link stopped.")
	ws.disconnect()




'''
#
# Scene change autoloop
#


try:
    scenes = ws.call(requests.GetSceneList())
    for s in scenes.getScenes():
        name = s['name']
        print(u"Switching to {}".format(name))
        ws.call(requests.SetCurrentScene(name))
        time.sleep(2)

    print("End of list")

except KeyboardInterrupt:
    pass

ws.disconnect()

'''

'''
#
# get events from OBS Studio
#

def on_event(message):
    print(u"Got message: {}".format(message))


def on_switch(message):
    print(u"You changed the scene to {}".format(message.getSceneName()))


ws = obsws(host, port, password)
ws.register(on_event)
ws.register(on_switch, events.SwitchScenes)
ws.connect()

try:
    print("OK")
    time.sleep(10)
    print("END")

except KeyboardInterrupt:
    pass

ws.disconnect()

'''

'''
 |  Core class for using obs-websocket-py
 |  
 |  Simple usage:
 |      >>> import obswebsocket, obswebsocket.requests
 |      >>> client = obswebsocket.obsws("localhost", 4444, "secret")
 |      >>> client.connect()
 |      >>> client.call(obswebsocket.requests.GetVersion()).getObsWebsocketVersion()
 |      u'4.1.0'
 |      >>> client.disconnect()
 |      
 |  For advanced usage, including events callback, see the 'samples' directory.
 |  
 |  Methods defined here:
 |  
 |  __init__(self, host=None, port=4444, password='')
 |      Construct a new obsws wrapper
 |      
 |      :param host: Hostname to connect to
 |      :param port: TCP Port to connect to (Default is 4444)
 |      :param password: Password for the websocket server (Leave this field empty if no auth enabled
 |          on the server)
 |  
 |  call(self, obj)
 |      Make a call to the OBS server through the Websocket.
 |      
 |      :param obj: Request (class from obswebsocket.requests module) to send to the server.
 |      :return: Request object populated with response data.
 |  
 |  connect(self, host=None, port=None)
 |      Connect to the websocket server
 |      
 |      :return: Nothing
 |  
 |  disconnect(self)
 |      Disconnect from websocket server
 |      
 |      :return: Nothing
 |  
 |  reconnect(self)
 |      Restart the connection to the websocket server
 |      
 |      :return: Nothing
 |  
 |  register(self, function, event=None)
 |      Register a new hook in the websocket client
 |      
 |      :param function: Callback function pointer for the hook
 |      :param event: Event (class from obswebsocket.events module) to trigger the hook on.
 |          Default is None, which means trigger on all events.
 |      :return: Nothing
 |  
 |  send(self, data)
 |      Make a raw json call to the OBS server through the Websocket.
 |      
 |      :param obj: Request (python dict) to send to the server. Do not include field "message-id".
 |      :return: Response (python dict) from the server.
 |  
 |  unregister(self, function, event=None)
 |      Unregister a new hook in the websocket client
 |      
 |      :param function: Callback function pointer for the hook
 |      :param event: Event (class from obswebsocket.events module) which triggered the hook on.
 |          Default is None, which means unregister this function for all events.
 |      :return: Nothing

 '''