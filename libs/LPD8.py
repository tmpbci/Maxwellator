#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
LPD8
v0.7.0

LPD8 Handler.
Start a dedicated thread to handle incoming events from LPD8 midi controller.

Depending on selected destination computer (Prog Chg + Pad number) actions will be done
locally or forwarded via OSC to given computer. Remote computer must run bhorpad or 
maxwellator.

# Note

# Program Change button selected : change destination computer

# CC rotary -> midi CC.         


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
import midi3, launchpad, gstt, maxwellccs, laser
#import midimacros, maxwellmacros
import traceback

from queue import Queue
#from libs import macros
import json, subprocess
from OSC3 import OSCServer, OSCClient, OSCMessage
import socket

#print()
print('LPD8 module...')
#myHostName = socket.gethostname()
#print("Name of the localhost is {}".format(myHostName))
#myIP = socket.gethostbyname(myHostName)
#print("IP address of the localhost is {}".format(myIP))

LPD8queue = Queue()

mode = "maxwell"
mididest = 'Session 1'

midichannel = 1
CChannel = 0
CCvalue = 0
Here = -1

ModeCallback = ''

computer = 0

ljpath = r'%s' % os.getcwd().replace('\\','/')

#nbmacro = 32
# /cc cc number value
def cc(ccnumber, value, dest=mididest, laser = 0):

    gstt.ccs[gstt.lasernumber][ccnumber]= value
    #print('Output CC',[CONTROLLER_CHANGE+midichannel-1, ccnumber, value], dest)
    if gstt.lasernumber == 0:
        midi3.MidiMsg([CONTROLLER_CHANGE+midichannel-1, ccnumber, value], dest)
    else:
        SendOSC(gstt.computerIP[gstt.lasernumber], gstt.MaxwellatorPort, '/cc/'+str(ccnumber),[value])

    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/cc/'+str(ccnumber), [value])


def NoteOn(note,velocity, dest=mididest):
    midi3.NoteOn(note,velocity, mididest)

def NoteOff(note, dest=mididest):
    midi3.NoteOn(note, mididest)


def ComputerUpdate(comput):
    global computer

    computer = comput

def Start(port):

    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/lpd8/on', [1])
    for pad1 in range(1,4):
        maxwellccs.cc(pad1, 0, dest = 'LPD8')
    for pad2 in range(5,8):
        maxwellccs.cc(pad2, 0, dest = 'LPD8')

    for pad1 in range(1,4):
        maxwellccs.cc(pad1, 127, dest = 'LPD8')
        time.sleep(0.05)
        maxwellccs.cc(pad1, 0, dest = 'LPD8')
    for pad2 in range(8,5,-1):
        maxwellccs.cc(pad2, 127, dest = 'LPD8')
        time.sleep(0.05)
        maxwellccs.cc(pad2, 0, dest = 'LPD8')
    maxwellccs.cc(1, 127, dest = 'LPD8')
    time.sleep(0.05)
    maxwellccs.cc(1, 0, dest = 'LPD8')


#       
# Events from OSC
#

# Client to export buttons actions from LPD8 or bhoreal

def SendOSC(ip,port,oscaddress,oscargs=''):
        
    oscmsg = OSCMessage()
    oscmsg.setAddress(oscaddress)
    oscmsg.append(oscargs)
    
    osclient = OSCClient()
    osclient.connect((ip, port)) 

    #print("sending OSC message : ", oscmsg, "to", ip, ":", port)

    try:
        osclient.sendto(oscmsg, (ip, port))
        oscmsg.clearData()
        return True
    except:
        print ('Connection to', ip, 'refused : died ?')
        return False

def FromOSC(path, args):

    if path.find('/rotary') > -1:

        #number = NoteXY(int(path[3:4]),int(path[2:3]))
        print('lpd8 OSC got rotary',path[2:4], args[0])
        Rotary(path[1:4], 1)

    if path.find('/button') > -1:

        #number = NoteXY(int(path[3:4]),int(path[2:3]))
        #print()
        print('lpd8 OSC got button', path[2:4], args[0])
        padCC('m'+path[2:4], int(args[0]))

# Send to Maxwell a pad value given its lpd8 matrix name
def padCC(buttonname, state):

    macronumber = findMacros(buttonname, gstt.lpd8Layers[gstt.lpd8Layer])
    #print('pad2CC :', buttonname, macronumber, state)
    
    if macronumber != -1:

        # Patch Led ?
        if state == 1:

            macrocode = macros[gstt.lpd8Layers[gstt.lpd8Layer]][macronumber]["code"]
            typevalue = macrocode[macrocode.rfind('/')+1:]
            values = list(enumerate(maxwellccs.specificvalues[typevalue]))
            init = macros[gstt.lpd8Layers[gstt.lpd8Layer]][macronumber]["init"]
            #print("matrix", buttonname, "macrocode", macrocode, "typevalue", typevalue,"macronumber", macronumber, "values", values, "init", init, "value", values[init][1], "cc", maxwellccs.FindCC(macrocode), "=", maxwellccs.specificvalues[typevalue][values[init][1]] )



            if init <0:

                # toggle button OFF -2 / ON -1
                if init == -2:
                    # goes ON
                    print(macrocode, 'ON')
                    maxwellccs.cc(maxwellccs.FindCC(macrocode), 127, 'to Maxwell 1')
                    macros[gstt.lpd8Layers[gstt.lpd8Layer]][macronumber]["init"] = -1
                else:
                    # goes OFF
                    print(macrocode, 'OFF')
                    maxwellccs.cc(maxwellccs.FindCC(macrocode), 0, 'to Maxwell 1')
                    macros[gstt.lpd8Layers[gstt.lpd8Layer]][macronumber]["init"] = -2

            else:
                # Many buttons (choices)
                # Reset all buttons 
                for button in range(macros[gstt.lpd8Layers[gstt.lpd8Layer]][macronumber]["choices"]):
                    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/lpd8/'+macros[gstt.lpd8Layers[gstt.LaunchpadLayer]][macronumber]["choice"+str(button)]+'/button', [0])

                maxwellccs.cc(maxwellccs.FindCC(macrocode), maxwellccs.specificvalues[typevalue][values[init][1]], 'to Maxwell 1')
        
                '''
                # Reset all buttons related to button name (see choices in lpd8.json)
                for button in range(macros[gstt.lpd8Layers[gstt.lpd8Layer]][macronumber]["choices"]):
                    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/lpd8/'+macros[gstt.lpd8Layers[gstt.lpd8Layer]][macronumber]["choice"+str(button)]+'/button', [0])

            
                maxwellccs.cc(maxwellccs.FindCC(macrocode), maxwellccs.specificvalues[typevalue][values[init][1]], 'to Maxwell 1')
                '''

        if state == 0:
            # Button released
            print('reselect button /lpd8/'+'m'+buttonname+'/button')
            SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/lpd8/'+'m'+buttonname+'/button', [1])

 

# send a CC to a local lpd8 (pads are on channel 10 with my lpd8 presets)
def CCpad(ccnumber, value, dest = mididest):

    #print("Sending Midi channel", midichannel, "cc", ccnumber, "value", value, "to", dest)
    #gstt.ccs[gstt.lasernumber][ccnumber]= value

    midi3.MidiMsg([CONTROLLER_CHANGE+ 10-1, ccnumber, value], dest)


#       
# Events from Midi
#


LPD8queue = Queue()


# LPD8 Mini call back : new msg forwarded to LPD8 queue 
class LPD8AddQueue(object):
    def __init__(self, port):
        self.port = port
        #print("LPD8AddQueue", self.port)
        self._wallclock = time.time()

    def __call__(self, event, data=None):
        message, deltatime = event
        self._wallclock += deltatime
        print()
        print("[%s] @%0.6f %r" % (self.port, self._wallclock, message))
        LPD8queue.put(message)


# Process events coming from LPD8 in a separate thread.

def MidinProcess(LPD8queue):
    global computer

 
    while True:
        LPD8queue_get = LPD8queue.get
        msg = LPD8queue_get()
        #print (msg)

        # Note
        if msg[0]==NOTE_ON:
  
            # note mode
            ModeNote(msg[1], msg[2], mididest)

            '''
            # ModeOS
            if msg[2] > 0:
                ModeOS(msg[0])
            '''


        # Program Change button selected : change destination computer
        if msg[0]==PROGRAM_CHANGE:
        
            print("Program change : ", str(msg[1]))
            # Change destination computer mode
            print("Destination computer",int(msg[1]))
            computer = int(msg[1])


        # CC rotary -> midi CC.         
        if msg[0] == CONTROLLER_CHANGE:

            print("CC :", msg[1], msg[2])

            if computer == 0 or computer == 1:
                maxwellccs.cc(int(msg[1]), int(msg[2]))

            else: 
                SendOSC(gstt.computerIP[computer-1], maxwellatorPort, '/cc', [int(msg[1]), int(msg[2])])


#
# lpd8 Patch UI
#


def ChangeLayer(layernumber, laser = 0):

    gstt.lpd8Layer = layernumber
    print('LPD8 layer :', layernumber)
    # update iPad UI
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/lpd8/status', [gstt.lpd8Layers[gstt.lpd8Layer]])
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/lpd8/m10/value', [format(layernumber, "03d")])
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/lpd8/m10/line1', ['Layer'])
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/lpd8/m10/line2', [''])
    UpdatePatch(gstt.patchnumber[laser])

def NLayer():

    print(gstt.lpd8Layer + 1, len(gstt.lpd8Layers))
    if gstt.lpd8Layer + 1 < len(gstt.lpd8Layers):
        ChangeLayer(gstt.lpd8Layer + 1)

def PLayer():

    if gstt.lpd8Layer != 0:
        ChangeLayer(gstt.lpd8Layer - 1)


def UpdatePatch(patchnumber):

    #print('lpd8 updatePatch', patchnumber)
    # update iPad UI
    #SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/lpd8/status', [gstt.lpd8Layers[gstt.lpd8Layer]])
    for macronumber in range(nbmacro):

        macrocode = macros[gstt.lpd8Layers[gstt.lpd8Layer]][macronumber]["code"]
        macroname = macros[gstt.lpd8Layers[gstt.lpd8Layer]][macronumber]["name"]
        macrotype = macros[gstt.lpd8Layers[gstt.lpd8Layer]][macronumber]["type"]
        #typevalue = macrocode[macrocode.rfind('/')+1:]

        #print()
        # print('number',macronumber, "code",macrocode, "name", macroname, "type", macrotype)

        if macrocode.count('/') > 0:
            macrocc = maxwellccs.FindCC(macrocode)
            macrolaser = macros[gstt.lpd8Layers[gstt.lpd8Layer]][macronumber]["laser"]
            

            # Display value
            #print("name",macroname, "cc", macrocc, "value", gstt.ccs[macrolaser][macrocc],"laser", macrolaser)
            SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/lpd8/'+macroname+'/value', [format(gstt.ccs[macrolaser][macrocc], "03d")])
            

            # Display text line 1
            if (macrocode[:macrocode.rfind('/')] in maxwellccs.shortnames) == True:
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/lpd8/'+macroname+'/line1', [maxwellccs.shortnames[macrocode[:macrocode.rfind('/')]]])
            else:
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/lpd8/'+macroname+'/line1', [macrocode[:macrocode.rfind('/')]])


            # Display text line 2
            if macronumber < 17 or (macronumber > 32 and macronumber < 50):

                # Encoders : cc function name like 'curvetype'
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/lpd8/'+macroname+'/line2', [macrocode[macrocode.rfind('/')+1:]])
            else:

                # button : cc function value like 'Square'
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/lpd8/'+macroname+'/button', [0])
                typevalue = macrocode[macrocode.rfind('/')+1:]
                #print('typevalue', typevalue)
                if  (typevalue in maxwellccs.specificvalues) == True:
                    #print(maxwellccs.specificvalues[typevalue])
                    values = list(enumerate(maxwellccs.specificvalues[typevalue]))
                    init = macros[gstt.lpd8Layers[gstt.lpd8Layer]][macronumber]["init"]
                    #print("init", init, "value", values[init][1] )
                    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/lpd8/'+macroname+'/line2', [values[init][1]])
                    print("line2", values[init][1] )
                else:
                    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/lpd8/'+macroname+'/line2', typevalue) 
                    #print("line2", typevalue )

            # Display laser number value
            SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/lpd8/'+macroname+'/laser', [macrolaser])
            

        else:
            SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/lpd8/'+macroname+'/line1', [macrocode])
     
# update LPD8 TouchOSC UI
def UpdateCC(ccnumber, value, laser = 0):

       
    # print('LPD8 UpdateCC', ccnumber, value)
    for macronumber in range(nbmacro):
        macrocode = macros[gstt.lpd8Layers[gstt.lpd8Layer]][macronumber]["code"]
        
        if macrocode == maxwellccs.maxwell['ccs'][ccnumber]['Function']:
           
            macroname = macros[gstt.lpd8Layers[gstt.lpd8Layer]][macronumber]["name"]
            SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/lpd8/'+macroname+'/value', [format(gstt.ccs[laser][ccnumber], "03d")])
            break


def Rotary(macroname, value):

    print("macro", macroname, "value", value)
    macronumber = findMacros(macroname, gstt.lpd8Layers[gstt.lpd8Layer])

    if macronumber != -1:
        macrocode = macros[gstt.lpd8Layers[gstt.lpd8Layer]][macronumber]["code"]
        print("lpd8 Layer", gstt.lpd8Layers[gstt.lpd8Layer], ":",macrocode)

        if macrocode.count('/') > 0:

            maxwellccs.EncoderPlusOne(value, path = macrocode)
            macrocc = maxwellccs.FindCC(macrocode)
            SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/lpd8/'+macroname+'/value', [format(gstt.ccs[0][macrocc], "03d")])

        else:
            print(macrocode+"("+str(value)+")")
            eval(macrocode+"("+str(value)+")")
    else:
        print("no callback")
 
#
# Modes :
# 

# Load Matrix only macros (for the moment) in LPD8.json 
def LoadMacros():
    global macros, nbmacro

    #print()
    #print("Loading LPD8 Macros...")

    if os.path.exists('LPD8.json'):
        #print('File is LPD8.json')
        f=open("LPD8.json","r")
    elif os.path.exists('../LPD8.json'):
            #print('File is ../lpd8.json')
            f=open("../LPD8.json","r")

    elif os.path.exists('libs/LPD8.json'):
        #print('File is libs/lpd8.json')
        f=open("libs/LPD8.json","r")

    elif os.path.exists(ljpath+'/../../libs/LPD8.json'):
        #print('File is '+ljpath+'/../../libs/lpd8.json')
        f=open(ljpath+"/../../libs/LPD8.json","r")





    s = f.read()
    macros = json.loads(s)
    #print(len(macros['OS']),"Macros")
    nbmacro = len(macros[gstt.lpd8Layers[gstt.lpd8Layer]])
    #print("Loaded.")


# return macroname number for given type 'OS', 'Maxwell'
def findMacros(macroname,macrotype):

    #print("searching", macroname,'...')
    position = -1
    for counter in range(len(macros[macrotype])):
        #print (counter,macros[macrotype][counter]['name'],macros[macrotype][counter]['code'])
        if macroname == macros[macrotype][counter]['name']:
            #print(macroname, "is ", counter)
            position = counter
    return position



LoadMacros()
SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/lpd8/status', ['LPD8'])
