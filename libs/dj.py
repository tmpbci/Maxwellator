#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
dj
v0.7.0

DJ mp3 Hercules Handler.
Start a dedicated thread to handle incoming events from DJ mp3 midi controller.

Depending on selected destination computer (Prog Chg + Pad number) actions will be done
locally or forwarded via OSC to given computer. Remote computer must run bhorpad or 
maxwellator.

# Note

# Program Change button selected : change destination computer

# CC rotary -> midi CC.         

cross        49
joystick UD  57
joystick LR  56

LEFT:

menu        7
play/pause  8
cue         9

beat        10

pitch +     19
pitch -     20
jog         54
headset     21
volume      50
load deck   27
beatlck     22
1           15
2           14
3           13
bass        46
medium      47
trebble     48
track -     11
track +     12


RIGHT:

menu        1
play/pause  2
cue         3

beat        4

pitch +     23
pitch -     24
jog         55
headset     25
volume      51
load deck   28 
beatlck     26
1           16
2           17
3           18
bass        43
medium      44
treblle     45
track -     5
track +     6



by Sam Neurohack 
from /team/laser


"""


import time
import rtmidi
from rtmidi.midiutil import open_midiinput 
from threading import Thread
from rtmidi.midiconstants import (CHANNEL_PRESSURE, CONTROLLER_CHANGE, NOTE_ON, NOTE_OFF,
                                  PITCH_BEND, POLY_PRESSURE, PROGRAM_CHANGE)

#print()
print('DJ module...')

from mido import MidiFile
import mido
import sys, os
import midi3, gstt
#import midimacros, maxwellmacros
import traceback

from queue import Queue
#from libs import macros
import json, subprocess
from OSC3 import OSCServer, OSCClient, OSCMessage
import socket
import scrolldisp, bhoreal, launchpad, maxwellccs

#scrolldisp.Display('.', color=(255,255,255), delay=0.2, mididest ='launchpad')


#myHostName = socket.gethostname()
#print("Name of the localhost is {}".format(myHostName))
#gstt.myIP = socket.gethostbyname(myHostName)
#print("IP address of the localhost is {}".format(gstt.myIP))

#gstt.myIP = "127.0.0.1"

#print('Used IP', gstt.myIP)
OSCinPort = 8080
maxwellatorPort = 8090

DJqueue = Queue()

mode = "maxwell"
mididest = 'Session 1'
djdest = 'Port'

midichannel = 1
CChannel = 0
CCvalue = 0
Here = -1
previousmacro = -1
ljpath = r'%s' % os.getcwd().replace('\\','/')


ModeCallback = ''


# Hercules DJ mp3 leds
# Top leds 13 14 15 16 17 18
# Beatclocks 22 26
# Beat 10 4
# Cue 9 3
# Play 8 2

DJleds = {13, 14, 15, 16, 17, 18, 22, 26, 10, 4, 9, 3, 8, 2}



# /cc cc number value
def cc(ccnumber, value, dest=mididest):

    #print('Output CC',[CONTROLLER_CHANGE+midichannel-1, ccnumber, value], dest)
    midi3.MidiMsg([CONTROLLER_CHANGE+midichannel-1,ccnumber,value], dest)

def NoteOn(note,velocity, dest=mididest):
    midi3.NoteOn(note,velocity, mididest)

def NoteOff(note, dest=mididest):
    midi3.NoteOn(note, mididest)


def ComputerUpdate(comput):
    global computer

    computer = comput

'''
# Change type 1 or 127
# Curvetype pot : to left 127 / to right 1
def ChangeType1(value):
    global maxwell

    maxwellccs. = FindCC(maxwellprefixLeft + '/curvetype')
    print(maxwellprefixLeft + '/curvetype')
    print("Maxwell CC :",maxwellccs.)
    print("Current :",maxwell['ccs'][maxwellccs.]['init'])
    print("curvetypes :",specificvalues["curvetype"])
    print("midi value :", value)


    curves = list(enumerate(specificvalues["curvetype"]))
    print(curves)
    nextype = maxwell['ccs'][maxwellccs.]['init']
    for count,ele in curves: 

        if ele == maxwell['ccs'][maxwellccs.]['init']:
            if count >0 and value == 127:
                nextype = curves[count-1][1]

            if count < len(curves)-1 and value == 1:
                #print("next is :",curves[count+1][1])
                nextype = curves[count+1][1]

    print("result :", nextype, "new value :",specificvalues["curvetype"][nextype],"Maxwell CC",maxwellccs.)
    maxwell['ccs'][maxwellccs.]['init'] = nextype
    maxwellccs.cc(maxwellccs.,specificvalues["curvetype"][nextype],dest ='to Maxwell 1')

'''


#
# OSC
#


# Client to export buttons actions from DJ or bhoreal

def SendOSC(ip,port,oscaddress,oscargs=''):
        
    oscmsg = OSCMessage()
    oscmsg.setAddress(oscaddress)
    oscmsg.append(oscargs)
    
    osclient = OSCClient()
    osclient.connect((ip, port)) 

    print("sending OSC message : ", oscmsg, "to", ip, ":", port)

    try:
        osclient.sendto(oscmsg, (ip, port))
        oscmsg.clearData()
        return True
    except:
        print ('Connection to', ip, 'refused : died ?')
        return False


#       
# Events from DJ buttons
#

# Process events coming from DJ in a separate thread.

def MidinProcess(DJqueue):
    #global computer, maxwellprefixLeft, maxwellprefixRight, maxwellsuffix, previousmacro
    global computer, previousmacro
 
    while True:
        DJqueue_get = DJqueue.get
        msg = DJqueue_get()
        #print (msg)


        # CC rotary -> midi CC.         
        if msg[0] == CONTROLLER_CHANGE:

            #print("DJmp3 CC :", msg[1],"value :",msg[2])

            macronumber = findDJMacros(msg[1])
            macro = kindDJMacros(macronumber)
            if macronumber != previousmacro and bhoreal.Here != -1:
                scrolldisp.Display(macros['dj'][macronumber]['Info'], color=(255,200,10), delay=0.2, mididest ='bhoreal')
            
            #print(macro, "X ?", macro.find('X'), "/ ?", macro.count('/') )
            print("DJmp3 CC :", msg[1],"value :",msg[2], 'is :', macro)

            # Left or Right X Y Z function selection
            if macro.find('X') != -1 or macro.find('Y') != -1 or macro.find('Z') != -1:

                
                # A new prefix -> Build complete path and send it to maxwell
                if macro.find('left') != -1:
                    ResetLeftPrefix()
                    maxwellccs.current["prefixLeft"] = macro
                    print(macro) 
                    #maxwellccs.cc(FindCC(maxwellprefixLeft + maxwellsuffix), msg[2], 'to Maxwell 1')

                else:
                    ResetRightPrefix()
                    maxwellccs.current["prefixRight"] = macro
                    print(macro)
                    #maxwellccs.cc(FindCC(maxwellprefixRight + maxwellsuffix), msg[2], 'to Maxwell 1')
                
                maxwellccs.cc(int(msg[1]), 127, dest=djdest)
            
            elif macro.count('/') > 0:
            
                # a center button function
                if macro.find('/center') > -1:
                    maxwellccs.cc(maxwellccs.FindCC(macro), msg[2], 'to Maxwell 1')

                # A complete maxwell function
                if macro.count('/') > 1 and macro.find('/center') == -1:
                    print(macro)
                    maxwellccs.cc(maxwellccs.FindCC(macro), msg[2], 'to Maxwell 1')

                # Suffix value -> Build complete path and send it to maxwell
                if macro.count('/') == 1 and macro.find('/center') == -1:

                    maxwellccs.current["suffix"]= macro
                    # Suffix of maxwell function
                    if nameDJMacros(macronumber).find('left') != -1:
                        #print(maxwellprefixLeft + maxwellsuffix)
                        maxwellccs.cc(maxwellccs.FindCC(maxwellccs.current["prefixLeft"] + maxwellccs.current["suffix"]), msg[2], 'to Maxwell 1')

                    else:
                        print(maxwellccs.current["prefixRight"] + maxwellccs.current["suffix"])
                        maxwellccs.cc(maxwellccs.FindCC(maxwellccs.current["prefixRight"] + maxwellccs.current["suffix"]), msg[2], 'to Maxwell 1')


            if macro.count('/') == 0:
                
                #if msg[2] == 127:
                #print("running :", macro)
                eval(macro+"("+str(msg[2])+")")
            '''
            if computer == 0 or computer == 1:
                cc(int(msg[1]), int(msg[2]))

            else: 
                SendOSC(computerIP[computer-1], maxwellatorPort, '/cc', [int(msg[1]), int(msg[2])])
            '''

        previousmacro = macronumber


DJqueue = Queue()


# DJ Mini call back : new msg forwarded to DJ queue 
class DJAddQueue(object):
    def __init__(self, port):
        self.port = port
        #print("DJAddQueue", self.port)
        self._wallclock = time.time()

    def __call__(self, event, data=None):
        message, deltatime = event
        self._wallclock += deltatime
        print()
        print("[%s] @%0.6f %r" % (self.port, self._wallclock, message))
        DJqueue.put(message)

#
# Modes :
# 

# Load Matrix only macros (for the moment) in dj.json 
def LoadMacros():
    global macros

    #print()
    #print("Loading DJ Macros...")

    if os.path.exists('dj.json'):
        #print('File dj.json exits')
        f=open("dj.json","r")

    elif os.path.exists('../dj.json'):
            #print('File ../dj.json exits')
            f=open("../dj.json","r")

    elif os.path.exists(ljpath + '/libs/dj.json'):
            #print('File ../dj.json exits')
            f=open(ljpath + "/libs/dj.json","r")



    s = f.read()
    macros = json.loads(s)
    #print(len(macros['dj']),"Macros")
    #print("Loaded.")




# return macro number for given CC nummber with 'dj' type
def findDJMacros(ccnumber):

    #print("searching", macroname,'...')
    position = -1
    for counter in range(len(macros['dj'])):
        #print (counter,macros[macrotype][counter]['name'],macros[macrotype][counter]['code'])
        if str(ccnumber) == macros['dj'][counter]['cc']:
            #print(macroname, "is ", counter)
            position = counter
    return position


# return macro number for given CC nummber with 'dj' type
def kindDJMacros(macronumber):

    return macros['dj'][macronumber]['Function']


def nameDJMacros(macronumber):

    return macros['dj'][macronumber]['Name']





# Not assigned buttons
def DefaultMacro(value):

    print ("DefaultMacro")


def StartDJ(port):

    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/dj/on', [1])
    '''
    # print(CONTROLLER_CHANGE, midichannel, "-1", DJleds)
    for led in DJleds:
        maxwellccs.cc(led, 127, dest = djdest)
        time.sleep(0.1)

        #maxwellccs.cc(9, 127, dest=djdest)
        #midi3.MidiMsg([CONTROLLER_CHANGE+midichannel-1,led,127], djdest)
        #maxwellccs.cc(led, 127, djdest)
    
    time.sleep(0.5)

    for led in DJleds:
        #midi3.MidiMsg([CONTROLLER_CHANGE+midichannel-1,led,0], djdest)
        #maxwellccs.cc(led, 0, djdest)
        maxwellccs.cc(led, 0, dest = djdest)
   
'''

def ResetLeftPrefix():

    for led in range(13,16):

        maxwellccs.cc(led, 0, dest = djdest)
        time.sleep(0.01)

def ResetRightPrefix():

    for led in range(16,19):
        maxwellccs.cc(led, 0, dest=djdest)
        time.sleep(0.01)



#
# Default macros
#


DJmacros = {

    "n1":      {"command": DefaultMacro, "default": 1},
    "n2":      {"command": DefaultMacro, "default": 2},
    "n3":      {"command": DefaultMacro, "default": 3},
    "n4":      {"command": DefaultMacro, "default": 4},
    "n5":      {"command": DefaultMacro, "default": 5},
    "n6":      {"command": DefaultMacro, "default": 6},
    "n7":      {"command": DefaultMacro, "default": 7},
    "n8":      {"command": DefaultMacro, "default": 8}
    }

'''
def Run(macroname, macroargs=''):

        doit = DJmacros[macroname]["command"]
        if macroargs=='':
            macroargs = DJmacros[macroname]["default"]
        #print("Running", doit, "with args", macroargs )
        doit(macroargs)
'''

LoadMacros()
maxwellccs.LoadCC()
#maxwellccs.cc(13, 127, dest=djdest)

if __name__ == '__main__':


    import traceback
    import time
    
    midi3.check()

    scrolldisp.Display('Dj', color=(255,255,255), delay=0.2, mididest ='launchpad')
    scrolldisp.Display('Dj', color=(255,230,0), delay=0.2, mididest ='bhoreal')
    # Light left X and right X
    maxwellccs.cc(15, 127, dest=djdest)
    maxwellccs.cc(16, 127, dest=djdest)
    try:

        while True:
            time.sleep(0.1)

    except Exception:
        traceback.print_exc()

    #finally:

