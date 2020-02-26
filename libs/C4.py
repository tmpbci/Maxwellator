#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
C4
v0.7.0

C4 OSC UI Handler.
Start a dedicated thread to handle incoming events from C4 midi controller.

Each C4 'template' (recall button) will trigger different "layer" of functions.
Encoders and pads assigned midi channel select wich layer is used :

i.e : an encoder with midi channel 1 will trigger in first layer of functions.


Possible encoder & buttons functions (goes to "code" in C4.json)

- Maxwell parameter example 

    /osc/left/X/curvetype 

- External code examples
    
    maxwellccs.MinusOneRight
    subprocess.call(['/usr/bin/open','/Applications/iTerm.app'])



by Sam Neurohack 
from /team/laser

Depending on selected destination computer (Prog Chg + Pad number) actions will be done
locally or forwarded via OSC to given computer. Remote computer must run maxwellator.

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
import midi3, launchpad, gstt
#import midimacros, maxwellmacros
import traceback

from queue import Queue
#from libs import macros
import json, subprocess
from OSC3 import OSCServer, OSCClient, OSCMessage
import socket
import maxwellccs

#print()
print('C4 module...')
#myHostName = socket.gethostname()
#print("Name of the localhost is {}".format(myHostName))
#gstt.myIP = socket.gethostbyname(myHostName)
#print("IP address of the localhost is {}".format(gstt.myIP))

#maxwellatorPort = 8090

C4queue = Queue()

mode = "maxwell"
mididest = 'C4'
gstt.C4Layer = 0

midichannel = 1
CChannel = 0
CCvalue = 0
Here = -1

#nbmacro = 70
computer = 0


C4path = r'%s' % os.getcwd().replace('\\','/')

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

    #print("C4 sending OSC message : ", oscmsg, "to", ip, ":", port)

    try:
        osclient.sendto(oscmsg, (ip, port))
        oscmsg.clearData()
        return True
    except:
        print ('Connection to', ip, 'refused : died ?')
        return False


def FromOSC(path, args):

    #print("Incoming path", path)

    if path.find('/encoder') > -1:

        #number = NoteXY(int(path[3:4]),int(path[2:3]))
        print('C4 OSC got encoder',path[1:3], args[0])
        if args[0] == 1.0:
            Encoder('m'+path[1:3], 1)
        else:
            Encoder('m'+path[1:3], 127)


    if path.find('/button') > -1:

        #number = NoteXY(int(path[3:4]),int(path[2:3]))
        #print()
        if path.find('/prev') > -1:
            PLayer()
            
        elif path.find('/next') > -1:
            NLayer()

        else:
            print('C4 OSC got button', path[1:3], args[0])
            padCC('m'+path[1:3], int(args[0]))


    if path.find('/rotary') > -1:

        print('C4 OSC got rotary',path[1:3], args[0])
        if args[0] == 1.0:
            Rotary(path[1:3], 1)
        else:
            Rotary(path[1:3], 127)


# Send to Maxwell a pad value given its C4 matrix name
def padCC(buttonname, state):

    macronumber = findMacros(buttonname, gstt.C4Layers[gstt.C4Layer])
    #print('pad2CC :', buttonname, macronumber, state)
    
    if macronumber != -1:

        # Patch Led ?
        if state == 1:

            macrocode = macros[gstt.C4Layers[gstt.C4Layer]][macronumber]["code"]
            typevalue = macrocode[macrocode.rfind('/')+1:]
            values = list(enumerate(maxwellccs.specificvalues[typevalue]))
            init = macros[gstt.C4Layers[gstt.C4Layer]][macronumber]["init"]
            macrotype = macros[gstt.C4Layers[gstt.C4Layer]][macronumber]["type"]
            print("matrix", buttonname, "macrocode", macrocode, "typevalue", typevalue,"macronumber", macronumber, "type", macrotype, "values", values, "init", init, "value", values[init][1], "cc", maxwellccs.FindCC(macrocode), "=", maxwellccs.specificvalues[typevalue][values[init][1]] )

            # toggle button : init OFF -2 / ON -1
            if init <0:

                if init == -2:
                    # goes ON
                    print(macrocode, 'ON')
                    maxwellccs.cc(maxwellccs.FindCC(macrocode), 127, 'to Maxwell 1')
                    macros[gstt.C4Layers[gstt.C4Layer]][macronumber]["init"] = -1
                else:
                    # goes OFF
                    print(macrocode, 'OFF')
                    maxwellccs.cc(maxwellccs.FindCC(macrocode), 0, 'to Maxwell 1')
                    macros[gstt.C4Layers[gstt.C4Layer]][macronumber]["init"] = -2

            if macrotype =='buttonmulti':

                # Many buttons (choices)
                # Reset all buttons 
                macrochoices = list(macros[gstt.C4Layers[gstt.C4Layer]][macronumber]["choices"].split(","))
                print("Resetting choices", macrochoices)
                for choice in macrochoices:
                    #print('/C4/'+choice+'/button')
                    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/'+choice+'/button', [0])
                #for button in range(macros[gstt.C4Layers[gstt.C4Layer]][macronumber]["choices"]):
                #    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/'+macros[gstt.C4Layers[gstt.LaunchpadLayer]][macronumber]["choice"+str(button)]+'/button', [0])

                print(maxwellccs.FindCC(macrocode),maxwellccs.specificvalues[typevalue][values[init][1]] )                
                maxwellccs.cc(maxwellccs.FindCC(macrocode), maxwellccs.specificvalues[typevalue][values[init][1]], 'to Maxwell 1')
        
                '''
                # Reset all buttons related to button name (see choices in C4.json)
                for button in range(macros[gstt.C4Layers[gstt.C4Layer]][macronumber]["choices"]):
                    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/'+macros[gstt.C4Layers[gstt.C4Layer]][macronumber]["choice"+str(button)]+'/button', [0])

            
                maxwellccs.cc(maxwellccs.FindCC(macrocode), maxwellccs.specificvalues[typevalue][values[init][1]], 'to Maxwell 1')
                '''

        if state == 0:
            # Button released
            print('reselect button /C4/'+'m'+buttonname+'/button')
            SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/'+'m'+buttonname+'/button', [1])

 

def Encoder(macroname, value):

    macronumber = findMacros(macroname, gstt.C4Layers[gstt.C4Layer])
    print("macro", macroname, "value", value, 'macronumber', macronumber)

    if macronumber != -1:
        macrocode = macros[gstt.C4Layers[gstt.C4Layer]][macronumber]["code"]
        print("C4 Layer", gstt.C4Layers[gstt.C4Layer], ":",macrocode)

        if macrocode.count('/') > 0:

            # encoder slowly turned to right
            if value == 1:
                maxwellccs.EncoderPlusOne(value, path = macrocode)
                macrocc = maxwellccs.FindCC(macrocode)
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/'+macroname+'/value', [format(gstt.ccs[0][macrocc], "03d")])

            # encoder fastly turned to right
            if value > 1 and value <20:
                maxwellccs.EncoderPlusTen(value, path = macrocode)
                macrocc = maxwellccs.FindCC(macrocode)
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/'+macroname+'/value', [format(gstt.ccs[0][macrocc], "03d")])


            # encoder slowly turned to left
            if value == 127:
                maxwellccs.EncoderMinusOne(value, path = macrocode)
                macrocc = maxwellccs.FindCC(macrocode)
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/'+macroname+'/value', [format(gstt.ccs[0][macrocc], "03d")])


            # encoder fasly turned to left
            if value < 127 and value > 90:
                maxwellccs.EncoderMinusTen(value, path = macrocode)
                macrocc = maxwellccs.FindCC(macrocode)
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/'+macroname+'/value', [format(gstt.ccs[0][macrocc], "03d")])

        else:
            print(macrocode+"("+str(value)+")")
            eval(macrocode+"("+str(value)+")")
    else:
        print("no callback")




def Rotary(macroname, value):

    print("macro", macroname, "value", value)
    macronumber = findMacros(macroname, gstt.C4Layers[gstt.C4Layer])

    if macronumber != -1:
        macrocode = macros[gstt.C4Layers[gstt.C4Layer]][macronumber]["code"]
        print("C4 Layer", gstt.C4Layers[gstt.C4Layer], ":",macrocode)

        if macrocode.count('/') > 0:

            maxwellccs.EncoderPlusOne(value, path = macrocode)
            macrocc = maxwellccs.FindCC(macrocode)
            SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/'+macroname+'/value', [format(gstt.ccs[0][macrocc], "03d")])

        else:
            print(macrocode+"("+str(value)+")")
            eval(macrocode+"("+str(value)+")")
    else:
        print("no callback")
 



# send a CC to a local C4 (pads are on channel 10 with my C4 presets)
def CCpad(ccnumber, value, dest = mididest):

    #print("Sending Midi channel", midichannel, "cc", ccnumber, "value", value, "to", dest)
    #gstt.ccs[gstt.lasernumber][ccnumber]= value

    midi3.MidiMsg([CONTROLLER_CHANGE+ 10-1, ccnumber, value], dest)

def NoteOn(note,velocity, dest = mididest):
    midi3.NoteOn(note, velocity, mididest)

def NoteOff(note, dest = mididest):
    midi3.NoteOn(note, mididest)


def ComputerUpdate(comput):
    global computer

    computer = comput


#       
# Events from Midi
#


C4queue = Queue()


# C4 Mini call back : new msg forwarded to C4 queue 
class C4AddQueue(object):
    def __init__(self, port):
        self.port = port
        #print("C4AddQueue", self.port)
        self._wallclock = time.time()

    def __call__(self, event, data=None):
        message, deltatime = event
        self._wallclock += deltatime
        print()
        print("[%s] @%0.6f %r" % (self.port, self._wallclock, message))
        C4queue.put(message)


# Process events coming from C4 in a separate thread.

def MidinProcess(C4queue):
    global computer

 
    while True:
        C4queue_get = C4queue.get
        msg = C4queue_get()
        

        # Note
        if msg[0]==NOTE_ON:
  
            # note mode
            ModeNote(msg[1], msg[2], mididest)


        # Program Change button selected : change destination computer
        if msg[0]==PROGRAM_CHANGE:
        
            print("Program change : ", str(msg[1]))
            # Change destination computer mode
            print("Destination computer", int(msg[1]))
            computer = int(msg[1])


        # Midi Channel 1 : CCnumber is matrix name -> midi CC          
        if msg[0] == CONTROLLER_CHANGE:

            if computer == 0 or computer == 1:

                macroname= "m"+str(msg[1]) 
                macroargs = msg[2]
                print ('C4 midi got CC msg', msg, 'macro', macroname, macroargs)
                Encoder(macroname, macroargs)

            else: 
                SendOSC(gstt.computerIP[computer-1], gstt.MaxwellatorPort, '/cc', [int(msg[1]), int(msg[2])])


        # Midi Channel 10 : ccnumber is actual CC number 
        if msg[0] == CONTROLLER_CHANGE + 10 -1 and msg[2] > 0:

            macroname= "m"+str(msg[1]) 
            #macrocode = macros[gstt.C4Layers[gstt.C4Layer]][msg[1]]["code"]
            print("channel 10 macro",macroname, "ccnumber",msg[1], "value", msg[2])

            #SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/'+macroname+'/button', [1])
            gstt.ccs[gstt.lasernumber][msg[1]]= msg[2]

            if gstt.lasernumber == 0:
                # CC message is sent locally to channel 1
                midi3.MidiMsg([CONTROLLER_CHANGE+midichannel-1, msg[1], msg[2]], 'to Maxwell 1')
                #SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/'+macroname+'/button', [1])
            else:
                SendOSC(gstt.computerIP[gstt.lasernumber], gstt.MaxwellatorPort, '/cc/'+str(msg[1]),[msg[2]])


#
# C4 Patch UI
#

def UpdatePatch(patchnumber):

    #print('C4 updatePatch', patchnumber)

    # update iPad UI
    #SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/status', [gstt.C4Layers[gstt.C4Layer]])
    
    for macronumber in range(nbmacro):
        #print(macronumber, len(macros[gstt.C4Layers[gstt.C4Layer]]))
        macrocode = macros[gstt.C4Layers[gstt.C4Layer]][macronumber]["code"]
        macroname = macros[gstt.C4Layers[gstt.C4Layer]][macronumber]["name"]
        #print()
        #print('number',macronumber, "code",macrocode, 'name', macroname)

        # OSC command
        if macrocode.count('/') > 0:
            macrocc = maxwellccs.FindCC(macrocode)
            macrolaser = macros[gstt.C4Layers[gstt.C4Layer]][macronumber]["laser"]
            macrotype = macros[gstt.C4Layers[gstt.C4Layer]][macronumber]["type"]
            

            # Display VALUE
            #print("name",macroname, "cc", macrocc, "value", gstt.ccs[macrolaser][macrocc],"laser", macrolaser, 'type', macrotype)
            SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/'+macroname+'/value', [format(gstt.ccs[macrolaser][macrocc], "03d")])
            

            # Display text LINE 1
            if (macrocode[:macrocode.rfind('/')] in maxwellccs.shortnames) == True:
                
                if macrotype =='encoder':
                    #SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/'+macroname+'/line1', [maxwellccs.shortnames[macrocode[:macrocode.rfind('/')]]])
                    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/'+macroname+'/line1', [maxwellccs.shortnames[macrocode[:macrocode.rfind('/')]]+" "+macrocode[macrocode.rfind('/')+1:]])
                
                if macrotype.find('button') >-1:
                    typevalue = macrocode[macrocode.rfind('/')+1:]
                    values = list(enumerate(maxwellccs.specificvalues[typevalue]))
                    init = macros[gstt.C4Layers[gstt.C4Layer]][macronumber]["init"]
                    #print(values)
                    #print("button",macroname, init, type(values[init][1]))
                    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/'+macroname+'/line1', [maxwellccs.shortnames[macrocode[:macrocode.rfind('/')]]+" "+values[init][1]])

            else:
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/'+macroname+'/line1', [macrocode[:macrocode.rfind('/')]])


            # Display text LINE 2
            #if macronumber < 17 or (macronumber > 32 and macronumber < 50):
            if macrotype == 'encoder':

                # Encoders : cc function name like 'curvetype'
                #print("encoders", macrotype)
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/'+macroname+'/line2', [macrocode[macrocode.rfind('/')+1:]])
                

            #if macrotype == 'button':
            if macrotype.find('button') >0:

                # button : cc function value like 'Square'
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/'+macroname+'/button', [0])
                #typevalue = macrocode[macrocode.rfind('/')+1:]
                #values = list(enumerate(maxwellccs.specificvalues[typevalue]))
                #init = macros[gstt.C4Layers[gstt.C4Layer]][macronumber]["init"]
                #print("button", typevalue, macrotype)
                #print("init", init, "value", values[init][1] )
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/'+macroname+'/line2', [values[init][1]])


            # Display LASER number value
            SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/'+macroname+'/laser', [macrolaser])
            
        # Code function
        if macrocode.find('.') >0:
            # maxwellccs.something
            print(macrocode.index('.'))
            SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/'+macroname+'/line1', [macrocode[macrocode.index('.')+1:]])
     

def UpdateCC(ccnumber, value, laser = 0):

    #print('C4 UpdateCC', ccnumber, value)
    # update iPad UI
    for macronumber in range(33):
        macrocode = macros[gstt.C4Layers[gstt.C4Layer]][macronumber]["code"]
        
        if macrocode == maxwellccs.maxwell['ccs'][ccnumber]['Function']:
           
            macroname = macros[gstt.C4Layers[gstt.C4Layer]][macronumber]["name"]
            SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/'+macroname+'/value', [format(gstt.ccs[laser][ccnumber], "03d")])
            break
           

#
# C4 Layers
#

def ChangeLayer(layernumber, laser = 0):

    gstt.C4Layer = layernumber
    print('C4 layer :', layernumber)
    # update iPad UI
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/status', [gstt.C4Layers[gstt.C4Layer]])
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/m10/value', [format(layernumber, "03d")])
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/m10/line1', ['Layer'])
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/m10/line2', [''])
    UpdatePatch(gstt.patchnumber[laser])

def NLayer():

    print(gstt.C4Layer + 1, len(gstt.C4Layers))
    if gstt.C4Layer + 1 < len(gstt.C4Layers):
        ChangeLayer(gstt.C4Layer + 1)

def PLayer():

    if gstt.C4Layer != 0:
        ChangeLayer(gstt.C4Layer - 1)


# Change Layer
def CLayer(value):

    print('Change Layer button with value', value)
    if value < 20:

        NLayer()
    else:
        PLayer()


def Start(port):

    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/on', [1])

    # if pads are CC 0, 12, 36, 48
    CCpad(0, 1, dest = 'Arturia')
    CCpad(0, 33, dest = 'Arturia')
    CCpad(0, 95, dest = 'Arturia')
    CCpad(0, 127, dest = 'Arturia')
    time.sleep(0.3)
    CCpad(0, 0, dest = 'Arturia')
    CCpad(12, 0, dest = 'Arturia')
    CCpad(36, 0, dest = 'Arturia')
    CCpad(48, 0, dest = 'Arturia')


    '''
    # Circle effect
    # if Pads are matrix CCs 31-48
    for pad1 in range(31,39):
        CCpad(pad1, 0, dest = 'Arturia')
    for pad2 in range(41,49):
        CCpad(pad2, 0, dest = 'Arturia')

    for pad1 in range(31,39):
        CCpad(pad1, 127, dest = 'Arturia')
        time.sleep(0.01)
        CCpad(pad1, 0, dest = 'Arturia')
    for pad2 in range(49,41,-1):
        CCpad(pad2, 127, dest = 'Arturia')
        time.sleep(0.01)
        maxwellccs.cc(pad2, 0, dest = 'Arturia')
    CCpad(31, 127, dest = 'Arturia')
    time.sleep(0.01)
    CCpad(31, 0, dest = 'Arturia')
    '''



# Load Matrix only macros (for the moment) in C4.json 
def LoadMacros():
    global macros, nbmacro

    #print()
    #print("Loading C4 Macros...")

    if os.path.exists('C4.json'):
        #print('File matrix.json exits')
        f=open("C4.json","r")
    elif os.path.exists('../C4.json'):
            #print('File ../C4.json exits')
            f=open("../C4.json","r")

    elif os.path.exists('libs/C4.json'):
        #print('File libs/C4.json exits')
        f=open("libs/C4.json","r")

    elif os.path.exists(C4path+'/../../libs/C4.json'):
        #print('File '+C4path+'/../../libs/C4.json exits')
        f=open(C4path+"/../../libs/C4.json","r")

    s = f.read()
    macros = json.loads(s)
    #print(len(macros['OS']),"Macros")
    nbmacro = len(macros[gstt.C4Layers[gstt.C4Layer]])
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
SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/C4/status', ['C4'])

