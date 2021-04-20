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

def SendOSCUI(address, args):
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, address, [args])


def AllStatus(message):
    SendOSCUI('/pad/status', [message])
    SendOSCUI('/bhoreal/status', [message])
    SendOSCUI('/c4/status', [message])
    SendOSCUI('/lpd8/status', [message])
    SendOSCUI('/bcr/status', [message])
    SendOSCUI('/beatstep/status', [message])
    SendOSCUI('/status', [message])

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
            midi3.NoteOn(msg[1], msg[2], mididest)


        # Program Change button selected : change destination computer
        if msg[0]==PROGRAM_CHANGE:
        
            print("Beatstep : Program change : ", str(msg[1]))
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
                            print("Beatstep : LccZcc",macros["LccZcc"][counter]["songname"], ":", macros["LccZcc"][counter]["name"])
                            
                            print("Beatstep LccZcc got song :", macros["LccZcc"][counter]["songname"],"  IN Channel :", macros["LccZcc"][counter]["chanIN"],"  value :",macros["LccZcc"][counter]["value"], )
                            if macros["LccZcc"][counter]["value"] == "linear":
                                print("Beatstep Linear", MidiVal)
                                midi3.MidiMsg((176 + macros["LccZcc"][counter]["chanOUT"]-1, macros["LccZcc"][counter]["ccOUT"], MidiVal), macros["LccZcc"][counter]["mididest"], laser = 0)

                            if macros["LccZcc"][counter]["value"] == "curved":
                                print("Beatstep :", MidiVal,"got curved", maxwellccs.curved(MidiVal) )
                                midi3.MidiMsg((176 + macros["LccZcc"][counter]["chanOUT"], macros["LccZcc"][counter]["ccOUT"], maxwellccs.curved(MidiVal)), macros["LccZcc"][counter]["mididest"], laser = 0)


            else: 
                SendOSC(gstt.computerIP[computer-1], gstt.MaxwellatorPort, '/cc', [int(msg[1]), int(msg[2])])



        # Beatstep Pads are on channel 10
        if msg[0] == CONTROLLER_CHANGE + 10 -1:
        #if msg[0] == CONTROLLER_CHANGE + 10 -1 and msg[2] > 0:

            MidiCC = msg[1]
            MidiVal = msg[2]
            state = MidiVal
            #print(MidiCC, MidiVal)

            macroname = "m"+str(MidiCC)

            print("Beatstep : macroname", macroname, "state", state)

            padCC(macroname, state)
        
        '''
        # Midi Channel 10 : ccnumber is actual CC number 
        if msg[0] == CONTROLLER_CHANGE + 10 -1 and msg[2] > 0:

            macroname= "m"+str(msg[1]) 
            #macrocode = macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][msg[1]]["code"]
            print("channel 10 macro",macroname, "ccnumber",msg[1], "value", msg[2])

            #SendOSCUI('/beatstep/'+macroname+'/button', [1])
            gstt.ccs[gstt.lasernumber][msg[1]]= msg[2]

            if gstt.lasernumber == 0:
                # CC message is sent locally to channel 1
                midi3.MidiMsg([CONTROLLER_CHANGE+midichannel-1, msg[1], msg[2]], 'to Maxwell 1')
                #SendOSCUI('/beatstep/'+macroname+'/button', [1])
            else:
                SendOSC(gstt.computerIP[gstt.lasernumber], gstt.MaxwellatorPort, '/cc/'+str(msg[1]),[msg[2]])

        '''



# Send to Maxwell a pad value given its beatstep matrix name
def padCC(buttonname, state):

    macronumber = findMacros(buttonname, gstt.BeatstepLayers[gstt.BeatstepLayer])
    print("padCC buttoname", buttonname, "macronumber" , macronumber, "state", state)
    macrotype = macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["type"]

    macrocode = macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["code"]
    typevalue = macrocode[macrocode.rfind('/')+1:]
    #print("typevalue :", typevalue, macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber] )
    #values = list(enumerate(maxwellccs.specificvalues[typevalue]))
    #print("matrix :", buttonname, "macrocode :", macrocode, "typevalue :", typevalue,"macronumber :", macronumber, "values :", values, "cc :", maxwellccs.FindCC(macrocode) )
    init = macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["init"]

    # Patch Led ?
    if state >0:

        SendOSCUI('/beatstep/'+buttonname+'/button', [1])
        typevalue = macrocode[macrocode.rfind('/')+1:]
        # print("macrocode",macrocode,"typevalue",typevalue)
        
        init = macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["init"]
        #print("matrix", buttonname, "macrocode", macrocode, "typevalue", typevalue,"macronumber", macronumber, "values", values, "init", init, "value", values[init][1], "cc", maxwellccs.FindCC(macrocode), "=", maxwellccs.specificvalues[typevalue][values[init][1]] )
        numbertime[macronumber] = time.time()

        # Toggle Button
        if macrotype =='buttontoggle':

            # toggle button OFF -2 / ON -1
            if init == -2 :
                print(macrocode, 'ON')

                # python function
                if macrocode.count('.') > 0:
                    #print(macrocode+"(0)")
                    eval(macrocode+"(0)")
    
                # Maxwell function
                elif macrocode.count('/') > 0:
                    #maxwellccs.cc(maxwellccs.FindCC(macrocode), maxwellccs.specificvalues[typevalue][values[init][1]], 'to Maxwell 1')
                    maxwellccs.cc(maxwellccs.FindCC(macrocode), macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["on"], 'to Maxwell 1')
                    SendOSCUI('/beatstep/' + buttonname + '/led', 1.0)
                    if (macrocode[:macrocode.rfind('/')] in maxwellccs.shortnames) == True:
                        AllStatus(maxwellccs.shortnames[macrocode[:macrocode.rfind('/')]]+" ON")

                    else:
                        AllStatus(macrocode+" ON")

                macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["init"] = -1

            else:
                print(macrocode, 'OFF')
                # python function
                if macrocode.count('.') > 0:
                    #print(macrocode+"OFF("+str(value)+')')
                    print(macrocode+"(0)")
                    eval(macrocode+"(0)")

                # Maxwell function
                elif macrocode.count('/') > 0:
                    #maxwellccs.cc(maxwellccs.FindCC(macrocode), maxwellccs.specificvalues[typevalue][values[init][1]], 'to Maxwell 1')
                    maxwellccs.cc(maxwellccs.FindCC(macrocode), macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["off"], 'to Maxwell 1')
                    SendOSCUI('/beatstep/' + buttonname + '/led', 0.0)
                    if (macrocode[:macrocode.rfind('/')] in maxwellccs.shortnames) == True:
                        AllStatus(maxwellccs.shortnames[macrocode[:macrocode.rfind('/')]]+" OFF")

                    else:
                        AllStatus(macrocode+" OFF")

                   
                macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["init"] = -2
  

        # Many buttons (choices)
        if macrotype =='buttonmulti':

            # Reset all buttons 
            values = list(enumerate(maxwellccs.specificvalues[typevalue]))
            macrochoices = list(macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["choices"].split(","))
            numbertime[findMacros(macrochoices[3], gstt.BeatstepLayers[gstt.BeatstepLayer])] = time.time()
            for choice in macrochoices:
                SendOSCUI('/beatstep/'+choice+'/button', [0])

            # Do the change
            maxwellccs.cc(maxwellccs.FindCC(macrocode), maxwellccs.specificvalues[typevalue][values[init][1]], 'to Maxwell 1')


        
        # simple action button
        if macrotype =='button':

            print(macrocode+"()")
            eval(macrocode+"()")
            #print(macrocode+"("+str(value)+',"'+macroname+'")')
            #eval(macrocode+"("+str(value)+',"'+macroname+'")')        
        '''
        else:
            # Many buttons (choices)
            # Reset all buttons 
            for button in range(macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["choices"]):
                SendOSCUI('/beatstep/'+macros[gstt.BeatstepLayers[gstt.LaunchpadLayer]][macronumber]["choice"+str(button)]+'/button', [0])

            maxwellccs.cc(maxwellccs.FindCC(macrocode), maxwellccs.specificvalues[typevalue][values[init][1]], 'to Maxwell 1')
        '''

    if state == 0:
        # Button released
        #print('reselect button /beatstep/'+buttonname+'/button')
        print('elapsed push :', buttonname, macrotype, macronumber, state, macrocode, time.time()-numbertime[macronumber])
        #numbertime[macronumber] = time.time()
        SendOSCUI('/beatstep/'+buttonname+'/button', [0])
        
        '''
        if macronumber != -1 and macrotype == 'button':
            value = 0
 
            print(macrocode+"("+str(value)+',"'+buttonname+'")')
            eval(macrocode+"("+str(value)+',"'+buttonname+'")')
        '''
        
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
    SendOSCUI('/beatstep/status', [gstt.BeatstepLayers[gstt.BeatstepLayer]])
    SendOSCUI('/beatstep/m10/value', [format(layernumber, "03d")])
    SendOSCUI('/beatstep/m10/line1', ['Layer'])
    SendOSCUI('/beatstep/m10/line2', [''])
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
    # SendOSCUI('/beatstep/status', [gstt.BeatstepLayers[gstt.BeatstepLayer]])
    for macronumber in range(nbmacro):

        macrocode = macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["code"]
        #print()
        #print('number',macronumber, "code", macrocode)

        if macrocode.count('/') > 0:
            macrocc = maxwellccs.FindCC(macrocode)
            macroname = macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["name"]
            macrolaser = macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["laser"]
            #print("macrocc", macrocc)
            
            # Display value
            #print("name",macroname, "cc", macrocc, "value", gstt.ccs[macrolaser][macrocc],"laser", macrolaser)
            SendOSCUI('/beatstep/'+macroname+'/value', [format(gstt.ccs[macrolaser][macrocc], "03d")])
            

            # Display text line 1
            if (macrocode[:macrocode.rfind('/')] in maxwellccs.shortnames) == True:
                SendOSCUI('/beatstep/'+macroname+'/line1', [maxwellccs.shortnames[macrocode[:macrocode.rfind('/')]]])
            else:
                SendOSCUI('/beatstep/'+macroname+'/line1', [macrocode[:macrocode.rfind('/')]])


            # Display text line 2
            if macronumber < 17 or (macronumber > 32 and macronumber < 50):

                # Encoders : cc function name like 'curvetype'
                SendOSCUI('/beatstep/'+macroname+'/line2', [macrocode[macrocode.rfind('/')+1:]])
            else:

                # button : cc function value like 'Square'
                SendOSCUI('/beatstep/'+macroname+'/button', [0])
                typevalue = macrocode[macrocode.rfind('/')+1:]
                values = list(enumerate(maxwellccs.specificvalues[typevalue]))
                #print('typevalue', typevalue)
                #print(maxwellccs.specificvalues[typevalue])
                init = macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["init"]
                #print("init", init, "value", values[init][1] )
                SendOSCUI('/beatstep/'+macroname+'/line2', [values[init][1]])


            # Display laser number value
            SendOSCUI('/beatstep/'+macroname+'/laser', [macrolaser])
            
        # Code in maxwellccs library : skip "maxwellccs." display only Empty. maxwellccs.Empty will call maxwellccs.Empty() 
        elif macrocode.find('maxwellccs') ==0:
                #print("BEATSTEP",macronumber, macrocode, '/beatstep/'+ macroname+'/line1', macrocode[11:])
                SendOSCUI('/beatstep/'+ macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["name"]+'/line2', [macrocode[11:]])
                SendOSCUI('/beatstep/'+macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["name"]+'/line1', [" "])
                SendOSCUI('/beatstep/'+macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["name"]+'/value', [format(gstt.ccs[macrolaser][macrocc], "03d")])
                #print( '/beatstep/'+macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["name"]+'/value', [format(gstt.ccs[macrolaser][macrocc], "03d")])
        else:
            SendOSCUI('/beatstep/'+macroname+'/line1', [macrocode])
     
# Update one CC value on TouchOSC Beatstep UI
def UpdateCC(ccnumber, value, laser = 0):

    '''
    if ccnumber > 127:
        midichannel = gstt.basemidichannel + 1
        ccnumber -= 127
    else:
        midichannel = gstt.basemidichannel
    '''
    #gstt.ccs[gstt.lasernumber][ccnumber + 127*(midichannel-1)] = value
    #ccnumber += 127*(midichannel-1)
    for macronumber in range(nbmacro):
        macrocode = macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["code"]
        
        if macrocode == maxwellccs.maxwell['ccs'][ccnumber]['Function']:
           
            macroname = macros[gstt.BeatstepLayers[gstt.BeatstepLayer]][macronumber]["name"]
            SendOSCUI('/beatstep/'+macroname+'/value', [format(value, "03d")])
            #print("BEATSTEP update cc :/beatstep/"+macroname+'/value', [format(value, "03d")], "for", macrocode)
            #print()
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

    print("searching", ccnumber, value, "in", macrotype,'...')
    print("total macros", len(macros[macrotype])-1)
    position = -1
    state = 0
    for counter in range(len(macros[macrotype])-1):
        
        macroname = macros[macrotype][counter]['name']
        macrocode = macros[macrotype][counter]['code']
        print ("current", counter,macros[macrotype][counter]['name'], counter,macros[macrotype][counter]['type'], macros[macrotype][counter]['code'], "macroname", macroname, "macrocode", macrocode)
        
        if macrotype == 'button':
            pass


        else:

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

# Get mxx for given macrocode
def findMatrix(macrocode, macrotype):

    print("searching", macrocode,'...')
    name = "None"
    for counter in range(len(macros[macrotype])):
        #print (counter,macros[macrotype][counter]['name'],macros[macrotype][counter]['code'])
        if macrocode == macros[macrotype][counter]['code']:
            #print(macroname, "is ", counter)
            position = counter
            return macros[macrotype][counter]['name']
    return name


# Start animation on first 4 pads.
def Start(port):

    SendOSCUI('/beatstep/on', [1])

    # if pads are CC 0, 12, 36, 48
    CCpad(0, 1, dest = 'Arturia BeatStep', channel = 10)
    CCpad(0, 33, dest = 'Arturia BeatStep', channel = 10)
    CCpad(0, 95, dest = 'Arturia BeatStep', channel = 10)
    CCpad(0, 127, dest = 'Arturia BeatStep', channel = 10)
    time.sleep(0.3)
    CCpad(0, 0, dest = 'Arturia BeatStep', channel = 10)
    CCpad(12, 0, dest = 'Arturia BeatStep', channel = 10)
    CCpad(36, 0, dest = 'Arturia BeatStep', channel = 10)
    CCpad(48, 0, dest = 'Arturia BeatStep', channel = 10)


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
                SendOSCUI('/beatstep/'+macroname+'/value', [format(gstt.ccs[0][macrocc], "03d")])

            # encoder fastly turned to right
            if value > 1 and value <20:
                maxwellccs.EncoderPlusTen(value, path = macrocode)
                macrocc = maxwellccs.FindCC(macrocode)
                SendOSCUI('/beatstep/'+macroname+'/value', [format(gstt.ccs[0][macrocc], "03d")])


            # encoder slowly turned to left
            if value == 127:
                maxwellccs.EncoderMinusOne(value, path = macrocode)
                macrocc = maxwellccs.FindCC(macrocode)
                SendOSCUI('/beatstep/'+macroname+'/value', [format(gstt.ccs[0][macrocc], "03d")])


            # encoder fasly turned to left
            if value < 127 and value > 90:
                maxwellccs.EncoderMinusTen(value, path = macrocode)
                macrocc = maxwellccs.FindCC(macrocode)
                SendOSCUI('/beatstep/'+macroname+'/value', [format(gstt.ccs[0][macrocc], "03d")])

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
SendOSCUI('/beatstep/status', ['BEATSTEP'])

