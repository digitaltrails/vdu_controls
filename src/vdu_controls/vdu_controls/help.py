# SPDX-FileCopyrightText: 2021-2026 Michael Hamilton
# SPDX-License-Identifier: GPL-3.0-or-later
"""
vdu_controls - a DDC control panel for monitors
===============================================

A control panel for DisplayPort, DVI, HDMI, or USB-connected VDUs (*Visual Display Units*).

Synopsis:
=========

        vdu_controls
                     [--help|-h] [--about] [--detailed-help]
                     [--show {brightness,contrast,audio-volume,input-source,power-mode,osd-language}]
                     [--hide {brightness,contrast,audio-volume,input-source,power-mode,osd-language}]
                     [--enable-vcp-code vcp_code] [--schedule|--no-schedule]
                     [--splash|--no-splash] [--system-tray|--no-system-tray]
                     [--hide-on-focus-out|--no-hide-on-focus-out]
                     [--smart-window|--no-smart-window] [-smart-uses-xwayland|-smart-uses-xwayland]
                     [--monochrome-tray|--no-monochrome-tray] [--mono-light-tray|--no-mono-light-tray]
                     [--tray-follows-theme|--no-tray-follows-theme]
                     [--toolbar-at-top|-no-toolbar-at-top]
                     [--separate-status-bar|--separate-status-bar]
                     [--laptop-panels|--no-laptop-panels]
                     [--protect-nvram|--no-protect-nvram]
                     [--lux-options|--no-lux-options]
                     [--schedule|--no-schedule] [--weather|--no-weather]
                     [--dbus-client|--no-dbus-client] [--dbus-events|--no-dbus-events]
                     [--syslog|--no-syslog] [--debug|--no-debug] [--warnings|--no-warnings]
                     [--translations|--no-translations]
                     [--location latitude,longitude] [--ddcutil-emulator emulator-path]
                     [--sleep-multiplier multiplier] [--ddcutil-extra-args 'extra args']
                     [--create-config-files] [--install] [--uninstall]

Optional arguments:
-------------------

Arguments supplied on the command line override config file equivalent settings.

      -h, --help            show this help message and exit
      --detailed-help       full help in Markdown format
      --about               info about vdu_controls
      --show control_name
                            show specified control only, may be specified multiple times
      --hide control_name
                            hide/disable a control, may be specified multiple times
      --enable-vcp-code vcp_code
                            enable a control for a vcp-code unavailable via hide/show,
                            may be specified multiple times
      --splash|--no-splash
                            show the splash screen.  ``--splash`` is the default.
      --system-tray|--no-system-tray
                            start up as an entry in the system tray.
                            ``--no-system-tray`` is the default.
      --hide-on-focus-out|--no-hide-on-focus-out
                            minimize the main window automatically on focus out.
                            ``--no-hide-on-focus-out`` is the default.
      --smart-window|--no-smart-window
                            smart main window placement and geometry.
                            ``--smart-window`` is the default (may force UI to XWayland).
      --smart-uses-xwayland|--no-smart-uses-xwayland
                            if ``--smart-window`` is enabled, use XWayland (force X11 xcb).
                            ``--smart-uses-xwayland`` is the default.
      --monochrome-tray|--no-monochrome-tray
                            monochrome dark-themed system-tray.
                            ``--no-monochrome-tray`` is the default.
      --mono-light-tray|--no-mono-light-tray
                            monochrome themed system-tray.
                            ``--no-mono-light-tray`` is the default.
      --tray-follows-theme|--no-tray-follows-theme
                            the tray-theme toggles between light/dark when the desktop-theme changes
                            ``--tray-follows-theme`` is the default.
      --toolbar-at-top|--no-toolbar-at-top
                            locate the toolbar at the top or bottom of the main window
                            ``--no-toolbar-at-top`` is the default
      --separate-status-bar|--no-separate-status-bar
                            separate the status-bar from the toolbar
                            ``--no-separate-status-bar`` is the default
      --laptop-panels|--no-laptop-panels
                            allow laptop panels to be controlled
                            ``--no-laptop-panels`` is the default
      --protect-nvram|--no-protect-nvram
                            alter options and defaults to minimize VDU NVRAM writes.
      --order-by-name|--no-order-by-name
                            order tabs, lists, and dropdowns by VDU name.
      --lux-options|--no-lux-options
                            enable/disable ambient light metering options.
                            ``--lux-options`` is the default.
      --schedule|--no-schedule
                            enable/disable preset scheduling. ``--schedule`` is the default.
      --weather|--no-weather
                            enable/disable weather lookups. ``--weather`` is the default.
      --dbus-client|--no-dbus-client
                            use the D-Bus ddcutil-service instead of the ddcutil command.
                            ``--dbus-client`` is the default
      --dbus-events|--no-dbus-events
                            enable D-Bus ddcutil-service client events
                            ``--dbus-events`` is the default
      --syslog|-no-syslog
                            divert diagnostic output to the syslog (journald).
                            ``--no-syslog`` is the default.
      --debug|--no-debug
                            enable/disable additional debug information.
                            ``--no-debug`` is the default.
      --warnings--no-warnings
                            popup a warning when a VDU lacks an enabled control.
                            ``--no-warnings`` is the default.
      --translations|--no-translations
                            enable/disable language translations.
                            ``--no-translations`` is the default.
      --location latitude,longitude
                            local latitude and longitude for triggering presets
                            by solar elevation.
      --ddcutil-emulator emulator-path
                            additional command-line ddcutil emulator for a special cases.
      --sleep-multiplier    set the default ddcutil sleep multiplier.
                            protocol reliability multiplier for ddcutil (typically
                            0.1 .. 2.0, default is 1.0)
      --ddcutil-extra-args  extra arguments to pass to ddcutil (enclosed in single quotes).

      --create-config-files
                            if they do not exist, create template config INI files
                            in $HOME/.config/vdu_controls/
      --install             installs the vdu_controls in the current user's path and
                            desktop application menu.
      --uninstall           uninstalls the vdu_controls application menu file and
                            script for the current user.

Description
===========

``vdu_controls`` is a control-panel for DisplayPort, DVI, HDMI, or USB connected VDUs.  Out of the
box, ``vdu_controls`` offers a subset of controls including brightness, contrast and audio
controls.  Additional controls can be enabled via the ``Settings`` dialog.

``vdu_controls`` interacts with VDUs by using ``ddcutil`` to issue standard VESA
*Virtual Control Panel* (*VCP*) commands via the VESA *Display Data Channel* (*DDC*).
``Ddcutil`` provides a robust interface that is tolerant of the vagaries of the many OEM DDC
implementations.

From ``vdu_controls 2.0`` onward, ``vdu_controls`` defaults to using the ``D-Bus ddcutil-service``.
Should the ``ddcutil-service`` be unavailable, ``vdu_controls`` will fall back to running the
``ddcutil`` command to perform each request.

The UI look-and-feel dynamically adjusts to dark and light themes. The application may
optionally run in the system tray of KDE, Deepin, GNOME, and Xfce (and possibly others).
For desktops that don't integrate with Qt/KDE themeing, the `qt5ct` and `qt6ct` utilities may
be used to alter the overall Qt theme.

The UI provides an optional ``ambient-light slider`` for simultaneously adjusting
all VDUs according to custom per-VDU ambient lux/brightness profiles.  Options are included
for semi-automatic adjustment proportional to daylight at a given geographic location, or
fully automatic adjustment by accessing hardware light-meters, webcams, or other devices.

Named ``Preset`` configurations can be saved and recalled. For example, presets may be created
for night, day, photography, movies, and so forth.   Presets can be triggered by specific ambient
light levels, scheduled according to local solar elevation, vetoed by local weather conditions,
or activated by UNIX signals.

From any UI window, `F1` accesses help, and `F10` accesses the main-menu.   The main-menu is
also available via the hamburger-menu, and also via the right-mouse button in either the
main-window or the system-tray icon.  The main-menu has `ALT-key` shortcuts for all menu items
(subject to sufficient letters being available to distinguish all user defined presets).

The main-toolbar includes a stealthy-drag-handle at extreme-left.  The toolbar
can be dragged and docked at either the top or bottom top of the main-window.
The toolbar's position persists across restarts.

For further information, including screenshots, see https://github.com/digitaltrails/vdu_controls .

The long-term effects of repeatably rewriting a VDUs setting are not well understood, but some
concerns have been expressed. See **LIMITATIONS** for further details.

Configuration
=============

Configuration changes can be made via the ``Settings`` dialog or by editing the config-files.

Settings Menu and Config files
------------------------------

The ``Settings`` dialog features a tab for editing common/default settings as well as
tabs specific to each VDU.  The config files are named according to the following scheme:

 - Application wide default config: ``$HOME/.config/vdu_controls/vdu_controls.conf``
 - VDU model and serial number config: ``$HOME/.config/vdu_controls/<model>_<serial|display_num>.conf``
 - VDU model-only config: ``$HOME/.config/vdu_controls/<model>.conf`` (deprecated, no longer created).

The VDU-specific config files can be used to:

 - Correct manufacturer built-in metadata.
 - Customize which controls are to be provided for each VDU.
 - Define a user-friendly label for each VDU.
 - Set optimal ``ddcutil`` DDC parameters for each VDU.

The config files are in INI-format divided into a number of sections as outlined below::

    [vdu-controls-globals]
    # The vdu-controls-globals section is only required in $HOME/.config/vdu_controls/vdu_controls.conf
    system-tray-enabled = yes|no
    splash-screen-enabled = yes|no
    translations-enabled = yes|no
    weather-enabled = yes|no
    schedule-enabled = yes|no
    lux-options-enabled = yes|no
    warnings-enabled = yes|no
    debug-enabled = yes|no
    syslog-enabled = yes|no

    [vdu-controls-widgets]
    # Yes/no for each of the control options that vdu_controls normally provides by default.
    brightness = yes|no
    contrast = yes|no
    audio-volume = yes|no
    audio-mute = yes|no
    audio-treble = yes|no
    audio-bass = yes|no
    audio-mic-volume = yes|no
    input-source = yes|no
    power-mode = yes|no
    osd-language = yes|no

    # Enable ddcutil supported codes not enabled in vdu_controls by default, CSV list of two-digit hex values.
    enable-vcp-codes = NN, NN, NN

    # User friendly VDU name
    vdu_name = My Main Monitor (on the right)

    [ddcutil-parameters]
    # Useful values appear to be >=0.1
    sleep-multiplier = 0.5

    [ddcutil-capabilities]
    # The (possibly edited) output from "ddcutil --display N capabilities" with leading spaces retained.
    capabilities-override =

Config files can only be used to enable and alter definitions of VCP codes supported by ``ddcutil``.
Unsupported manufacturer-specific features should only be enabled with caution; some
may have irreversible consequences, including bricking the hardware.

As well as using the ``Settings``, config files may also be created by the command line option::

    vdu_controls --create-config-files

which will create initial templates based on the currently connected VDUs.

The config files are completely optional, they need not be used if the default options are found to be
adequate.

Adding value restrictions to a VDU's capabilities override
----------------------------------------------------------

In some cases, a VDU's DDC reported minimums and maximums may be incorrect or overstated.  Within
vdu_controls this can be corrected by overriding the DDC reported range. For example, perhaps a VDU
reports it supports a brightness range of 0 to 100, but in fact only practically supports 20 to 90.
This can be corrected by bringing up the VDU's settings tab and editing the text in
the **capabilities override**:

 1. Open the *Settings* tab for the VDU, navigate to the "capabilities override* field
 2. locate the feature, in this example, the brightness,
 3. add a **Values:** **min..max** specification to the line following the feature definition,
 4. save the changes.

For the brightness example, the completed edit would look like::

    Feature: 10 (Brightness)
        Values: 20..80

The vdu_controls slider for that value will now be restricted to the specified range.

Adding a refresh/reload requirement to a VDU's capabilities override
--------------------------------------------------------------------

Altering the values of some VCP codes may result in a cascade of changes to other
codes.  For example, changing a VCP value for *Picture Mode* might result in changes
to several VCP-code features, including brightness, contrast, and others. Exactly
which codes have these kinds of side effects isn't indicated in the metadata
obtained from each VDU, however, vdu_controls supports adding *refresh* annotations
to the feature-names within the **capabilities override**.  For example::

    Feature: 15 (Picture Mode)

Can be annotated with::

    Feature: 15 (Picture Mode *refresh*)

With this annotation, when ever *Picture Mode* is altered, vdu_controls will
reload all configuration files and refresh all control values from the VDUs.

Laptop-Panel brightness control
-------------------------------

Starting with version 2.6, laptop panels are supported for brightness-only control.
When laptop support is enabled, the widely available command line utility ``brightnessctl``
is used to emulate DDC control of brightness (https://github.com/Hummer12007/brightnessctl).
Additionally, ``vdu_controls`` will react to laptop brightness-function-keys or
inactivity-dimming by using the ``python3-pyudev`` library to monitor udev
for _brightness_ events.

DBUS ddcutil-service
--------------------

When available, ``vdu_controls`` defaults to interacting with VDUs via the DBUS ``ddcutil-service``
service rather than the ``ddcutil`` command. The service should be both faster and more
reliable (especially when multiple VDUs need to be controlled). Whether to use the service
can be controlled by the ``DBUS client`` checkbox in the settings dialog.

When using the service, you may optionally enable service detection of DPMS events and
VDU connectivity events (hot-plugging cables or power-cycling VDUs).  Whether to enable events
is controlled by the ``DBUS events`` checkbox in the settings dialog.  The reliability
and timeliness of events may vary depending on the GPU model, GPU driver, VDU model,
and VDU connector-cable (DP, HDMI, ...).  In some cases, the service polling for DPMS or
connection status may wake some VDU models.  Both ``ddcutil-service`` or ``libddcutil`` offer
options for finer control over which events are detected and how.

Presets
-------

A named _Preset_ can be used to save the current VDU settings for later recall. Any number of
presets can be created for different lighting conditions or different applications, for example,
*Night*, *Day*, *Overcast*, *Sunny*, *Photography*, and *Video*. Each preset can be assigned a
name and icon.

The ``Presets`` item in ``main-menu`` will bring up a ``Presets`` dialog for managing and
applying presets.  The ``main-menu`` also includes an item for each existing preset.

Any small SVG or PNG can be assigned as a preset's icon.  Monochrome SVG icons that conform to the
Plasma color conventions will be automatically inverted if the desktop them is changed from dark to
light. If a preset lacks an icon, an icon will be created from the initials of the first and last
words of its name. A starter set of icons is included in ``/usr/share/vdu_controls/icons/``.

Any time the current VDUs settings match those of a preset, the preset's name and icon will
automatically show in the window-title, tray tooltip, tray icon.

Presets may be set to transition immediately (the default); gradually on schedule (solar elevation);
or gradually always (when triggered by schedule, main-menu, or UNIX signal).  The speed of
transition is determined by how quickly each VDU can respond to adjustment.  During a transition,
the transition will be abandoned if the controls involved in the transition are altered by any other
activity.

Each preset is stored in config directory as: ``$HOME/.config/vdu_controls/Preset_<preset_name>.conf``

Preset files are saved in INI-file format for ease of editing.  Each preset file contains a
section for each connected VDU, for example::

    [preset]
    icon = /usr/share/icons/breeze/status/16/cloudstatus.svg
    solar-elevation = eastern-sky 40
    transition-type = scheduled
    transition-step-interval-seconds = 5

    [HP_ZR24w_CNT008]
    brightness = 50
    osd-language = 02

    [LG_HDR_4K_89765]
    brightness = 13
    audio-speaker-volume = 16

When creating a preset file, you may select which controls to save for each VDU.  For example,
you might create a preset that includes the brightness, but not the contrast or audio-volume.
Keeping the included controls to a minimum speeds up the transition and reduces the chances of the
VDU failing to keep up with the associated stream of DDC commands.

While using the GUI to create or edit a preset, activation of scheduled presets and adjustments due
to light-metering are blocked until editing is complete.

Presets - VDU initialization-presets
------------------------------------

For a VDU named `abc` with a serial number `xyz`, if a preset named `abx xyz` exists, that
preset will be restored at startup or when ever the VDU is subsequently detected.

This feature is designed to restore settings that cannot be saved in the VDU’s NVRAM
or for VDUs where the NVRAM capacity has been exhausted or is faulty.

Presets - solar elevation triggers
----------------------------------

A preset may be set to automatically trigger when the sun rises to a specified elevation. The idea
is to allow a preset to trigger relative to dawn or dusk, or when the sun rises above some
surrounding terrain (the time of which will vary as the seasons change).

If a preset has an elevation, the preset will be triggered each day at a time calculated according
to the latitude and longitude specified by in the ``vdu-controls-globals`` ``location`` option.
By choosing an appropriate ``solar-elevation`` a preset may be confined to specific times of the
year.  For example, a preset with a positive solar elevation will not trigger at mid-winter in the
Arctic circle (because the sun never gets that high).  Any preset may be manually invoked
regardless of its specified solar elevations.

To assign a trigger, use the Preset Dialog to set a preset's ``solar-elevation``.  A solar elevation
may range from -19 degrees in the eastern sky (morning/ascending) to -19 degrees in the western sky
(afternoon/descending), with a maximum nearing 90 degrees at midday.

On any given day, the Preset Dialog may be used to temporarily override any trigger, in which case
the trigger is suspended until the following day.  For example, a user might choose to disable
a trigger intended for the brightest part of the day if the day is particularly dull.

At startup ``vdu_controls`` will restore the most recent preset that would have been triggered for
this day (if any).  For example, say a user has ``vdu_controls`` set to run at login, and they've
also set a preset to trigger at dawn, but they don't log in until just after dawn, the
overdue dawn preset will be triggered at login.

Presets - time-of-day triggers
------------------------------

A preset may be set to trigger at a fixed time each day.  This is an alternative to the
elevation trigger.  It's not possible for a single preset to have both kinds of trigger.

As with the elevation trigger, the Preset Dialog may be used to temporarily
override any trigger, in which case the trigger is suspended until the following day.
Similarly, at startup, the most recent preset that would have been triggered for this
day will be restored.

Presets - Smooth Transitions
----------------------------

__To minimize writes to VDU NVRAM, smooth-transitions have been deprecated and are disabled by
default. To re-enable smooth transitions, uncheck the ``protect-nvram`` option in _Settings_.__

A preset may be set to ``Smoothly Transition``, in which case changes to controls continuous-value
slider controls such as brightness and contrast will be stepped by one until the final values are
reached.  Any non-continuous values will be set after all continuous values have reached their
final values, for example, if input-source is included in a preset, it will be restored at the end.

The Preset Dialog includes a combo-box for defining when to apply transitions to a preset:

 - ``None`` - change immediately;
 - ``On schedule`` - slowly change according to a solar elevation trigger;
 - ``On signal`` - slowly change on the appropriate UNIX signal;
 - ``On menu`` - slowly change when selected in the main-menu;

Normally a transition single-steps the controls as quickly as possible.  In practice, this means each
step takes one or more seconds and increases linearly depending on the number of VDUs and number of
controls being altered.  The Presets Dialog includes a ``Transition Step seconds`` control that can
be used to increase the step interval and extend a transition over a longer period of time.

If any transitioning controls change independently of the transition, the transition will cease.  In
that manner, a transition can be abandoned by dragging a slider or choosing a different preset.

Presets - supplementary weather requirements
--------------------------------------------

A solar elevation trigger can have a weather requirement which will be checked against the weather
reported by https://wttr.in.

By default, there are three possible weather requirements: ``good``, ``bad``, and ``all weather``.
Each  requirement is defined by a file containing a list of WWO (https://www.worldweatheronline.com)
weather codes, one per line.  The three default requirements are contained in the files
``$HOME/.config/vdu_controls/{good,bad,all}.weather``.  Additional weather requirements can be
created by using a text editor to create further files.  The ``all.weather`` file exists primarily
as a convenient resource that lists all possible codes.

Because reported current weather conditions may be inaccurate or out of date, it's best to use
weather requirements as a coarse measure. Going beyond good and bad may not be very practical.
What's possible might depend on your local weather conditions.

To ensure ``wttr.in`` supplies the weather for your location, please ensure that ``Settings``
``Location`` includes a place-name suffix.  The ``Settings`` ``Location`` ``Detect`` button has been
enhanced to fill out a place-name for you.  Should ``wttr.in`` not recognize a place-name, the
place-name can be manually edited to something more suitable. The nearest big city or an
airport-code will do, for example: LHR, LAX, JFK.  You can use a web browser to test a place-name,
for example: https://wttr.in/JFK

When weather requirements are in use, ``vdu_controls`` will check that the coordinates in
``Settings`` ``Location`` are a reasonable match for those returned from ``wttr.in``, a warning will
be issued if they are more than 200 km (124 miles) apart.

If the place-name is left blank, the ``wttr.in`` server will try to guess your location from your
external IP address.  The guess may not be accurate and may vary over time.

Presets - remote control
------------------------

UNIX/Linux signals may be used to cause ``vdu_controls`` to restore a preset or to initiate a
refresh of the application from the connected monitors.  Signals in the range 40 to 55 correspond to
first to last presets (if any are defined).  Additionally, SIGHUP can be used to initiate "Refresh
settings from monitors".  For example:

    Identify the running vdu_controls (assuming it is installed as /usr/bin/vdu_controls)::

        ps axwww | grep '[/]usr/bin/vdu_controls'

    Combine this with kill to trigger a preset change::

        kill -40 $(ps axwww | grep '[/]usr/bin/vdu_controls' | awk '{print $1}')
        kill -41 $(ps axwww | grep '[/]usr/bin/vdu_controls' | awk '{print $1}')

    If some other activity has changed a VDU's settings, trigger vdu_controls to update its UI::

        kill -HUP $(ps axwww | grep '[/]usr/bin/vdu_controls' | awk '{print $1}')

Any other signals will be handled normally (in many cases they will result in process termination).

Ambient Light Levels and Light/Lux Metering
-------------------------------------------

The default UI includes an ``ambient-light slider`` which will simultaneously adjust all VDUs
according to custom VDU profiles.  As well as manual adjustment, the
slider-value can adjust semi-automatically based on geolocation and local-datetime, or
fully-automatically by hardware light-metering.

The ``Light-Metering`` dialog provides options for setting up light-metering, adjustment
intervals, and per-VDU lux/brightness profiles.  The metering dialog additionally provides a
rolling display of current metered light level and VDU brightness levels.

``Semi-automatic ambient-light level adjustment`` periodically adjusts the light-level in
proportion to the estimated sunlight for your geolocation. Set the
current light level by adjusting the ambient-light-level slider.  Starting from your chosen level,
the application will adjust the light-level following a trajectory based on the estimated sunlight.
If conditions change, adjust the slider to alter the trajectory.  The trajectory is plotted in
the Light-Metering dialog, along with the estimate of outdoor lux (Eo) and the Daylight-Factor
(DF) - the ratio of indoor to outdoor lux.

``Fully-automatic ambient-light level adjustment`` requires setting up a hardware lux metering device.
A metering device may be a serial-device, a UNIX FIFO (named-pipe), or an executable (script or
program):

 - A serial-device must periodically supply one floating-point lux-value
   terminated by a carriage-return newline.
 - A FIFO must periodically supply one floating-point lux-value terminated by a newline.
 - An executable must supply one floating-point lux-value reading terminated by a newline each time
   it is run.

Possible hardware devices include:

 - An Arduino with a GY-30/BH1750 lux meter writing to a usb serial-port.
 - A webcam periodically sampled to produce approximate lux values.  Values
   might be estimated by analyzing image content or image settings that
   contribute to exposure, such as ISO values, apertures, and shutter speed.

Further information on various lux metering options, as well as instructions for constructing and
programming an Arduino with a GY-30/BH1750, can be found at:

    https://github.com/digitaltrails/vdu_controls/blob/master/Lux-metering.md

Example scripts for mapping a webcam's average-brightness to approximate lux values are included in
``/usr/share/vdu_controls/sample-scripts/``, or they can also be downloaded from the following
location:

    https://github.com/digitaltrails/vdu_controls/tree/master/sample-scripts.

The examples include ``vlux_meter.py``, a beta-release Qt-GUI python-script that meters from a
webcam and writes to a FIFO (`$HOME/.cache/vlux_fifo`). Controls are included for mapping
image-brightness to lux mappings, and for defining a crop from which to sample brightness values.
The script optionally runs in the system-tray.

The examples may require customizing for your own webcam and lighting conditions.

If ambient light level controls are not required, the Settings Dialog includes an option to
disable and hide them.

Lux Metering and brightness transitions
---------------------------------------

Due to VDU hardware and DDC protocol limitations, gradual transitions from one brightness level to
another are likely to be noticeable and potentially annoying.  As well as being annoying,
excessive stepping may eat into VDU NVRAM lifespan.

The auto-brightness adjustment feature includes several measures to reduce the number of
changes passed to the VDU:

 - Lux/Brightness Profiles may be altered for local conditions so that
   brightness levels remain constant over set ranges of lux values (night, day, and so forth).
 - Adjustments are only made at intervals of one or more minutes (default is 10 minutes).
 - The adjustment task passes lux values through a smoothing low-pass filter.
 - When a VDU brightness profile is set to interpolate, changes specified by the
   curve will only be applied when they cross a minimum threshold (default 10%).
 - A VDU brightness profile may be set to stair-step with no interpolation
   of intermediate values.

When ambient light conditions are fluctuating, for example, due to passing clouds, automatic adjust
can be manually suspended.  The main-panel, main-menu, and light-metering dialog each contain controls for
toggling Auto/Manual.  Additionally, moving the manual lux-slider turns off automatic adjustment.

The Light-metering dialog includes an option to enable auto-brightness interpolation. This option
will enable the calculation of values between steps in the profiles. To avoid small
fluctuating changes, interpolation won't result in brightness changes less than 10%.  During
interpolation, if a lux value is found to be close to any attached-preset, the preset
values will be preferred over interpolated ones.

Light/Lux Metering and Presets
-------------------------------

The Light-Metering Dialog includes the ability to set a Preset to trigger at a lux value.  This feature
is accessed by hovering under the bottom axis of the Lux Profile Chart.

When a preset is attached to a lux value, the preset's brightness values become fixed points on the
Lux Profile Chart.  When the specified metered lux value is achieved, the stepping process will
restore the preset's brightness values and then trigger the full restoration of the preset.  This
ordering of events reduces the likelihood of metered-stepping and preset-restoration from clashing.

A preset that does not include a VDU's brightness may be attached to a lux point to restore one or
more non-brightness controls.  For example, on reaching a particular lux level, an attached preset
might restore a contrast setting.

If a preset is attached to a lux value and then detached, the preset's profile points will be
converted to normal (editable) profile points. Attach/detach is a quick way to copy VDU brightness
values from presets if you don't want to permanently attach them.

If you use light-metered auto-brightness and preset-scheduling together, their combined effects
may conflict. For example, a scheduled preset may set a reduced brightness, but soon after,
light-metering might increase it.  If you wish to use the two together, design your lux/brightness
profile steps to match the brightness levels of specific presets - for example, a full-sun preset
and the matching step in a lux/brightness Profile might both be assigned the same brightness level.

Lux Metering Internal Parameters
--------------------------------

The following internal constants can be altered by manually editing
`~/.config/vdu_controls/AutoLux.conf`.  They guide the various metering and auto-adjustment
heuristics::

      [lux-meter]
      # How many times per minute to sample from the Lux meter (for auto-adjustment)
      samples-per-minute=3
      # How many samples to include in the smoothing process
      smoother-n=5
      # How heavily should past values smooth the present value (smaller = more smoothing)
      # See: https://en.wikipedia.org/wiki/Low-pass_filter#Simple_infinite_impulse_response_filter
      smoother-alpha=0.5
      # If an interpolated value yields a change in brightness, how big should the change
      # be to trigger an actual VDU change in brightness? Also determines how close
      # an interpolated value needs to be to an attached preset's brightness in order
      # to prefer triggering the preset over applying the interpolated value.
      interpolation-sensitivity-percent=10
      # Jump brightness in one step up to this maximum, after which transition in steps.
      max-brightness-jump=100


Improving Response Time: Dynamic Optimization and Sleep Multipliers
-------------------------------------------------------------------

If you are using ``ddcutil`` version 2.0 or greater, ``vdu_controls`` will default to using the
``ddcutil`` *dynamic sleep optimizer*.  The optimizer automatically tunes and caches VDU specific
timings when ever ``ddcutil`` is run.  Any reliability-issues or errors may be automatically
resolved as the optimizer refines its cached timings.  Should problems persist, the
optimizer can be disabled by adding `--disable-dynamic-sleep` to the **ddcutil extra arguments** in
the **Settings Dialog** (either globally on the **vdu_controls tab** or selectively under each VDU's
tab).  If dynamic sleep is disabled, multipliers can then be manually assigned. The optimizer's
heuristics continue to be refined, it may be that some issues may be resolved by moving to a more
recent version of ``libddcutil/ddcutil``.

For versions of ``ddcutil`` prior to 2.0, you can manually set the ``vdu_control``
``sleep-multiplier`` passed to ``ddcutil``.  A sleep multiplier less than one will speed up the i2c
protocol interactions at the risk of increased protocol errors. The default sleep multiplier of 1.0
has to be quite conservative, many VDUs can cope with smaller multipliers. A bit of experimentation
with multiplier values may greatly speed up responsiveness. In a multi-VDU setup, individual sleep
multipliers can be configured.

Improving Response Time and Reliability: Connections and Controls
-----------------------------------------------------------------

``DDC/I2C`` is not a totally reliable form of communication. VDUs may vary in their responsiveness
and compliance.  GPUs, GPU drivers, and types of connection may affect the reliability. Both ddcutil
and vdu_controls attempt to manage the reliability by using repetition and by adjusting timings.

If you have the choice, a ``DisplayPort`` to ``DisplayPort`` connection may be more reliable than
``DVI`` or ``HDMI``.

Reducing the number of enabled controls can speed up initialization, decrease the refresh time, and
reduce the time taken to restore presets.

There's plenty of useful info for getting the best out of ``ddcutil`` at https://www.ddcutil.com/.

Limitations
===========

Possible impact on VDU lifespan
-------------------------------

Repeatably altering VDU settings might affect VDU lifespan, exhausting the NVRAM write
cycles, stressing the VDU power-supply, or increasing panel burn-in.

That said, ``vdu_controls`` does include a number of features that can be used
to reduce the overall frequency of adjustments to acceptable levels.

+ Inbuilt mitigations:
  + Slider and spin-box controls only update the VDU when adjustments become slow or stop (when
    no change occurs in 0.5 seconds).
  + Preset restoration only updates the VDU values that differ from its current values.
  + Transitioning smoothly has been disabled by default and deprecated for version 2.1.0 onward.
  + Automatic ambient brightness adjustment only triggers a change when the proposed brightness
    differs from the current brightness by at least 10%.

+ Electable mitigations:
  + Choose to restore pre-prepared 'presets' instead of dragging sliders.
  + Refrain from adding transitions to `presets`.
  + If using the ambient-light brightness response curves, tune the settings and
    curves to minimize frequent small changes.
  + If using a light-meter, disengage metered automatic adjustment when faced with
    rapidly fluctuating levels of ambient brightness.
  + Consider adjusting the ambient lighting instead of the VDU.

+ Monitoring to assist with making adjustments:
  + Hovering over a VDU name in the main window reveals a popup that includes
    the number of VCP (NVRAM) writes.
  + The bottom of the About-dialog shows the same numbers. They update dynamically.

Cross-platform differences
--------------------------

The UI attempts to step around minor differences between KDE, GNOME, and the rest,
the UI on each may not be exactly the same.

Depending on which desktop or system-tray-extension you are using, a
left-mouse-click on the app-icon in the system-tray may restore
the application's main-widow or it may bring up the the application's
context-menu.  To support both kinds of desktop, the context-menu includes a
a _Control Panel_  menu option that toggles visibility of the main window.

Wayland doesn't allow an application to precisely position its windows.  When the
``smart-window`` option is enabled and the desktop platform is Wayland, the
application switches its platform to XWayland (X11 xcb).

The scaling and appearance of Qt6 differs from Qt5, its more chunky and rounded.  If you
have Qt5 installed and prefer it, you can uncheck prefer-qt6 in settings.

Desktop Theming
---------------

Achieving desktop neutrality comes at the price of the application not being
fully aware or compliant with the theming conventions of any particular desktop.

For some desktops, Qt can detect in-session theme changes, such as the change from
a day-theme to a night-theme, and the application can respond appropriately.  For
desktops where theme changes aren't detected, the application can only conform
to the theme detected at startup.

In some cases, the system-tray or dock theming may contrast with the theming
applied to windows.  There isn't a straight forward Qt mechanism to discover
whether a tray or dock is differently themed. As a result the application includes
several manual settings that can alter the tray/dock icon theming between
colored, monochrome-dark and monochrome-light.

Other concerns
--------------

The power-supplies in some older VDUs may buzz/squeel audibly when the brightness is
turned way down. This may not be a major issue because, in normal surroundings,
older VDUs are often not usable below about 85-90% brightness.

Going beyond the standard DDC features by attempting to experiment with hidden
or undocumented features or values has the potential to make irreversible changes.

Some controls change the number of connected devices (for example, some VDUs support a power-off
command). If such controls are used, ``vdu_controls`` will detect the change and will reconfigure
the controls for the new situation (for example, DDC VDU 2 may now be DDC VDU 1).  If you change
settings independently of ``vdu_controls``, for example, by using a VDU's physical controls, the
``vdu_controls`` UI includes a refresh button to force it to assess the new configuration.

Some VDU settings may disable or enable other settings in the VDU. For example, setting a VDU to a
specific picture-profile might result in the contrast-control being disabled, but ``vdu_controls``
will not be aware of the restriction resulting in its contrast-control erring or appearing to do
nothing.

If your VDUs support *picture-modes*, altering any controls in vdu_controls will most likely
result in the picture-mode being customized.  For example, say you have selected the
VDU's *Vivid* picture-mode, if you use vdu_controls to change the brightness, it's likely
that this will now become the brightness for *Vivid* until the VDU is reset to its defaults.
To avoid confusion, it may be advisable to stick to one picture-mode for use with vdu_controls,
preserving the others unaltered.


Examples
========

    vdu_controls
        All default controls.

    vdu_controls --show brightness --show contrast
        Specified controls only:

    vdu_controls --hide contrast --hide audio-volume
        All default controls except for those to be hidden.

    vdu_controls --system-tray --no-splash --show brightness --show audio-volume
        Start as a system tray entry without showing the splash-screen.

    vdu_controls --create-config-files --system-tray --no-splash --show brightness --show audio-volume
        Create template config files in $HOME/.config/vdu_controls/ that include the other settings.

    vdu_controls --enable-vcp-code 63 --enable-vcp-code 93 --warnings --debug
        All default controls, plus controls for VCP_CODE 63 and 93, show any warnings, output debugging info.

This script often refers to displays and monitors as VDUs in order to disambiguate the noun/verb
duality of "display" and "monitor"

Prerequisites
=============

Described for OpenSUSE, similar for other distros:

Software::

        zypper install python3 python3-qt5 noto-sans-math-fonts noto-sans-symbols2-fonts
        zypper install ddcutil
        zypper install libddcutil ddcutil-service  # optional, but recommended if available
        zypper install brightnessctl  # optional, needed for controlling laptop-panels
        zypper install python3-udev   # optional, needed for detecting brighntess changes on laptop-panels

If you wish to use a serial-port lux metering device, the ``pyserial`` module is a runtime requirement.

Get ddcutil working first. Check that the detect command detects your VDUs without issuing any
errors:

        ddcutil detect

Read ddcutil documentation concerning config of i2c_dev with nvidia GPUs. Detailed ddcutil info
at https://www.ddcutil.com/

Environment
===========

    LC_ALL, LANG, LANGUAGE
        These variables specify the locale for language translations and units of distance.
        LC_ALL is used by python, LANGUAGE is used by Qt. Normally, they should all have the same
        value, for example, ``Da_DK``. For these to have any effect on language, ``Settings``
        ``Translations Enabled`` must also be enabled.

    VDU_CONTROLS_UI_IDLE_SECS
        The length of pause in slider or spin-box control motion that triggers commit of
        the controls value to the VDU.  This prevents altering a slider from constantly updating
        a VDU, which might shorten its NVRAM lifespan. The default is 0.5 seconds.

    VDU_CONTROLS_IPINFO_URL
        Overrides the default ip-address to location service URL (``https://ipinfo.io/json``).

    VDU_CONTROLS_WTTR_URL
         Overrides the default weather service URL (``https://wttr.in``).

    VDU_CONTROLS_WEATHER_KM
        Overrides the default maximum permissible spherical distance (in kilometres)
        between the ``Settings`` ``Location`` and ``wttr.in`` reported location (``200 km``, 124 miles).

    VDU_CONTROLS_DDCUTIL_ARGS
        Add to the list of arguments passed to each exec of ddcutil.

    VDU_CONTROLS_DDCUTIL_RETRIES
        Set the number of times to repeat a ddcutil getvcp or setvcp before returning an error.

    VDU_CONTROLS_DEVELOPER
        Changes some search paths to be more convenient in a development
        scenario. (``no`` or yes)

    VDU_CONTROLS_DBUS_TIMEOUT_MILLIS
        Dbus call wait timeout. Default is 10000, 10 seconds.

Files
=====
    $HOME/.config/vdu_controls/
        Location for config files, Presets, and other persistent data.

    $HOME/.config/vdu_controls/tray_icon.svg
        If present, this file is the preferred source for the system-tray icon. It can be used if the normal
        icon conflicts with the desktop theme. If the ``Settings`` ``monochrome-tray``
        and ``mono-light-tray`` are enabled, they are applied to the file when it is read.

    $HOME/.config/vdu_controls/translations/
        Location for user supplied translations.

    $HOME/.config/vdu_controls.qt.state/
        Location for Qt/desktop state such as the past window sizes and locations.

    /usr/share/vdu_controls
        Location for system-wide icons, sample-scripts, and translations.

Reporting Bugs
==============
https://github.com/digitaltrails/vdu_controls/issues

GNU License
===========

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, version 3.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
more details.

You should have received a copy of the GNU General Public License along
with this program. If not, see https://www.gnu.org/licenses/.
"""
import re

from vdu_controls.dialog_singleton import DialogSingletonMixin
from vdu_controls.icon_utils import StdPixmap, si
from vdu_controls.internationalization import tr
from vdu_controls.qt_imports import QVBoxLayout, QSize, QTextEdit, Qt
from vdu_controls.scaling import npx
from vdu_controls.widgets import SubWinDialog, StdButton

class HelpDialog(SubWinDialog, DialogSingletonMixin):

    @staticmethod
    def invoke() -> None:
        HelpDialog.show_existing_dialog() if HelpDialog.exists() else HelpDialog()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(tr('Help'))
        layout = QVBoxLayout()
        markdown_view = QTextEdit()
        markdown_view.setReadOnly(True)
        markdown_view.setViewportMargins(npx(80), npx(80), npx(50), npx(30))
        markdown_view.setMarkdown(re.sub(r"^$([^ ])", r"<br/>\n\1", __doc__, flags=re.MULTILINE))  # hack Qt markdown
        layout.addWidget(markdown_view)
        close_button = StdButton(icon=si(self, StdPixmap.SP_DialogCloseButton), title=tr("Close"), clicked=self.hide)
        layout.addWidget(close_button, 0, Qt.AlignmentFlag.AlignRight)
        self.setLayout(layout)
        self.make_visible()

    def sizeHint(self) -> QSize:
        return QSize(npx(1600), npx(1000))
