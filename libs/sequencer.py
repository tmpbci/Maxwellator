#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Sequencer
v0.7.0

Sequencer Handler.
Start a dedicated thread to handle incoming events from Sequencer midi controller.

Each Sequencer 'template' (recall button) will trigger different "layer" of functions.
Encoders and pads assigned midi channel select wich layer is used :

i.e : an encoder with midi channel 1 will trigger in first layer of functions.


Possible encoder & buttons functions (goes to "code" in Sequencer.json)

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
print('Sequencer module...')
#myHostName = socket.gethostname()
#print("Name of the localhost is {}".format(myHostName))
#gstt.myIP = socket.gethostbyname(myHostName)
#print("IP address of the localhost is {}".format(gstt.myIP))

#maxwellatorPort = 8090

SEQUENCERqueue = Queue()

mode = "maxwell"
mididest = 'to Maxwell 1'
gstt.SequencerLayer = 0

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

    #print("Sequencer sending OSC message : ", oscmsg, "to", ip, ":", port)

    try:
        osclient.sendto(oscmsg, (ip, port))
        oscmsg.clearData()
        return True
    except:
        print ('Connection to', ip, 'refused : died ?')
        return False


def FromOSC(path, args):

    if path.find('/encoder') > -1:

        #number = NoteXY(int(path[3:4]),int(path[2:3]))
        print('Sequencer OSC got encoder',path[2:4], args[0])
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
            print('Sequencer OSC got button', path[2:4], args[0])
            padCC('m'+path[2:4], int(args[0]))


#       
# Events from Midi
#


SEQUENCERqueue = Queue()


# Sequencer Mini call back : new msg forwarded to Sequencer queue 
class SequencerAddQueue(object):
    def __init__(self, port):
        self.port = port
        #print("SequencerAddQueue", self.port)
        self._wallclock = time.time()

    def __call__(self, event, data=None):
        message, deltatime = event
        self._wallclock += deltatime
        message.append(deltatime)
        #print()
        #print("[%s] @%0.6f %r" % (self.port, self._wallclock, message))
        SEQUENCERqueue.put(message)


# Process events coming from Sequencer in a separate thread.

def MidinProcess(SEQUENCERqueue):
    global computer

 
    while True:

        SEQUENCERqueue_get = SEQUENCERqueue.get
        msg = SEQUENCERqueue_get()
        print()
        print ("Sequencer got msg ;", msg[0], msg[1], msg[2])


        # NOTE ON message (will trigger even if midivel = 0)
        if NOTE_ON -1 < msg[0] < 160:
  
            # note mode
            #ModeNote(msg[1], msg[2], mididest)
            #print(type(portname), portname, gstt.Midikeyboards, portname in gstt.Midikeyboards)

            #if portname in gstt.Midikeyboards:

            MidiChannel = msg[0]-144
            MidiNote = msg[1]
            MidiVel = msg[2]
            print ("NOTE ON :", MidiNote, 'velocity :', MidiVel, "Channel", MidiChannel)
            
            '''
            NoteOn(msg[1], msg[2], "Bus 1")
            
            
            # Lead : RIGHT part, for richter midi file : lead minimal note is E3 (64)
            if MidiNote > gstt.MidiSplitNote:

                # right curvetype is sin
                #SendCC('/osc/right/X/curvetype',0)
                #MidiMsg((CONTROLLER_CHANGE,36,0),mididest)

                # octave is frequency. 25.6 is CC range (128)/5 low octave
                #SendCC('/lfo/2/freq',round(MidiNote/12)*25.6)
                midi3.MidiMsg((CONTROLLER_CHANGE, 80, round(MidiNote/12)*25.6), mididest)
                
                # note is phase : decimal part of midinote number = CC range percentage 
                #SendCC('/lfo/2/phase',(MidiNote/12)%1*128)
                midi3.MidiMsg((CONTROLLER_CHANGE, 78, (MidiNote/12)%1*128), mididest)

                # velocity is scale
                midi3.MidiMsg((CONTROLLER_CHANGE, 98, MidiVel), mididest)

            # if note < 64 (E3) set LEFT part
            else:

                # If lead note set a preset :
                # midi3.NoteOn(MidiFileNote-63, MidiFileVel,'to Maxwell 1')
                
                # left curvetype is sin
                #SendCC('/osc/left/X/curvetype',0)
                #MidiMsg((CONTROLLER_CHANGE,0,0),mididest)

                # octave is frequency. 25.6 is CC range (128)/5 low "pentatonic octave"
                #SendCC('/lfo/1/freq',round(MidiNote/12)*25.6)
                midi3.MidiMsg((CONTROLLER_CHANGE,75,round(MidiNote/12)*25.6),mididest)

                # note is phase : decimal part of midinote number = CC range percentage 
                #SendCC('/lfo/1/phase',(MidiNote/12)%1*128)
                midi3.MidiMsg((CONTROLLER_CHANGE,73,(MidiNote/12)%1*128),mididest)

                # velocity is scale
                midi3.MidiMsg((CONTROLLER_CHANGE,98,MidiVel),mididest)
            '''
            # ZnotesLcc
            if len(macros["ZnotesLcc"]) > 0:
                
                for counter in range(len(macros["ZnotesLcc"])):

                    print()
                    print("Name", macros["ZnotesLcc"][counter]["name"])
                    print("Song", macros["ZnotesLcc"][counter]["songname"], gstt.songs[gstt.song])    # name, "all"
                    print("Channel", macros["ZnotesLcc"][counter]["chanIN"], MidiChannel)             # number, "all"
                    print("Note", macros["ZnotesLcc"][counter]["notes"], MidiNote)                    # number, "all"
                    print("Notetype", macros["ZnotesLcc"][counter]["notetype"], "on")                 # "on", "off", "all"

                    if (macros["ZnotesLcc"][counter]["songname"] == gstt.songs[gstt.song] or macros["ZnotesLcc"][counter]["songname"] == "all") and (macros["ZnotesLcc"][counter]["chanIN"] == MidiChannel or macros["ZnotesLcc"][counter]["chanIN"] == "all") and  (macros["ZnotesLcc"][counter]["notes"] == MidiNote or macros["ZnotesLcc"][counter]["notes"] == "all")  and  (macros["ZnotesLcc"][counter]["notetype"] == "on" or macros["ZnotesLcc"][counter]["notetype"] == "all") :
                        print("selection of ",macros["ZnotesLcc"][counter]["songname"], ":", macros["ZnotesLcc"][counter]["name"])
                        #print("ZnotesLcc NoteON got Song :", macros["ZnotesLcc"][counter]["songname"],"  IN Channel :", macros["ZnotesLcc"][counter]["chanIN"],"  Code :", macros["ZnotesLcc"][counter]["code"], "  CC", maxwellccs.FindCC(macros["ZnotesLcc"][counter]["code"]), "  value :",macros["ZnotesLcc"][counter]["value"], "  laser :", macros["ZccLcc"][counter]["laser"] )
                        midi3.MidiMsg((CONTROLLER_CHANGE, maxwellccs.FindCC(macros["ZnotesLcc"][counter]["code"]), macros["ZnotesLcc"][counter]["value"]), mididest, laser = macros["ZccLcc"][counter]["laser"])

            # Note ON Specials features
            if len(macros["Specials"]) > 0:
                
                for counter in range(len(macros["Specials"])):

                    '''
                    print()
                    print("Name", macros["Specials"][counter]["name"])
                    print("Song", macros["Specials"][counter]["songname"], gstt.songs[gstt.song])    # name, "all"
                    print("Channel", macros["Specials"][counter]["chanIN"], MidiChannel)             # number, "all"
                    print("Note", macros["Specials"][counter]["notes"], MidiNote)                    # number, "all"
                    print("Notetype", macros["Specials"][counter]["notetype"], "on")                 # "on", "off", "all"
                    '''

                    if (macros["Specials"][counter]["songname"] == gstt.songs[gstt.song] or macros["Specials"][counter]["songname"] == "all") and (macros["Specials"][counter]["chanIN"] == MidiChannel or macros["Specials"][counter]["chanIN"] == "all") and  (macros["Specials"][counter]["notes"] == MidiNote or macros["Specials"][counter]["notes"] == "all")  and  (macros["Specials"][counter]["notetype"] == "on" or macros["Specials"][counter]["notetype"] == "all") :
                        macrocode = macros["Specials"][counter]["code"]
                        # print("Specials function :",macros["Specials"][counter]["songname"], ":", macros["Specials"][counter]["name"], macrocode)
                        
                        # python function
                        if macrocode.count('.') > 0 and MidiVel > 0:
                            print(macrocode+"("+str(MidiNote)+')')
                            eval(macrocode+"("+str(MidiNote)+')')

                        # Maxwell function
                        elif macrocode.count('/') > 0 and MidiVel > 0:
                            print("Specials NoteON got Song :", macros["Specials"][counter]["songname"],"  IN Channel :", macros["Specials"][counter]["chanIN"],"  Code :", macrocode, "  CC", maxwellccs.FindCC(macros["Specials"][counter]["code"]), "  value :",macros["Specials"][counter]["value"], "  laser :", macros["ZccLcc"][counter]["laser"] )
                            midi3.MidiMsg((CONTROLLER_CHANGE, maxwellccs.FindCC(macros["Specials"][counter]["code"]), macros["Specials"][counter]["value"]), mididest, laser = macros["Specials"][counter]["laser"])


        # Note Off
        if msg[0]==NOTE_OFF:

            MidiChannel = msg[0]-128
            MidiNote = msg[1]

            print ("NOTE OFF :", MidiNote, "Channel", MidiChannel)
            #NoteOff(msg[1],msg[2], mididest)
            # NoteOff(msg[2], mididest)
            # Webstatus(''.join(("note ",msg[1]," to ",msg[2])))
            
            # ZnotesLcc
            if len(macros["ZnotesLcc"]) > 0:

                for counter in range(len(macros["ZnotesLcc"])):
                    if  (macros["ZnotesLcc"][counter]["songname"] == gstt.songs[gstt.song] or macros["ZnotesLcc"][counter]["songname"] == "all") and (macros["ZnotesLcc"][counter]["chanIN"] == MidiChannel or macros["ZnotesLcc"][counter]["chanIN"] == "all") and  (macros["ZnotesLcc"][counter]["notes"] == MidiNote or macros["ZnotesLcc"][counter]["notes"] == "all")  and  (macros["ZnotesLcc"][counter]["notetype"] == "off" or macros["ZnotesLcc"][counter]["notetype"] == "all") :
                        print(macros["ZnotesLcc"][counter]["songname"], ":", macros["ZnotesLcc"][counter]["name"])
                        #print("ZnotesLcc Note OFF got Song :", macros["ZnotesLcc"][counter]["songname"],"  IN Channel :", macros["ZnotesLcc"][counter]["chanIN"],"  Code :", macros["ZnotesLcc"][counter]["code"], "  CC", maxwellccs.FindCC(macros["ZnotesLcc"][counter]["code"]), "  value :",macros["ZnotesLcc"][counter]["value"], "  laser :", macros["ZccLcc"][counter]["laser"])
                        midi3.MidiMsg((CONTROLLER_CHANGE,maxwellccs.FindCC(macros["ZnotesLcc"][counter]["code"]), macros["ZnotesLcc"][counter]["value"]), mididest, laser = macros["ZccLcc"][counter]["laser"])



        # PROGRAM CHANGE button selected : change destination computer
        if msg[0]==PROGRAM_CHANGE:
        
            print("Program change : ", str(msg[1]))
            # Change destination computer mode
            print("Destination computer", int(msg[1]))
            computer = int(msg[1])


        # CONTROLLER CHANGE Encoders are on Midi Channel 1 : CCnumber is matrix name -> midi CC          
        if msg[0] == CONTROLLER_CHANGE:

            MidiChannel = msg[0]-176
            MidiCC = msg[1]
            MidiVal = msg[2]
            print("CC :", MidiCC , " Value :", MidiVal, "Channel :", MidiChannel)
            '''
            if computer == 0 or computer == 1:

                macroname= "m"+str(msg[1]) 
                macroargs = msg[2]
                Encoder(macroname, macroargs)

            else: 
                SendOSC(gstt.computerIP[computer-1], gstt.MaxwellatorPort, '/cc', [int(msg[1]), int(msg[2])])
            '''
            # ZccLcc
            if len(macros["ZccLcc"]) > 0 :

                for counter in range(len(macros["ZccLcc"])):

                    if (macros["ZccLcc"][counter]["songname"] == gstt.songs[gstt.song] or macros["ZccLcc"][counter]["songname"] == "all") and  (macros["ZccLcc"][counter]["chanIN"] == MidiChannel or macros["ZccLcc"][counter]["chanIN"] == "all") and (macros["ZccLcc"][counter]["ccs"] == MidiCC or macros["ZccLcc"][counter]["ccs"] == "all"):
                        print(macros["ZccLcc"][counter]["songname"], ":", macros["ZccLcc"][counter]["name"])
                        macrocode = macros["ZccLcc"][counter]["code"]

                        # python function
                        if macrocode.count('.') > 0:
                            print(macrocode+"("+str(MidiCC)+","+str(MidiVal)+')')
                            eval(macrocode+"("+str(MidiCC)+',"'+str(MidiVal)+'")')

                        # Maxwell function
                        elif macrocode.count('/') > 0:                        

                            #print("ZccLcc got song :", macros["ZccLcc"][counter]["songname"],"  IN Channel :", macros["ZccLcc"][counter]["chanIN"],"  Code :", macros["ZccLcc"][counter]["code"], "  value :",macros["ZnotesLcc"][counter]["value"], )
                            midi3.MidiMsg((CONTROLLER_CHANGE,maxwellccs.FindCC(macros["ZccLcc"][counter]["code"]),macros["ZccLcc"][counter]["value"]), mididest, laser = macros["ZccLcc"][counter]["laser"])


            # CC Specials features
            if len(macros["Specials"]) > 0:

                for counter in range(len(macros["Specials"])):
                    
                    if (macros["Specials"][counter]["songname"] == gstt.songs[gstt.song] or macros["Specials"][counter]["songname"] == "all") and (macros["Specials"][counter]["chanIN"] == MidiChannel or macros["Specials"][counter]["chanIN"] == "all") and  (macros["Specials"][counter]["ccs"] == MidiCC or macros["Specials"][counter]["ccs"] == "all")  and  (macros["Specials"][counter]["notetype"] == "on" or macros["Specials"][counter]["notetype"] == "all") :
                        macrocode = macros["Specials"][counter]["code"]
                        # print("Specials CC function :",macros["Specials"][counter]["songname"], ":", macros["Specials"][counter]["name"], macrocode)
                        
                        # python function
                        if macrocode.count('.') > 0:
                            print(macrocode+"("+str(MidiCC)+","+str(MidiVal)+')')
                            eval(macrocode+"("+str(MidiCC)+',"'+str(MidiVal)+'")')

                        # Maxwell function
                        elif macrocode.count('/') > 0:
                            print("Specials NoteON got Song :", macros["Specials"][counter]["songname"],"  IN Channel :", macros["Specials"][counter]["chanIN"],"  Code :", macrocode, "  CC", maxwellccs.FindCC(macros["Specials"][counter]["code"]), "  value :",macros["Specials"][counter]["value"], "  laser :", macros["ZccLcc"][counter]["laser"] )
                            midi3.MidiMsg((CONTROLLER_CHANGE, maxwellccs.FindCC(macros["Specials"][counter]["code"]), macros["Specials"][counter]["value"]), mididest, laser = macros["Specials"][counter]["laser"])



        '''
        # Pads are on channel 10
        if msg[0] == CONTROLLER_CHANGE + 10 -1:
        #if msg[0] == CONTROLLER_CHANGE + 10 -1 and msg[2] > 0:
            
            # if button cc number = m grid position
            #print("channel 10 macro","m"+str(msg[1]) , "ccnumber",msg[1], "value", msg[2], macros[gstt.SequencerLayers[gstt.SequencerLayer]][msg[1]]["code"])
            #padCC('m'+str(msg[1]), msg[2])
            
            # if button is actually the cc number
            macronumber, state = findCCMacros(msg[1], msg[2], gstt.SequencerLayers[gstt.SequencerLayer])
            print("channel 10 macro","m"+str(msg[1]), "ccnumber",msg[1], "value", msg[2], "name", macros[gstt.SequencerLayers[gstt.SequencerLayer]][macronumber]["name"], "macronumber", macronumber,"state", state, "code", macros[gstt.SequencerLayers[gstt.SequencerLayer]][macronumber]["code"])
            
            padCC(macros[gstt.SequencerLayers[gstt.SequencerLayer]][macronumber]["name"],state)
        '''


        '''
        # Midi Channel 10 : ccnumber is actual CC number 
        if msg[0] == CONTROLLER_CHANGE + 10 -1 and msg[2] > 0:

            macroname= "m"+str(msg[1]) 
            #macrocode = macros[gstt.SequencerLayers[gstt.SequencerLayer]][msg[1]]["code"]
            print("channel 10 macro",macroname, "ccnumber",msg[1], "value", msg[2])

            #SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/Sequencer/'+macroname+'/button', [1])
            gstt.ccs[gstt.lasernumber][msg[1]]= msg[2]

            if gstt.lasernumber == 0:
                # CC message is sent locally to channel 1
                midi3.MidiMsg([CONTROLLER_CHANGE+midichannel-1, msg[1], msg[2]], 'to Maxwell 1')
                #SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/Sequencer/'+macroname+'/button', [1])
            else:
                SendOSC(gstt.computerIP[gstt.lasernumber], gstt.MaxwellatorPort, '/cc/'+str(msg[1]),[msg[2]])

        '''




# Send to Maxwell a pad value given its Sequencer matrix name
def padCC(buttonname, state):

    macronumber = findMacros(buttonname, gstt.SequencerLayers[gstt.SequencerLayer])
    macrotype = macros[gstt.SequencerLayers[gstt.SequencerLayer]][macronumber]["type"]
    #print()
    print("padCC buttoname", buttonname,"in", gstt.SequencerLayers[gstt.SequencerLayer], "macronumber" , macronumber, "state", state)
    
    #if macronumber != -1:

    # Patch Led ?
    if state >0:

        SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/Sequencer/'+buttonname+'/button', [1])
        macrocode = macros[gstt.SequencerLayers[gstt.SequencerLayer]][macronumber]["code"]
        typevalue = macrocode[macrocode.rfind('/')+1:]
        values = list(enumerate(maxwellccs.specificvalues[typevalue]))
        init = macros[gstt.SequencerLayers[gstt.SequencerLayer]][macronumber]["init"]
        #print("matrix", buttonname, "macrocode", macrocode, "typevalue", typevalue,"macronumber", macronumber, "values", values, "init", init, "value", values[init][1], "cc", maxwellccs.FindCC(macrocode), "=", maxwellccs.specificvalues[typevalue][values[init][1]] )
        numbertime[macronumber] = time.time()

        # Toggle Button
        if macrotype =='buttontoggle':

            # toggle button OFF -2 / ON -1
            if init == -2:
                # goes ON
                print(macrocode, 'ON')
                maxwellccs.cc(maxwellccs.FindCC(macrocode), 127, 'to Maxwell 1')
                macros[gstt.SequencerLayers[gstt.SequencerLayer]][macronumber]["init"] = -1
            else:
                # goes OFF
                print(macrocode, 'OFF')
                maxwellccs.cc(maxwellccs.FindCC(macrocode), 0, 'to Maxwell 1')
                macros[gstt.SequencerLayers[gstt.SequencerLayer]][macronumber]["init"] = -2
        
        # Many buttons (choices)
        if macrotype =='buttonmulti':

            # Reset all buttons 
            macrochoices = list(macros[gstt.SequencerLayers[gstt.SequencerLayer]][macronumber]["choices"].split(","))
            numbertime[findMacros(macrochoices[3], gstt.SequencerLayers[gstt.SequencerLayer])] = time.time()
            for choice in macrochoices:
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/Sequencer/'+choice+'/button', [0])

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
            for button in range(macros[gstt.SequencerLayers[gstt.SequencerLayer]][macronumber]["choices"]):
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/Sequencer/'+macros[gstt.SequencerLayers[gstt.LaunchpadLayer]][macronumber]["choice"+str(button)]+'/button', [0])

            maxwellccs.cc(maxwellccs.FindCC(macrocode), maxwellccs.specificvalues[typevalue][values[init][1]], 'to Maxwell 1')
        '''

    if state == 0:
        # Button released
        macrocode = macros[gstt.SequencerLayers[gstt.SequencerLayer]][macronumber]["code"]
        #print('reselect button /Sequencer/'+buttonname+'/button')
        print('elapsed push :', buttonname, macrotype, macronumber, state, macrocode, time.time()-numbertime[macronumber])
        #numbertime[macronumber] = time.time()
        SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/Sequencer/'+buttonname+'/button', [0])
        
        if macronumber != -1 and macrotype == 'button':
            value = 0
 
            print(macrocode+"("+str(value)+',"'+buttonname+'")')
            eval(macrocode+"("+str(value)+',"'+buttonname+'")')

# send a CC to a local Sequencer (pads are on channel 10 with my Sequencer presets)
def CCpad(ccnumber, value, dest = mididest, channel = midichannel):

    #print("Sending Midi channel", midichannel, "cc", ccnumber, "value", value, "to", dest)
    #gstt.ccs[gstt.lasernumber][ccnumber]= value

    midi3.MidiMsg([CONTROLLER_CHANGE+ 10-1, ccnumber, value], dest)

def NoteOn(note,velocity, dest = mididest, laser=gstt.lasernumber):
    midi3.NoteOn(note, velocity, mididest, laser)

def NoteOff(note, dest = mididest, laser = gstt.lasernumber):
    midi3.NoteOff(note, mididest, laser)


def ComputerUpdate(comput):
    global computer

    computer = comput


#
# Sequencer Patch UI
#

def ChangeLayer(layernumber, laser = 0):

    gstt.SequencerLayer = layernumber
    print('Sequencer layer :', layernumber)
    # update iPad UI
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/sequencer/status', [gstt.SequencerLayers[gstt.SequencerLayer]])
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/sequencer/m10/value', [format(layernumber, "03d")])
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/sequencer/m10/line1', ['Layer'])
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/sequencer/m10/line2', [''])
    UpdatePatch(gstt.patchnumber[laser])

def NLayer():

    print(gstt.SequencerLayer + 1, len(gstt.SequencerLayers))
    if gstt.SequencerLayer + 1 < len(gstt.SequencerLayers):
        ChangeLayer(gstt.SequencerLayer + 1)

def PLayer():

    if gstt.SequencerLayer != 0:
        ChangeLayer(gstt.SequencerLayer - 1)


def UpdatePatch(patchnumber):

    #print('Sequencer updatePatch', patchnumber)
    # update iPad UI
    # SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/Sequencer/status', [gstt.SequencerLayers[gstt.SequencerLayer]])
    for macronumber in range(nbmacro):

        macrocode = macros[gstt.SequencerLayers[gstt.SequencerLayer]][macronumber]["code"]
        #print()
        #print('number',macronumber, "code",macrocode)

        if macrocode.count('/') > 0:
            macrocc = maxwellccs.FindCC(macrocode)
            macroname = macros[gstt.SequencerLayers[gstt.SequencerLayer]][macronumber]["name"]
            macrolaser = macros[gstt.SequencerLayers[gstt.SequencerLayer]][macronumber]["laser"]
            

            # Display value
            #print("name",macroname, "cc", macrocc, "value", gstt.ccs[macrolaser][macrocc],"laser", macrolaser)
            SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/sequencer/'+macroname+'/value', [format(gstt.ccs[macrolaser][macrocc], "03d")])
            

            # Display text line 1
            if (macrocode[:macrocode.rfind('/')] in maxwellccs.shortnames) == True:
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/sequencer/'+macroname+'/line1', [maxwellccs.shortnames[macrocode[:macrocode.rfind('/')]]])
            else:
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/sequencer/'+macroname+'/line1', [macrocode[:macrocode.rfind('/')]])


            # Display text line 2
            if macronumber < 17 or (macronumber > 32 and macronumber < 50):

                # Encoders : cc function name like 'curvetype'
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/sequencer/'+macroname+'/line2', [macrocode[macrocode.rfind('/')+1:]])
            else:

                # button : cc function value like 'Square'
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/sequencer/'+macroname+'/button', [0])
                typevalue = macrocode[macrocode.rfind('/')+1:]
                values = list(enumerate(maxwellccs.specificvalues[typevalue]))
                #print('typevalue', typevalue)
                #print(maxwellccs.specificvalues[typevalue])
                init = macros[gstt.SequencerLayers[gstt.SequencerLayer]][macronumber]["init"]
                #print("init", init, "value", values[init][1] )
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/sequencer/'+macroname+'/line2', [values[init][1]])


            # Display laser number value
            SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/sequencer/'+macroname+'/laser', [macrolaser])
            
        # Code in maxwellccs library : skip "maxwellccs." display only Empty. maxwellccs.Empty will call maxwellccs.Empty() 
        elif macrocode.find('maxwellccs') ==0:
                #print("SEQUENCER",macronumber, macrocode, '/sequencer/'+ macroname+'/line1', macrocode[11:])
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/sequencer/'+ macros[gstt.SequencerLayers[gstt.SequencerLayer]][macronumber]["name"]+'/line2', [macrocode[11:]])
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/sequencer/'+macros[gstt.SequencerLayers[gstt.SequencerLayer]][macronumber]["name"]+'/line1', [" "])
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/sequencer/'+macros[gstt.SequencerLayers[gstt.SequencerLayer]][macronumber]["name"]+'/value', [format(gstt.ccs[macrolaser][macrocc], "03d")])
                #print( '/sequencer/'+macros[gstt.SequencerLayers[gstt.SequencerLayer]][macronumber]["name"]+'/value', [format(gstt.ccs[macrolaser][macrocc], "03d")])
        else:
            SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/sequencer/'+macroname+'/line1', [macrocode])
     

def UpdateCC(ccnumber, value, laser = 0):

    #print('Sequencer UpdateCC', ccnumber, value)
    # update iPad UI
    for macronumber in range(nbmacro):
        macrocode = macros[gstt.SequencerLayers[gstt.SequencerLayer]][macronumber]["code"]
        
        if macrocode == maxwellccs.maxwell['ccs'][ccnumber]['Function']:
           
            macroname = macros[gstt.SequencerLayers[gstt.SequencerLayer]][macronumber]["name"]
            SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/sequencer/'+macroname+'/value', [format(gstt.ccs[laser][ccnumber], "03d")])
            break
           

# Load Matrix only macros (for the moment) in sequencer.json 
def LoadMacros():
    global macros, nbmacro

    #print()
    #print("Loading Sequencer Macros...")

    if os.path.exists('sequencer.json'):
        #print('File matrix.json exits')
        f=open("sequencer.json","r")
    elif os.path.exists('../sequencer.json'):
            #print('File ../sequencer.json exits')
            f=open("../sequencer.json","r")

    elif os.path.exists('libs/sequencer.json'):
        #print('File libs/sequencer.json exits')
        f=open("libs/sequencer.json","r")

    elif os.path.exists(ljpath+'/../../libs/sequencer.json'):
        #print('File '+ljpath+'/../../libs/sequencer.json exits')
        f=open(ljpath+"/../../libs/sequencer.json","r")



    s = f.read()
    macros = json.loads(s)
    #print(len(macros['OS']),"Macros")
    nbmacro = len(macros[gstt.SequencerLayers[gstt.SequencerLayer]])
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

def Start(port):

    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/sequencer/on', [1])

    # if pads are CC 0, 12, 36, 48
    CCpad(0, 1, dest = 'Sequencer',channel = 10)
    CCpad(0, 33, dest = 'Sequencer',channel = 10)
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
    macronumber = findMacros(macroname, gstt.SequencerLayers[gstt.SequencerLayer])

    if macronumber != -1:
        macrocode = macros[gstt.SequencerLayers[gstt.SequencerLayer]][macronumber]["code"]
        #print("Sequencer Layer", gstt.SequencerLayers[gstt.SequencerLayer], ":",macrocode)

        if macrocode.count('/') > 0:

            # encoder slowly turned to right
            if value == 1:
                maxwellccs.EncoderPlusOne(value, path = macrocode)
                macrocc = maxwellccs.FindCC(macrocode)
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/sequencer/'+macroname+'/value', [format(gstt.ccs[0][macrocc], "03d")])

            # encoder fastly turned to right
            if value > 1 and value <20:
                maxwellccs.EncoderPlusTen(value, path = macrocode)
                macrocc = maxwellccs.FindCC(macrocode)
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/sequencer/'+macroname+'/value', [format(gstt.ccs[0][macrocc], "03d")])


            # encoder slowly turned to left
            if value == 127:
                maxwellccs.EncoderMinusOne(value, path = macrocode)
                macrocc = maxwellccs.FindCC(macrocode)
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/sequencer/'+macroname+'/value', [format(gstt.ccs[0][macrocc], "03d")])


            # encoder fasly turned to left
            if value < 127 and value > 90:
                maxwellccs.EncoderMinusTen(value, path = macrocode)
                macrocc = maxwellccs.FindCC(macrocode)
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/sequencer/'+macroname+'/value', [format(gstt.ccs[0][macrocc], "03d")])

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
SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/sequencer/status', ['SEQUENCER'])

