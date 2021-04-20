# coding=UTF-8
'''

Global states variables
v0.8.0

LICENCE : CC NC

'''
BhorealLayer = 0
BhorealLayers = ['Maxwell1','Maxwell2','Maxwell3']

LaunchpadLayer = 0
LaunchpadLayers = ['Maxwell1','Maxwell2','OS']

BeatstepLayer = 2
BeatstepLayers = ['XY','TraRot',"HueInt","Zregulators"]

BCRLayer = 0
BCRLayers = ['Main','Second']

SequencerLayer = 3
SequencerLayers = ['XY','TraRot',"HueInt","Zregulators"]

lpd8Layer = 0
lpd8Layers = ['Maxwell1','Maxwell2','Maxwell3','OS']

C4Layer = 0
C4Layers = ['Midi1','Midi2','Maxwell3','OS']

debug = False

currentbpm = 60
MaxwellatorPort = 8090

TouchOSCPort = 8101

#TouchOSCIP = '192.168.1.67' 	# iPad 1 for Laser network
TouchOSCIP = '192.168.2.67' 	# iPad 1
#TouchOSCIP = '192.168.2.156' 	# iPad mini
#TouchOSCIP = '192.168.43.146' 	# iPad mini @ fuzz
#TouchOSCIP = '192.168.151.213' # CCN
#TouchOSCIP = '127.0.0.1'		# Localhost

computer = 2
computerIP = ['192.168.2.43','192.168.2.64','192.168.2.42',
              '127.0.0.1','127.0.0.1','127.0.0.1','127.0.0.1', '127.0.0.1']
myIP= '127.0.0.1'

# Will be updated a startup
myNetIP = myIP
MasterMode = True


basemidichannel = 1
lasernumber = 0
patchnumber = [0,0,0,0]
patchnext = [1,1,1,1]

morphsteps = 50
morphing = -1
morphCCinc = [0.0] * 140
morphCC = [0] * 140

# reset one CC mode when modified
resetCC = False

# Bang modes OFF
bang0 = True
bang1 = False
bang2 = False
bang3 = False
bangbang = True

# Link (Ableton) flag
link = True

# automodification at each Beat from Link
autolink = False
# random ccvalue between 0-autovalue
autoval = 127

strobe = False


ccs =[[0] * 140] * 4

# Strobe data storage for LFO color mode
intoff = 0


#PatchFiles = ["3d.json","3d.json","3d.json","3d.json"]
PatchFiles = ["lasamples.json","3d.json","rands.json","rands.json"]
Midikeyboards = ["midikeys","Samson Carbon49"]

songs = ["song1", "song2"]
song = 0

SequencerNameIN = "Virtual Sequencer"
SequencerNameOUT = "Virtual Sequencer"
#SequencerNameIN = 'electribe2 SOUND'
#SequencerNameOUT = 'electribe2 PAD/KNOB'

# Modifiers
mod1 = 1
mod2 = 1
mod3 = 1
mod4 = 1
mod5 = 1

MidiSplitNote = 64
steps = 90
rate = 90
Range = 32
inhib = 0
fixedgenes = [200]
lasermode = 0


# DMX serial port max 4, because why not ?
dmxport = [0,0,0,0]
#songname = "song1"
