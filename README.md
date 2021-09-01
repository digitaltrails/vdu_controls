# vdu_controls - a GUI wrapper for ddutil

A GUI for controlling connected *Visual Display Units* (*VDU*'s) (also known as *displays*, or *monitors*).

## Description

``vdu_controls`` is a virtual control panel for physically connected VDU's.  It displays a set of controls for
each  DVI/DP/HDMI/USB connected VDU and uses the ``ddcutil`` command line utility to issue *Display Data Channel*
(*DDC*) *Virtual Control Panel*  (*VCP*) commands to each of them.

By default ``vdu_controls`` offers a subset of the possible controls including brightness, and contrast.  Additional 
controls can be enabled via the ``--enable-vcp-code`` option.

![Default](screen-shots/Screenshot_Large-330.png)  ![Custom](screen-shots/Screenshot_Small-227.png) 

## Getting Started

### Dependencies

All the following dependencies are likely to be available pre-packaged on any modern Linux distribution 
(``vdu_controls`` was originally developed on OpenSUSE Tumbleweed).

* Linux: but may be able to run on any operating system that provides the required dependencies.
* ddcutil: the command line utility that interfaces to VDU's via DDC over i2c-dev or USB.
* i2c-dev: the i2c-dev Linux kernel module required by ddutil
* python 3.8: ``vdu_controls`` is written in python and may depend on some features present only in 3.8 onward.
* python 3.8 QtPy: the python GUI library used by ``vdu_controls``.

### Installing

The ``vdu_vontrols.py`` script is fully self-contained and is the only component required (beyond the prerequisites).

* The script can be run without installation by using a python interpreter, for example:\
  ``% python3 vdu_controls.py`` 
* The script can be self installed as desktop application in the desktop menu as *Settings->VDU Controls* by running:\
  ``% python3 vdu_controls.py --install``

If you wish to reverse the ``--install`` process, just rerun ``--install`` and remove the two files it reports
as already installed (depending on which desktop you're running menu changes may require logout before they become
visible).

### Executing the program

* If installed  by the ``--install`` option, ``vdu_controls`` should be in $HOME/bin. Provinding $HOME/bin is on the
  user's ``PATH``, ``vdu_controls`` should be able to be run from the command line, for example:\
  ``% vdu_controls --show brightness --show contrast --show audio-volume``
* If installed  by the ``--install`` option, a menu item named **VDU Controls** should be able to be located in 
the settings menu or by entering part of its name in the application menus search bar.
* If the script has not been "installed", it can still be run on the command line via the python interpreter, 
  for example:\
  ``% python3 vdu_controls.py  --show brightness --show contrast``
  

Whether run from the desktop application-menu or run from the command line, ``vdu-controls`` behaviour can be altered
by a number of command line options, see the [man page](https://github.com/digitaltrails/vdu_controls/docs/html/index.html) 
for details.

Command line options can be added to the desktop application-menu by editing the application menu item
directly in the desktop (for *KDE-Plasma* this can be achieved by right-mousing on the **VDU Controls** menu 
item and selecting **Edit Application**).  Alternatively, it is just as easy to use your preferred text editor to
edit the desktop definition file ``$HOME/.local/share/applications/vdu_controls.desktop`` and add options to
the ``Exec=`` line.

## Help

Brief help can always be accessed via the command line help option
```
% python3 vdu_controls.py --help
# or if installed in $HOME/bin
% vdu_controls --help
```

Some controls change the number of connected devices (for example, some VDU's support a power-off command). If
such controls are used, ``vdu_controls`` will detect the change and will restart itself to reconfigure the controls
for the new situation (for example, DDC VDU 2 may now be DD VDU 1).  Similarly, if you physically unplug monitor, the
same thing will happen.

Note that some VDU settings may disable or enable other settings. For example, setting a monitor to a specific
picture-profile might result in the contrast-control being disabled, but ``ddc_controls`` will not be aware of
the restriction resulting in its contrast-control appearing to do nothing.

Builtin laptop displays normally don't implement DDC and those displays are not supported, but a laptop's
externally connected VDU's are likely to be controllable.

## Authors

Michael Hamilton\
``m i c h a e l   @  a c t r i x   .   g e n  . n z``


## Version History

* 1.0
    * Initial Release

## License

This project is licensed under the **GNU General Public License Version 3** - see the LICENSE.md file for details

#### vdu_controls Copyright (C) 2021 Michael Hamilton

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, version 3.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
more details.

You should have received a copy of the GNU General Public License along
with this program. If not, see <https://www.gnu.org/licenses/>.

## Acknowledgments

Inspiration, code snippets, etc.
* [awesome-readme](https://github.com/matiassingers/awesome-readme)
* [PurpleBooth](https://gist.github.com/PurpleBooth/109311bb0361f32d87a2)
* [dbader](https://github.com/dbader/readme-template)
* [zenorocha](https://gist.github.com/zenorocha/4526327)
* [fvcproductions](https://gist.github.com/fvcproductions/1bfc2d4aecb01a834b46)

python3 -m build

Prerequisites:

zypper install python38-QtPy
zypper install ddcutil
lsmod | grep i2c-dev
modprobe i2c-dev

cd docs
make man html