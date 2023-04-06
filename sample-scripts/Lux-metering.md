Lux metering - sample scripts
=============================

For lux metering I primarily use a simple light meter built using an Arduino and a GY30/BH1750 sensor.

I've also written a couple of alternative webcam based light metering scripts in this folder work on 
my system with my Logitech Webcam C270.

These hardware solutions and there configuration are quite likely to require some customisation
for local ambient lighting conditions and local hardware conditions.  In order to use them you'll
need to be comfortable editing and configuring hardware and scripts using the command line.

GY30/BH1750 + Arduino Lux metering
----------------------------------

Using an Arduino and a GY30/BH1750 is the most reliable way of obtaining true Lux values.  A simple Sketch 
using [Christopher Laws' BH1750 library](https://github.com/claws/BH1750) can be uploaded 
to the Arduino to retrieve a feed of Lux values.  The sketch I'm using in my Arduino employs the 
following code:

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

This provides a feed of Lux values to a USB tty on a Linux host, typically /dev/ttyUSB0 (or /dev/ttyUSB1, etc).  

You may need to configure access to the tty device.  On many systems this would mean adding your username
to an appropriate group,  as can be seen if we inspect the device when the Arduino is connected to the system:

```
ls -l /dev/ttyUSB0                                                                              1 ↵  10269  08:45:34
crw-rw---- 1 root dialout 188, 0 Apr  7 07:32 /dev/ttyUSB0
```

The above is from my OpenSUSE system, the required group is named ``dialout``. So I'd need to do:

```
sudo usermod --append --groups dialout michael
```

Note this would grant access to all ``dialout`` devices (all ttys/modems), so you have to comfortable 
with that.  You may also need to re-login to pick up the new group access.

Once the sketch is running and the permissions have been set up, the tty feed can be directly read 
by ``vdu_controls``, just configure the correct device path in the ``Light Metering Dialog``. 

Webcam based approximation to Lux metering
------------------------------------------

Some webcams can be used to measure light levels in a way that can be approximately 
mapped over a typical lux range.  

This is easily achieved if the webcam includes Linux accessible options for setting
a manual fixed exposure. By setting a fixed exposure, the measured average brightness
in a still capture should vary according to ambient lighting conditions.  By sampling 
stills over a range of typical lighting conditions a mapping of brightness to 
approximate lux values can be developed.  

A webcam based mapping need not be contiguous, accurate, or realistic, the mapping 
just needs to be sufficient for use with ``vdu_controls``.  Seek a range of values that 
corresponded to useful cutoffs/transitions.  For example, I've used these values 
with a Logitech Webcam C270 in a study with access to  a large amount of natural 
daylight:

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

 * ``lux-from-webcam.bash``:  This bash script averages a webcam capture by converting 
     it to a 1 pixel image (I barely understand the imagemagick voodoo, but
     it seems to work).  Requirements: ``ImageMagick-7`` (image conversion software),
     and ``v4l-utils`` (Video 4 Linux camera controls)

 * ``lux-from-webcam.py``:  Averages a webcam capture by using OpenCV, otherwise
     it's pretty much the same as the bash script.  Requirements: the ``cv2`` 
     (opencv-python real-time computer vision library)

In order to use these with ``vdu_controls``, they must be set to be executable:

```
chmod u+x lux-from-webcam.bash
chmod U+x lux-from-webcam.py
```

Once they are set to be executable, they can be selected in  `Light Metering Dialog` and
it will recognise then as "Runnable" scripts that provide a single value per run.

The requirements for the two scripts are packaged for all major distributions.

Both of the scripts are set to use options available with a Logitech Webcam C270,
they may need editing to use similar options on other webcams.  

Because I use a GY30/BH1750 + Arduino, I'm not sure how much support I can 
provide for webcam based approaches over the long term.  Hence, these are 
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

