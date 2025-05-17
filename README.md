vdu_controls - a DDC control panel for monitors
===============================================

A control panel for external monitors (*Visual Display Units*).

> [!WARNING]
> **KDE 6** introduced energy saving brighness dimming after 5 minutes of idle
> time.  This may interfere with changes made via **vdu_controls**, including
> *scheduled-presets* and *ambient-light-control*.  The relevant KDE 6 options can 
> be found under ***System Settings -> System -> Energy Saving***.

Description
-----------
![Custom](screen-shots/ambient-slider-example.png) 

``vdu_controls`` is a virtual control panel for external Visual Display Units 
(VDUs, monitors, displays). It supports displays connected via DisplayPort, 
DVI, HDMI, or USB - but not built-in laptop panels (though laptop integration
is possible via plugin scripting; see below).

By default, `vdu_controls` offers a subset of controls - these include brightness, 
contrast, and audio controls - with additional options available via the 
**Settings dialog**.

For convenience, a single **ambient-light-level slider** can  simultaniously
adjust _all_ displays, each following its own custom profile:
_one slider to rule them all_.  Each profile defines a a curve that maps 
ambient light-level to display-brightness. Realtively flat curves
can be created for older displays and steeper ones for newer HDR 
displays.

Several methods are supported for integrating a hardware light-meter to
achieve **fully automatic** brightness control. (An _arduino_
based meter [can be built for around $10](https://github.com/digitaltrails/vdu_controls/blob/master/Lux-metering.md).)

The ambient-light-level slider can be combined with an estimate of 
local solar illumination to achieve **semi-automatic brightness control**
throughout the day.  Adjusting the slider sets the
ratio between indoor-illumination and outdoor solar-illumination.
Brightness is automatically adjusted as the sun moves across the sky. 
Should circumstances change, adjusting the slider updates 
the ratio.

Favorite settings can be saved as named **Presets**, such as
_night_, _day_, _photography_, _movies_, and so forth.  Presets may be set to 
automatically trigger according to ambient light levels or solar-elevation, 
display hotplug-events, or UNIX signals.

The application may optionally run in the **system tray** of KDE, Deepin, 
GNOME, COSMIC, and Xfce (and possibly others). It automatically adapts to the 
different tray implementations.

The UI automatically adjusts to **light and dark desktop-themes**.
Where a desktop supports Qt theming events, the UI dynamically adjusts 
to light/dark theme changes.

From any application window, use **F1** to access **help**, and **F10** to access the context-menu.   The 
**Context Menu** is also available via the right-mouse button in the main-window, the hamburger-menu item 
on the bottom right of the main window, and the right-mouse button on the system-tray icon. The 
context-menu provides **ALT-_key_ shortcuts** for all menu items (subject to sufficient letters being
available to support all user defined Presets).

> [!TIP]
> A formatted versions of the [vdu_controls.1](https://htmlpreview.github.io/?https://raw.githubusercontent.com/digitaltrails/vdu_controls/master/docs/_build/man/vdu_controls.1.html) manual page is available for preview on github.
> 
> Within the UI, **tool-tips** are often available when hovering over UI components.

![Default](screen-shots/Screenshot_Large-330.png)  ![Custom](screen-shots/Screenshot_Small-227.png) 
![Custom](screen-shots/Screenshot_tray-200.png) ![Custom](screen-shots/Screenshot_settings-300.png)
![Custom](screen-shots/presets.png) ![Custom](screen-shots/lux-profiles.png)

#### Technical background

Historically, there was little need to frequently adjust display brightness.
This changed with the introduction of displays offerring HDR (High Dynamic Range)
and increased contrast. These newer displays can cope better with very bright
conditions, but they often need to be turned down when the ambient light level
descreases. I created `vdu_controls` to allow me to more easily adjust my own 
displays.

`vdu_controls` communicates with displays by using either 
[ddcutil](https://www.ddcutil.com/), a command line utility, 
or the [ddcutil-service](https://github.com/digitaltrails/ddcutil-service), 
a D-Bus interface to [libddcutil](https://www.ddcutil.com/api_main/).
The `ddcutil` command line utility is commonly available in most Linux 
distributions. The D-Bus `ddcutil-service` is relatively new and less widely
distributed.  The service is preferred, it's faster, more reliable, 
and supports DPMS and hotplug events.  If `ddcutil-service` isn't 
available, `vdu_controls` falls back to the `ddcutil` command.
(ddcutil-service is relatively easy to build, does not run as root, 
a custom DIY install realtively simple.)

Both `ddcutil` and `libddcutil` interface to the **VESA** standard
*Display Data Channel* (**DDC**) *Virtual Control Panel*  (**VCP**) interface.
Both the command and the library  provide a robust interface that supports 
many different OEM DDC implementations and GPU drivers. 

`Vdu_controls` supports a _virtual-DDC plugin_ for interfacing to non DDC 
displays, such as laptops. No complete plugins are currently available (a 
sample incomplete template bash script is included).

Does adjusting a VDU affect its lifespan or health?
---------------------------------------------------

Repeatably altering VDU settings might affect VDU lifespan.  Possible reasons 
include the consumption of NVRAM write cycles, stressing the VDU power-supply, 
or increasing the LED panel burn-in.  

How many writes VDU NVRAM can accommodate is unknown, it is likely to vary by model
and vintage. VDUs from past decades are likely to have NVRAM that can accommodate
10,000 to 100,000+ writes depending on the technology used. For a ten year lifespan
this might indicate a sustainable limit of only 2.7 writes per day or 27 writes per 
day respectively.

Some modern types of NVRAM have upper limits that are for practical purposes unlimited. 
Brighter back-lights, along with scene and gaming options, would appear to require 
moving to NVRAM with increased durability. However, the uptake of such technologies 
by the manufacturers is unknown. 

A vintage-2010 VDU, that has been used for four years of intensive testing of 
vdu_controls, now shows signs of of the NVRAM having bad blocks.  After loss of 
power the VDU will sometimes revert to its factory defaults, but not always, which 
suggests the NVRAM is being cycled through and only some of it is bad.  This experience
may indicate a write limit of at least 100,000 for a VDU of this vintage. I've 
subsequently implemented the ___initialization-preset___ feature as a fallback 
for failed NVRAM, so the problem with this VDU is, for the most part, eliminated.

All that said, ``vdu_controls`` does include a number of features that reduce 
the frequency of writes to VDU NVRAM:

 + Slider and spin-box controls only update the VDU when adjustments become slow or stop (when no change occurs in 0.5 seconds).
 + Preset restoration only updates the VDU values that differ from its current values.
 + Transitioning effects and transition controls have been disabled by default and are 
   deprecated for version 2.1.0 onward.
 + Automatic ambient brightness adjustment only triggers a change when the proposed brightness differs from the current brightness by at least 10%.

There are also some things you can do to futher minimise NVRAM writes:

 + Drag sliders to target values with no in-between pauses greater than 0.5 seconds.
 + Choose to restore pre-prepared ‘presets’ instead of dragging sliders.
 + Leave `protect-nvram` enabled which disables transitions for presets.
 + If using the ambient-light brightness response curves, tune the settings and curves to avoid frequent small changes.
 + If using a light-meter, disengage automatic adjustment when ambient light levels
   are  fluctuating (under condtions such as intermittent cloud cover).
 + Consider adjusting the ambient lighting instead of the VDU.

Some feedback is provided to help with making reducing NVRAM usage:

  + Hovering over a display name in the main window reveals a tooltip that includes
    the number of VCP (NVRAM) writes. 
  + The bottom of the About-Dialog shows the same numbers. They update dynamically.

#### Other concerns

> [!Caution]
> Going beyond the standard DDC features by experimenting with undocumented-features 
> or undocumented-values has the potential to make **irreversible** changes.
> Consider the potential cost in time and money before trying anything speculative.

The power-supplies in some older VDUs may buzz/squeel audibly when the brightness is
turned way down. This may not be a major issue, in normal circumstances
older VDUs are often not usable below 85-90% brightness.

Getting Started
---------------

To get started with ``vdu_controls``, you only need to download the ``vdu_controls.py`` python script and
check that the dependencies described below are in place.  Alternatively, should you wish to install ``vdu_controls`` 
for all users, RPMs are available for **OpenSUSE**, **Fedora**, and there is an  **archlinux** AUR package
which also works in **Manjaro**.  See the *Install* section below. 

> [!Note]
> Development is **trunk-based**.  It is my intention that the trunk 
> ([master](https://github.com/digitaltrails/vdu_controls)) should always be usable
> as a daily-driver.  If you want the latest features, download from master. 
> That being said, a download of trunk may sometimes be less stable than downloading 
> one of the formal [releases](https://github.com/digitaltrails/vdu_controls/releases) 
> or installing one of the packages that are available in various distros.

Dependencies
------------

All the following runtime dependencies are likely to be pre-packaged on any modern Linux distribution 
(``vdu_controls`` was originally developed on OpenSUSE Tumbleweed).

* **ddcutil >= 1.2, >= 1.4 recommended**: the command line utility that interfaces to VDUs via DDC over i2c-dev or USB. (If 
  anyone requires support for versions of ddcutil prior to v1.2 please contact me directly.)
* **i2c-dev**: the i2c-dev kernel module normally shipped with all Linux distributions and required by [ddcutil](https://www.ddcutil.com)
* **python >=3.8**: ``vdu_controls`` is written in python and may depend on some features present only in 3.8 onward.
* **python >=3.8 QtPy**: the python GUI library used by ``vdu_controls``.

It's best to confirm that ``ddcutil`` is functioning before using ``vdu_controls``:

* See [https://www.ddcutil.com/config/](https://www.ddcutil.com/config/) for instructions on configuring ``ddcutil``
  (including some extra steps for Nvidia GPU users).
* See [https://www.ddcutil.com/i2c_permissions/](https://www.ddcutil.com/i2c_permissions/) for instructions on setting 
  and testing the required permissions.  
* Fo some VDUs, DDC/CI over Display-Port to Display-Port connections may work when others 
  connections don't (mainly with some Nvidia GPUs).

As of ddcutil 1.4, installing a pre-packaged ddcutil will most likely set the correct udev rules to 
grant users access to the required devices.  If you are using an earlier ddcutil, it may be necessary to follow 
all the steps detailed in the links above.  

Installing
----------

As previously stated, the ``vdu_vontrols.py`` script is only file required beyond the prerequisites. There
are also **OpenSUSE** RPMs available at: [https://software.opensuse.org/package/vdu_controls](https://software.opensuse.org/package/vdu_controls),
some unoffical **Fedora** RPMs available at: [build.opensuse.org](https://build.opensuse.org/projects/home:mchnz/packages/vdu_controls/repositories/Fedora_37/binaries)
and an **archlinux** (**manjaro** compatible) **AUR** package at: [https://aur.archlinux.org/packages/vdu_controls](https://aur.archlinux.org/packages/vdu_controls)

That makes three options for "installation": 

1. The script can be run without installation by using a python interpreter, for example:
   ```
   % python3 vdu_controls.py
   ```
2. The script can be self installed as desktop application in the current user's desktop menu 
   as *Applications->Settings->VDU Controls* by running:
   ```
    % python3 vdu_controls.py --install
   ```
      Depending on which desktop you're running menu changes may require logout before they become visible.
3. A system-wide installation using a distribution's packaging system which will install all of:

   ```
   /usr/bin/vdu_controls
   /usr/share/applications/vdu_controls.desktop
   /usr/share/licenses/vdu_controls/LICENSE.md
   /usr/share/vdu_controls/icons/*
   /usr/share/vdu_controls/sample-scripts/*
   /usr/share/vdu_controls/translations/*
   /usr/share/man/man1/vdu_controls.1.gz
   ```

Please note the first two options only install ``vdu-controls`` for the current user.  The script and desktop-file 
installed for a single user could be modified and copied into /usr or /usr/local hierarchies should you 
wish to do so.  If using the first two options, you might want to follow up by manually downloading
some of the other items such as the [starter set of icons](icons) for use when creating Presets.

Executing the program
---------------------

* If installed from rpm, **VDU Controls** should be in everyone's application menu under **Settings**. 
  The ``vdu_controls`` command will also be in everyone's ``PATH`` and will be able to be run from the command
  line, for example:
     ```
     % vdu_controls --show brightness --show contrast --show audio-volume
     ```
* If installed by the current user via the ``--install`` option, **VDU Controls** should be in
  the current user's application menu under **Settings**. The ``vdu_controls`` command will be in ``$HOME/bin``.
  If ``$HOME/bin`` is on the user's ``PATH``, ``vdu_controls`` will be also able to be run from the command
  line in the same manner as above.
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
# or if installed as an executable:
% vdu_controls --help
% vdu_controls --detailed-help
% vdu_controls --detailed-help | pandoc --from markdown --to html > vdu_controls_help.html
```

Whether run from the desktop application-menu or run from the command line, ``vdu-controls`` behaviour can be altered
in a number of ways:

* The `Settings` item in the context-menu.
* Command line options.
* Configurations files in `$HOME/.config/vdu_controls/`

See the context-menu or the  [man page](https://htmlpreview.github.io/?https://raw.githubusercontent.com/digitaltrails/vdu_controls/master/docs/_build/man/vdu_controls.1.html)
 for details.

Bugs and Suggestions
--------------------
If you encounter a bug or issue, or wish to make a suggestion, you're most welcome to raise 
it on the [issues page](https://github.com/digitaltrails/vdu_controls/issues).

Development
-----------

I've set up the ``vdu_controls`` source as a typical Python development, but there is only one real source
file, ``vdu_controls.py``, so the file hierarchy is rather over the top.  A standard python distributable 
can be built by issuing the following commands at the top of the project hierarchy:
```
% python3 -m pip install build
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
I prefer [Pandoc](https://pandoc.org/)'s HTML generation. There is a util script that generates the
Sphinx outputs and then pandoc for the html:
```
% ./util/make-man
```

My IDE for this project is [PyCharm Community Edition](https://www.jetbrains.com/pycharm/).

Coverage testing is assisted by [Coverage.py](https://coverage.readthedocs.io/) and [Vulture](https://pypi.org/project/vulture/).
Type checking is assisted by [Mypy](https://mypy.readthedocs.io/).

My development Linux desktop is [OpenSUSE Tumbleweed](https://get.opensuse.org/tumbleweed/). The python3
interpreter and python3 libraries are from the standard Tumbleweed repositories. 

Acknowledgements
----------------

* Sanford Rockowitz ([rockowitz](https://github.com/rockowitz)), for the robust [ddcutil](https://github.com/rockowitz/ddcutil) utility and all the friendly help and assistance.
* Mark Wagie ([yochananmarqos](https://github.com/yochananmarqos)), for Gnome related suggestions and AUR port.
* Denilson Sá Maia ([denilsonsa](https://github.com/denilsonsa)), for many suggestions, assistance, and contributions.
* Matthew Coleman ([crashmatt](https://github.com/crashmatt)), Mark Lowne ([lowne](https://github.com/lowne)), [usr3](https://github.com/usr3),
  Mateo Bohorquez G. ([Milor123](https://github.com/Milor123)), Andrew Sun ([apsun](https://github.com/apsun)), 
  Extent ([Extent421](https://github.com/Extent421))
  for contributing fixes to code and documentation.
* [Jakeler](https://github.com/Jakeler), [kupiqu](https://github.com/kupiqu), Mateo Bohorquez ([Milor123](https://github.com/Milor123)), Johan Grande ([nahoj](https://github.com/nahoj)), 
  [0xCUBE](https://github.com/0xCUB3), [RokeJulianLockhart](https://github.com/RokeJulianLockhart), [abil76](https://github.com/abil76), Andrew Sun ([apsun](https://github.com/apsun))
  for contributing suggestions for enhancements. 
* Malcolm Lewis ([malcolmlewis](https://github.com/malcolmlewis)) for assistance with the OpenSUSE Open Build Service submissions.
* Christopher Laws ([claws](https://github.com/claws)) for the [BH1750 library](https://github.com/claws/BH1750) 
  and [example build](https://github.com/claws/BH1750#example) (lux-metering).
* Plus others who have supplied feedback and suggestions.

Author
------

Michael Hamilton

Version History
---------------

* 2.4.0
  * New light-metering option, semi-automatic ambient-light-level estimation based on geolocated solar-lux.
  * Fix size of Lux Dialog scale, adjust for display DPI.
  * Fix size of Solar Elevation chart, adjust for display DPI.
  * Fix Lux brightness adjustment, allow protect-nvam to be disabled.
  * Don't create model-only config files, they're confusing and likely not used (they can still be created manually).
  * Fix dbus ddcutil-service detect, only request valid displays.
  * Prevent a lux adjustment infinite loop if no brightness controls are enabled.
  * Code refactoring for clarity/brevity.

* 2.3.0
  * Fix the doze function, this improves the responsiveness of all slider controls.
  * Fix an infinite loop if menu->quit is used when the "Failed to obtain capabilities" dialog is showing.
  * The Settings-Dialog has been reorganized to make it scrollable.
  * When lux options are enabled, the tray will show the icon for current light-level (if no preset is active). 
  * Renamed two light-light levels more appropriately (room becomes subdued, rise-set becomes twilight).
  * Support a user-defined ddcutil-emulator executable for controlling laptop-panels 
    or other non-DDC-capable displays. A template sample emulator written in bash is included 
    as a DIY starter (sample-scripts/laptop-ddcutil-emulator.bash).
  * Add smart-uses-xcb option to control the use of XWayland for the smart positioning of windows (defaults to yes).
  * Fix title-bars on sub-windows in COSMIC. 
  * The About Dialog now includes some desktop and platform information.
  
* 2.2.0
  * Add a vdu-name option for assigning meaningful/user-friendly names to each VDU.
  * Implement an order-by-name option that orders lists and tabs by VDU name.
  * Hovering over a settings-dialog tab-name or save-button reveals the settings-filename as a tooltip. 
  * If smart-window is enabled in a Wayland desktop, automatically use XWayland. (Wayland
    doesn't allow an application to precisely place it's own windows!)
  * Altering the smart-window option now requires a restart (due to the Wayland/XWayland changes).
  * The smart-window option save/restore of main-window has been made more consistent.
  * The COSMIC desktop is treated as GNOME-like (the system-tray right-mouse menu includes a "control-panel" menu-item).  

* 2.1,4
  * Provide a setting for enabling dbus-events - ddcutil-service DPMS and hotplug detection. 
  * Default the dbus-event setting to off, which is less troublesome for some VDUs/GPUs/drivers.

* 2.1.3
  * Fix the error-dialog option "Ignore-VDU" when ddcutil cannot communicate with a VDU.  
  * Avoid abrupt u-turns in automatic brightness, don't reassess the lux level while making an adjustment.
  * Update the EDID-parser to accept the command line output from ddcutil 2.2 (for those not using ddcutil-service).

* 2.1.2
  * Replace the Preset-scheduler with an implementation that remains accurate after PC-sleep/hibernation.
  * Fix the day-rollover which was scheduling for the wrong day if triggered at 12:59:59. 
  * When performing a set-vcp, don't increment the NVRAM write count if the VDU doesn't respond.
  * When reconfiguring VDU controllers, discard pending VDU VCP changes from previous controllers. 
  * Eliminate a potential for deadlock when handling change-events from ddcutil-service.
  * Better handle ddcutil-service unexpected event types (don't raise an error dialog).
  * The main window height will now automatically resize to accommodate the number of controls present.
  * Toggling lux brightness-interpolation now immediately updates the profile-plot to reflect the change.
  * Fix the Lux Dialog, it was turning off interpolation when first constructed.
  
* 2.1.1
  * Removed --dbus-signals-enabled. DBus signals are now always enabled when --dbus-client
    is enabled.
  * Fix the active Preset icon display which was sometimes incorrect after DPMS-sleep or errors. 
  * Fix a code regression when handling non-DDC-capable VDUs (fix status=-3020 exception).
  * The About-Dialog now includes counts of per-VDU set_vcp/NVRAM-writes.
  * Hovering over a VDU-name in the main-window reveals the write count for that VDU.
  * Minor changes to reduce unnecessary work and improve log messages.

* 2.1.0
  * Preset _transitions_ have been deprecated.  All presets are now restored instantly no 
    matter how they have been set to transition.  The Preset-Dialog controls for assigning
    transitions have been hidden.   __All  transition related code may be removed in a future 
    version, please contact me or comment on issue #93 if you prefer transitions to be retained.__
  * Transitions and related controls can be re-enabled by disabling `protect-nvram` in the _Settings-Dialog_. 
  * To avoid unnecessary updates, preset restoration now queries the VDU's existing
    values. This may slow down preset restoration.
  * Lux-metered auto adjustment has been defaulted to 10 minute intervals (up from 5).
  * Color-Preset (VCP code 0x14) has been added to the list of standard controls.
  * Added a VDU  ___Initializer-Preset___ feature to provide a replacement for dead NVRAM.
    This also provides a way to restore settings not persisted in VDU NVRAM.  A VDU's initializer-preset is 
    automatically run if the target VDU is present at startup or is subsequently detected.
    Any preset that has a name that matches a VDU model and serial-number will be treated
    as an Initializer-Preset. 
  * The ___Preset-Dialog___ now includes a tool-button  to the right of the preset-name entry 
    that will create a VDU specific ___Initializer-Preset___.
  
* 2.0.4
  * The About-Dialog now refreshes the ddcutil version info on each invocation. 
  * Increased dbus timeout to 10 seconds (in case numerous VDUs or errors slow down VDU detection).
  * Dynamically enable a scroll-area when the main-panel exceeds the available screen height.
  
* 2.0.3
  * Reduce the number of writes to VDU NVRAM by sliders, spinners, and ambient brightness adjustments.
    * Slider and spin-box controls now only update the VDU when adjustments become slow or stop (when 
      the control value remains constant for 0.5 seconds).
    * Spin-Boxes now select the entire text on focus in (enables easier overtyping and decreases VDU updates).
    * Ambient lighting initiated changes in brightness of up to 20% are applied without any transitional 
      steps (plus the existing code ignores updates of less than 10%). 
    * Set the default ambient-light brightness adjustment-interval to 5 minutes.
  * React to DPMS awake signal from ddcutil-service by re-assessing ambient brightness.
  * Simplified locking and conformed to a locking hierarchy/protocol to avoid potential deadlocks.

* 2.0.2
  * Added a *refresh* annotation suffix for use with VCP-codes which cause multiple changes.
  * Make manual adjustment of the ambient Light Level more accurate and responsive.
  * Updates are sent to the VDU as sliders are dragged (rather than only on release).
  * Fix exception on monitors that return invalid/unexpected combo-box VCP values.
  * Fix exception on monitors with blank VCP value descriptions.
  * When refresh is pressed, only auto adjust ambient brightness if auto-brightness is enabled.
  * Don't automatically refresh on error, eliminate popup dialog loops.
  * Eliminate deadlocks when exceptions occur.
  * Cleanup the initialisation of the ddcutil-service connection.
  * Add more caveats and limitations to the documentation.
  * Fix manual ambient light slider when light meter is uninitialized.
  * Promote Simple-Non-Continuous values whose metadata exceeds one-byte to two-byte Complex-NC.
  
* 2.0.1
  * Fix D-Bus client code for python versions prior to 3.11.
  * Fix infinite-loop when altering an existing FIFO lux-meter in the Lux-Dialog.
  * Fix the refresh of the LuxDialog meter-readout/plot when changing to a new meter.
  * Apply context-aware defaults to the LuxDialog device file-chooser. 
  * Improve/fix the handling of displays/laptop-displays that may be detected but lack proper DDC.
  * Force the file-picker to always show devices and FIFOs - it wasn't showing then on some desktops.

* 2.0.0
  * Added an optional D-Bus interface to ddcutil for up to 10x faster response times.
  * Added an immediate-lighting-check button and corresponding context-menu item (when lux-metering is enabled).
  * Added an ambient-light-control for manual lux input, one slider to adjust brightness on all displays.
  * Added more preset icons.

* 1.20.0
  * Added options monochrome-tray and mono-light-tray to enable a monochrome tray-icon (dark and light).
  * Optional $HOME/.config/vdu_controls/tray_icon.svg overrides the normal tray icon.
  * Improved the adjustment of icon/window dimensions by scaling them in respect to the user's default-font height.
  * Remove adjust-for-dpi in favour of the the above which automatically accounts for DPI.
  * When a Preset is transitioning slowly (i.e. not immediately), the UI controls can be used to stop the transition.
  * Considerable internal refactoring of option handling.

* 1.12.0
  * Added an F10_key context menu shortcut to all application windows (KDE accessibility standard).
  * Set icon and pixmap sizes appropriately for Normal and High DPI (controlled by adjust-for-dpi) (issue #63).
  * Icon/device-chooser-dialog: init-time reduced from 30 to 5 seconds for users with large home folders (issue #61).
  * Improvements/Fixes to the vlux_meter.py sample-script and the related vdu_controls FIFO reader.
  * Improved visibility of the app-icon's preset-transitioning indicator and auto-lux indicator.
  * Increased contrast for generated text preset-abbreviation icons.
  * Encode translations in plain text rather than escaped XML (for easier editing).

* 1.11.1
  * Fix Preset text size in tray icon.
  * Fix occasional concurrency lockup issue in lux_metering.
  * Update the Settings Dialog when a new VDU becomes available.
  * Light-metering: show both a lux-auto indicator (an orange "LED") AND the current preset (if any) in the app icon.
  * Fix first time use crash (issue #60).
  * Allow % in config files by turning off ConfigParser interpolation (issue #60).
* 1.11.0
  * Made vdu_controls ddcutil-2.0-ready.
  * Added support for ddcutil versions earlier than 1.3 (issue #43, #53).
  * Main-Window: added a hide-on-focus-out option to minimize the main window on focus out (issue #57).
  * Main-Window: changed the layout to display brightness and contrast as the first two controls for each VDU.
  * Main-Window: added jump to clicked value to sliders (issue #59).
  * Main-Window: added a smart-main-window option to make main window placement and geometry preservation optional.
  * Main-Window: the main window can now be raised above the other sub-windows (gnome issue only).
  * Main-Window and Context Menu: added alt-key keyboard shortcuts (issue #13).
  * Context-Menu: added an indicator mark suffix to the currently active Preset (if any) (issue #55).
  * Context-Menu: made changes to Preset ordering propagate to the menu without requiring an application restart.
  * Tray-Icon: made the app icon un-themed so that overlaid active Preset text/icon is more visible (issue #55).
  * Settings-Dialog: added a Reset button to makes it possible to un-ignore a VDU (issue #51).
  * Settings-Dialog: added tool-tips to main config-settings, made them consistent with command line help (issue #52).
  * Preset-Dialog: combined the Activate and Edit buttons into one button (simpler and more intuitive).
  * Preset Dialog: made the dialog bold the text button of the currently active Preset (if any).
  * Preset Dialog: added code to detect and and warn of unsaved changes.
  * Preset Dialog: made the dialog lock out any scheduled or automatic VDU changes while a Preset is being edited.
  * Preset-Dialog: supplied a starter set of Prest icons - a selection of KDE breeze5-icons (issue #56).
  * Popup-Messages: made message box popups resizable for increased readability.
  * Command-line: made config-settings and command-line arguments consistent, command line has precedence (issue #52).
  * Command-line: fixed --sleep-multiplier so that it is actually applied (issue #54).
  * Prevented potential crashes in the event of utf-8 decoding errors for EDIDs and capabilities (issue #49).
  * Added logging of stack traces for some errors if debugging is set to on (issue #49).
  * Improved the handling of ddcutil not found (issue #48).
  * Refactored to improve maintainability and run-time efficiency (issue #52).
  * Added Deepin 23 pyqt library compatibility.
  * Numerous minor enhancements and fixes.
  * An alpha release of vlux_meter.py, a system-tray webcam lux-meter, has been included in the sample scripts folder.
* 1.10.2
  * Fix Preset non-zero transition-step-seconds, so it works properly.
  * Changing log-to-syslog or log-debug-enabled no longer requires a restart.
  * Fix Lux Auto menu icon when starting with Auto disabled.
  * Use the progress bar area on the main panel for status messages.
  * Make auto brightness behave more predictably by removing unnecessary constraints on interpolation.
  * Improve auto-lux/preset tray icon interaction - better reflect actions and current state.
* 1.10.1
  * Restore lux meter displayed-value when restoring LuxDialog window.
  * Minor fixes to reduce and improve displayed and logged messages.
  * Rollup release prior to downtime for ToTK
* 1.10.0
  * Added hardware lux metering options (GY30/BH1750+Arduino, UNIX-fifo, or executable-script).
  * Added lux-to-brightness profiles per VDU.
  * Added sample scripts for using a webcam to produce approximate lux values.
  * Added an option to transition smoothly on UNIX signal.
  * Replaced the transition combo-box with a button+checkboxes.
  * Added drag-to-change, click-to-delete, to the elevation chart component.
  * Added a setting to quickly disable weather and another for elevation-scheduling.
  * Cleanup of thread handling - clarification of GUI/non-GUI thread operations.
  * Reduced logging and eliminated popup dialogs when monitors are suspended or powered off.
* 1.9.2
  * Optional _Smooth Transitions_ for presets:
    * The Presets Dialog now includes an option to set a Preset to _Transition Smoothly_.
    * The tray, main panel, and Preset Dialog indicate when a smooth transition is in progress.
    * Transitions are performed by a non-GUI thread, the GUI remains accessible during smooth transitions.
    * A smooth transition can be interrupted by moving the controls being transitioned or invoking a preset.
* 1.9.1
  * The text input to right of slider controls has been replaced with a SpinBox with up/down arrows.
  * The main panel progress-bar spinner will now also display during preset-activation (in addition to displaying during refresh).
  * Refresh and preset controls now lock during refresh and preset-activation (to prevent conflicting actions).
  * The context menu and hamburger menu are now available during refresh (a subset of actions is available, such as help and about).
  * The VDU `EDID` 128/256 byte identifier is now used internally to ensure the controls operate on the correct monitor.
  * Build changes for submission to _OpenSUSE_  _Development_ and _Factory_ by @malcolmlewis.
  * The thread handling and error handling has been cleaned up.
* 1.9.0
  * Bug fixes and speedy performance improvements:
    * Speed up initialization and refresh by combining multiple ddcutil `getvcp` requests.
    * Stop executing a `getvcp` precheck before each `setvcp`. 
    * Fix repeat-initialisation bug in _Context-Menu Refresh_.
    * Fix _Settings Dialog_ text field validation, some errors were invisibly ignored.
    * Fix _Settings Dialog_ _Settings Enable VCP Codes_, they had stopped working.
    * Fix the monitor specific sleep multipliers, they were not always being used.
    * Treat all monitor detection situations as needing time to stabilise (helps in disconnect situations).
    * Fix event handling so that tablet+pen input works on the main window.
    * Default to a sleep-multiplier of 1.0 to support a wider range of monitors out of the box.
  * V1.9.0 drops support for converting from v1.6.* config and preset files. To convert 
    from v1.6.* and earlier versions, follow these steps to download and run v1.8.3:
    ```
     % wget https://github.com/digitaltrails/vdu_controls/blob/v1.8.3/vdu_controls.py
     % python3 vdu_controls.py
    ```
    Alternatively, start fresh by moving or removing the old configs from `$HOME/.config/vdu_controls`.
* 1.8.3
  * Fix for a crash when the network is down and the weather site cannot be contacted. 
* 1.8.2
  * Solar elevation weather requirements.
  * Locale language support and sample AI generated translations.
* 1.8.0
  * Presets can be scheduled to activate according to solar elevation at a given latitude and longitude.
* 1.7.2
  * Better handle monitors being powered off: on set-value errors, check what's connected. 
  * The display ordering of presets can now be manually altered in the Presets dialog.
  * Do not exit if no controllable monitor is found.
* 1.7.1
  * Refactoring in 1.7 broke the signal handling - incorporate fix from Mark Lowne. 
* 1.7.0
  * Presets can now optionally have icons which display in the menu and overlay the tray icon.
  * The Preset-management dialog now includes an icon selection button.
* 1.6.11
  * Display current preset in window and tray title and detect if a preset is in use at startup.
* 1.6.10, 1.6.9
  * Cope better with invalid slider values caused by a monitor being too slow/busy when responding.
  * Wait for monitor detection to stabilise at session restoration (at login time).
* 1.6.8
  * Fix preset restore/save bug introduced in 1.6.7
* 1.6.7
  * Gnome system tray behaviour made consistent with gnome - when in gnome do as the gnomens do.
* 1.6.5
  * Widen handling of pare exceptions for VDU capabilities - catch more exceptions.
* 1.6.4
  * Wait for system tray to become available (for autostart Plasma Wayland).
  * Enable HiDPI icons (for the bottom toolbar) - fix blurred toolbar icons on up-scaled desktops.
* 1.6.3
  * Added a hamburger menu as an obvious alternate path to the context menu.
  * Minor cosmetic UI changes.
* 1.6.2
  * Added a Feature Values: min..max override to optionally restrict brightness and other sliders.
* 1.6.1
  * Alterations for Wayland compatibility (cosmetic)
* 1.6.0
  * Let other processes trigger vdu_controls preset changes and settings refreshes via UNIX/Linux signals.
* 1.5.2
  * ``vdu-controls`` is now feature complete in respect to my own requirements.
  * Raise popup dialogs to the top (in case Qt renders them behind existing windows).
  * Documentation tweaks.
* 1.5.1
  * New grey-scale reference chart for assistance with brightness and contrast adjustment.
  * About/help/settings/presets dialogs are now singletons, only one of each can be visible.
* 1.5.0
  * New presets feature: easily switch between named presets such as *Night*, *Day*, *Overcast*, *Sunny*, 
    *Photography*, and *Video*.
  * ``Presets`` context-menu item for access to the new ``preset management widget``.
  * Context menu shortcuts for quickly accessing presets.
  * INI preset file format for ease of editing.
* 1.4.2
  * Fix increasing indentation of multiline capabilities text on each config file save.
  * Prune the VDU settings-editor control-list to only show controls supported by the VDU.
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
    This can be used to prevent the slowest VDU from dragging down response time for all connected VDUs.
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

