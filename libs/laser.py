#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Laser
v0.7.0

by Sam Neurohack 
from /team/laser


"""

import time
import rtmidi
from rtmidi.midiutil import open_midiinput 
from threading import Thread
from rtmidi.midiconstants import (CHANNEL_PRESSURE, CONTROLLER_CHANGE, NOTE_ON, NOTE_OFF,
                                  PITCH_BEND, POLY_PRESSURE, PROGRAM_CHANGE)

from mido import MidiFile
import mido
import sys, os
import midi3, launchpad, gstt, bhoreal
#import midimacros, maxwellmacros
import traceback

from queue import Queue
#from libs import macros
import json, subprocess
from OSC3 import OSCServer, OSCClient, OSCMessage
import socket
import maxwellccs

#print()
print('Laser module...')


# Generic OSC client

def SendOSC(ip,port,oscaddress,oscargs=''):
        
    oscmsg = OSCMessage()
    oscmsg.setAddress(oscaddress)
    oscmsg.append(oscargs)
    
    osclient = OSCClient()
    osclient.connect((ip, port)) 

    #print("Beatstep sending OSC message : ", oscmsg, "to", ip, ":", port)

    try:
        osclient.sendto(oscmsg, (ip, port))
        oscmsg.clearData()
        return True
    except:
        print ('Connection to', ip, 'refused : died ?')
        return False

def SendOSCUI(address, args):
    if gstt.debug >0:
        print("SendOSCUI is sending", address, args)
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, address, [args])



def FromOSC(path, args):

    if path.find('/button') > -1:

        if args[0] == 1.0:

            # New laser choice
            SendOSCUI('/laser/led/'+str(gstt.lasernumber), [0])
            bhoreal.NoteOnXY(5+gstt.lasernumber, 8, 1)
            gstt.lasernumber = int(path[1:2])
            print("New lasernumber", gstt.lasernumber)
            SendOSCUI('/laser/led/'+str(gstt.lasernumber), [1])
            bhoreal.NoteOnXY(5+gstt.lasernumber, 8, 127)

            for ccnumber in range(0,len(maxwellccs.maxwell['ccs'])):
                maxwellccs.UpdateCCs(ccnumber, gstt.ccs[gstt.lasernumber][ccnumber], laser = gstt.lasernumber)
        else:
            print('laser led off')

def ResetUI():

    for laserid in range(0,4):
        SendOSCUI('/laser/led/'+str(laserid), [0])
