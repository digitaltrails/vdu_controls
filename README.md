vdu_controls - a GUI wrapper for ddcutil
========================================

A GUI for controlling connected *Visual Display Units* (*VDU*'s) (also known as *displays*, or *monitors*).

Description
-----------

``vdu_controls`` is a virtual control panel for physically connected VDU's.  It displays a set of controls for
each  DVI/DP/HDMI/USB connected VDU and uses the ``ddcutil`` command line utility to issue *Display Data Channel*
(*DDC*) *Virtual Control Panel*  (*VCP*) commands to each of them.

By default ``vdu_controls`` offers a subset of the possible controls including brightness, and contrast.  Additional 
controls can be enabled via the ``--enable-vcp-code`` option.  ``vdu_controls`` may optionally run as an entry in the 
system tray.

![Default](screen-shots/Screenshot_Large-330.png)  ![Custom](screen-shots/Screenshot_Small-227.png) 
![Custom](screen-shots/Screenshot_tray-200.png) ![Custom](screen-shots/Screenshot_settings-300.png)

Getting Started
---------------

To get started with ``vdu_controls``, you only need to download the ``vdu_controls.py`` python script and
check that the dependencies described below are in place.

Dependencies
------------

All the following runtime dependencies are likely to be available pre-packaged on any modern Linux distribution 
(``vdu_controls`` was originally developed on OpenSUSE Tumbleweed).

* ddcutil: the command line utility that interfaces to VDU's via DDC over i2c-dev or USB.
* i2c-dev: the i2c-dev kernel module normally shipped with all Linux distributions and required by [ddcutil](https://www.ddcutil.com)
* python 3.8: ``vdu_controls`` is written in python and may depend on some features present only in 3.8 onward.
* python 3.8 QtPy: the python GUI library used by ``vdu_controls``.

It's best confirm that ``ddcutils`` is functioning before using ``vdu_controls``:

* See [https://www.ddcutil.com/config/](https://www.ddcutil.com/config/) for instructions on configuring ``ddcutils``.
* See [https://www.ddcutil.com/i2c_permissions/](https://www.ddcutil.com/i2c_permissions/) for instructions on setting 
  and testing the required permissions.  

The steps to obtaining the necessary rw permissions on ``/dev/i2c-[0-9]`` varies from one Linux distribution to 
another. On some distributions, such as OpenSUSE Tumbleweed, loading the i2c-dev module at boot will automatically 
result in the correct permissions being set on login (and removed on logout).  On other distributions it may be 
necessary to follow all the steps described at www.ddcutil.com.  

For the impatient the following steps can be followed to perform an insecure quick test (they grant anyone on the 
target machine access to the i2c devices):

1. Load i2c-dev: ``sudo modprobe i2c-dev``
2. Temporarily grant rw to everyone: ``sudo chmod a+rw /dev/i2c-*``
3. See if ddcutils works in a normal user's account: ``ddcutils detect``
4. See if vdu_controls now works in a normal user's account: ``python3 vdu_controls.py``

If this works, then following the longer series of steps detailed by the links in the previous comment would be 
the key to getting permissions set permanently.

Installing
----------

As previously stated, the ``vdu_vontrols.py`` script is only file required beyond the prerequisites. There are
two options for "installation": 

* The script can be run without installation by using a python interpreter, for example:\
  ``% python3 vdu_controls.py`` 
* The script can be self installed as desktop application in the current user's desktop menu 
  as *Applications->Settings->VDU Controls* by running: ``% python3 vdu_controls.py --install``\
  Depending on which desktop you're running menu changes may require logout before they become visible.

Please note above options only install ``vdu-controls`` for the current user. At this time there is no
automated support for installing ``vdu-controls`` into a shared location.  The script and desktop-file 
installed for a single user could be modified and copied into /usr or /usr/local hierarchies should you 
wish to do so.

Executing the program
---------------------

* If installed by running the ``--install`` option, a menu item named **VDU Controls** should be able to be located in 
the settings menu or by entering part of its name in the application menus search bar.
* If ``--install`` option has been run, a script called ``vdu_controls`` should be in $HOME/bin.
  If ``$HOME/bin`` is on the user's ``PATH``, ``vdu_controls`` will be able to be run from the command
  line, for example:\
  ``% vdu_controls --show brightness --show contrast --show audio-volume``
* If the script has not been installed, it can still be run on the command line via the python interpreter, 
  for example:\
  ``% python3 vdu_controls.py --no-splash --system-tray --show brightness --show contrast``

Help
----

Detailed help can be accessed by using the right mouse-button to bring up a context-menu.  Access to the context-menu
is available in the application-window and in the system-tray icon.

Both brief help and detailed help can also be accessed via the command line:
```
% python3 vdu_controls.py --help
% python3 vdu_controls.py --detailed-help
% python3 vdu_controls.py --detailed-help | pandoc --from markdown --to html > vdu_controls_help.html
# or if installed in $HOME/bin
% vdu_controls --help
% vdu_controls --detailed-help
% vdu_controls --detailed-help --detailed-help | pandoc --from markdown --to html > vdu_controls_help.html
```

Whether run from the desktop application-menu or run from the command line, ``vdu-controls`` behaviour can be altered
in a number of ways:

* Command line options.
* The `Settings` item in the context-menu.
* Configurations files in `$HOME/.config/vdu_controls/`

See the context-menu or the  [man page](https://htmlpreview.github.io/?https://raw.githubusercontent.com/digitaltrails/vdu_controls/master/docs/_build/man/vdu_controls.1.html)
 for details.

VDU controls and optimisations can be specified in the global or VDU-specific config-files.

Development
-----------

I've set up the ``vdu_controls`` source with a typical Python development, but there is only one real source
file, ``vdu_controls.py``, so the file hierarchy is rather over the top.  A standard python distributable 
can be built by issuing the following commands at the top of the project hierarchy:
```
% python3 -m build
...
% ls -1 dist/
total 268
vdu_controls_digitaltrails-1.0.0-py3-none-any.whl
vdu_controls-digitaltrails-1.0.0.tar.gz
```

The source includes configuration files for the 
[Sphinx Python Documentation Generator](https://www.sphinx-doc.org/en/master/index.html). 
The following commands will extract documentation from ``vdu_controls.py``:
```
% cd docs
% make man
% make html
```

My IDE for this project is [PyCharm Community Edition](https://www.jetbrains.com/pycharm/).

My development Linux desktop is [OpenSUSE Tumbleweed](https://get.opensuse.org/tumbleweed/). The python3
interpreter and python3 libraries are from the standard OpenSUSE Tumbleweed repositories (Tumbleweed currently
defaults python3 to [python 3.8](https://www.python.org/downloads/release/python-380/)).

Authors
-------

Michael Hamilton\
``m i c h a e l   @  a c t r i x   .   g e n  . n z``


Version History
---------------
* 1.4.2
  * Fix increasing indentation of multiline capabilities text on each config file save.
  * Prune the settings editor VDU tab list of controls to those actually supported by the VDU.
  * Use grid layout in the ``settings`` editor.
* 1.4.1
  * Internal code cleanups after switching to INI config files (no functional changes).
  * Updated the help.
* 1.4.0
  * Added global and VDU-specific INI style configuration files in `$HOME/.conf/vdu_controls/`.
  * Added a GUI settings-editor as a `settings` menu-item in the context-menu.
* 1.3.1
  * A minor enhancement to ease installation on Ubuntu, create ``$HOME/bin`` if it doesn't exist. 
* 1.3.0
  * Add a CUSTOM::Sleep_Multiplier VDU config-file option to allow VDU specific sleep multipliers.
    This can be used to prevent the slowest VDU from dragging down response time for all connected VDU's.
  * Added a main UI right-mouse action that makes the context menu available in the UI window.
  * Added a help option to context menu, it displays a formatted version of the ``--detailed-help`` text.
  * Added a ``--detailed-help`` command line option to extract the help from the script (in Markdown format).
* 1.2.2
  * Generalise and simplify the error handling changes initiated in v1.2.1.
* 1.2.1
  * Catch ddcutil error exit and offer to try a slower --sleep-multiplier
* 1.2
  * Better handle out of range values.
  * Enable audio-mute,audio-treble,audio-bass,audio-mic-volume.
  * Allow ddcutil to be anywhere on the user's PATH.
  * Improve parsing to ignore laptop non-MCCS displays when present with external monitors. 
  * Improve the documentation.
  * Add an --about command line option and an "about" tray option.
* 1.0
  * Initial Release

License
-------

This project is licensed under the **GNU General Public License Version 3** - see the [LICENSE.md](LICENSE.md) file 
for details

**vdu_controls Copyright (C) 2021 Michael Hamilton**

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

* [ddcutil](https://www.ddcutil.com)
* [pyqt](https://riverbankcomputing.com/software/pyqt/)
* [Sphinx Python Documentation Generator](https://www.sphinx-doc.org/en/master/index.html)
* [PyCharm Community Edition](https://www.jetbrains.com/pycharm/)
* [Pandoc](https://pandoc.org/)
