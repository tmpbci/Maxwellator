#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Midi3
v0.7.0

Midi Handler : 

- Hook to the MIDI host
- Enumerate connected midi devices and spawn a process/device to handle incoming events
- Provide sending functions to 
    - found midi devices with IN port
    - OSC targets /noteon /noteoff /cc (see midi2OSC).
- Launchpad mini led matrix from/to, see launchpad.py
- Bhoreal led matrix from/to, see bhoreal.py
- LPD8
- Hercules DJmp3
- Arturia Beatstep
- Electribe 2 as external musical sequencer
- BCR 2000


todo :

Midi macros : plusieurs parametres evoluant les uns apres les autres ou en meme temps.
cadence

by Sam Neurohack 
from /team/laser

for python 2 & 3

Laser selection 
one universe / laser

Plugin selection 
bank change/scene/


"""


import time

import rtmidi
from rtmidi.midiutil import open_midiinput 
from threading import Thread
from rtmidi.midiconstants import (CHANNEL_PRESSURE, CONTROLLER_CHANGE, NOTE_ON, NOTE_OFF,
                                  PITCH_BEND, POLY_PRESSURE, PROGRAM_CHANGE)
import mido
from mido import MidiFile
import traceback
import weakref
import sys
from sys import platform

from queue import Queue
from OSC3 import OSCServer, OSCClient, OSCMessage

print()
#print('midi3')
#print('Midi startup.')

sys.path.append('libs/')
import log
import gstt, bhoreal
import launchpad
import LPD8, dj, beatstep, sequencer, bcr



midiname = ["Name"] * 16
midiport = [rtmidi.MidiOut() for i in range(16) ]

OutDevice = [] 
InDevice = []

# max 16 midi port array 

midinputsname = ["Name"] * 16
midinputsqueue = [Queue() for i in range(16) ]
midinputs = []

# with MacOS Sierra Bhoreal is 
BhorealMidiName = "Leonardo"
LaunchMidiName = "Launch"
DJName = "DJ"
BeatstepName = "Arturia BeatStep"
BCRName = "BCR2000"

BhorealPort, Midi1Port, Midi2Port, VirtualPort, MPort = -1,-1,-1, -1, -1
VirtualName = "LaunchPad Mini"
Mser = False

# Myxolidian 3 notes chords list
Myxo = [(59,51,54),(49,52,56),(49,52,56),(51,54,57),(52,56,59),(52,56,59),(54,57,48),(57,49,52)]
MidInsNumber = 0


clock = mido.Message(type="clock")

start = mido.Message(type ="start")
stop = mido.Message(type ="stop")
ccontinue = mido.Message(type ="continue")
reset = mido.Message(type ="reset")
songpos = mido.Message(type ="songpos")

mode = "maxwell"

'''
print("clock",clock)
print("start",start)
print("continue", ccontinue)
print("reset",reset)
print("sonpos",songpos)
'''

try:
    input = raw_input
except NameError:
    # Python 3
    StandardError = Exception


STATUS_MAP = {
    'noteon': NOTE_ON,
    'noteoff': NOTE_OFF,
    'programchange': PROGRAM_CHANGE,
    'controllerchange': CONTROLLER_CHANGE,
    'pitchbend': PITCH_BEND,
    'polypressure': POLY_PRESSURE,
    'channelpressure': CHANNEL_PRESSURE
}

# OSC targets list
midi2OSC = {
      "lj": {"oscip": "127.0.0.1", "oscport": 8002, "notes": False, "msgs": False},
      "nozoid": {"oscip": "127.0.0.1", "oscport": 8003, "notes": False, "msgs": False},
      "dump": {"oscip": "127.0.0.1", "oscport": 8040, "notes": True, "msgs": True}
      }

notes = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
def midi2note(midinote):

    print("midinote",midinote, "note", notes[midinote%12]+str(round(midinote/12)))
    return notes[midinote%12]+str(round(midinote/12))


def hz_to_note_number(frequency):
    """Convert a frequency in Hz to a (fractional) note number.
    Parameters
    ----------
    frequency : float
        Frequency of the note in Hz.
    Returns
    -------
    note_number : float
        MIDI note number, can be fractional.
    """
    # MIDI note numbers are defined as the number of semitones relative to C0
    # in a 440 Hz tuning
    return 12*(np.log2(frequency) - np.log2(440.0)) + 69

def note_number_to_hz(note_number):
    """Convert a (fractional) MIDI note number to its frequency in Hz.
    Parameters
    ----------
    note_number : float
        MIDI note number, can be fractional.
    Returns
    -------
    note_frequency : float
        Frequency of the note in Hz.
    """
    # MIDI note numbers are defined as the number of semitones relative to C0
    # in a 440 Hz tuning
    return 440.0*(2.0**((note_number - 69)/12.0))  

#mycontroller.midiport[LaunchHere].send_message([CONTROLLER_CHANGE, LaunchTop[number-1], color])

def send(msg,device):

    '''
    # if device is the midi name
    if device in midiname:
        deviceport = midiname.index(device)
        midiport[deviceport].send_message(msg)
    '''
    if device == "Launchpad":
        #print LaunchHere
        midiport[launchpad.Here].send_message(msg)

    if device == "Bhoreal":
        midiport[bhoreal.Here].send_message(msg)

    if device == "DJ":
        midiport[dj.Here].send_message(msg)

    if device == "Beatstep":
        midiport[beatstep.Here].send_message(msg)

    if device == "BCR2000":
        midiport[bcr.Here].send_message(msg)

    if device == gstt.SequencerNameIN:
        midiport[sequencer.Here].send_message(msg)

# mididest : all, launchpad, bhoreal, specificname
def NoteOn(note,color, mididest, laser = gstt.lasernumber):
    global MidInsNumber

    gstt.note = note
    gstt.velocity = color
    
    for port in range(MidInsNumber):

        # To Launchpad, if present.
        if mididest == "launchpad" and midiname[port].find(LaunchMidiName) == 0:
            launchpad.PadNoteOn(note%64,color)

        # To Bhoreal, if present.
        elif mididest == "bhoreal" and midiname[port].find(BhorealMidiName) == 0:
            gstt.BhorLeds[note%64]=color
            midiport[port].send_message([NOTE_ON, note%64, color])
            #bhorosc.sendosc("/bhoreal", [note%64 , 0])

        # To mididest
        elif midiname[port].find(mididest) == 0:
            midiport[port].send_message([NOTE_ON, note, color])

        # To All 
        elif mididest == "all" and midiname[port].find(mididest) != 0 and  midiname[port].find(BhorealMidiName) != 0 and midiname[port].find(BeatstepName) != 0:
            midiport[port].send_message([NOTE_ON, note, color])

        #virtual.send_message([NOTE_ON, note, color])

    for OSCtarget in midi2OSC:
        if (OSCtarget == mididest or mididest == 'all') and midi2OSC[OSCtarget]["notes"]:
            OSCsend(OSCtarget, "/noteon", [note, color])

# mididest : all, launchpad, bhoreal, specificname 
def msg(note, mididest):
    global MidInsNumber

    gstt.note = note
    gstt.velocity = 0

    for port in range(MidInsNumber):

        # To Launchpad, if present.
        if mididest == "launchpad" and midiname[port].find(LaunchMidiName) == 0:
            launchpad.PadNoteOff(note%64)

        # To Bhoreal, if present.
        elif mididest == "bhoreal" and midiname[port].find(BhorealMidiName) == 0:
            midiport[port].send_message([NOTE_OFF, note%64, 0])
            gstt.BhorLeds[note%64] = 0
            #bhorosc.sendosc("/bhoreal", [note%64 , 0])

        # To mididest
        elif midiname[port].find(mididest) != -1:
            midiport[port].send_message([NOTE_OFF, note, 0])

        # To All 
        elif mididest == "all" and midiname[port].find(mididest) == -1 and  midiname[port].find(BhorealMidiName) == -1 and midiname[port].find(LaunchMidiName) == -1:
                midiport[port].send_message([NOTE_OFF, note, 0])
        
        #virtual.send_message([NOTE_OFF, note, 0])

    for OSCtarget in midi2OSC:
        if (OSCtarget == mididest or mididest == 'all') and midi2OSC[OSCtarget]["notes"]:
            OSCsend(OSCtarget, "/noteoff", note)


# mididest : all or specifiname, won't be sent to launchpad or Bhoreal.
def MidiMsg(midimsg, mididest, laser = gstt.lasernumber):
    
    # not in bang 0 mode or in bang mode and a bang has arrived.
    #if gstt.bang0 == False or (gstt.bang0 == True and gstt.bangbang == True and mididest =="to Maxwell 1"):
    if gstt.bang0 == True:
        print("midi3 sending : post bang check, got MidiMsg :", midimsg, "for Dest :", mididest, "  laser :", laser) #, "bang", gstt.bang, "bangbang", gstt.bangbang)
        desterror = -1
    
        #for port in range(MidInsNumber):
        for port in range(len(OutDevice)):
    
            #print("port",port,"midiname", midiname[port])
            # To mididest
            if midiname[port].find(mididest) != -1:
                #print("midi 3 sending to name", midiname[port], "port", port, ":", midimsg)
                midiport[port].send_message(midimsg)
                desterror = 0
    
            # To All 
            elif mididest == "all" and midiname[port].find(mididest) == -1 and  midiname[port].find(BhorealMidiName) == -1 and midiname[port].find(LaunchMidiName) == -1 and midiname[port].find(DJName) == -1 and midiname[port].find(BeatstepName) == -1 and midiname[port].find(gstt.SequencerNameIN) == -1 and midiname[port].find(gstt.BCRName) == -1:
                print("all sending to port",port,"name", midiname[port])
                midiport[port].send_message(midimsg)
                desterror = 0
    
        for OSCtarget in midi2OSC:
            if (OSCtarget == mididest or mididest == 'all') and midi2OSC[OSCtarget]["msgs"]:
                 OSCsend(OSCtarget, "/cc", [midimsg[1], midimsg[2]])
                 desterror = 0
        
        if gstt.bangbang ==0:
            print()
            print("BANG RESET")
            print()
            gstt.bangbang = -1

        if desterror == -1:
            print (mididest," Midi or OSC destination doesn't exists")
    else: 
        print("Midi3 didnt sent", midimsg, mididest, "bang", gstt.bang0, "bangbang", gstt.bangbang)

def OSCsend(name, oscaddress, oscargs =''):

    ip = midi2OSC[name]["oscip"]
    port = midi2OSC[name]["oscport"]
    osclient = OSCClient()
    osclient.connect((ip, port)) 
    oscmsg = OSCMessage()
    oscmsg.setAddress(oscaddress)
    oscmsg.append(oscargs)

    try:
        if gstt.debug > 0:
            print("Midi OSCSend : sending", oscmsg,"to", name, "at", ip , ":", port)
        
        osclient.sendto(oscmsg, (ip, port))
        oscmsg.clearData()   
        return True

    except:
        if gstt.debug > 0:
            print('Midi OSCSend : Connection to IP', ip ,':', port,'refused : died ?')
        #sendWSall("/status No plugin.")
        #sendWSall("/status " + name + " is offline")
        #sendWSall("/" + name + "/start 0")
        #PluginStart(name)
        return False


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





def Webstatus(message):
    OSCsend("lj","/status", message)

#
# MIDI Startup and handling
#
      
mqueue  = Queue()
inqueue = Queue()

#
# Events from Generic MIDI Handling
#
'''
def midinProcess(midiqueue):

    midiqueue_get = midiqueue.get
    while True:
        msg = midiqueue_get()
        print("midin ", msg)
        time.sleep(0.001)
'''
# Event from Bhoreal or Launchpad
# Or it could be the midinprocess in launchpad.py or bhoreal.py
def MidinProcess(inqueue, portname):

    inqueue_get = inqueue.get
    mididest = "to Maxwell 1"
    while True:
        time.sleep(0.001)
        msg = inqueue_get()
        print()
        print("Generic from", portname,"msg : ", msg)
        
        # Note On
        #if NOTE_ON -1 < msg[0] < 160:
        if msg[0]==NOTE_ON:
            print ("Generic midi Note : from", portname, "noteon", msg[1])
            #print(type(portname), portname, gstt.Midikeyboards, portname in gstt.Midikeyboards)

            #if portname in gstt.Midikeyboards:

            MidiChannel = msg[0]-144
            MidiNote = msg[1]
            MidiVel = msg[2]
            print ("Generic NOTE ON :", MidiNote, 'velocity :', MidiVel, "Channel", MidiChannel)
            NoteOn(msg[1], msg[2], "Bus 1")
            
           #print(gstt.maxwell)
            # Lead : RIGHT part, for richter midi file : lead minimal note is E3 (64)
            if MidiNote > gstt.MidiSplitNote:

                # right curvetype is sin
                #SendCC('/osc/right/X/curvetype',0)
                #MidiMsg((CONTROLLER_CHANGE,36,0),mididest)

                # octave is frequency. 25.6 is CC range (128)/5 low octave
                #SendCC('/lfo/2/freq',round(MidiNote/12)*25.6)
                MidiMsg((CONTROLLER_CHANGE, 80, round(MidiNote/12)*25.6),mididest)
                
                # note is phase : decimal part of midinote number = CC range percentage 
                #SendCC('/lfo/2/phase',(MidiNote/12)%1*128)
                MidiMsg((CONTROLLER_CHANGE, 78, (MidiNote/12)%1*128),mididest)

                # velocity is scale
                MidiMsg((CONTROLLER_CHANGE, 98, maxwellccs.curved(MidiVel)), mididest)

            # if note < 64 (E3) set LEFT part
            else:

                # If lead note set a preset :
                # midi3.NoteOn(MidiFileNote-63, MidiFileVel,'to Maxwell 1')
                
                # left curvetype is sin
                #SendCC('/osc/left/X/curvetype',0)
                #MidiMsg((CONTROLLER_CHANGE,0,0),mididest)

                # octave is frequency. 25.6 is CC range (128)/5 low "pentatonic octave"
                #SendCC('/lfo/1/freq',round(MidiNote/12)*25.6)
                MidiMsg((CONTROLLER_CHANGE,75,round(MidiNote/12)*25.6), mididest)

                # note is phase : decimal part of midinote number = CC range percentage 
                #SendCC('/lfo/1/phase',(MidiNote/12)%1*128)
                MidiMsg((CONTROLLER_CHANGE,73,(MidiNote/12)%1*128), mididest)

                # velocity is scale
                MidiMsg((CONTROLLER_CHANGE, 98, maxwellccs.curved(MidiVel)), mididest)

        #else:
        NoteOn(msg[1],msg[2],mididest)
        # Webstatus(''.join(("note ",msg[1]," to ",msg[2])))
                
        # Note Off
        if msg[0]==NOTE_OFF:
            
            '''
            if NOTE_OFF -1 < msg[0] < 144 or (NOTE_ON -1 < msg[0] < 160 and msg[2]==0):

               if msg[0] > 144:
                   MidiChannel = msg[0]-144
               else:
                   MidiChannel = msg[0]-128
            '''
            print ("Generic NOTE OFF :", MidiNote, 'velocity :', MidiVel, "Channel", MidiChannel)
            #print("from", portname,"noteoff", msg[0], msg[1],msg[2])
            #NoteOff(msg[1],msg[2], mididest)
            NoteOff(msg[2], mididest)
            # Webstatus(''.join(("note ",msg[1]," to ",msg[2])))
                
        # Midi CC message          
        if msg[0] == CONTROLLER_CHANGE:
            print("Generic CC :", msg[1], msg[2])
            '''
            Webstatus("CC :" + str(msg[1]) + " " + str(msg[2]))
            for OSCtarget in midi2OSC:
                if OSCtarget["notes"]:
                    pass
                    #OSCsend(OSCtarget, "/CC", note)
            '''

        # other midi message  
        if msg[0] != NOTE_OFF and  msg[0] != NOTE_ON and msg[0] != CONTROLLER_CHANGE:
            #print("from", portname,"other midi message :",msg )
            MidiMsg((msg[0],msg[1],msg[2]),mididest)
            # Webstatus(''.join(("msg : ",msg[0],"  ",msg[1],"  ",msg[2])))
            if portname == "electribe2 PAD/KNOB":
                print("from electribe2 PAD/KNOB other midi message :",msg )


       
# Generic call back : new msg forwarded to queue 
class AddQueue(object):
    def __init__(self, portname, port):
        self.portname = portname
        self.port = port
        #print("AddQueue", port)
        self._wallclock = time.time()

    def __call__(self, event, data=None):
        message, deltatime = event
        self._wallclock += deltatime
        #print("inqueue : [%s] @%0.6f %r" % ( self.portname, self._wallclock, message))
        message.append(deltatime)
        midinputsqueue[self.port].put(message)


#    
# MIDI OUT Handling
#


class OutObject():

    _instances = set()
    counter = 0

    def __init__(self, name, kind, port):

        self.name = name
        self.kind = kind
        self.port = port
        
        self._instances.add(weakref.ref(self))
        OutObject.counter += 1

        print(self.name, "kind", self.kind, "port", self.port)

    @classmethod
    def getinstances(cls):
        dead = set()
        for ref in cls._instances:
            obj = ref()
            if obj is not None:
                yield obj
            else:
                dead.add(ref)
        cls._instances -= dead

    def __del__(self):
        OutObject.counter -= 1



def OutConfig():
    global midiout, MidInsNumber
    
    # 
    if len(OutDevice) == 0:
        print("")
        log.info("MIDIout...")
        print("List and attach to available devices on host with IN port :")
    
        # Display list of available midi IN devices on the host, create and start an OUT instance to talk to each of these Midi IN devices 
        midiout = rtmidi.MidiOut()
        available_ports = midiout.get_ports()
    
        for port, name in enumerate(available_ports):
    
            midiname[port]=name
            midiport[port].open_port(port)
            #print()
            #print("New OutDevice [%i] %s" % (port, name))
            #MidIns[port][1].open_port(port)
                
            # Search for a Bhoreal
            if name.find(BhorealMidiName) > -1:
                
                OutDevice.append(OutObject(name, "bhoreal", port))
                print("Bhoreal start animation")
                bhoreal.Here = port
                bhoreal.Start(port)
                time.sleep(0.5)
    
            # Search for a LaunchPad
            elif name.find(LaunchMidiName) == 0:
                
                OutDevice.append(OutObject(name, "launchpad", port))
                print("Launchpad mini start animation")
                launchpad.Here = port
                launchpad.Start(port)
                time.sleep(0.2)

            # Search for a LPD8
            elif name.find('LPD8') == 0:
                
                OutDevice.append(OutObject(name, "LPD8", port))
                #print("LPD8 mini start animation")
                LPD8.Here = port
                LPD8.Start(port)
                time.sleep(0.2)

            # Search for a Guitar Wing
            elif name.find("Livid") == 0:
                OutDevice.append(OutObject(name, "livid", port))
                #print("Livid Guitar Wing start animation")
                gstt.WingHere = port
                time.sleep(0.2)    

            # Search for a DJmp3
            elif name.find(DJName) == 0:
                OutDevice.append(OutObject(name, "DJmp3", port))
                #print("DJmp3 start animation")
                #dj.StartDJ(port)
                dj.Here = port
                time.sleep(0.2)   

            # Search for a Beatstep
            elif name.find(BeatstepName) == 0:
                OutDevice.append(OutObject(name, "Beatstep", port))
                print("BeatStep start animation")
                beatstep.Start(port)
                beatstep.Here = port
                time.sleep(0.2) 


            # Search for a BCR 2000
            elif name.find(BCRName) == 0:
                OutDevice.append(OutObject(name, "BCR2000", port))
                print("BCR2000 start animation")
                bcr.Start(port)
                bcr.Here = port
                time.sleep(0.2)   

            # Search for a Sequencer
            elif name.find(gstt.SequencerNameIN) == 0:
                OutDevice.append(OutObject(name, "Sequencer", port))
                #print("Sequencer start animation")
                #beatstep.Start(port)
                sequencer.Here = port
                time.sleep(0.2)   

            else:
                
                OutDevice.append(OutObject(name, "generic", port))
    
        #print("")      
        print(len(OutDevice), "Out devices")
        #ListOutDevice()
        MidInsNumber = len(OutDevice)+1

def ListOutDevice():

    for item in OutObject.getinstances():

        print(item.name)

def FindOutDevice(name):

    port = -1
    for item in OutObject.getinstances():
        #print("searching", name, "in", item.name)
        if name == item.name:
            #print('found port',item.port)
            port = item.port
    return port


def DelOutDevice(name):

    Outnumber = Findest(name)
    print('deleting OutDevice', name)

    if Outnumber != -1:
        print('found OutDevice', Outnumber)
        delattr(OutObject, str(name))
        print("OutDevice", Outnumber,"was removed")
    else:
        print("OutDevice was not found")



#    
# MIDI IN Handling 
# Create processing thread and queue for each device
#

class InObject():

    _instances = set()
    counter = 0

    def __init__(self, name, kind, port, rtmidi):

        self.name = name
        self.kind = kind
        self.port = port
        self.rtmidi = rtmidi
        self.queue = Queue()
        
        self._instances.add(weakref.ref(self))
        InObject.counter += 1

        #print("Adding InDevice name", self.name, "kind", self.kind, "port", self.port,"rtmidi", self.rtmidi, "Queue", self.queue)

    @classmethod
    def getinstances(cls):
        dead = set()
        for ref in cls._instances:
            obj = ref()
            if obj is not None:
                yield obj
            else:
                dead.add(ref)
        cls._instances -= dead

    def __del__(self):
        InObject.counter -= 1


def InConfig():

    print("")
    log.info("MIDIin...")
    print("List and attach to available devices on host with OUT port :")

    if platform == 'darwin':
        mido.set_backend('mido.backends.rtmidi/MACOSX_CORE')

    genericnumber = 0

    for port, name in enumerate(mido.get_input_names()):

        #print()
        # Maxwell midi IN & OUT port names are different 
        
        if name.find("from ") == 0:
            #print ("name",name)
            name = "to "+name[5:]
            #print ("corrected to",name)

        outport = FindOutDevice(name)
        midinputsname[port]=name
        
        #print()
        # print("name",name, "Port",port, "Outport", outport)
        
        '''
        # New Bhoreal found ?
        if name.find(BhorealMidiName) == 0:

            try:
                bhorealin, port_name = open_midiinput(outport) # weird rtmidi call port number is not the same in mido enumeration and here

                BhoreralDevice = InObject(port_name, "bhoreal", outport, bhorealin)
                print("BhorealDevice.queue",BhoreralDevice.queue )
                # thread launch to handle all queued MIDI messages from Bhoreal device    
                thread = Thread(target=bhoreal.MidinProcess, args=(bhoreal.bhorqueue,))
                thread.setDaemon(True)
                thread.start()
                print("Attaching MIDI in callback handler to Bhoreal : ",  name, "port", port, "portname", port_name)
                BhoreralDevice.rtmidi.set_callback(bhoreal.AddQueue(port_name))
            except Exception:
                traceback.print_exc()

        '''
        # Bhoreal found ?
        #print(BhorealMidiName, name.find(BhorealMidiName))
        if name.find(BhorealMidiName) > -1:

            try:
                bhorealin, port_name = open_midiinput(outport) # weird rtmidi call port number is not the same in mido enumeration and here
            except (EOFError, KeyboardInterrupt):
                sys.exit

            #print('Bhoreal Found..')
            #midinputs.append(bhorealin)
            InDevice.append(InObject(name, "bhoreal", outport, bhorealin))
            # thread launch to handle all queued MIDI messages from Bhoreal device    
            print("Launching Thread for Bhoreal")
            thread = Thread(target=bhoreal.MidinProcess, args=(bhoreal.bhorqueue,))
            #thread = Thread(target=bhoreal.MidinProcess, args=(InDevice[port].queue,))
            thread.setDaemon(True)
            thread.start()
            #print("midinputs[port]", midinputs[port])
            print(name)
            InDevice[port].rtmidi.set_callback(bhoreal.AddQueue(name))
            #midinputs[port].set_callback(bhoreal.AddQueue(name))

        '''

        # New LaunchPad Mini Found ?
        if name.find(LaunchMidiName) == 0:
   
            
            try:
                launchin, port_name = open_midiinput(outport)
            except (EOFError, KeyboardInterrupt):
                sys.exit()

            LaunchDevice = InObject(port_name, "launchpad", outport, launchin)
            thread = Thread(target=launchpad.MidinProcess, args=(launchpad.launchqueue,))
            thread.setDaemon(True)
            thread.start()
            print("Attaching MIDI in callback handler to Launchpad : ", name, "port", port, "portname", port_name)
            LaunchDevice.rtmidi.set_callback(launchpad.LaunchAddQueue(name))

        '''
 
        # Old LaunchPad Mini Found ?
        if name.find(LaunchMidiName) == 0:
   
            
            try:
                launchin, port_name = open_midiinput(outport)
            except (EOFError, KeyboardInterrupt):
                sys.exit()
            #midinputs.append(launchin)

            #print('Launchpad Found..')
            InDevice.append(InObject(name, "launchpad", outport, launchin))
            print("Launching Thread for Launchpad")
            thread = Thread(target=launchpad.MidinProcess, args=(launchpad.launchqueue,))
            #thread = Thread(target=launchpad.MidinProcess, args=(InDevice[port].queue,))
            thread.setDaemon(True)
            thread.start()
            # print(name, "port", port, "portname", port_name)
            InDevice[port].rtmidi.set_callback(launchpad.LaunchAddQueue(name))
            #launchin.set_callback(launchpad.LaunchAddQueue(name))

 
        # LPD8 Found ?
        if name.find('LPD8') == 0:
   
            #print('LPD8 Found..')
            
            try:
                LPD8in, port_name = open_midiinput(outport)
            except (EOFError, KeyboardInterrupt):
                sys.exit()
            #midinputs.append(LPD8in)
            InDevice.append(InObject(name, "LPD8", outport, LPD8in))
            print("Launching Thread for Launchpad")
            thread = Thread(target=LPD8.MidinProcess, args=(LPD8.LPD8queue,))
            #thread = Thread(target=LPD8.MidinProcess, args=(InDevice[port].queue,))
            thread.setDaemon(True)
            thread.start()
            # print(name, "port", port, "portname", port_name)
            InDevice[port].rtmidi.set_callback(LPD8.LPD8AddQueue(name))
  
        # DJmp3 Found ?
        if name.find(DJName) == 0:
   

            #print('DJmp3 Found..')
            
            try:
                DJin, port_name = open_midiinput(outport)
            except (EOFError, KeyboardInterrupt):
                sys.exit()
            InDevice.append(InObject(name, "DJmp3", outport, DJin))
            print("Launching Thread for DJmp3")
            thread = Thread(target=dj.MidinProcess, args=(dj.DJqueue,))
            thread.setDaemon(True)
            thread.start()
            # print(name, "port", port, "portname", port_name)
            InDevice[port].rtmidi.set_callback(dj.DJAddQueue(name))

        # Beatstep Found ?
        if name.find(BeatstepName) == 0:
   

            #print('Beatstep Found..')
            
            try:
                Beatstepin, port_name = open_midiinput(outport)
            except (EOFError, KeyboardInterrupt):
                sys.exit()
            InDevice.append(InObject(name, "Beatstep", outport, Beatstepin))
            print("Launching Thread for Beatstep")
            thread = Thread(target=beatstep.MidinProcess, args=(beatstep.BEATSTEPqueue,))
            thread.setDaemon(True)
            thread.start()
            # print(name, "port", port, "portname", port_name)
            InDevice[port].rtmidi.set_callback(beatstep.BeatstepAddQueue(name))

        # BCR 2000 Found ?
        if name.find(BCRName) == 0:
   
            #print('BCR2000 Found..')
            
            try:
                BCRin, port_name = open_midiinput(outport)
            except (EOFError, KeyboardInterrupt):
                sys.exit()
            InDevice.append(InObject(name, "BCR2000", outport, BCRin))
            print("Launching Thread for BCR 2000")
            thread = Thread(target=bcr.MidinProcess, args=(bcr.BCRqueue,))
            thread.setDaemon(True)
            thread.start()
            # print(name, "port", port, "portname", port_name)
            InDevice[port].rtmidi.set_callback(bcr.BCRAddQueue(name))



        # Sequencer Found ?
        if name.find(gstt.SequencerNameOUT) == 0:
   

            #print('Sequencer Found..')
            
            try:
                Sequencerin, port_name = open_midiinput(outport)
            except (EOFError, KeyboardInterrupt):
                sys.exit()
            InDevice.append(InObject(name, "Sequencer", outport, Sequencerin))
            print("Launching Thread for Sequencer")
            thread = Thread(target=sequencer.MidinProcess, args=(sequencer.SEQUENCERqueue,))
            thread.setDaemon(True)
            thread.start()
            # print(name, "port", port, "portname", port_name)
            InDevice[port].rtmidi.set_callback(sequencer.SequencerAddQueue(name))


        # Everything that is not Bhoreal, Launchpad, beatstep, Sequencer, LPD8, BCR 2000 or DJmp3
        if name.find(BhorealMidiName) != 0 and name.find(LaunchMidiName) != 0 and name.find('LPD8') != 0 and name.find(DJName) != 0 and name.find(BeatstepName) != 0  and name.find(BCRName) != 0 and name.find(gstt.SequencerNameOUT) != 0:

            try:
                #print (name, name.find("RtMidi output"))
                if name.find("RtMidi output") > -1:
                    print("No thread started for device", name)
                else:
                    portin = object
                    port_name = ""
                    portin, port_name = open_midiinput(outport)
                    #midinputs.append(portin)
                    InDevice.append(InObject(name, "generic", outport, portin))
                    
                    thread = Thread(target=MidinProcess, args=(midinputsqueue[port],port_name))
                    thread.setDaemon(True)
                    thread.start() 

                    print("Launching thread for", name, "port", port, "portname", port_name)
                    #midinputs[port].set_callback(AddQueue(name),midinputsqueue[port])
                    #midinputs[port].set_callback(AddQueue(name))
                    #genericnumber += 1
                    InDevice[port].rtmidi.set_callback(AddQueue(name,port))

            except Exception:
                traceback.print_exc()
                        
    #print("")      
    print(InObject.counter, "In devices")
    #ListInDevice()


def ListInDevice():

    for item in InObject.getinstances():

        print(item.name)

def FindInDevice(name):

    port = -1
    for item in InObject.getinstances():
        #print("searching", name, "in", item.name)
        if name in item.name:
            #print('found port',item.port)
            port = item.port
    return port


def DelInDevice(name):

    Innumber = Findest(name)
    print('deleting InDevice', name)

    if Innumber != -1:
        print('found InDevice', Innumber)
        delattr(InObject, str(name))
        print("InDevice", Innumber,"was removed")
    else:
        print("InDevice was not found")


        # all other devices

        '''
        

        port = mido.open_ioport(name,callback=AddQueue(name))
        
        This doesn't work on OS X on French system "Réseau Session" has a bug with accent.
        Todo : stop using different midi framework.
        
        if name.find(BhorealMidiName) != 0 and name.find(LaunchMidiName) != 0:
            thread = Thread(target=midinProcess, args=(midinputsqueue[port],))
            thread.setDaemon(True)
            thread.start()    
            try:
                port = mido.open_ioport(name,callback=AddQueue(name))
                #port_port, port_name = open_midiinput(port)
            except (EOFError, KeyboardInterrupt):
                sys.exit()

            #midinputs.append(port_port)
            print "Attaching MIDI in callback handler to : ", name
            #midinputs[port].set_callback(AddQueue(name))
            #MIDInport = mido.open_ioport("Laser",virtual=True,callback=MIDIn)
            
        '''

def End():
    global midiout
    
    #midiin.close_port()
    midiout.close_port()
  
    #del virtual
    if launchpad.Here != -1:
        del launchpad.Here
    if bhoreal.Here  != -1:
        del bhoreal.Here
    if LPD8.Here  != -1:
        del LPD8.Here


def listdevice(number):
	
	return midiname[number]
	
def check():

    OutConfig()
    InConfig()
    
    #return listdevice(255)


if __name__ == '__main__':

    check()
	