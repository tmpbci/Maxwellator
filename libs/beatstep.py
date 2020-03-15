#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Beatstep
v0.7.0

Beatstep Handler.
Start a dedicated thread to handle incoming events from Beatstep midi controller.

Each Beatstep 'template' (recall button) will trigger different "layer" of functions.
Encoders and pads assigned midi channel select wich layer is used :

i.e : an encoder with midi channel 1 will trigger in first layer of functions.


Possible encoder & buttons functions (goes to "code" in beatstep.json)

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
print('Beatstep module...')
#myHostName = socket.gethostname()
#print("Name of the localhost is {}".format(myHostName))
#gstt.myIP = socket.gethostbyname(myHostName)
#print("IP address of the localhost is {}".format(gstt.myIP))

#maxwellatorPort = 8090

BEATSTEPqueue = Queue()

mode = "maxwell"
mididest = 'BeatStep'
# gstt.BeatstepLayer = 0

midichannel = 1
CChannel = 0
CCvalue = 0
Here = -1

numbertime = [time.time()]*40
#nbmacro = 33
computer = 0


ljpath = r'%s' % os.getcwd().replace('\\','/')

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

    #print("Beatstep sending OSC message : ", oscmsg, "to", ip, ":", port)

    try:
        osclient.sendto(oscmsg, (ip, port))
        oscmsg.clearData()
        return True
    except:
        print ('Connection to', ip, 'refused : died ?')
        return False


def FromOSC(path, args):

    print('Beatstep OSC got',path, args)
    if path.find('/encoder') > -1:

        #number = NoteXY(int(path[3:4]),int(path[2:3]))
        print('Beatstep OSC got encoder',path[2:4], args[0])
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
            print('Beatstep OSC got button', path[2:4], args[0])
            padCC('m'+path[2:4], int(args[0]))


#       
# Events from Midi
#


BEATSTEPqueue = Queue()


# Beatstep Mini call back : new msg forwarded to Beatstep queue 
class BeatstepAddQueue(object):
    def __init__(self, port):
        self.port = port
        #print("BeatstepAddQueue", self.port)
        self._wallclock = time.time()

    def __call__(self, event, data=None):
        message, deltatime = event
        self._wallclock += deltatime
        print()
        print("[%s] @%0.6f %r" % (self.port, self._wallclock, message))
        BEATSTEPqueue.put(message)


# Process events coming from Beatstep in a separate thread.

def MidinProcess(BEATSTEPqueue):
    global computer

 
    while True:

        BEATSTEPqueue_get = BEATSTEPqueue.get
        msg = BEATSTEPqueue_get()
        # print (msg)

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


        # Beatstep Encoders are on Midi Channel 1 : CCnumber is matrix name -> midi CC          
        if msg[0] == CONTROLLER_CHANGE:

            if computer == 0 or computer == 1:

                macroname= "m"+str(msg[1]) 
                macroargs = msg[2]
                MidiChannel = msg[0]-175
                MidiCC = msg[1]
                MidiVal = msg[2]
                Encoder(macroname, macroargs)

                # LccZcc

                '''
    
                # encoder slowly turned to right
                if MidiVal == 1:
                    +1
                # encoder fastly turned to right
                if MidiVal > 1 and MidiVal <20:
                    +10  
    
                # encoder slowly turned to left
                if MidiVal == 127:
                    -1
    
                # encoder fasly turned to left
                if MidiVal < 127 and MidiVal > 90:
                    -10

                gstt.ccs[0][MaxwellCC] + value
                
                '''

                if len(macros["LccZcc"]) > 0 :
                    # print("LccZcc test...", MidiChannel, MidiCC, MidiVal, macros["LccZcc"][0]["chanIN"], gstt.songs[gstt.song])
                    for counter in range(len(macros["LccZcc"])):
                        if (macros["LccZcc"][counter]["songname"] == gstt.songs[gstt.song] or macros["LccZcc"][counter]["songname"] == "all") and  (macros["LccZcc"][counter]["chanIN"] == MidiChannel or macros["LccZcc"][counter]["chanIN"] == "all") and (macros["LccZcc"][counter]["ccs"] == msg[1] or macros["LccZcc"][counter]["ccs"] == "all"):
                            print("LccZcc",macros["LccZcc"][counter]["songname"], ":", macros["LccZcc"][counter]["name"])
                            #print("LccZcc got song :", macros["LccZcc"][counter]["songname"],"  IN Channel :", macros["LccZcc"][counter]["chanIN"],"  Code :", macros["LccZcc"][counter]["code"], "  value :",macros["ZnotesLcc"][counter]["value"], )
                            if macros["LccZcc"][counter]["value"] == "linear":
                                print("Linear", MidiVal)
                                midi3.MidiMsg((176 + macros["LccZcc"][counter]["chanOUT"], macros["LccZcc"][counter]["ccOUT"], MidiVal), macros["LccZcc"][counter]["mididest"], laser = 0)

                            if macros["LccZcc"][counter]["value"] == "curved":
                                print(MidiVal,"got curved",maxwellccs.curved(MidiVal) )
                                midi3.MidiMsg((176 + macros["LccZcc"][counter]["chanOUT"], macros["LccZcc"][counter]["ccOUT"], maxwellccs.curved(MidiVal)), macros["LccZcc"][counter]["mididest"], laser = 0)


            else: 
                SendOSC(gstt.computerIP[computer-1], gstt.MaxwellatorPort, '/cc', [int(msg[1]), int(msg[2])])



        # Beatstep Pads are on channel 10
        if msg[0] == CONTROLLER_CHANGE + 10 -1:
        #if msg[0] == CONTROLLER_CHANGE + 10 -1 and msg[2] > 0:
            '''
            # if button cc number = m grid position
            print("channel 10 macro","m"+str(msg[1]) , "ccnumber",msg[1], "value", msg[2], macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][msg[1]]["code"])
            padCC('m'+str(msg[1]), msg[2])
            '''
            # if button is actually the cc number
            macronumber, state = findCCMacros(msg[1], msg[2], gstt.BeatstepLayers[gstt.BeatstepLayer])
            print("channel 10 macro","m"+str(msg[1]), "ccnumber",msg[1], "value", msg[2], "name", macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["name"], "macronumber", macronumber,"state", state, "code", macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["code"])
            
            padCC(macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["name"],state)
        
        '''
        # Midi Channel 10 : ccnumber is actual CC number 
        if msg[0] == CONTROLLER_CHANGE + 10 -1 and msg[2] > 0:

            macroname= "m"+str(msg[1]) 
            #macrocode = macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][msg[1]]["code"]
            print("channel 10 macro",macroname, "ccnumber",msg[1], "value", msg[2])

            #SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/'+macroname+'/button', [1])
            gstt.ccs[gstt.lasernumber][msg[1]]= msg[2]

            if gstt.lasernumber == 0:
                # CC message is sent locally to channel 1
                midi3.MidiMsg([CONTROLLER_CHANGE+midichannel-1, msg[1], msg[2]], 'to Maxwell 1')
                #SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/'+macroname+'/button', [1])
            else:
                SendOSC(gstt.computerIP[gstt.lasernumber], gstt.MaxwellatorPort, '/cc/'+str(msg[1]),[msg[2]])

        '''



# Send to Maxwell a pad value given its beatstep matrix name
def padCC(buttonname, state):

    macronumber = findMacros(buttonname, gstt.BeatstepLayers[gstt.BeatstepLayer])
    macrotype = macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["type"]
    #print()
    print("padCC buttoname", buttonname,"in", gstt.BeatstepLayers[gstt.BeatstepLayer], "macronumber" , macronumber, "state", state)
    
    #if macronumber != -1:

    # Patch Led ?
    if state >0:

        SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/'+buttonname+'/button', [1])
        macrocode = macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["code"]
        typevalue = macrocode[macrocode.rfind('/')+1:]
        values = list(enumerate(maxwellccs.specificvalues[typevalue]))
        init = macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["init"]
        #print("matrix", buttonname, "macrocode", macrocode, "typevalue", typevalue,"macronumber", macronumber, "values", values, "init", init, "value", values[init][1], "cc", maxwellccs.FindCC(macrocode), "=", maxwellccs.specificvalues[typevalue][values[init][1]] )
        numbertime[macronumber] = time.time()

        # Toggle Button
        if macrotype =='buttontoggle':

            # toggle button OFF -2 / ON -1
            if init == -2:
                # goes ON
                print(macrocode, 'ON')
                maxwellccs.cc(maxwellccs.FindCC(macrocode), 127, 'to Maxwell 1')
                macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["init"] = -1
            else:
                # goes OFF
                print(macrocode, 'OFF')
                maxwellccs.cc(maxwellccs.FindCC(macrocode), 0, 'to Maxwell 1')
                macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["init"] = -2
        
        # Many buttons (choices)
        if macrotype =='buttonmulti':

            # Reset all buttons 
            macrochoices = list(macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["choices"].split(","))
            numbertime[findMacros(macrochoices[3], gstt.BeatstepLayers[gstt.BeatstepLayer])] = time.time()
            for choice in macrochoices:
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/'+choice+'/button', [0])

            # Do the change
            maxwellccs.cc(maxwellccs.FindCC(macrocode), maxwellccs.specificvalues[typevalue][values[init][1]], 'to Maxwell 1')

        '''
        # simple action button
        if macrotype =='button':

            print(macrocode+"("+str(value)+',"'+macroname+'")')
            eval(macrocode+"("+str(value)+',"'+macroname+'")')
        '''
        '''
        else:
            # Many buttons (choices)
            # Reset all buttons 
            for button in range(macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["choices"]):
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/'+macros[gstt.BeatstepLayers[gstt.LaunchpadLayer]][macronumber]["choice"+str(button)]+'/button', [0])

            maxwellccs.cc(maxwellccs.FindCC(macrocode), maxwellccs.specificvalues[typevalue][values[init][1]], 'to Maxwell 1')
        '''

    if state == 0:
        # Button released
        macrocode = macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["code"]
        #print('reselect button /beatstep/'+buttonname+'/button')
        print('elapsed push :', buttonname, macrotype, macronumber, state, macrocode, time.time()-numbertime[macronumber])
        #numbertime[macronumber] = time.time()
        SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/'+buttonname+'/button', [0])
        
        if macronumber != -1 and macrotype == 'button':
            value = 0
 
            print(macrocode+"("+str(value)+',"'+buttonname+'")')
            eval(macrocode+"("+str(value)+',"'+buttonname+'")')

# send a CC to a local beatstep (pads are on channel 10 with my beatstep presets)
def CCpad(ccnumber, value, dest = mididest, channel = midichannel):

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
# Beatstep Patch UI
#

def ChangeLayer(layernumber, laser = 0):

    gstt.BeatstepLayer = layernumber
    print('BeatStep layer :', layernumber)
    # update iPad UI
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/status', [gstt.BeatstepLayers[gstt.BeatstepLayer]])
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/m10/value', [format(layernumber, "03d")])
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/m10/line1', ['Layer'])
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/m10/line2', [''])
    UpdatePatch(gstt.patchnumber[laser])

def NLayer():

    print(gstt.BeatstepLayer + 1, len(gstt.BeatstepLayers))
    if gstt.BeatstepLayer + 1 < len(gstt.BeatstepLayers):
        ChangeLayer(gstt.BeatstepLayer + 1)

def PLayer():

    if gstt.BeatstepLayer != 0:
        ChangeLayer(gstt.BeatstepLayer - 1)


def UpdatePatch(patchnumber):

    #print('Beatstep updatePatch', patchnumber)
    # update iPad UI
    # SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/status', [gstt.BeatstepLayers[gstt.BeatstepLayer]])
    for macronumber in range(nbmacro):

        macrocode = macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["code"]
        #print()
        #print('number',macronumber, "code",macrocode)

        if macrocode.count('/') > 0:
            macrocc = maxwellccs.FindCC(macrocode)
            macroname = macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["name"]
            macrolaser = macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["laser"]
            

            # Display value
            #print("name",macroname, "cc", macrocc, "value", gstt.ccs[macrolaser][macrocc],"laser", macrolaser)
            SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/'+macroname+'/value', [format(gstt.ccs[macrolaser][macrocc], "03d")])
            

            # Display text line 1
            if (macrocode[:macrocode.rfind('/')] in maxwellccs.shortnames) == True:
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/'+macroname+'/line1', [maxwellccs.shortnames[macrocode[:macrocode.rfind('/')]]])
            else:
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/'+macroname+'/line1', [macrocode[:macrocode.rfind('/')]])


            # Display text line 2
            if macronumber < 17 or (macronumber > 32 and macronumber < 50):

                # Encoders : cc function name like 'curvetype'
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/'+macroname+'/line2', [macrocode[macrocode.rfind('/')+1:]])
            else:

                # button : cc function value like 'Square'
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/'+macroname+'/button', [0])
                typevalue = macrocode[macrocode.rfind('/')+1:]
                values = list(enumerate(maxwellccs.specificvalues[typevalue]))
                #print('typevalue', typevalue)
                #print(maxwellccs.specificvalues[typevalue])
                init = macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["init"]
                #print("init", init, "value", values[init][1] )
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/'+macroname+'/line2', [values[init][1]])


            # Display laser number value
            SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/'+macroname+'/laser', [macrolaser])
            
        # Code in maxwellccs library : skip "maxwellccs." display only Empty. maxwellccs.Empty will call maxwellccs.Empty() 
        elif macrocode.find('maxwellccs') ==0:
                #print("BEATSTEP",macronumber, macrocode, '/beatstep/'+ macroname+'/line1', macrocode[11:])
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/'+ macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["name"]+'/line2', [macrocode[11:]])
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/'+macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["name"]+'/line1', [" "])
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/'+macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["name"]+'/value', [format(gstt.ccs[macrolaser][macrocc], "03d")])
                #print( '/beatstep/'+macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["name"]+'/value', [format(gstt.ccs[macrolaser][macrocc], "03d")])
        else:
            SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/'+macroname+'/line1', [macrocode])
     
# Update one CC value on TouchOSC Beatstep UI
def UpdateCC(ccnumber, value, laser = 0):

    #print('Beatstep UpdateCC', ccnumber, value)
    for macronumber in range(nbmacro):
        macrocode = macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["code"]
        
        if macrocode == maxwellccs.maxwell['ccs'][ccnumber]['Function']:
           
            macroname = macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["name"]
            SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/'+macroname+'/value', [format(gstt.ccs[laser][ccnumber], "03d")])
            break
           

# Load Matrix only macros (for the moment) in beatstep.json 
def LoadMacros():
    global macros, nbmacro

    #print()
    #print("Loading Beatstep Macros...")

    if os.path.exists('beatstep.json'):
        #print('File matrix.json exits')
        f=open("beatstep.json","r")
    elif os.path.exists('../beatstep.json'):
            #print('File ../beatstep.json exits')
            f=open("../beatstep.json","r")

    elif os.path.exists('libs/beatstep.json'):
        #print('File libs/beatstep.json exits')
        f=open("libs/beatstep.json","r")

    elif os.path.exists(ljpath+'/../../libs/beatstep.json'):
        #print('File '+ljpath+'/../../libs/beatstep.json exits')
        f=open(ljpath+"/../../libs/beatstep.json","r")



    s = f.read()
    macros = json.loads(s)
    #print(len(macros['OS']),"Macros")
    nbmacro = len(macros[gstt.BeatstepLayers[gstt.BeatstepLayer]])
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

# return macroname number for given type 'OS', 'Maxwell'
def findCCMacros(ccnumber, value, macrotype):

    #print("searching", ccnumber, value, "in", macrotype,'...')
    position = -1
    state = 0
    for counter in range(len(macros[macrotype])):
        #print (counter,macros[macrotype][counter]['name'],macros[macrotype][counter]['code'])
        macroname = macros[macrotype][counter]['name']
        macrocode = macros[macrotype][counter]['code']
        if (macroname[:2]=="m3" or macroname[:2]=="m4") and ccnumber == macros[macrotype][counter]['cc']:
            #print("macrorange", macroname)
            position = counter
            #print (counter, macroname, macroname[:2], macrocode, macros[macrotype][counter])

            if macrotype == 'buttonmulti' and value>0 and value == macros[macrotype][counter]['value']:
                print("button multi position is ", counter)
                position = counter
                state = 1
                break
    return position, state

# Start animation on first 4 pads.
def Start(port):

    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/on', [1])

    # if pads are CC 0, 12, 36, 48
    CCpad(0, 1, dest = 'BeatStep',channel = 10)
    CCpad(0, 33, dest = 'BeatStep',channel = 10)
    CCpad(0, 95, dest = 'Arturia',channel = 10)
    CCpad(0, 127, dest = 'Arturia',channel = 10)
    time.sleep(0.3)
    CCpad(0, 0, dest = 'Arturia',channel = 10)
    CCpad(12, 0, dest = 'Arturia',channel = 10)
    CCpad(36, 0, dest = 'Arturia',channel = 10)
    CCpad(48, 0, dest = 'Arturia',channel = 10)


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



def Encoder(macroname, value):


    #print("Encoder : macro", macroname, "value", value)
    macronumber = findMacros(macroname, gstt.BeatstepLayers[gstt.BeatstepLayer])

    if macronumber != -1:
        macrocode = macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["code"]
        #print("Beatstep Layer", gstt.BeatstepLayers[gstt.BeatstepLayer], ":",macrocode)

        if macrocode.count('/') > 0:

            # encoder slowly turned to right
            if value == 1:
                maxwellccs.EncoderPlusOne(value, path = macrocode)
                macrocc = maxwellccs.FindCC(macrocode)
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/'+macroname+'/value', [format(gstt.ccs[0][macrocc], "03d")])

            # encoder fastly turned to right
            if value > 1 and value <20:
                maxwellccs.EncoderPlusTen(value, path = macrocode)
                macrocc = maxwellccs.FindCC(macrocode)
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/'+macroname+'/value', [format(gstt.ccs[0][macrocc], "03d")])


            # encoder slowly turned to left
            if value == 127:
                maxwellccs.EncoderMinusOne(value, path = macrocode)
                macrocc = maxwellccs.FindCC(macrocode)
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/'+macroname+'/value', [format(gstt.ccs[0][macrocc], "03d")])


            # encoder fasly turned to left
            if value < 127 and value > 90:
                maxwellccs.EncoderMinusTen(value, path = macrocode)
                macrocc = maxwellccs.FindCC(macrocode)
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/'+macroname+'/value', [format(gstt.ccs[0][macrocc], "03d")])

        else:
            print(macrocode+"("+str(value)+',"'+macroname+'")')
            eval(macrocode+"("+str(value)+',"'+macroname+'")')
    else:
        print("no callback")
    '''
    SendOSC('127.0.0.1', monomePort, prefix+'/press', (x,y,1))
    SendOSC('127.0.0.1', monomePort, prefix+'/grid/key', (x,y,1))
    '''

# Change Layer
def CLayer(value):

    print('Change Layer button with value', value)
    if value < 20:

        NLayer()
    else:
        PLayer()


LoadMacros()
SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/beatstep/status', ['BEATSTEP'])

