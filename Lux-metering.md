Lux metering - sample scripts
=============================

For lux metering I use a simple light meter built using an Arduino and 
a __GY30/BH1750__ sensor.  

I've also written a couple of alternative webcam based light metering 
scripts that use my Logitech Webcam C270 to achieve an approximate 
metering value.


GY30/BH1750 + Arduino Lux metering
----------------------------------

Using an Arduino and a GY30/BH1750 is the most reliable way of obtaining
true Lux values.  A simple Sketch using [Christopher Laws' BH1750 library](https://github.com/claws/BH1750) 
can be uploaded to the Arduino to enable a feed of Lux values.  The 
sketch I'm using in my build employs the following code:

```
#include <BH1750.h>
#include <Wire.h>

BH1750 lightMeter;

void setup() {
…  // Serial.println(F("BH1750 Lux values stream..."));
}

void loop() {
  float lux = lightMeter.readLightLevel();
  Serial.println(lux);
  delay(1000);
}
```

This sketch can provide a feed of Lux values to a USB tty on a Linux host, 
typically /dev/ttyUSB0 (or /dev/ttyUSB1, etc).  

You may need to configure access-rights to the tty device.  On many systems 
this would mean adding your username to an appropriate group - use the `ls`
command to see what user and group owns the device:

```
% ls -l /dev/ttyUSB0                                                                              1 ↵  10269  08:45:34
crw-rw---- 1 root dialout 188, 0 Apr  7 07:32 /dev/ttyUSB0
```

The above example is from my OpenSUSE system, the required group is ``dialout``. So I'd need to do:

```
sudo usermod --append --groups dialout michael
```

Note this would grant access to all ``dialout`` devices (all ttys and modems) - you 
have to comfortable with that.  After making any access changes, you will 
have to re-login so that the entire desktop session will pick up the changes.

Once the sketch is running and the permissions have been set up, the tty 
feed can be directly read by ``vdu_controls``, just configure the correct 
device path in the ``Light Metering Dialog``. 

Webcam based approximation to Lux metering
------------------------------------------

If you don't wish to obtain and build an Arduino based solution, you 
may be able to employ a webcam.

Some webcams can be used to achieve an approximate metering values. 
I've written a couple f scripts that take this approach.  They will
require customisation for the local ambient lighting conditions and 
local hardware options.  In order to use them you'll need to be 
comfortable editing and configuring hardware and scripts using the 
command line.

Using a webcam easiest of if the webcam includes 
Linux accessible options for setting a manual fixed exposure. By 
setting a fixed exposure, the measured average brightness in a 
still capture should vary according to ambient lighting conditions.
A mapping of brightness to approximate lux values can be developed
by sampling stills over a range of lighting conditions.  

A webcam based mapping need not be contiguous, accurate, or realistic, 
the mapping just needs to be sufficient for use with ``vdu_controls``.  
Seek a range of values that corresponded to a variety of normal 
circumstances. For example, I've used the follow values with in
a study with access to a large amount of natural daylight:

```
Typical scene     Lux Brightness
SUNLIGHT       100000 250
DAYLIGHT        10000 160
OVERCAST         1000 110
SUNRISE_SUNSET    400  50
DARK_OVERCAST     100  20
LIVING_ROOM        50   5
NIGHT               5   0  
```

I've included two scripts which can read such mapping. They both take the
raw webcam value and interpolate between mapped values to produce a "lux" 
output suitable for ``vdu_controls``:

 * [lux-from-webcam.bash](/sample-scripts/lux-from-webcam.bash):  This bash script averages a webcam capture by converting 
     it to a 1 pixel image (I barely understand the imagemagick voodoo, but
     it seems to work).  Requirements: ``ImageMagick-7`` (image conversion software),
     and ``v4l-utils`` (Video 4 Linux camera controls)

 * [lux-from-webcam.py](/sample-scripts/lux-from-webcam.py):  Averages a webcam capture by using OpenCV, otherwise
     it's pretty much the same as the bash script.  Requirements: the ``cv2`` 
     (opencv-python real-time computer vision library)

In order to use these with ``vdu_controls``, they must be set to be 
executable:

```
chmod u+x lux-from-webcam.bash
chmod U+x lux-from-webcam.py
```

Once they are set to be executable, they can be selected 
in  `Light Metering Dialog` and ``vdu_controls`` will recognise 
then as "Runnable" scripts that provide a single value per run.

The requirements for the two scripts are available on all major Linux distributions.

Both of the scripts are set to use options available with a 
__Logitech Webcam C270__, they may need editing to use similar 
options on other webcams.  

If a webcam doesn't support fixed manual exposures, it may still be
possible to use some heuristics to guess at the available light, or
to perhaps at least guess at whether it is day or night by recognising
differing light or dark areas in the image (such as weather a lamp is
lit). Such heuristics would likely be very specific to local 
circumstances, I've not explored them to any great degree.

Because I use a GY30/BH1750 + Arduino, the webcam based scripts are 
provided as sample scripts with the expectation that the end-user is happy
to edit and maintain their own versions.

Other options
-------------

You can improvise your own light metering device and scripts, the ``Light Metering Dialog``
provides three options for light metering inputs:

 * A tty device (assumed to provide a stream of values separated by carriage-return+linefeed.
 * A UNIX FIFO (assumed to provide a stream of values separated by linefeed).
 * An executable (assume to provide one value each time it is run).

Remember, they need not supply accurate or realistic values, the values just
have to be useful for setting up mappings in the ``Light Metering Dialog``

