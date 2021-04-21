#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Livecode mainly for incoming OSC 
v0.1b

by Sam Neurohack 
from /team/laser

/livecode/bpm 160
/livecode/tick *
/livecode/pattern/1 “xx-o[---]”
/livecode/xy/1 0.5 0.2
/livecode/color/2 0.8 0.2 0.7
/livecode/mood “purple”
/livecode/say “Thank you for choosing algorithms”

"""


import time
import sys, os
import midi3, gstt
#import midimacros, maxwellmacros
import traceback

from queue import Queue
#from libs import macros
import json, subprocess
from OSC3 import OSCServer, OSCClient, OSCMessage
import socket
import maxwellccs

#print()
print('Livecode module...')
#myHostName = socket.gethostname()
#print("Name of the localhost is {}".format(myHostName))
#gstt.myIP = socket.gethostbyname(myHostName)
#print("IP address of the localhost is {}".format(gstt.myIP))

#maxwellatorPort = 8090

numbertime = [time.time()]*40
#nbmacro = 33
computer = 0

ljpath = r'%s' % os.getcwd().replace('\\','/')


# Dcode OSC Timecode /TC1/time/30 "00:01:07:12" or /TC2/time/30 "00:01:07:12"
def OSCtimecode(timepath, timestr, tags, source):

    timelayer = int(timepath[3:4])
    times = timestr[0].split(":")
    hour = times[0]
    minutes = times[1]
    seconds = times[2]
    msecs = times[3]

    print('timecode layer', timelayer, "hour", hour, "min", minutes, "sec", seconds, "ms", msecs)


#       
# Events from OSC
#

# Generic OSC client

def SendOSC(ip,port,oscaddress,oscargs=''):
        
    oscmsg = OSCMessage()
    oscmsg.setAddress(oscaddress)
    oscmsg.append(oscargs)
    
    osclient = OSCClient()
    osclient.connect((ip, port)) 

    #print("BCR2000 sending OSC message : ", oscmsg, "to", ip, ":", port)

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

    print('/livecode OSC got', path, args)


    # /livecode/bpm 160
    if path.find('/bpm') > -1:
        print('/livecode OSC got bpm', args[0])
        maxwellccs.newtempo(int(args[0]))

    # /livecode/tick *
    if path.find('/tick') > -1:
        print('/livecode OSC got tick', args[0])

    # /livecode/color/2 0.8 0.2 0.7
    if path.find('/color') > -1:
        print('/livecode OSC got color', path, args[0])

    # /livecode/pattern/1 “xx-o[---]”
    if path.find('/pattern') > -1:
        print('/livecode OSC got pattern', path, args[0])

    # /livecode/mood “purple”
    if path.find('/mood') > -1:
        print('/livecode OSC got mood', path, args[0])

    # /livecode/say “Thank you for choosing algorithms”
    if path.find('/say') > -1:
        print('/livecode OSC got say', args[0])

    if path.find('/encoder') > -1:

        #number = NoteXY(int(path[3:4]),int(path[2:3]))
        print('/livecode OSC got encoder',path[1:4], args[0])
        if args[0] == 1.0:
            Encoder(path[1:4], 1)
        else:
            Encoder(path[1:4], 127)

    if path.find('/button') > -1:

        #number = NoteXY(int(path[3:4]),int(path[2:3]))
        #print()
        if path.find('/prev') > -1:
            PLayer()
            
        elif path.find('/next') > -1:
            NLayer()

        else:
            print('/livecode OSC got button', path[2:4], args[0])
            padCC('m'+path[2:4], int(args[0]))
