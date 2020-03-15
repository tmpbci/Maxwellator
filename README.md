
Maxwellator v0.2.4b (python3)
By Sam Neurohack, AC

LICENCE : CC NC

There is this great piece of software for abstracts synthesis by BlueFang

![Maxwell](https://img.itch.zone/aW1hZ2UvNjQ0NzYvNDE0NjY0LnBuZw==/original/zfa4Dk.png)

Even it's not sure wether Maxwell is still in dev, we use it a lot for lasers workshops. Within 10 minutes everybody can create great visuals. It's MAX/MSP based and if you don't treat it with love it will certainly crash.

Main idea is to easily control several lasers/computers/Maxwells in live performances in a DJ manner : no computer screens, no mouses, just buttons, rotating stuff and one tablet for feedback/control.

Note that Maxwellator is still in beta stage.


![Controllers](https://www.teamlaser.fr/images/maxwellatorui1.png)

Control Features : 

- Yes ! : you can easily control and see all parameters of 4 Maxwell/laser with only one iPad (4*140 parameters !!)
- Easy midi learn. Maxwellator give names to Maxwell functions.
- It's possible to setup macros or an all show via your favorite midi/DMX/Artnet software.
- Supports different midi controller : Launchpad mini, Bhoreal, LPD8, Beatstep, BCR 2000 and DJmp3.
- Each supported controller have several layer you can select.
- Uses Maxwell presets ('patch') files. 

Every feature is an OSC function : 

- You can make your own UI.
- Several maxwellators can talk to each other. Modify ComputerIP in libs/gstt.py
- Visual parameters feedback needs a TouchOSC tablet. It works great even on iPad 1 (= very cheap now)

Yes you can do all that with midi learn and rtpmidi. Problems starts with several Maxwells, presets changes and hardware interface with 130+ buttons are not easy to find, deal with. 

![Tablet Beatstep UI](https://www.teamlaser.fr/images/maxwellatorui2.png)

# What's new ?

- v0.2.3b : BCR 2000 module, BPM tap tempo, Songs
- v0.2.4b : support Link, reset CCs to default value button



# Modes 

Different modes are available, you obviously need to run it in "programall" mode first :

- "programall" : will guide/ease the Maxwell MIDI LEARN process 130+ parameters per laser. Maxwellator ask for a Maxwell UI, shift-click it (turn violet), then any keyboard key in maxwellator window to send a MIDI CC. Quit Maxwell properly so it can save the new midi configuration.

- "program" : is like "programall" but you enter the specific function to be map. Osc mode inside

- "list" : will show you the list of CC/OSC/DMX/Artnet channels and corresponding Maxwell functions 

- "startup" : will send all "init" values for all Maxwell functions in maxwell.json. 

- "command" : will endlessly ask a function and a value and send it to Maxwell

- "osc" : will only forward osc message (OSC port is 8090) and redis stored artnet to maxwell

- "live" : Listen to Midi/OSC and (Artnet published to redis) then forward incoming messages to the local Maxwell or to selected computer/Maxwell/laser over OSC.

- "Mitraille" : Read specific explanation

- "rand" : Read specific explanation


# Rand Mode 

Think a genetic evolving synthetic "animal". Each maxwell function like frequency for the left X oscillator is a Gene. Genes mutates by randomness, so you control mainly randomness in this mode. Usefull capabilities (like eyes) are kept, so you can order to keep the last change. Try it ! (Artnet & OSC)


# Mitraille Mode


Read a midifile a generate curve changes according to notes. Osc & Artnet support. Code to explore ideas, work in Progress !!

Lead : Maxwell left part (lfo1), for richter midi file : lead minimal note is E3 (64)

	octave is lfo 1 frequency.
	note is amplitude or lfo 1 phase

if note < E3 set Maxwell right part

	octave is lfo2 frequency.                         
	note could be amplitude or lfo 2 phase 


# Midi Mapping

2 maxwellator "modules" have advanced midi mapping to laser <-> "music" : sequencer, BCR 2000 and beatstep. Sequencer is a generic name, you need to edit gstt to your device Midi names, i.e for an Electribe 2 : SequencerNameIN = 'electribe2 SOUND' and SequencerNameOUT = 'electribe2 PAD/KNOB'

- Each mapped function can be valid for all or given : song, midi channel,... 
- CC output maybe translated on linear or squareroot curve (0-127)



# About Maxwell midi :

All Maxwell interface buttons are midi CC, notes are for presets change.

To overwrite a midi assignement (green color) click on the given maxwell UI button with shift key : button get purple so you can assign a midi CC.

Midi changes are saved when Maxwell quit. On MacOS midi learned stuff is in 
~/Library/ApplicationSupport/Maxwell/ (midimap.json and controllist.json)

Maxwellator is tested on MacOS and send midi only to "to Maxwell 1", on channels 1 and 2/
You can of course use Maxwell built in midi learn capabilities but it will listen on all midi port. You can monitor the midi process with a tool like midi monitor.




# "Devices" configuration files

Are obviously in devices directory :

- beatstep.beatstep, for manufacturer's Midi control center
- BCR1.bcr, for BC Manager
- C4, for touchOSC



# How to use it :

First Use : 

- You should edit the config file (libs/gstt.py) to fit your network layout,...
- *To talk to Maxwell correctly YOU MUST run Maxwellator in "programall" mode at least once on each computer. See "Modes" in this readme.* : python3 maxwellator.py -m "programall"
- Your Maxwell presets files must be in patchs directory. In live condition, you should switch Maxwell presets from Maxwellator.
- With many etherdreams, it's a nightmare to get one Maxwell feed the etherdream you want. To make Maxwell talk to a given etherdream (i.e 192.168.1.3) on OS X, we made a custom libetherdream. (greetings to Cocoadaemon)

1/ Replace /Applications/Maxwell.app/Contents/Frameworks/etherdream.dylib by the one in libetherdream/etherdream.dylib or you can compile it. 

2/ Edit Maxwell.sh : modify the IP to your need.

3/ launch Maxwell from terminal with a Maxwell.sh.

Launching many Maxwell on a given computer is not recommended, they usually crash at some point, not because of this "hack" but probably of resources that get shared like midi device name,...


Typical use : 

Launch redis server, i.e from CLI : redis-server &

Load in maxwell the preset file if needed. Everything else will be via maxwellator. 

On a each computer with Maxwell :

python3 maxwellator.py 


To run a particular mode : 

python3 maxwellator.py -m "mode"

where mode is any of "startup", "program", "programall", "list", "command", "osc", "live", "rand", "mitraille", "keyboard" (live by default)


Read the help :

python3 maxwellator.py -h




# Install

You need python3 and pip3 

sudo apt-get install python3-pip 

sudo easy_install pip

pip3 install pysimpledmx
pip3 install DMXEnttecPro

pip3 install redis

pip3 install python-rtmidi (sudo apt install libasound2-dev, sudo apt install libjack-dev)

pip3 install mido

pip3 install numpy



# Compile Maxwellator with nuitka :

python3 -m nuitka --follow-imports --plugin-enable=pylint-warnings --include-package=rtmidi  maxwellator.py



# OSC Reference

Global OSC commands :

/song/status  	Display current song name

/song/prev/button		Switch to next song if available

/song/next/button		Switch to previous song if available


/notes 			Send note to Maxwell (Maxwell preset change)

/cc/			Send CC to Maxwell.


/laser number 	Select given laser


/bhoreal 		Prefix to forward the osc command to bhoreal module (in bhoreal.py OSC Handler)

/beatstep		Prefix to forward the osc command to beatstep module

/pad			Prefix to forward the osc command to launchpad module

/LPD8			Prefix to forward the osc command to LPD8 module

/C4				Prefix to forward the osc command to C4 module

/bcr			Prefix to forward the osc command to BCR 2000 module

/blackout		Self explanatory

/aurora			Prefix for Aurora parameters
/bpm
/patch 	Display next patch number
/patch/prev/button
/patch/next/button
/go
/morph

Each module has it's own OSC commands and common ones like :
/modulename/status


# Maxwell functions Reference : OSC / Artnet channel / Midi channel & CC


-----------------------------------------------------------
| Name                      | Artnet | Midi Chan | MidiCC |
-----------------------------------------------------------

Oscillator LEFT X Functions

/osc/left/X/curvetype is Artnet 0  MIDI Channel 1 CC  0

/osc/left/X/freq is Artnet 1  MIDI Channel 1 CC 1

/osc/left/X/freqlimit is Artnet 2  MIDI Channel 1 CC 2

/osc/left/X/amp is Artnet 3  MIDI Channel 1 CC 3

/osc/left/X/amplimit is Artnet 4  MIDI Channel 1 CC 4

/osc/left/X/phasemod is Artnet 5  MIDI Channel 1 CC 5

/osc/left/X/phasemodlimit is Artnet 6  MIDI Channel 1 CC 6

/osc/left/X/phaseoffset is Artnet 7  MIDI Channel 1 CC 7

/osc/left/X/phaseoffsetlimit is Artnet 8  MIDI Channel 1 CC 8

/osc/left/X/ampoffset is Artnet 9  MIDI Channel 1 CC 9

/osc/left/X/ampoffsetlimit is Artnet 10  MIDI Channel 1 CC 10

/osc/left/X/inversion is Artnet 11  MIDI Channel 1 CC 11


Oscillator LEFT Y Functions

/osc/left/Y/curvetype is Artnet 12  MIDI Channel 1 CC 12

/osc/left/Y/freq is Artnet 13  MIDI Channel 1 CC 13

/osc/left/Y/freqlimit is Artnet 14  MIDI Channel 1 CC 14

/osc/left/Y/amp is Artnet 15  MIDI Channel 1 CC 15

/osc/left/Y/amplimit is Artnet 16  MIDI Channel 1 CC 16

/osc/left/Y/phasemod is Artnet 17  MIDI Channel 1 CC 17

/osc/left/Y/phasemodlimit is Artnet 18  MIDI Channel 1 CC 18

/osc/left/Y/phaseoffset is Artnet 19  MIDI Channel 1 CC 19

/osc/left/Y/phaseoffsetlimit is Artnet 20  MIDI Channel 1 CC 20

/osc/left/Y/ampoffset is Artnet 21  MIDI Channel 1 CC 21

/osc/left/Y/ampoffsetlimit is Artnet 22  MIDI Channel 1 CC 22

/osc/left/Y/inversion is Artnet 23  MIDI Channel 1 CC 23


Oscillator LEFT Z Functions

/osc/left/Z/curvetype is Artnet 24  MIDI Channel 1 CC 24

/osc/left/Z/freq is Artnet 25  MIDI Channel 1 CC 25

/osc/left/Z/freqlimit is Artnet 26  MIDI Channel 1 CC 26

/osc/left/Z/amp is Artnet 27  MIDI Channel 1 CC 27

/osc/left/Z/amplimit is Artnet 28  MIDI Channel 1 CC 28

/osc/left/Z/phasemod is Artnet 29  MIDI Channel 1 CC 29

/osc/left/Z/phasemodlimit is Artnet 30  MIDI Channel 1 CC 30

/osc/left/Z/phaseoffset is Artnet 31  MIDI Channel 1 CC 31

/osc/left/Z/phaseoffsetlimit is Artnet 32  MIDI Channel 1 CC 32

/osc/left/Z/ampoffset is Artnet 33  MIDI Channel 1 CC 33

/osc/left/Z/ampoffsetlimit is Artnet 34  MIDI Channel 1 CC 34

/osc/left/Z/inversion is Artnet 35  MIDI Channel 1 CC 35


Oscillator RIGHT X Functions

/osc/right/X/curvetype is Artnet 36  MIDI Channel 1 CC 36

/osc/right/X/freq is Artnet 37  MIDI Channel 1 CC 37

/osc/right/X/freqlimit is Artnet 38  MIDI Channel 1 CC 38

/osc/right/X/amp is Artnet 39  MIDI Channel 1 CC 39

/osc/right/X/amplimit is Artnet 40  MIDI Channel 1 CC 40

/osc/right/X/phasemod is Artnet 41  MIDI Channel 1 CC 41

/osc/right/X/phasemodlimit is Artnet 42  MIDI Channel 1 CC 42

/osc/right/X/phaseoffset is Artnet 43  MIDI Channel 1 CC 43

/osc/right/X/phaseoffsetlimit is Artnet 44  MIDI Channel 1 CC 44

/osc/right/X/ampoffset is Artnet 45  MIDI Channel 1 CC 45

/osc/right/X/ampoffsetlimit is Artnet 46  MIDI Channel 1 CC 46

/osc/right/X/inversion is Artnet 47  MIDI Channel 1 CC 47


Oscillator RIGHT Y Functions

/osc/right/Y/curvetype is Artnet 48  MIDI Channel 1 CC 48

/osc/right/Y/freq is Artnet 49  MIDI Channel 1 CC 49

/osc/right/Y/freqlimit is Artnet 50  MIDI Channel 1 CC 50

/osc/right/Y/amp is Artnet 51  MIDI Channel 1 CC 51

/osc/right/Y/amplimit is Artnet 52  MIDI Channel 1 CC 52

/osc/right/Y/phasemod is Artnet 53  MIDI Channel 1 CC 53

/osc/right/Y/phasemodlimit is Artnet 54  MIDI Channel 1 CC 54

/osc/right/Y/phaseoffset is Artnet 55  MIDI Channel 1 CC 55

/osc/right/Y/phaseoffsetlimit is Artnet 56  MIDI Channel 1 CC 56

/osc/right/Y/ampoffset is Artnet 57  MIDI Channel 1 CC 57

/osc/right/Y/ampoffsetlimit is Artnet 58  MIDI Channel 1 CC 58

/osc/right/Y/inversion is Artnet 59  MIDI Channel 1 CC 59


Oscillator RIGHT Z Functions

/osc/right/Z/curvetype is Artnet 60  MIDI Channel 1 CC 60

/osc/right/Z/freq is Artnet 61  MIDI Channel 1 CC 61

/osc/right/Z/freqlimit is Artnet 62  MIDI Channel 1 CC 62

/osc/right/Z/amp is Artnet 63  MIDI Channel 1 CC 63

/osc/right/Z/amplimit is Artnet 64  MIDI Channel 1 CC 64

/osc/right/Z/phasemod is Artnet 65  MIDI Channel 1 CC 65

/osc/right/Z/phasemodlimit is Artnet 66  MIDI Channel 1 CC 66

/osc/right/Z/phaseoffset is Artnet 67  MIDI Channel 1 CC 67

/osc/right/Z/phaseoffsetlimit is Artnet 68  MIDI Channel 1 CC 68

/osc/right/Z/ampoffset is Artnet 69  MIDI Channel 1 CC 69

/osc/right/Z/ampoffsetlimit is Artnet 70  MIDI Channel 1 CC 70

/osc/right/Z/inversion is Artnet 71  MIDI Channel 1 CC 71


LFO 1 Functions

/lfo/1/curvetype is Artnet 72  MIDI Channel 1 CC 72

/lfo/1/freq is Artnet 73  MIDI Channel 1 CC 73

/lfo/1/freqlimit is Artnet 74  MIDI Channel 1 CC 74

/lfo/1/phase is Artnet 75  MIDI Channel 1 CC 75

/lfo/1/inversion is Artnet 76  MIDI Channel 1 CC 76


LFO 2 Functions

/lfo/2/curvetype is Artnet 77  MIDI Channel 1 CC 77

/lfo/2/freq is Artnet 78  MIDI Channel 1 CC 78

/lfo/2/freqlimit is Artnet 79  MIDI Channel 1 CC 79

/lfo/2/phase is Artnet 80  MIDI Channel 1 CC 80

/lfo/2/inversion is Artnet 81  MIDI Channel 1 CC 81


LFO 3 Functions

/lfo/3/curvetype is Artnet 82  MIDI Channel 1 CC 82

/lfo/3/freq is Artnet 83  MIDI Channel 1 CC 83

/lfo/3/freqlimit is Artnet 84  MIDI Channel 1 CC 84

/lfo/3/phase is Artnet 85  MIDI Channel 1 CC 85

/lfo/3/inversion is Artnet 86  MIDI Channel 1 CC 86


Duplicator Functions

/duplicator/num is Artnet 87  MIDI Channel 1 CC 87

/duplicator/offset is Artnet 88  MIDI Channel 1 CC 88


Mixer Functions

/mixer/operation is Artnet 89  MIDI Channel 1 CC 89

/mixer/value is Artnet 90  MIDI Channel 1 CC 90


Intensity Functions

/intensity/mod is Artnet 91  MIDI Channel 1 CC 91

/intensity/freq is Artnet 92  MIDI Channel 1 CC 92


Scaler Functions

/scaler/curvetype is Artnet 93  MIDI Channel 1 CC 93

/scaler/speed is Artnet 94  MIDI Channel 1 CC 94

/scaler/switch is Artnet 95  MIDI Channel 1 CC 95

/scaler/width is Artnet 96  MIDI Channel 1 CC 96

/scaler/amt is Artnet 97  MIDI Channel 1 CC 97

/scaler/scale is Artnet 98  MIDI Channel 1 CC 98


Rotator X Functions

/rotator/X/curvetype is Artnet 99  MIDI Channel 1 CC 99

/rotator/X/speed is Artnet 100  MIDI Channel 1 CC 100

/rotator/X/lfo/switch is Artnet 101  MIDI Channel 1 CC 101

/rotator/X/direct is Artnet 102  MIDI Channel 1 CC 102


Rotator Y Functions

/rotator/Y/curvetype is Artnet 103  MIDI Channel 1 CC 103

/rotator/Y/speed is Artnet 104  MIDI Channel 1 CC 104

/rotator/Y/lfo/switch is Artnet 105  MIDI Channel 1 CC 105

/rotator/Y/direct is Artnet 106  MIDI Channel 1 CC 106


Rotator Z Functions

/rotator/Z/curvetype is Artnet 107  MIDI Channel 1 CC 107

/rotator/Z/speed is Artnet 108  MIDI Channel 1 CC 108

/rotator/Z/lfo/switch is Artnet 109  MIDI Channel 1 CC 109

/rotator/Z/direct is Artnet 110  MIDI Channel 1 CC 110


Translator X Functions

/translator/X/curvetype is Artnet 111  MIDI Channel 1 CC 111

/translator/X/speed is Artnet 112  MIDI Channel 1 CC 112

/translator/X/lfo/switch is Artnet 113  MIDI Channel 1 CC 113

/translator/X/amt is Artnet 114  MIDI Channel 1 CC 114


Translator Y Functions

/translator/Y/curvetype is Artnet 115  MIDI Channel 1 CC 115

/translator/Y/speed is Artnet 116  MIDI Channel 1 CC 116

/translator/Y/lfo/switch is Artnet 117  MIDI Channel 1 CC 117

/translator/Y/amt is Artnet 118  MIDI Channel 1 CC 118


Translator Z Functions

/translator/Z/curvetype is Artnet 119  MIDI Channel 1 CC 119

/translator/Z/speed is Artnet 120  MIDI Channel 1 CC 120

/translator/Z/lfo/switch is Artnet 121  MIDI Channel 1 CC 121

/translator/Z/amt is Artnet 122  MIDI Channel 1 CC 122


Colors Functions

/color/colortype is Artnet 123  MIDI Channel 1 CC 123

/color/huewidth is Artnet 124  MIDI Channel 1 CC 124

/color/hueoff is Artnet 125  MIDI Channel 1 CC 125

/color/huemod is Artnet 126  MIDI Channel 1 CC 126

/color/huerot is Artnet 127  MIDI Channel 1 CC 127

/color/intwidth is Artnet 128  MIDI Channel 2 CC 1

/color/intoff is Artnet 129  MIDI Channel 2 CC 2

/color/intmod is Artnet 130  MIDI Channel 2 CC 3

/color/intfreq is Artnet 131  MIDI Channel 2 CC 4

/color/satwidth is Artnet 132  MIDI Channel 2 CC 5

/color/satmod is Artnet 133  MIDI Channel 2 CC 6

/color/saturation is Artnet 134  MIDI Channel 2 CC 7

/color/modtype is Artnet 135  MIDI Channel 2 CC 8

/color/picker is Artnet 136 MIDI Channel 2 CC 9


Draw Functions 

/draw/mode is Artnet 137 MIDI Channel 2 CC 10

Point Mode

/points/number is Artnet 138 MIDI Channel 2 CC 11
/points/x10 is Artnet 139 MIDI Channel 2 CC 12



141 functions
