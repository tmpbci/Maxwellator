#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
BCR 2000
v0.7.0

BCR 2000 Handler.
Start a dedicated thread to handle incoming events from BCR2000 midi controller.

Each BCR2000 'template' (recall button) will trigger different "layer" of functions.
Encoders and pads assigned midi channel select wich layer is used :

i.e : an encoder with midi channel 1 will trigger in first layer of functions.


Possible encoder & buttons functions (goes to "code" in bcr.json)

- Maxwell parameter example 

    /osc/left/X/curvetype 

- External code examples
    
    maxwellccs.MinusOneRight
    subprocess.call(['/usr/bin/open','/Applications/iTerm.app'])


Modes avances : cf bcr.json

Auto tempo      : chan 16 note 127 note on  
Mode resetCC    : chan 16 note 126 ON sur note on / OFF sur note off
Mode Bang       : chan 16 note 125 ON sur note on / OFF sur note off

Maxwell functions 

Color type      : chan 16 CC 123 LFO sur 127 / Solid sur 0


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
print('BCR2000 module...')
#myHostName = socket.gethostname()
#print("Name of the localhost is {}".format(myHostName))
#gstt.myIP = socket.gethostbyname(myHostName)
#print("IP address of the localhost is {}".format(gstt.myIP))

#maxwellatorPort = 8090

BCRqueue = Queue()

mode = "maxwell"
mididest = 'BCR2000'
gstt.BCRLayer = 0

midichannel = 1
CChannel = 0
CCvalue = 0
Here = -1

numbertime = [time.time()]*40
#nbmacro = 33
#computer = 0


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

    print('BCR2000 OSC got', path, args)
    if path.find('/encoder') > -1:

        #number = NoteXY(int(path[3:4]),int(path[2:3]))
        print('BCR2000 OSC got encoder',path[1:4], args[0])
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
            print('BCR2000 OSC got button', path[2:4], args[0])
            padCC('m'+path[2:4], int(args[0]))


#       
# Events from Midi
#


BCRqueue = Queue()


# BCR2000 Mini call back : new msg forwarded to BCR2000 queue 
class BCRAddQueue(object):
    def __init__(self, port):
        self.port = port
        #print("BCRAddQueue", self.port)
        self._wallclock = time.time()

    def __call__(self, event, data=None):
        message, deltatime = event
        self._wallclock += deltatime
        print()
        print("[%s] @%0.6f %r" % (self.port, self._wallclock, message))
        BCRqueue.put(message)


# Process events coming from BCR2000 in a separate thread.

def MidinProcess(BCRqueue):

 
    while True:

        BCRqueue_get = BCRqueue.get
        msg = BCRqueue_get()
        #print("BCR got", msg)

        # Noteon message on all midi channels   
        if NOTE_ON -1 < msg[0] < 160 and msg[2] !=0 :
  
            # note mode
            #ModeNote(msg[1], msg[2], mididest)

            MidiChannel = msg[0]-143
            MidiNote = msg[1]
            MidiVel = msg[2]
            print ("NOTE ON :", MidiNote, 'velocity :', MidiVel, "Channel", MidiChannel)
            

            # Specials features
            if len(macros["Specials"]) > 0:
                            
                for counter in range(len(macros["Specials"])):

                    #print()
                    #print("Name", macros["Specials"][counter]["name"])
                    #print("Song", macros["Specials"][counter]["songname"], gstt.songs[gstt.song])    # name, "all"
                    #print("Channel", macros["Specials"][counter]["chanIN"], MidiChannel)             # number, "all"
                    #print("Note", macros["Specials"][counter]["notes"], MidiNote)                    # number, "all"
                    #print("Notetype", macros["Specials"][counter]["notetype"], "on")                 # "on", "off", "all"

                    if (macros["Specials"][counter]["songname"] == gstt.songs[gstt.song] or macros["Specials"][counter]["songname"] == "all") and (macros["Specials"][counter]["chanIN"] == MidiChannel or macros["Specials"][counter]["chanIN"] == "all") and  (macros["Specials"][counter]["notes"] == MidiNote or macros["Specials"][counter]["notes"] == "all")  and  (macros["Specials"][counter]["notetype"] == "on" or macros["Specials"][counter]["notetype"] == "all") :
                        macrocode = macros["Specials"][counter]["code"]
                        print("Specials function :",macros["Specials"][counter]["songname"], ":", macros["Specials"][counter]["name"], macrocode)
                        
                        # python function on velocity > 0
                        if macrocode.count('.') > 0 and MidiVel > 0:
                            #print(macrocode+"("+str(MidiNote)+')')
                            eval(macrocode+"("+str(MidiNote)+')')

                        # Maxwell function
                        elif macrocode.count('/') > 0:
                            #print("Specials NoteON got Song :", macros["Specials"][counter]["songname"],"  IN Channel :", macros["Specials"][counter]["chanIN"],"  Code :", macrocode, "  CC", maxwellccs.FindCC(macros["Specials"][counter]["code"]), "  value :",macros["Specials"][counter]["value"], "  laser :", macros["ZccLcc"][counter]["laser"] )
                            midi3.MidiMsg((CONTROLLER_CHANGE, maxwellccs.FindCC(macros["Specials"][counter]["code"]), macros["Specials"][counter]["value"]), mididest, laser = macros["Specials"][counter]["laser"])



        # Note Off or Note with 0 velocity on all midi channels
        if NOTE_OFF -1 < msg[0] < 144 or (NOTE_OFF -1 < msg[0] < 160 and msg[2] == 0):

            if msg[0] > 144:
                MidiChannel = msg[0]-143
            else:
                MidiChannel = msg[0]-128
            
            MidiNote = msg[1]
            MidiVel = msg[2]

            print ("NOTE OFF :", MidiNote, "Channel", MidiChannel)
            

            # Specials features ?
            if len(macros["Specials"]) > 0:
                            
                for counter in range(len(macros["Specials"])):

                    # print()
                    # print("Name", macros["Specials"][counter]["name"])
                    # print("Song", macros["Specials"][counter]["songname"], gstt.songs[gstt.song])    # name, "all"
                    # print("Channel", macros["Specials"][counter]["chanIN"], MidiChannel)             # number, "all"
                    # print("Note", macros["Specials"][counter]["notes"], MidiNote)                    # number, "all"
                    # print("Notetype", macros["Specials"][counter]["notetype"], "on")                 # "on", "off", "all"

                    if (macros["Specials"][counter]["songname"] == gstt.songs[gstt.song] or macros["Specials"][counter]["songname"] == "all") and (macros["Specials"][counter]["chanIN"] == MidiChannel or macros["Specials"][counter]["chanIN"] == "all") and  (macros["Specials"][counter]["notes"] == MidiNote or macros["Specials"][counter]["notes"] == "all")  and  (macros["Specials"][counter]["notetype"] == "off" or macros["Specials"][counter]["notetype"] == "all") :
                        macrocode = macros["Specials"][counter]["code"]
                        print("Specials function :",macros["Specials"][counter]["songname"], ":", macros["Specials"][counter]["name"], macrocode)
                        
                        # python function
                        if macrocode.count('.') > 0:
                            #print(macrocode+"("+str(MidiNote)+')')
                            eval(macrocode+"("+str(MidiNote)+')')

                        # Maxwell function
                        elif macrocode.count('/') > 0:
                            #print("Specials NoteON got :", macros["Specials"][counter]["songname"],"  IN Channel :", macros["Specials"][counter]["chanIN"],"  Code :", macrocode, "  CC", maxwellccs.FindCC(macros["Specials"][counter]["code"]), "  value :",macros["Specials"][counter]["value"], "  laser :", macros["ZccLcc"][counter]["laser"] )
                            midi3.MidiMsg((CONTROLLER_CHANGE, maxwellccs.FindCC(macros["Specials"][counter]["code"]), macros["Specials"][counter]["value"]), mididest, laser = macros["Specials"][counter]["laser"])



        # Program Change button selected : change destination computer
        if msg[0]==PROGRAM_CHANGE:
        
            print("BCR Program change : ", str(msg[1]))
            # Change destination computer mode
            print("Destination computer", int(msg[1]))
            gstt.computer = int(msg[1])


        # CC on all Midi Channels         
        if CONTROLLER_CHANGE -1 < msg[0] < 192:

            if gstt.lasernumber == 0:

                #macroname= "m"+str(msg[1]) 
                #macroargs = msg[2]
                MidiChannel = msg[0]-175
                MidiCC = msg[1]
                MidiVal = msg[2]

                if gstt.resetCC == True:
                    gstt.ccs[0][MidiCC] =  64
                    print("BCR CC Reset on channel :",MidiChannel, "CC", MidiCC)
                    #print("Change CC (in bcr) : path =", path, "CC :", midi3.FindCC(path), "is now ", gstt.ccs[0][MaxwellCC])
                    maxwellccs.cc(MidiCC, 64 , midichannel = MidiChannel, dest ='to Maxwell 1')
                    SendOSCUI('/status', ["CC", MidiCC, "to 64"])

                else:
                    gstt.ccs[0][MidiCC] =  MidiVal
                    print("BCR CC change on channel :",MidiChannel, "CC", MidiCC, "Val", MidiVal)
                    #print("Change CC (in bcr) : path =", path, "CC :", midi3.FindCC(path), "is now ", gstt.ccs[0][MaxwellCC])
                    maxwellccs.cc(MidiCC, gstt.ccs[0][MidiCC] , midichannel = MidiChannel, dest ='to Maxwell 1')

                #midi3.MidiMsg([CONTROLLER_CHANGE+MidiChannel-1, MidiCC, MidiVal], "to Maxwell 1")
                # Encoder(macroname, macroargs)

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
                SendOSC(gstt.computerIP[gstt.lasernumber], gstt.MaxwellatorPort, '/cc/'+str(msg[1]), [int(msg[2])])
                #SendOSC(gstt.computerIP[gstt.computer-1], gstt.MaxwellatorPort, '/cc', [int(msg[1]), int(msg[2])])
                print("storing for laser", gstt.lasernumber, "CC", int(msg[1]), "value", int(msg[2]))
                gstt.ccs[gstt.lasernumber][int(msg[1])] =  int(msg[2])


        '''
        # BCR2000 Pads are on channel 10
        if msg[0] == CONTROLLER_CHANGE + 10 -1:

            # if button is actually the cc number
            macronumber, state = findCCMacros(msg[1], msg[2], gstt.BCRLayers[gstt.BCRLayer])
            print("BCR pads channel 10 macro","m"+str(msg[1]), "ccnumber",msg[1], "value", msg[2], "name", macros[gstt.BCRLayers[gstt.BCRLayer]][macronumber]["name"], "macronumber", macronumber,"state", state, "code", macros[gstt.BCRLayers[gstt.BCRLayer]][macronumber]["code"])
            
            padCC(macros[gstt.BCRLayers[gstt.BCRLayer]][macronumber]["name"],state)
        

        # Midi Channel 10 : ccnumber is actual CC number 
        if msg[0] == CONTROLLER_CHANGE + 10 -1 and msg[2] > 0:

            macroname= "m"+str(msg[1]) 
            #macrocode = macros[gstt.BCRLayers[gstt.BCRLayer]][msg[1]]["code"]
            print("channel 10 macro",macroname, "ccnumber",msg[1], "value", msg[2])

            #SendOSCUI('/bcr/'+macroname+'/button', [1])
            gstt.ccs[gstt.lasernumber][msg[1]]= msg[2]

            if gstt.lasernumber == 0:
                # CC message is sent locally to channel 1
                midi3.MidiMsg([CONTROLLER_CHANGE+midichannel-1, msg[1], msg[2]], 'to Maxwell 1')
                #SendOSCUI('/bcr/'+macroname+'/button', [1])
            else:
                SendOSC(gstt.computerIP[gstt.lasernumber], gstt.MaxwellatorPort, '/cc/'+str(msg[1]),[msg[2]])

        '''



# Send to Maxwell a pad value given its BCR2000 matrix name
def padCC(buttonname, state):

    macronumber = findMacros(buttonname, gstt.BCRLayers[gstt.BCRLayer])
    print("padCC buttoname", buttonname,"in", gstt.BCRLayers[gstt.BCRLayer], "macronumber" , macronumber, "state", state)
    macrotype = macros[gstt.BCRLayers[gstt.BCRLayer]][macronumber]["type"]
    macrocode = macros[gstt.BCRLayers[gstt.BCRLayer]][macronumber]["code"]
    typevalue = macrocode[macrocode.rfind('/')+1:]
    #print("typevalue :", typevalue, macros[gstt.BCRLayers[gstt.BCRLayer]][macronumber] )
    values = list(enumerate(maxwellccs.specificvalues[typevalue]))
    #print("matrix :", buttonname, "macrocode :", macrocode, "typevalue :", typevalue,"macronumber :", macronumber, "values :", values, "cc :", maxwellccs.FindCC(macrocode) )
    init = macros[gstt.BCRLayers[gstt.BCRLayer]][macronumber]["init"]

 
    #print("matrix :", buttonname, "macrocode :", macrocode, "typevalue :", typevalue,"macronumber :", macronumber, "values :", values, "init :", init, "value :", values[init][1], "cc :", maxwellccs.FindCC(macrocode), "=", maxwellccs.specificvalues[typevalue][values[init][1]] )

    # Patch Led ?
    if state >0:

        SendOSCUI('/bcr/'+buttonname+'/button', [1])
        numbertime[macronumber] = time.time()

        # Toggle Button
        if macrotype =='buttontoggle':

            # toggle button OFF -2 / ON -1
            if init == -2:
                # goes ON
                print(macrocode, 'ON')
                SendOSCUI('/status', [macrocode+" ON"])
                SendOSCUI('/bcr/status', [macrocode+" ON"])
                maxwellccs.cc(maxwellccs.FindCC(macrocode), 127, 'to Maxwell 1')
                macros[gstt.BCRLayers[gstt.BCRLayer]][macronumber]["init"] = -1
            else:
                # goes OFF
                print(macrocode, 'OFF')
                SendOSCUI('/status', [macrocode+" OFF"])
                SendOSCUI('/bcr/status', [macrocode+" OFF"])
                maxwellccs.cc(maxwellccs.FindCC(macrocode), 0, 'to Maxwell 1')
                macros[gstt.BCRLayers[gstt.BCRLayer]][macronumber]["init"] = -2
        
        # Many buttons (choices)
        if macrotype =='buttonmulti':

            # Reset all buttons 
            macrochoices = list(macros[gstt.BCRLayers[gstt.BCRLayer]][macronumber]["choices"].split(","))
            numbertime[findMacros(macrochoices[3], gstt.BCRLayers[gstt.BCRLayer])] = time.time()
            for choice in macrochoices:
                SendOSCUI('/bcr/'+choice+'/button', [0])

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
            for button in range(macros[gstt.BCRLayers[gstt.BCRLayer]][macronumber]["choices"]):
                SendOSCUI('/bcr/'+macros[gstt.BCRLayers[gstt.LaunchpadLayer]][macronumber]["choice"+str(button)]+'/button', [0])

            maxwellccs.cc(maxwellccs.FindCC(macrocode), maxwellccs.specificvalues[typevalue][values[init][1]], 'to Maxwell 1')
        '''

    # Button released
    if state == 0:
        
        #print('reselect button /bcr/'+buttonname+'/button')
        print('elapsed push :', buttonname, macrotype, macronumber, state, macrocode, time.time()-numbertime[macronumber])
        #numbertime[macronumber] = time.time()
        SendOSCUI('/bcr/'+buttonname+'/button', [0])
        
        if macronumber != -1 and macrotype == 'button':
            value = 0
 
            # python function
            if macrocode.count('.') > 0:
                print(macrocode+"("+str(value)+',"'+buttonname+'")')
                eval(macrocode+"("+str(value)+',"'+buttonname+'")')

            # Maxwell function
            elif macrocode.count('/') > 0:
                maxwellccs.cc(maxwellccs.FindCC(macrocode), maxwellccs.specificvalues[typevalue][values[init][1]], 'to Maxwell 1')



# send a CC to a local BCR2000 (pads are on channel 10 with my BCR2000 presets)
def CCpad(ccnumber, value, dest = mididest, channel = midichannel):

    #print("Sending Midi channel", midichannel, "cc", ccnumber, "value", value, "to", dest)
    #gstt.ccs[gstt.lasernumber][ccnumber]= value

    midi3.MidiMsg([CONTROLLER_CHANGE+ 10-1, ccnumber, value], dest)

def NoteOn(note,velocity, dest = mididest):
    midi3.NoteOn(note, velocity, mididest)

def NoteOff(note, dest = mididest):
    midi3.NoteOn(note, mididest)


def ComputerUpdate(comput):

    gstt.computer = comput


#
# BCR2000 Patch UI
#

def ChangeLayer(layernumber, laser = 0):

    gstt.BCRLayer = layernumber
    print('BCR2000 layer :', layernumber)
    # update iPad UI
    SendOSCUI('/bcr/status', [gstt.BCRLayers[gstt.BCRLayer]])
    UpdatePatch(gstt.patchnumber[laser])

def NLayer():

    print(gstt.BCRLayer + 1, len(gstt.BCRLayers))
    if gstt.BCRLayer + 1 < len(gstt.BCRLayers):
        ChangeLayer(gstt.BCRLayer + 1)

def PLayer():

    if gstt.BCRLayer != 0:
        ChangeLayer(gstt.BCRLayer - 1)


def UpdatePatch(patchnumber):

    
    # update iPad UI
    
    #print('BCR2000 updatePatch', patchnumber)
    # SendOSCUI('/bcr/status', [gstt.BCRLayers[gstt.BCRLayer]])
    for macronumber in range(nbmacro):

        macrocode = macros[gstt.BCRLayers[gstt.BCRLayer]][macronumber]["code"]
        #print()
        #print('number',macronumber, "code",macrocode)

        if macrocode.count('/') > 0:
            macrocc = maxwellccs.FindCC(macrocode)
            macroname = macros[gstt.BCRLayers[gstt.BCRLayer]][macronumber]["name"]
            macrolaser = macros[gstt.BCRLayers[gstt.BCRLayer]][macronumber]["laser"]
            

            # Display value
            # print("name",macroname, "cc", macrocc, "value", gstt.ccs[macrolaser][macrocc],"laser", macrolaser)
            SendOSCUI('/bcr/'+macroname+'/value', [format(gstt.ccs[macrolaser][macrocc], "03d")])
            

            # Display text line 1
            if (macrocode[:macrocode.rfind('/')] in maxwellccs.shortnames) == True:
                # print(macroname,"line 1",maxwellccs.shortnames[macrocode[:macrocode.rfind('/')]])
                SendOSCUI('/bcr/'+macroname+'/line1', [maxwellccs.shortnames[macrocode[:macrocode.rfind('/')]]+" "+macrocode[macrocode.rfind('/')+1:]])
                #SendOSCUI('/bcr/'+macroname+'/line1', [maxwellccs.shortnames[macrocode[:macrocode.rfind('/')]]])
            else:
                # print(macroname,"line 1",macrocode[:macrocode.rfind('/')])
                SendOSCUI('/bcr/'+macroname+'/line1', [macrocode[:macrocode.rfind('/')]])

            # Display laser number value
            SendOSCUI('/bcr/'+macroname+'/laser', [macrolaser])
            
        # Code in maxwellccs library : skip "maxwellccs." display only Empty. maxwellccs.Empty will call maxwellccs.Empty() 
        elif macrocode.find('maxwellccs') ==0:
                #print("BCR 2000",macronumber, macrocode, '/bcr/'+ macroname+'/line1', macrocode[11:])
                SendOSCUI('/bcr/'+ macros[gstt.BCRLayers[gstt.BCRLayer]][macronumber]["name"]+'/line2', [" "])
                SendOSCUI('/bcr/'+macros[gstt.BCRLayers[gstt.BCRLayer]][macronumber]["name"]+'/line1', [macrocode[11:]])
                SendOSCUI('/bcr/'+macros[gstt.BCRLayers[gstt.BCRLayer]][macronumber]["name"]+'/value', [format(gstt.ccs[macrolaser][macrocc], "03d")])
                #print( '/bcr/'+macros[gstt.BCRLayers[gstt.BCRLayer]][macronumber]["name"]+'/value', [format(gstt.ccs[macrolaser][macrocc], "03d")])
        else:
            SendOSCUI('/bcr/'+macroname+'/line1', [macrocode])
     

# Update one CC value to BCR 2000 via MIDI and TouchOSC BCR 2000 UI
def UpdateCC(ccnumber, value, laser = 0):

    # Update TouchOSC UI
    # print('BCR 2000 UpdateCC', ccnumber, value, "or", gstt.ccs[laser][ccnumber], "?")
    for macronumber in range(nbmacro):
        macrocode = macros[gstt.BCRLayers[gstt.BCRLayer]][macronumber]["code"]
        
        if macrocode == maxwellccs.maxwell['ccs'][ccnumber]['Function']:
           
            macroname = macros[gstt.BCRLayers[gstt.BCRLayer]][macronumber]["name"]
            
            SendOSCUI('/bcr/'+macroname+'/value', [format(value, "03d")])
            #SendOSCUI('/bcr/'+macroname+'/value', [format(gstt.ccs[laser][ccnumber], "03d")])

            # Update BCR 2000 via MIDI if connected.
            if Here != -1:
                midi3.MidiMsg([CONTROLLER_CHANGE, ccnumber, value], "BCR2000")
                #midi3.MidiMsg([CONTROLLER_CHANGE, ccnumber, gstt.ccs[laser][ccnumber]], "BCR2000")
            
            break


# Load Matrix only macros (for the moment) in bcr.json 
def LoadMacros():
    global macros, nbmacro

    #print()
    #print("Loading BCR2000 Macros...")

    if os.path.exists('bcr.json'):
        #print('File matrix.json exits')
        f=open("bcr.json","r")
    elif os.path.exists('../bcr.json'):
            #print('File ../bcr.json exits')
            f=open("../bcr.json","r")

    elif os.path.exists('libs/bcr.json'):
        #print('File libs/bcr.json exits')
        f=open("libs/bcr.json","r")

    elif os.path.exists(ljpath+'/../../libs/bcr.json'):
        #print('File '+ljpath+'/../../libs/bcr.json exits')
        f=open(ljpath+"/../../libs/bcr.json","r")



    s = f.read()
    macros = json.loads(s)
    #print(len(macros['OS']),"Macros")
    nbmacro = len(macros[gstt.BCRLayers[gstt.BCRLayer]])
    #print("Loaded.")


# return macroname number for given type 'OS', 'Maxwell'
def findMacros(macroname, macrotype):

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

def Start(port):


    SendOSCUI('/bcr/on', [1])
    
    '''
    Startline = [0]
    # if pads are CC 0, 12, 36, 48
    for encoder in Startline:
        for value in range(0, 127, 15):

            midi3.MidiMsg([CONTROLLER_CHANGE, encoder, value], mididest = 'BCR2000 Port 1')
            time.sleep(0.02)
        midi3.MidiMsg([CONTROLLER_CHANGE, encoder, 0], mididest = 'BCR2000 Port 1')
    '''

def Encoder(macroname, value):

    print("Encoder : macro", macroname, "value", value)
    macronumber = findMacros(macroname, gstt.BCRLayers[gstt.BCRLayer])

    if macronumber != -1:
        macrocode = macros[gstt.BCRLayers[gstt.BCRLayer]][macronumber]["code"]
        print("BCR 2000 Layer", gstt.BCRLayers[gstt.BCRLayer], ":", macrocode)

        if macrocode.count('/') > 0:

            # encoder slowly turned to right
            if value == 1:
                maxwellccs.EncoderPlusOne(value, path = macrocode)
                macrocc = maxwellccs.FindCC(macrocode)
                SendOSCUI('/bcr/'+macroname+'/value', [format(gstt.ccs[0][macrocc], "03d")])

            # encoder fastly turned to right
            if value > 1 and value <20:
                maxwellccs.EncoderPlusTen(value, path = macrocode)
                macrocc = maxwellccs.FindCC(macrocode)
                SendOSCUI('/bcr/'+macroname+'/value', [format(gstt.ccs[0][macrocc], "03d")])


            # encoder slowly turned to left
            if value == 127:
                maxwellccs.EncoderMinusOne(value, path = macrocode)
                macrocc = maxwellccs.FindCC(macrocode)
                SendOSCUI('/bcr/'+macroname+'/value', [format(gstt.ccs[0][macrocc], "03d")])


            # encoder fasly turned to left
            if value < 127 and value > 90:
                maxwellccs.EncoderMinusTen(value, path = macrocode)
                macrocc = maxwellccs.FindCC(macrocode)
                SendOSCUI('/bcr/'+macroname+'/value', [format(gstt.ccs[0][macrocc], "03d")])

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
SendOSCUI('/bcr/status', ['BCR 2000'])

