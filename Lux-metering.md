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
typically `/dev/ttyUSB0`, `/dev/ttyUSB1`, ...  

You may need to configure access-rights to the tty device.  On many systems 
this would mean adding your username to an appropriate group. Use the `ls`
command to see what user and group owns the device:

```
% ls -l /dev/ttyUSB0                                                                              1 ↵  10269  08:45:34
crw-rw---- 1 root dialout 188, 0 Apr  7 07:32 /dev/ttyUSB0
```

The above example is from my OpenSUSE system, which assigns
these devices to the `dialout` group.  In my case, I'd needed to do:

```
sudo usermod --append --groups dialout michael
```

This grants access to all ``dialout`` devices (all ttys and modems) - which 
may have other security implications.  After adding a user to a group, 
the user will have to re-login - it's the easiest way to ensure the 
whole desktop session hierarchy takes on the change.

Once the sketch is running and the permissions have been set up, the tty 
feed can be directly read by ``vdu_controls``, just configure the correct 
device path in the ``Light Metering Dialog``. 

Webcam based approximation to Lux metering
------------------------------------------

If you don't wish to build an Arduino based solution, you 
may be able to use a webcam to achieve an usable metering values. 

I've developed two scripts:  

 * [lux-from-webcam.bash](/sample-scripts/lux-from-webcam.bash):  This bash script averages a webcam capture by converting 
     it to a 1 pixel image (I barely understand the imagemagick voodoo, but
     it seems to work).  Requirements: ``ImageMagick-7`` (image conversion software),
     and ``v4l-utils`` (Video 4 Linux camera controls)

 * [lux-from-webcam.py](/sample-scripts/lux-from-webcam.py):  Averages a webcam capture by using OpenCV, otherwise
     it's pretty much the same as the bash script.  Requirements: the ``cv2`` 
     (opencv-python real-time computer vision library)

They are intended for webcams that feature manual exposure controls. By 
using manual exposure to set a constant/fixed exposure, images can be 
sampled from a variety of lighting conditions. The average brightness in 
the images can be used to develop a mapping of brightness values to 
approximate lux values. The mapping need not be contiguous, accurate, or 
realistic, they just need to be produce values sufficient for 
use with ``vdu_controls``.

The scripts will require customisation for the local ambient lighting 
conditions and  local hardware options.  In order to use them you'll need 
to be comfortable editing and configuring hardware and scripts using the 
command line. The requirements for the two scripts are available on 
all major Linux distributions.

Both scripts are similar in their approach:
1. capture a still image, 
2. compute the average brightness for the captured image (0..255), 
3. consult a table of brightness to lux mappings, 
4. interpolate (log10) between the matched mapping entries,
5. output a single lux value (typically 0 to 10000 on a log10 scale).

They both read the same config file: 

  `~/.config/lux-from-webcam.data`. 
  
You can use either script, or even switch from one to the other.

In order to use these with ``vdu_controls``, they must be set to be 
executable:

```
chmod u+x lux-from-webcam.bash
chmod U+x lux-from-webcam.py
```

Once they are set to be executable, they will be able to be selected 
as _"Runnable"_ script in the  `Light Metering Dialog`. Then
metering can be enabled, and ``vdu_controls`` will periodically
run the selected script to obtain a single lux values.

They can also be run in a shell to experiment with creating new
mapping values. They both output diagnostics to stderr, for example:

```
% /usr/share/vdu_controls/sample-scripts/lux-from-webcam.bash
INFO: camera-brightness: 129/255
INFO: log10 interpolating 129 over 110..160 to lux 1000..10000
INFO: brightness=129, value=110, lux=1031.81, name=OVERCAST
1031.81
```

I've derived the following example mapping in a study with access 
to a large amount of natural daylight:

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


Both of the scripts are set to use options available with a 
__Logitech Webcam C270__, they may need editing to use similar 
options on other webcams.  

If a webcam doesn't support fixed manual exposures, it may still be
possible to use some heuristics to guess at the available light, or
to perhaps at least guess at whether it is day or night by recognising
differing light or dark areas in the image (such as weather a lamp is
lit). Such heuristics would likely be very specific to local 
circumstances, I've not explored such an approach to any great degree.

Other options
-------------

You can improvise your own light metering device and scripts. 
The ``Light Metering Dialog`` provides three options for light metering 
input:

 * A tty device (assumed to provide a stream of values separated by carriage-return+linefeed.
 * A UNIX FIFO (assumed to provide a stream of values separated by linefeed).
 * An executable (assume to provide one value each time it is run).

Remember, a light meter need not supply accurate or realistic values, the 
values just have to be useful for setting up mappings 
in the ``Light Metering Dialog``. Any scale of values ranging from 0 to 
10000 would likely be usable because ``vdu_controls`` allows you to
chart out a custom mapping from lux to VDU brightness. If you 
want to map pitch dark to 1000 "lux", that's fine, within ``vdu_controls``
just map 1000 "lux" to an appropriate VDU brightness (within this closed
system lux can mean what ever you want it to mean).

See the  [vdu_controls(1) man page](https://htmlpreview.github.io/?https://raw.githubusercontent.com/digitaltrails/vdu_controls/master/docs/_build/man/vdu_controls.1.html)
for further infor on Lux Metering.

