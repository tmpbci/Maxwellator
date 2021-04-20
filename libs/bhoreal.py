# coding=UTF-8
"""
Bhoreal
v0.7.0
Bhoreal Led matrix Handler 

Start a dedicated thread to handle incoming events from Bhoreal.

Cls()
AllColor(color) 
StarttBhoreal(port)  : Start animation 

Led Matrix can be access with X and Y coordinates and as midi note (0-63)

NoteOn(note,color)
NoteOff(note)
NoteOnXY(x,y,color):
NoteOffXY(x,y):
NoteXY(x,y):

gstt.BhorLeds[] array stores matrix current state

Possible LED functions (goes to "code" in bhoreal.json)

- Maxwell parameter example 

    /osc/left/X/curvetype 

- Built in : PPatch will launch PPatch()

    PPatch          Previous maxwell patch
    NPatch          Next maxwell patch
    Reload          Reload current maxwell patch if modified + save in Maxwell
    Load            Load a new maxwell patch with file dialog (not working yet)
    beatstep        Display Beatstep screen 
    Bhoreal         Display Bhoreal screen 
    Launchpad       Display Launchpad screen 
    Maxwell         Display Maxwell screen 
    L               Mixer full left
    R               Mixer full right
    PLayer          Beatstep previous layer
    NLayer          Beatstep next layer
    Laser0          Set current laser to 0
    Laser1          Set current laser to 1
    Laser2          Set current laser to 2
    Laser3          Set current laser to 3

- External code examples
    
    maxwellccs.MinusOneRight
    subprocess.call(['/usr/bin/open','/Applications/iTerm.app'])



by Sam Neurohack 
from /team/laser

"""

import time
from rtmidi.midiconstants import (CHANNEL_PRESSURE, CONTROLLER_CHANGE, NOTE_ON, NOTE_OFF,
                                  PITCH_BEND, POLY_PRESSURE, PROGRAM_CHANGE)

import sys, os, json
sys.path.append('libs/')
import gstt, midi3, maxwellccs, beatstep

from OSC3 import OSCServer, OSCClient, OSCMessage

gstt.BhorLeds = [0]*65
#nbmacro = 33

Here = -1
from queue import Queue

import socket
#print()
print('Bhoreal module..')
#print("For Bhoreal IP is", gstt.myIP)

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

    #print("Bhoreal sending OSC message : ", oscmsg, "to", ip, ":", port)

    try:
        osclient.sendto(oscmsg, (ip, port))
        oscmsg.clearData()
        return True
    except:
        print ('Connection to', ip, 'refused : died ?')
        return False

def FromOSC(path, args):

    if path.find('/button') > -1:

        print('Bhoreal OSC got ', path, args[0])

        number = NoteXY(int(path[3:4]),int(path[2:3]))
        if args[0] == 1.0:
            LedOn(number)
        else:
            LedOff(number)
 


def NoteOn(note,color):
    
    #print ("bhoreal noteon", note, color)
    msg = [NOTE_ON, note, color]
    midi3.send(msg,"Bhoreal")
    gstt.BhorLeds[note]=color
    
def NoteOff(note):
    msg = [NOTE_OFF, note, 0]
    midi3.send(msg,"Bhoreal")
    gstt.BhorLeds[note]=0

def NoteOnXY(x,y,color):
    #print x,y
    msg = [NOTE_ON, NoteXY(x,y), color]
    midi3.send(msg,"Bhoreal")
    gstt.BhorLeds[NoteXY(x,y)]=color
    
def NoteOffXY(x,y):
    msg = [NOTE_OFF, NoteXY(x,y), 0]
    midi3.send(msg,"Bhoreal")
    gstt.BhorLeds[NoteXY(x,y)]=0

# Leds position are humans numbers 1-8. So -1 for pythonic array position 0-7
def NoteXY(x,y):
    note = (x -1)+ (y-1) * 8 
    return note

def Index(note):
    y=note/8
    x=note%8
    #print "Note : ",note
    #print "BhorIndex : ", x+1,y+1
    return int(x+1),int(y+1)

#    
# Bhoreal Start anim
#

# AllColor for bhoreal on given port

def AllColor(port,color):
    for led in range(0,64,1):
        msg = [NOTE_ON, led, color]
        midi3.send(msg,"Bhoreal")
 
# Cls for bhoreal on given port

def Cls(port):
    for led in range(0,64,1):
        msg = [NOTE_OFF, led, 0]
        midi3.send(msg,"Bhoreal")


# ClsPatch 5th lines for bhoreal on given port

def ClsPatch(port):
    for led in range(0,40,1):
        msg = [NOTE_OFF, led, 0]
        midi3.send(msg,"Bhoreal")

# Start Rainbow in time
def StartBhoreal(port):

    Cls(port)
    time.sleep(0.2)
    for color in range(0,126,1):
        AllColor(port,color)
        time.sleep(0.02)
    time.sleep(0.2)
    Cls(port)

# Start Rainbow
def Start(port):

    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/bhoreal/on', [1])
    Cls(port)
    time.sleep(0.2)

    # Rainbow
    for color in range(0,64,1):
        msg = [NOTE_ON, color, color*2]
        midi3.send(msg,"Bhoreal")

    time.sleep(0.3)
    Cls(port)
    DisplayUpdate()
    
    #DisplayFunctionsLeds()
    #DisplayPatchs()

def UpdateLine(line,newval):
    if Here  != -1:
        for led in range(8):
            NoteOffXY(led,line)
    
        NoteOnXY(newval,line,64)

def DisplayFunctionsLeds():

    for led in range(40,64):
        #print(gstt.BhorealLayers[gstt.BhorealLayer])
        NoteOn(led, macros[gstt.BhorealLayers[gstt.BhorealLayer]][led]["color"])
        SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/bhoreal', [1])
    #macros[gstt.BhorealLayers[gstt.BhorealLayer]][macronumber]["code"]

def DisplayPatchs():

    for led in range(0,64):
        #print(macros[gstt.BhorealLayers[gstt.BhorealLayer]])
        if macros[gstt.BhorealLayers[gstt.BhorealLayer]][led]["code"] == 'patch' and (str(led + 1) in gstt.patchs['pattrstorage']['slots']) != False:
            NoteOn(led, 19)

def DisplayUpdate():

    for led in range(0,64):

        # Maxwell Patchs
        if macros[gstt.BhorealLayers[gstt.BhorealLayer]][led]["code"] == 'patch':
            if str(led + 1) in gstt.patchs['pattrstorage']['slots'] != False:
                #print('/bhoreal/' + macros[gstt.BhorealLayers[gstt.BhorealLayer]][led]["name"],":",'Patch '+ str(led))
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/bhoreal/' + macros[gstt.BhorealLayers[gstt.BhorealLayer]][led]["name"], [str(led)])
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/bhoreal/' + macros[gstt.BhorealLayers[gstt.BhorealLayer]][led]["name"]+'/led', [1.0])
                NoteOn(led, 19)

        else:

            NoteOn(led, macros[gstt.BhorealLayers[gstt.BhorealLayer]][led]["color"])
            macrocode = macros[gstt.BhorealLayers[gstt.BhorealLayer]][led]["code"]
         
            if (macrocode[:macrocode.rfind('/')] in maxwellccs.shortnames) == True:
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/bhoreal/' + macros[gstt.BhorealLayers[gstt.BhorealLayer]][led]["name"], [maxwellccs.shortnames[macrocode[:macrocode.rfind('/')]]])
            
            elif macrocode.find('maxwellccs') ==0:
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/bhoreal/' + macros[gstt.BhorealLayers[gstt.BhorealLayer]][led]["name"], [macrocode[11:]])

            else:
                SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/bhoreal/' + macros[gstt.BhorealLayers[gstt.BhorealLayer]][led]["name"], [macrocode])

# Update one CC value on TouchOSC Bhoreal UI
def UpdateCC(ccnumber, value, laser = 0):


    # print('Bhoreal UpdateCC', ccnumber, value)
    for macronumber in range(nbmacro):
        macrocode = macros[gstt.BhorealLayers[gstt.BhorealLayer]][macronumber]["code"]
        
        if macrocode == maxwellccs.maxwell['ccs'][ccnumber]['Function']:
           
            macroname = macros[gstt.BhorealLayers[gstt.BhorealLayer]][macronumber]["name"]
            # Update TouchOSC Bhoreal UI
            SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/bhoreal/'+macroname+'/value', [format(gstt.ccs[laser][ccnumber], "03d")])
            
            break

# Update Laser 
def Noteon_Update(note):

    '''
    # forward new instruction ? 
    if gstt.MyLaser != gstt.Laser:
        doit = jumplaser.get(gstt.Laser)
        doit("/noteon",note)
    '''
    # 

 
    if note < 8:
        pass

    # 
    if note > 7 and note < 16:
        pass

    # 
    if  note > 15 and note < 24:
        pass

    # change current simulator PL
    if  note > 23 and note < 32:
        pass

    if note == 57 or note == 58:
        pass

    if note > 58:
        pass


#       
# Events from Midi
#

# Process events coming from Bhoreal in a separate thread.
def MidinProcess(bhorqueue):


    bhorqueue_get = bhorqueue.get  
    while True:
    
        msg = bhorqueue_get()

        # Bhoreal Led pressed
        print ("Bhoreal Matrix : ", str(msg[1]), gstt.BhorLeds[msg[1]])

        # A led is pressed
        if msg[0] == NOTE_ON and msg[2] == 64:
            LedOn(msg[1])
          

        # Bhoreal Led depressed
        elif msg[0] == NOTE_ON and msg[2] == 0:
            LedOff(msg[1])


def LedOn(number):

    macrocode = macros[gstt.BhorealLayers[gstt.BhorealLayer]][number]["code"]
    # Patch Led ?
    #print('bhoreal ledon', number)
    if macrocode == "patch":
       
        # If patch exist in loaded maxwell patchs
        if (str(number + 1) in gstt.patchs['pattrstorage']['slots']) == True:
            print('ledon', number, '/bhoreal/' + macros[gstt.BhorealLayers[gstt.BhorealLayer]][number]["name"]+'/button')
            NoteOn(number, 127)
            SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/bhoreal/' + macros[gstt.BhorealLayers[gstt.BhorealLayer]][gstt.patchnumber[gstt.lasernumber]]["name"]+'/button', [0])
            NoteOn(gstt.patchnumber[0],18)
            SendOSC(gstt.computerIP[gstt.lasernumber], 8090, '/bhoreal/note', number)
            gstt.patchnumber[gstt.lasernumber] = number

        else:
            print("No Maxwell patch here !")

    # Code led 
    else:
        if macrocode.find('/') > -1:
            # maxwell CC
            padCC(macros[gstt.BhorealLayers[gstt.BhorealLayer]][number]["name"],1)

        else:
            # code function    
            eval(macros[gstt.BhorealLayers[gstt.BhorealLayer]][number]["code"]+"()")
            NoteOn(number, 127)


def LedOff(number):

    if macros[gstt.BhorealLayers[gstt.BhorealLayer]][number]["code"] != 'patch':
            NoteOn(number, macros[gstt.BhorealLayers[gstt.BhorealLayer]][number]["color"])
            
    else:
        if (str(number + 1) in gstt.patchs['pattrstorage']['slots']) == True:
            SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/bhoreal/' + macros[gstt.BhorealLayers[gstt.BhorealLayer]][number]["name"]+'/button', [1.0])




bhorqueue = Queue()


# New Bhoreal call back : new msg forwarded to Bhoreal queue 
class AddQueue(object):
    def __init__(self, portname):
        self.portname = portname
        self._wallclock = time.time()


    def __call__(self, event, data=None):
        message, deltatime = event
        self._wallclock += deltatime
        print()
        print("[%s] @%0.6f %r" % (self.portname, self._wallclock, message))
        bhorqueue.put(message)
 
#
# Matrix Layers
#

def ChangeLayer(layernumber):

    gstt.BhorealLayer = layernumber
    print('Bhoreal layer :', layernumber)
    # update iPad UI
    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/bhoreal/status', [gstt.BhorealLayers[gstt.BhorealLayer]])
    
    DisplayUpdate()
    '''
    for macronumber in range(33):
        macrocode = macros[gstt.BhorealLayers[gstt.BhorealLayer]][macronumber]["code"]
        macroname = macros[gstt.BhorealLayers[gstt.BhorealLayer]][macronumber]["name"]
        #print("Bhoreal layer", gstt.BhorealLayers[gstt.BhorealLayer], ":",macroname,"macro",macrocode)

        if macrocode.count('/') > 0:
            macrocc = maxwellccs.FindCC(macrocode)
            #print("macro value", maxwellccs.cc1[macrocc])
            SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/bhoreal/' + macros[gstt.BhorealLayers[gstt.BhorealLayer]][led]["name"], [macros[gstt.BhorealLayers[gstt.BhorealLayer]][led]["code"]])

            #SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/'+macroname+'/value', [format(maxwellccs.cc1[macrocc], "03d")])
            #SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/'+macroname+'/line1', [macrocode[:macrocode.rfind('/')]])
            #SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/'+macroname+'/line2', [macrocode[macrocode.rfind('/')+1:]])
    '''




# Load Matrix only macros (for the moment) in Bhoreal.json 
def LoadMacros():
    global macros, nbmacro

    #print()
    #print("Loading Bhoreal Macros...")

    if os.path.exists('libs/bhoreal.json'):
        #print('File is libs/bhoreal.json')
        f=open("libs/bhoreal.json","r")
    
    elif os.path.exists('../bhoreal.json'):
        #print('File is ../bhoreal.json')
        f=open("../bhoreal.json","r")

    elif os.path.exists('bhoreal.json'):
        #print('File is bhoreal.json')
        f=open("bhoreal.json","r")

    elif os.path.exists(ljpath+'/../../libs/bhoreal.json'):
        #print('File is '+ljpath+'/../../libs/bhorealjson')
        f=open(ljpath+"/../../libs/bhoreal.json","r")

    s = f.read()
    macros = json.loads(s)
    #print("Loading Bhoreal Macros...")
    #print(len(macros['OS']),"Macros")
    nbmacro = len(macros[gstt.BhorealLayers[gstt.BhorealLayer]])
    #print(macros['OS'])
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


# Send to Maxwell a pad value given its Bhoreal matrix name
def padCC(buttonname, state):

    macronumber = findMacros(buttonname, gstt.BhorealLayers[gstt.BhorealLayer])
    #print('pad2CC :', buttonname, macronumber, state)
    
    if macronumber != -1:

        # Button pressed
        if state == 1:

            macrocode = macros[gstt.BhorealLayers[gstt.BhorealLayer]][macronumber]["code"]
            typevalue = macrocode[macrocode.rfind('/')+1:]
            values = list(enumerate(maxwellccs.specificvalues[typevalue]))
            init = macros[gstt.BhorealLayers[gstt.BhorealLayer]][macronumber]["init"]
            #print("matrix", buttonname, "macrocode", macrocode, "typevalue", typevalue,"macronumber", macronumber, "values", values, "init", init, "value", values[init][1], "cc", maxwellccs.FindCC(macrocode), "=", maxwellccs.specificvalues[typevalue][values[init][1]] )

            if init <0:

                # toggle button OFF -2 / ON -1
                if init == -2:
                    # goes ON
                    print(macrocode, 'ON')
                    maxwellccs.cc(maxwellccs.FindCC(macrocode), 127, 'to Maxwell 1')
                    macros[gstt.BhorealLayers[gstt.BhorealLayer]][macronumber]["init"] = -1
                else:
                    # goes OFF
                    print(macrocode, 'OFF')
                    maxwellccs.cc(maxwellccs.FindCC(macrocode), 0, 'to Maxwell 1')
                    macros[gstt.BhorealLayers[gstt.BhorealLayer]][macronumber]["init"] = -2

            else:
                # Many buttons (choices)
                # Reset all buttons 
                for button in range(macros[gstt.BhorealLayers[gstt.BhorealLayer]][macronumber]["choices"]):
                    SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/bhoreal/'+macros[gstt.BhorealLayers[gstt.BhorealLayer]][macronumber]["choice"+str(button)]+'/button', [0])

        
                maxwellccs.cc(maxwellccs.FindCC(macrocode), maxwellccs.specificvalues[typevalue][values[init][1]], 'to Maxwell 1')
        
        if state == 0:
            # Button released
            print('reselect button /Bhoreal/'+'m'+buttonname+'/button')
            SendOSC(gstt.TouchOSCIP, gstt.TouchOSCPort, '/bhoreal/'+'m'+buttonname+'/button', [1])





LoadMacros()


