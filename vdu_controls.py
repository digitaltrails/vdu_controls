#!/usr/bin/python3
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
                            additional command-line ddcutil emulator for a laptop panel
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

Laptops
-------

A laptop's builtin-panel normally doesn't implement DDC and cannot be controlled
by ``ddcutil`` or ``ddcutil-service``.  Laptop panel brightness is controlled
by a variety of methods that vary by vendor and hardware.  If you have a laptop
where such adjustments can be scripted, you can use the ``--ddcutil-emulator``
option and provide ``vdu_controls`` with a ddcutil-like script for getting and
setting the panel brightness; then ``vdu_controls`` will treat the laptop panel
just like any other VDU.  A template script is provided in the ``sample-scripts``.

Cross-platform differences
--------------------------

Wayland doesn't allow an application to precisely position its windows.  When the
``smart-window`` option is enabled and the desktop platform is Wayland, the
application switches its platform to XWayland (X11 xcb).

The UI attempts to step around minor differences between KDE, GNOME, and the rest,
the UI on each may not be exactly the same.

The scaling and appearance of Qt6 differs from Qt5, its more chunky and rounded.  If you
have Qt5 installed and prefer it, you can uncheck prefer-qt6 in settings.


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

# vdu_controls Copyright (C) 2021 Michael Hamilton

from __future__ import annotations

import argparse
import base64
import configparser
import glob
import inspect
import io
import json
import locale
import math
import os
import pathlib
import queue
import random
import re
import select
import signal
import socket
import stat
import subprocess
import sys
import syslog
import termios
import textwrap
import threading
import time
import traceback
import unicodedata
import urllib.request
from ast import literal_eval
from collections import namedtuple
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum, IntFlag
from functools import partial
from importlib import import_module
from pathlib import Path
from threading import Lock
from typing import List, Tuple, Mapping, Type, Dict, Callable, Any, NewType, cast
from urllib.error import URLError

CONFIG_DIR_PATH = Path.home().joinpath('.config', 'vdu_controls')
CONFIG_FILE_PREFER_QT5 = CONFIG_DIR_PATH.joinpath('_prefer_qt5_')
for qt_version in (5, 6) if CONFIG_FILE_PREFER_QT5.exists() else (6, 5):
    print(f"Trying Qt{qt_version}")
    try:
        if qt_version == 6:
            from PyQt6 import QtCore, QtNetwork
            from PyQt6.QtCore import Qt, QCoreApplication, QThread, pyqtSignal, QProcess, QPoint, QObject, QEvent, \
                QSettings, QSize, QTimer, QTranslator, QLocale, QT_TR_NOOP, QVariant, pyqtSlot, QMetaType, QDir, QRegularExpression, QPointF
            from PyQt6.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage, QDBusArgument, QDBusVariant
            from PyQt6.QtGui import QAction, QShortcut, QPixmap, QIcon, QCursor, QImage, QPainter, QRegularExpressionValidator, \
                QPalette, QGuiApplication, QColor, QValidator, QPen, QFont, QFontMetrics, QMouseEvent, QResizeEvent, QKeySequence, QPolygon, \
                QDoubleValidator, QScreen
            from PyQt6.QtSvg import QSvgRenderer
            from PyQt6.QtSvgWidgets import QSvgWidget
            from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QMessageBox, QLineEdit, QLabel, \
                QSplashScreen, QPushButton, QProgressBar, QComboBox, QSystemTrayIcon, QMenu, QStyle, QTextEdit, QDialog, QTabWidget, \
                QCheckBox, QPlainTextEdit, QGridLayout, QSizePolicy, QMainWindow, QToolBar, QToolButton, QFileDialog, \
                QWidgetItem, QScrollArea, QGroupBox, QFrame, QSplitter, QSpinBox, QDoubleSpinBox, QInputDialog, QStatusBar, \
                QSpacerItem, QListWidget, QListWidgetItem
            QT5_USE_HIGH_DPI_PIXMAPS = None
            QT5_QPAINTER_HIGH_QUALITY_ANTIALIASING = None
        elif qt_version == 5:  # Covers all other values.
            from PyQt5 import QtCore, QtNetwork
            from PyQt5.QtCore import Qt, QCoreApplication, QThread, pyqtSignal, QProcess, QPoint, QObject, QEvent, \
                QSettings, QSize, QTimer, QTranslator, QLocale, QT_TR_NOOP, QVariant, pyqtSlot, QMetaType, QDir, QRegularExpression, QPointF
            from PyQt5.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage, QDBusArgument, QDBusVariant
            from PyQt5.QtGui import QPixmap, QIcon, QCursor, QImage, QPainter, QRegularExpressionValidator, \
                QPalette, QGuiApplication, QColor, QValidator, QPen, QFont, QFontMetrics, QMouseEvent, QResizeEvent, QKeySequence, QPolygon, \
                QDoubleValidator
            from PyQt5.QtSvg import QSvgWidget, QSvgRenderer
            from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QMessageBox, QLineEdit, QLabel, \
                QSplashScreen, QPushButton, QProgressBar, QComboBox, QSystemTrayIcon, QMenu, QStyle, QTextEdit, QDialog, QTabWidget, \
                QCheckBox, QPlainTextEdit, QGridLayout, QSizePolicy, QAction, QMainWindow, QToolBar, QToolButton, QFileDialog, \
                QWidgetItem, QScrollArea, QGroupBox, QFrame, QSplitter, QSpinBox, QDoubleSpinBox, QInputDialog, QStatusBar, QShortcut, \
                QSpacerItem, QListWidget, QListWidgetItem
            QT5_USE_HIGH_DPI_PIXMAPS = Qt.ApplicationAttribute.AA_UseHighDpiPixmaps
            QT5_QPAINTER_HIGH_QUALITY_ANTIALIASING = QPainter.RenderHint.HighQualityAntialiasing
        break
    except (ImportError, ModuleNotFoundError) as no_qt_exc:
        print(f"Failed to import PyQt6: {repr(no_qt_exc)}", file=sys.stderr)

def flag_qt_version_preference(config: ConfIni) -> None:  # use a flag file to work around the chicken-and-egg issue at startup.
    if config.has_section(ConfOpt.PREFER_QT6.conf_section) and config.getboolean(ConfOpt.PREFER_QT6.conf_section,
                                                                                 ConfOpt.PREFER_QT6.conf_name, fallback=True):
        if CONFIG_FILE_PREFER_QT5.exists():
            CONFIG_FILE_PREFER_QT5.unlink()
    else:
        CONFIG_FILE_PREFER_QT5.touch()

StdPixmap = QStyle.StandardPixmap


APPNAME = "VDU Controls"
VDU_CONTROLS_VERSION = '2.4.2'
VDU_CONTROLS_VERSION_TUPLE = tuple(int(i) for i in VDU_CONTROLS_VERSION.split('.'))
assert sys.version_info >= (3, 8), f'{APPNAME} utilises python version 3.8 or greater (your python is {sys.version}).'

WESTERN_SKY = 'western-sky'
EASTERN_SKY = 'eastern-sky'

IP_ADDRESS_INFO_URL = os.getenv('VDU_CONTROLS_IPINFO_URL', default='https://ipinfo.io/json')
WEATHER_FORECAST_URL = os.getenv('VDU_CONTROLS_WTTR_URL', default='https://wttr.in')
TESTING_TIME_ZONE = os.getenv('VDU_CONTROLS_TEST_TIME_ZONE')  # for example, 'Europe/Berlin' 'Asia/Shanghai'
TESTING_TIME_DELTA = None  # timedelta(hours=-6.2)

TIME_CLOCK_SYMBOL = '\u25F4'  # WHITE CIRCLE WITH UPPER-LEFT QUADRANT
WEATHER_RESTRICTION_SYMBOL = '\u2614'  # UMBRELLA WITH RAINDROPS
TOO_HIGH_SYMBOL = '\u29BB'  # CIRCLE WITH SUPERIMPOSED X
DEGREE_SYMBOL = '\u00B0'  # DEGREE SIGN
SUN_SYMBOL = '\u2600'  # BLACK SUN WITH RAYS
WEST_ELEVATION_SYMBOL = '\u29A9'  # MEASURED ANGLE WITH OPEN ARM ENDING IN ARROW POINTING UP AND RIGHT
EAST_ELEVATION_SYMBOL = '\u29A8'  # MEASURED ANGLE WITH OPEN ARM ENDING IN ARROW POINTING UP AND LEFT
TIMER_RUNNING_SYMBOL = '\u23F3'  # HOURGLASS WITH FLOWING SAND
WEATHER_CANCELLATION_SYMBOL = '\u2744'  # SNOWFLAKE
SKIPPED_SYMBOL = '\u2718'  # HEAVY BALLOT X
SUCCESS_SYMBOL = '\u2714'  # CHECKMARK
PRESET_APP_SEPARATOR_SYMBOL = '\u2014'  # EM DASH
MENU_SYMBOL = '\u2630'  # TRIGRAM FOR HEAVEN - hamburger menu
TRANSITION_SYMBOL = '\u25b9'  # WHITE RIGHT POINTING SMALL TRIANGLE
TRANSITION_ALWAYS_SYMBOL = '\u25b8\u2732'  # BLACK RIGHT POINTING SMALL TRIANGLE + OPEN CENTER ASTERIX
PROCESSING_LUX_SYMBOL = '\u25b9' * 3  # WHITE RIGHT POINTING SMALL TRIANGLE * 3
SIGNAL_SYMBOL = '\u26a1'  # HIGH VOLTAGE - lightning bolt
ERROR_SYMBOL = '\u274e'  # NEGATIVE SQUARED CROSS MARK
WARNING_SYMBOL = '\u26a0'  # WARNING SIGN
ALMOST_EQUAL_SYMBOL = '\u2248'  # ALMOST EQUAL TO
SMOOTHING_SYMBOL = '\u21dd'  # RIGHT POINTING SQUIGGLY ARROW
STEPPING_SYMBOL = '\u279f'  # DASHED TRIANGLE-HEADED RIGHTWARDS ARROW
RAISED_HAND_SYMBOL = '\u270b'  # RAISED HAND
RIGHT_POINTER_WHITE = '\u25B9'  # WHITE RIGHT-POINTING SMALL TRIANGLE
RIGHT_POINTER_BLACK = '\u25B8'  # BLACK RIGHT-POINTING SMALL TRIANGLE
MENU_ACTIVE_PRESET_SYMBOL = '\u25c2'  # BLACK LEFT-POINTING SMALL TRIANGLE
SET_VCP_SYMBOL = "\u25B7"  # WHITE RIGHT-POINTING TRIANGLE

SolarElevationKey = namedtuple('SolarElevationKey', ['direction', 'elevation'])
SolarElevationData = namedtuple('SolarElevationData', ['azimuth', 'zenith', 'when'])

Shortcut = namedtuple('Shortcut', ['letter', 'annotated_word'])


gui_thread: QThread | None = None


def intV(type_id: Enum|int) -> int:
    return type_id.value if isinstance(type_id, Enum) else type_id  # awfulness of enums in pyqt6


def is_gnome_desktop() -> bool:
    return os.environ.get('XDG_CURRENT_DESKTOP', default='unknown').lower() == 'gnome'


def is_cosmic_desktop() -> bool:
    return os.environ.get('XDG_CURRENT_DESKTOP', default='unknown').lower() == 'cosmic'


def is_running_in_gui_thread() -> bool:
    return QThread.currentThread() == gui_thread


def zoned_now(rounded_to_minute: bool = False) -> datetime:
    now = datetime.now().astimezone()
    if TESTING_TIME_ZONE:  # This is a testing-only path that requires python > 3.8
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo(TESTING_TIME_ZONE))  # for testing scheduling
    result = (now + timedelta(seconds=30)).replace(second=0, microsecond=0) if rounded_to_minute else now
    if TESTING_TIME_DELTA:
        result += TESTING_TIME_DELTA
    return result


def format_solar_elevation_abbreviation(elevation: SolarElevationKey) -> str:
    direction_char = EAST_ELEVATION_SYMBOL if elevation.direction == EASTERN_SKY else WEST_ELEVATION_SYMBOL
    return f"{SUN_SYMBOL} {direction_char} {elevation.elevation}{DEGREE_SYMBOL}"


def format_solar_elevation_description(elevation: SolarElevationKey) -> str:
    # Note - repeating the constants here to force them to be included by pylupdate5 internationalisation
    direction_text = tr('eastern-sky') if elevation.direction == EASTERN_SKY else tr('western-sky')
    return f"{direction_text} {elevation.elevation}{DEGREE_SYMBOL}"


def format_solar_elevation_ini_text(elevation: SolarElevationKey | None) -> str:
    return f"{elevation.direction} {elevation.elevation}" if elevation is not None else ''


def parse_solar_elevation_ini_text(ini_text: str) -> SolarElevationKey:
    parts = ini_text.strip().split()
    if len(parts) != 2:
        raise ValueError(f"Invalid SolarElevation: '{ini_text}'")
    if parts[0] not in [EASTERN_SKY, WESTERN_SKY]:
        raise ValueError(f"Invalid value for  SolarElevation direction: '{parts[0]}'")
    solar_elevation = SolarElevationKey(parts[0], int(parts[1]))
    return solar_elevation


def proper_name(*args) -> str:
    return re.sub(r'[^A-Za-z0-9._-]', '_', '_'.join([arg.strip() for arg in args]))


def tr(source_text: str, disambiguation: str | None = None) -> str:
    """
    This function is named tr() so that it matches what pylupdate5 is looking for.
    If this method is ever renamed to something other than tr(), then you must
    pass -ts-function=new_name to pylupdate5.

    For future internationalization:
    1) Generate template file from this code, for example, for French:
       ALWAYS BACKUP THE CURRENT .ts FILE BEFORE RUNNING AN UPDATE - it can go wrong!
           pylupdate5 vdu_controls.py -ts translations/fr_FR.ts
       where translations is a subdirectory of your current working directory.
    2) Edit that using a text editor or the linguist-qt5 utility.
       If using an editor, remove the 'type="unfinished"' as you complete each entry.
    3) Convert the .ts to a binary .qm file
           lrelease-qt5 translations/fr_FR.ts
           mkdir -p $HOME/.config/vdu_controls/translations/
           translations/fr_FR.qm $HOME/.config/vdu_controls/translations/
    4) Test using by setting LC_ALL for python and LANGUAGE for Qt
           LC_ALL=fr_FR LANGUAGE=fr_FR python3 vdu_controls.py
       At startup the app will log several messages as it searches for translation files.
    5) Completed .qm files can reside in $HOME/.config/vdu_controls/translations/
       or  /user/share/vdu_controls/translations/
    """
    # If the source .ts file is newer, we load messages from the XML into ts_translations
    # and use the most recent translations. Using the .ts files in production may be a good
    # way to allow the users to help themselves.
    if ts_translations:
        if source_text in ts_translations:
            return ts_translations[source_text]
    # the context @default is what is generated by pylupdate5 by default
    return QCoreApplication.translate('@default', source_text, disambiguation=disambiguation)


def translate_option(option_text) -> str:
    # We can't be sure of the case in capability descriptions retrieved from the monitors.
    # If there is no direct translation, we try a canonical version of the name (all lowercase with '-' replaced with ' ').
    if (translation := tr(option_text)) != option_text:  # Probably a command line option
        return translation
    canonical = option_text.lower().replace('-', ' ')
    return tr(canonical)


ABOUT_TEXT = f"""

<b>vdu_controls version {VDU_CONTROLS_VERSION}</b>
<p>
A virtual control panel for external Visual Display Units.
<p>
Visit <a href="https://github.com/digitaltrails/vdu_controls">https://github.com/digitaltrails/vdu_controls</a> for
more details.
<p>
Release notes: <a href="https://github.com/digitaltrails/vdu_controls/releases/tag/v{VDU_CONTROLS_VERSION}">
v{VDU_CONTROLS_VERSION}.</a>
<p>
<hr>
<small>
<b>vdu_controls Copyright (C) 2021 Michael Hamilton</b>
<br><br>
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, version 3.
<br><br>

<bold>
This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
more details.
</bold>
<br><br>
You should have received a copy of the GNU General Public License along
with this program. If not, see <a href="https://www.gnu.org/licenses/">https://www.gnu.org/licenses/</a>.
</small>
<hr>
<p><p>
<quote>
<small>
Vdu_controls relies on <a href="https://www.ddcutil.com/">ddcutil</a>, a robust interface to DDC capable VDUs.
<br>
At your request, your geographic location may be retrieved from <a href="{IP_ADDRESS_INFO_URL}">{IP_ADDRESS_INFO_URL}</a>.
<br>
At your request, weather for your location may be retrieved from <a href="{WEATHER_FORECAST_URL}">{WEATHER_FORECAST_URL}</a>.
</small>
</quote>
"""

RELEASE_WELCOME = QT_TR_NOOP("Welcome to vdu_controls {}").format(VDU_CONTROLS_VERSION)
RELEASE_NOTE = QT_TR_NOOP("Please read the online release notes:")
RELEASE_ANNOUNCEMENT = """<h3>{WELCOME}</h3>{NOTE}<br/>
<a href="https://github.com/digitaltrails/vdu_controls/releases/tag/v{VERSION}">
https://github.com/digitaltrails/vdu_controls/releases/tag/v{VERSION}</a>
<br/>___________________________________________________________________________"""
RELEASE_INFO = QT_TR_NOOP('Bug fix release.')

CURRENT_PRESET_NAME_FILE = CONFIG_DIR_PATH.joinpath('current_preset.txt')
CUSTOM_TRAY_ICON_FILE = CONFIG_DIR_PATH.joinpath('tray_icon.svg')
LOCALE_TRANSLATIONS_PATHS = [
    Path.cwd().joinpath('translations')] if os.getenv('VDU_CONTROLS_DEVELOPER', default="no") == 'yes' else [] + [
    Path(CONFIG_DIR_PATH).joinpath('translations'), Path("/usr/share/vdu_controls/translations"), ]
STANDARD_ICON_PATHS = (Path("/usr/share/vdu_controls/icons"), Path("/usr/share/icons/breeze/actions/24"), Path("/usr/share/icons"),)


class MsgDestination(Enum):
    DEFAULT = 0
    COUNTDOWN = 1


# Use Linux/UNIX signals to trigger preset changes - 16 presets should be enough for anyone.
PRESET_SIGNAL_MIN = 40
PRESET_SIGNAL_MAX = 55

unix_signal_handler: SignalWakeupHandler | None = None

# On Plasma Wayland, the system tray may not be immediately available at login - so keep trying for...
SYSTEM_TRAY_WAIT_SECONDS = 20

SVG_LIGHT_THEME_COLOR = b"#232629"
SVG_LIGHT_THEME_TEXT_COLOR = b"#000000"
SVG_DARK_THEME_COLOR = b"#f3f3f3"
SVG_DARK_THEME_TEXT_COLOR = SVG_DARK_THEME_COLOR

mono_light_tray = False
MONOCHROME_APP_ICON = b"""
<svg viewBox="0 0 22 22" version="1.1" id="svg1" xmlns="http://www.w3.org/2000/svg">
  <defs id="defs3051"><style type="text/css" id="current-color-scheme">.ColorScheme-Text {color:#ffffff;}</style></defs>
  <path style="fill:currentColor;fill-opacity:1;stroke:none" class="ColorScheme-Text"
     d="m 3.012318,1.987629 -0.086226,13.98553 h 1 l 5.0022397,0.02464 -1e-7,2 -2.0022396,-0.02464 v 1 h 8.0000002 v -1 
     l -2.00224,-0.01232 -0.01232,-2 5.01456,0.01232 h 1 L 18.957944,2.0296853 17.989795,2.0050493 4.0174203,1.9774244 
     Z m 0.9927843,1.0339651 13.9651597,-0.01742 -0.01954,10.9465899 -14.0000001,0.02464 z" id="rect4211"/>
</svg>"""

# modified brightness icon from breeze5-icons: LGPL-3.0-only
BRIGHTNESS_SVG = b"""
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 24 24" width="24" height="24">
  <style type="text/css" id="current-color-scheme"> .ColorScheme-Text { color:#232629; } </style>
  <g transform="translate(1,1)">
    <g shape-rendering="auto"  class="ColorScheme-Text" fill="currentColor">
      <path d="m11 7c-2.2032167 0-4 1.7967833-4 4 0 2.203217 1.7967833 4 4 4 2.203217 0 4-1.796783 4-4 0-2.2032167
       -1.796783-4-4-4zm0 1c1.662777 0 3 1.3372234 3 3 0 1.662777-1.337223 3-3 3-1.6627766 0-3-1.337223-3-3 
       0-1.6627766 1.3372234-3 3-3z"/>  <path d="m10.5 3v3h1v-3h-1z"/> <path d="m10.5 16v3h1v-3h-1z"/> 
      <path d="m3 10.5v1h3v-1h-3z"/> <path d="m16 10.5v1h3v-1h-3z"/>
      <path d="m14.707031 14-0.707031 0.707031 2.121094 2.121094 0.707031-0.707031-2.121094-2.121094z"/>
      <path d="M 5.7070312 5 L 5 5.7070312 L 7.1210938 7.828125 L 7.828125 7.1210938 L 5.7070312 5 z "/>
      <path d="M 7.1210938 14 L 5 16.121094 L 5.7070312 16.828125 L 7.828125 14.707031 L 7.1210938 14 z "/>
      <path d="M 16.121094 5 L 14 7.1210938 L 14.707031 7.828125 L 16.828125 5.7070312 L 16.121094 5 z "/>
      <g>
        <path d="m11.000001 7.7500005v6.4999985h2.166665l1.083333-2.166666v-2.1666663l-1.083333-2.1666662z"/>
        <path d="m10.984375 7.734375v0.015625 6.515625h2.191406l1.089844-2.177734v-2.1757816l-1.089844-2.1777344h
         -2.191406zm0.03125 0.03125h2.140625l1.078125 2.1542969v2.1601561l-1.078125 2.154297h-2.140625v-6.46875z"/>
      </g>
    </g>
  </g>
</svg>
"""

SUN_SVG = re.sub(b'm0 1c1.662777 0 3 1.3372234[^"]+"', b'"', BRIGHTNESS_SVG)

# modified contrast icon from breeze5-icons: LGPL-3.0-only
CONTRAST_SVG = b"""
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 24 24" width="24" height="24">
  <style type="text/css" id="current-color-scheme"> .ColorScheme-Text { color:#232629; } </style>
  <g transform="translate(1,1)">
    <path transform="translate(-1,-1)" class="ColorScheme-Text" style="fill:currentColor;fill-opacity:1;stroke:none" 
      d="m 12,7 c -2.761424,0 -5,2.2386 -5,5 0,2.7614 2.238576,5 5,5 2.761424,0 5,-2.2386 5,-5 0,-2.7614 
      -2.238576,-5 -5,-5 z m 0,1 v 8 C 9.790861,16 8,14.2091 8,12 8,9.7909 9.790861,8 12,8"  id="path79" />
  </g>
</svg>
"""

AUTO_LUX_ON_SVG = BRIGHTNESS_SVG.replace(b'viewBox="0 0 24 24"', b'viewBox="3 3 18 18"').replace(b'#232629', b'#ff8500')
AUTO_LUX_OFF_SVG = BRIGHTNESS_SVG.replace(b'viewBox="0 0 24 24"', b'viewBox="3 3 18 18"').replace(b'#232629', b'#84888c')
AUTO_LUX_LED_COLOR = QColor(0xff8500)
PRESET_TRANSITIONING_LED_COLOR = QColor(0x55ff00)

# adjust rgb icon from breeze5-icons: LGPL-3.0-only
COLOR_TEMPERATURE_SVG = b"""
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
  <defs> <clipPath> <path d="m7 1023.36h1v1h-1z" style="fill:#f2f2f2"/> </clipPath> </defs>
  <g transform="translate(1,1)">
    <path d="m11.5 9c-1.213861 0-2.219022.855928-2.449219 2h-6.05078v1h6.05078c.230197 1.144072 1.235358 2 2.449219 2 1.213861 0
     2.219022-.855928 2.449219-2h5.05078v-1h-5.05078c-.230197-1.144072-1.235358-2-2.449219-2" style="fill:#2ecc71"/>
    <path d="m5.5 14c-1.385 0-2.5 1.115-2.5 2.5 0 1.385 1.115 2.5 2.5 2.5 1.21386 0 2.219022-.855928
     2.449219-2h11.05078v-1h-11.05078c-.230196-1.144072-1.235358-2-2.449219-2m0 1c.831 0 1.5.669 1.5 1.5 0 .831-.669
      1.5-1.5 1.5-.831 0-1.5-.669-1.5-1.5 0-.831.669-1.5 1.5-1.5" style="fill:#1d99f3"/>
    <path d="m14.5 3c-1.21386 0-2.219022.855928-2.449219 2h-9.05078v1h9.05078c.230197 1.144072 1.235359 2 2.449219 2 1.21386 0
     2.219022-.855928 2.449219-2h2.050781v-1h-2.050781c-.230197-1.144072-1.235359-2-2.449219-2m0 1c.831 0 1.5.669 1.5 1.5 0
      .831-.669 1.5-1.5 1.5-.831 0-1.5-.669-1.5-1.5 0-.831.669-1.5 1.5-1.5" style="fill:#da4453"/>
  </g>
</svg>
"""

# audio-volume-high icon from breeze5-icons: LGPL-3.0-only
VOLUME_SVG = b"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="-7 -7 40 40" width="24" height="24">
  <style type="text/css" id="current-color-scheme"> .ColorScheme-Text { color:#232629; } </style>
  <g transform="translate(1,1)">
    <g class="ColorScheme-Text" fill="currentColor">
      <path d="m14.324219 7.28125-.539063.8613281a4 4 0 0 1 1.214844 2.8574219 4 4 0 0 1 -1.210938 
       2.861328l.539063.863281a5 5 0 0 0 1.671875-3.724609 5 5 0 0 0 -1.675781-3.71875z"/>
      <path d="m13.865234 3.5371094-.24414.9765625a7 7 0 0 1 4.378906 6.4863281 7 7 0 0 1 -4.380859 
       6.478516l.24414.974609a8 8 0 0 0 5.136719-7.453125 8 8 0 0 0 -5.134766-7.4628906z"/>
      <path d="m3 8h2v6h-2z" fill-rule="evenodd"/>
      <path d="m6 14 5 5h1v-16h-1l-5 5z"/>
    </g>
  </g>
</svg>
"""

# application-menu icon from breeze5-icons: LGPL-3.0-only
MENU_ICON_SOURCE = b"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <style type="text/css" id="current-color-scheme"> .ColorScheme-Text { color:#232629; } </style>
  <g transform="translate(1,1)"> <path style="fill:currentColor;fill-opacity:1;stroke:none" d="m3 5v2h16v-2h-16m0
   5v2h16v-2h-16m0 5v2h16v-2h-16" class="ColorScheme-Text"/> </g>
</svg>
"""

VDU_CONNECTED_ICON_SOURCE = b"""
<svg viewBox="0 0 24 24" width="24" height="24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <style type="text/css" id="current-color-scheme"> .ColorScheme-Text { color:#232629; } </style>
    <g class="ColorScheme-Text" stroke="currentColor" stroke-linecap="round"  stroke-width="2" transform="">
        <path fill="None" d="M14 12 A 5 5 0 1 0 20 12 M 17 11 L 17 16.5 M 9 20 L 1 20 1 5 20 5 20 8"/>
    </g>
</svg>
"""

# view-refresh icon from breeze5-icons: LGPL-3.0-only
REFRESH_ICON_SOURCE = b"""
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 24 24" width="24" height="24">
  <style type="text/css" id="current-color-scheme"> .ColorScheme-Text { color:#232629; } </style>
  <g transform="translate(1,1)">
    <path class="ColorScheme-Text" fill="currentColor" d="m 19,11 c 0,1.441714 -0.382922,2.789289 -1.044922,3.955078 
     l -0.738281, -0.738281 c 0,0 0.002,-0.0019 0.002,-0.0019 l -2.777344,-2.779297 0.707032,-0.707031 2.480468,2.482422 
     C 17.861583, 12.515315 18,11.776088 18,11 18,7.12203 14.878,4 11,4 9.8375,4 8.746103,4.285828 7.783203,4.783203 
     L 7.044922,4.044922 C 8.210722,3.382871 9.5583,3 11,3 c 4.432,0 8,3.568034 8,8 z m -4.044922,6.955078 
     C 13.789278,18.617129 12.4417,19 11,19 6.568,19 3,15.431966 3,11 3,9.558286 3.382922,8.210711 4.044922,7.044922 
     l 0.683594,0.683594 0.002,-0.002 2.828125,2.828126 L 6.851609,11.261673 4.373094,8.783157 
     C 4.139126,9.480503 4,10.221736 4,11 c 0,3.87797 3.122,7 7,7 1.1625,0 2.253897,-0.285829 3.216797,-0.783203 z"/>
  </g>
</svg>
"""

LIGHTING_CHECK_SVG = b"""
<svg version="1.1" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
    <defs> <style id="current-color-scheme" type="text/css">.ColorScheme-Text { color:#232629; }
      .ColorScheme-LED { color:#ff8500; }</style> </defs>
    <path style="fill:currentColor;fill-opacity:1;stroke:none" class="ColorScheme-Text" d="M 5,3 V 4 H 7 V 5.0507812
     C 4.7620407,5.3045267 3,7.1975144 3,9.5 3,11.813856 4.7794406,13.714649 7.0332031,13.953125 6.6992186,13.613635 
     6.43803,13.209557 6.265625,12.765625 4.9435886,12.265608 4,10.997158 4,9.5 4,7.5670034 5.5670034,6 7.5,6 
     c 1.4804972,0 2.738502,0.9218541 3.25,2.2207031 0.447476,0.1661231 0.856244,0.4220185 1.201172,0.7519531 
     -0.10518,-0.8491863 -0.442085,-1.62392 -0.957031,-2.2597656 l 0.754297,-0.7542968 
     0.398046,0.3949218 0.707032,-0.7070312 -1.5,-1.5 L 10.646484,4.8535156 11.042969,5.25 10.291016,6.0019531 
     C 9.6449906,5.4911251 8.858964,5.1481728 8,5.0507812 V 4 h 2 V 3 Z"/>
    <path style="fill:currentColor;fill-opacity:1;stroke:none" class="ColorScheme-LED" d="m12 11.5a2.5 2.5 0
     0 1-2.5 2.5 2.5 2.5 0 0 1-2.5-2.5 2.5 2.5 0 0 1 2.5-2.5 2.5 2.5 0 0 1 2.5 2.5z"/>
</svg>
"""
LIGHTING_CHECK_OFF_SVG = LIGHTING_CHECK_SVG.replace(b'#ff8500', b'#84888c')

TRANSITION_ICON_SOURCE = b"""
<svg  xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 24 24" width="24" height="24"></svg>
"""

SWATCH_ICON_SOURCE = b"""
<svg  xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 24 24" width="24" height="24">
  <rect width="20" height="20" rx="4" x="2" y="3" stroke="black" stroke-width="1" fill="#ffffff" />
</svg>
"""

# Creates an SVG of grey rectangles typical of the sort used for VDU calibration.
GREY_SCALE_SVG = f'''
<svg xmlns="http://www.w3.org/2000/svg" version="1.1"  width="256" height="152" viewBox="0 0 256 152">
    <rect width="256" height="152" x="0" y="0" style="fill:rgb(128,128,128);stroke-width:0;" />
    {"".join(
    [f'<rect width="16" height="32" x="{x}" y="38" style="fill:rgb({v},{v},{v});stroke-width:0;" />'
     for x, v in list(zip([x + 48 for x in range(0, 160, 16)], [v for v in range(0, 120, 12)]))]
)}
    {"".join(
    [f'<rect width="16" height="32" x="{x}" y="80" style="fill:rgb({v},{v},{v});stroke-width:0;" />'
     for x, v in list(zip([x + 48 for x in range(0, 160, 16)], [v for v in range(147, 256, 12)]))]
)}
</svg>
'''.encode()


class ThemeType(Enum):  # Indicates how colors should be altered to fit a color theme.
    UNTHEMED = 5,          # Unthemed - for colored app icon - overlay should be unthemed.
    UNDECIDED = 0,         # Theme to be decided - normal icon - will force a dark/light theme lookup
    POLYCHROME_LIGHT = 1,  # Normal icon - after decision
    POLYCHROME_DARK = 2,   # Normal icon
    MONOCHROME_LIGHT = 3,  # Monochrome icon - for tray use - light themed tray
    MONOCHROME_DARK = 4,   # Monochrome icon - for tray use - dark themed tray


# A high resolution image. We will fall back to an internal PNG if this file isn't found on the local system
DEFAULT_SPLASH_PNG = "/usr/share/icons/hicolor/256x256/apps/vdu_controls.png"

# Internal special exit code used to signal that the exit handler should restart the program.
EXIT_CODE_FOR_RESTART = 1959

# Number of times to retry getting/setting attributes - in case a monitor is slow after being powered up.
DDCUTIL_RETRIES = int(os.getenv("VDU_CONTROLS_DDCUTIL_RETRIES", default='4'))

# Use a slight hack to make MsgBox.resizable.
RESIZABLE_MESSAGEBOX_HACK = True

IGNORE_VDU_MARKER_STR = 'Ignore VDU'

ASSUMED_CONTROLS_CONFIG_VCP_CODES = ['10', '12']
ASSUMED_CONTROLS_CONFIG_TEXT = ('\n'
                                'capabilities-override = Model: unknown\n'
                                '	MCCS version: 2.2\n'
                                '	Commands:\n'
                                '       Command: 01 (VCP Request)\n'
                                '       Command: 02 (VCP Response)\n'
                                '       Command: 03 (VCP Set)\n'
                                '	VCP Features:\n'
                                '	   Feature: 10 (Brightness)\n'
                                '	   Feature: 12 (Contrast)\n'
                                '	   Feature: 60 (Input Source)')

#: Could be a str enumeration of VCP types
CONTINUOUS_TYPE = 'C'
SIMPLE_NON_CONTINUOUS_TYPE = 'SNC'
COMPLEX_NON_CONTINUOUS_TYPE = 'CNC'

LOG_SYSLOG_CAT = {syslog.LOG_INFO: "INFO:", syslog.LOG_ERR: "ERROR:", syslog.LOG_WARNING: "WARNING:", syslog.LOG_DEBUG: "DEBUG:"}
log_to_syslog = False
log_debug_enabled = False  # Often used to guard needless computation: log_debug(needless) if log_debug_enabled else None

VduStableId = NewType('VduStableId', str)

original_qt_qpa_platform: str | None = None

def force_xwayland():  # Force Qt to use XWayland, or reverse the previous force
    global original_qt_qpa_platform
    original_qt_qpa_platform = os.environ.get('QT_QPA_PLATFORM', '')  # save original value
    log_info("Forcing Xwayland, setting environment variable QT_QPA_PLATFORM=xcb")
    os.environ['QT_QPA_PLATFORM'] = 'xcb'


def reverse_force_xwayland():
    if original_qt_qpa_platform:
        log_info(f"Restoring environment variable QT_QPA_PLATFORM={original_qt_qpa_platform}")
        os.environ['QT_QPA_PLATFORM'] = original_qt_qpa_platform  # restore original value
    elif original_qt_qpa_platform == '':  # Will be '' if force_xwayland() has been called, otherwise it will be None
        log_info(f"Removing environment variable QT_QPA_PLATFORM")
        os.environ.pop('QT_QPA_PLATFORM')  # before the call to force_xwayland() it did not previously exist, remove it.


def is_dark_theme() -> bool:
    palette = QPalette()
    text_color, window_color = palette.color(QPalette.ColorRole.WindowText), palette.color(QPalette.ColorRole.Window)
    return text_color.lightness() > window_color.lightness()


def polychrome_light_or_dark():
    return ThemeType.POLYCHROME_DARK if is_dark_theme() else ThemeType.POLYCHROME_LIGHT


def get_tray_theme_type(main_config: VduControlsConfig):
    if main_config.is_set(ConfOpt.MONO_LIGHT_TRAY_ENABLED):
        return ThemeType.MONOCHROME_LIGHT
    if main_config.is_set(ConfOpt.MONOCHROME_TRAY_ENABLED):
        return ThemeType.MONOCHROME_DARK
    return ThemeType.UNTHEMED  # Don't alter colors for overlay onto app icon in tray


DEVELOPERS_NATIVE_FONT_HEIGHT = 32  # The font height in physical pixels being used on my development desktop.
native_font_height_pixels: int | None = None  # A metric for use in sizing components relative to DEVELOPERS_NATIVE_FONT_HEIGHT.


def native_font_height(scaled: int | float = 1):  # In real hardware pixels
    global native_font_height_pixels
    if native_font_height_pixels is None:
        native_font_height_pixels = QFontMetrics(QLabel("ABC").font()).height()
        log_info(f"{native_font_height_pixels=}")
    return round(native_font_height_pixels * scaled)


def npx(developers_pixels: int):  # native pixels - real hardware pixels
    return round((native_font_height() * developers_pixels) / DEVELOPERS_NATIVE_FONT_HEIGHT)


def get_splash_image() -> QPixmap:
    """Get the splash pixmap from the installed png, failing that, the internal splash png."""
    pixmap = QPixmap()
    if os.path.isfile(DEFAULT_SPLASH_PNG) and os.access(DEFAULT_SPLASH_PNG, os.R_OK):
        pixmap.load(DEFAULT_SPLASH_PNG)
    else:
        pixmap.loadFromData(base64.decodebytes(FALLBACK_SPLASH_PNG_BASE64), 'PNG')
    return pixmap


def clamp(v: int, min_v: int, max_v: int) -> int:
    return max(min(max_v, v), min_v)


def log_wrapper(severity, *args, trace=False) -> None:
    with io.StringIO() as output:
        print(*args, file=output, end='')
        message = output.getvalue()
        prefix = LOG_SYSLOG_CAT[severity]
        if log_to_syslog:
            syslog_message = prefix + " " + message if severity == syslog.LOG_DEBUG else message
            syslog.syslog(severity, syslog_message)
        else:
            print(datetime.now().strftime("%H:%M:%S"), prefix, message)
    if log_debug_enabled and trace:
        log_debug("TRACEBACK:", ''.join(traceback.format_stack()))


def log_debug(*args, trace=False) -> None:
    log_wrapper(syslog.LOG_DEBUG, *args, trace=trace) if log_debug_enabled else None


def log_info(*args, trace=False) -> None:
    log_wrapper(syslog.LOG_INFO, *args, trace=trace)


def log_warning(*args, trace=False) -> None:
    log_wrapper(syslog.LOG_WARNING, *args, trace=trace)


def log_error(*args, trace=False) -> None:
    log_wrapper(syslog.LOG_ERR, *args, trace=trace)


def thread_pid():
    return threading.get_native_id()  # More unique than get_ident (internal IDs get recycled immediately) - see with htop -H.


@dataclass
class VcpCapability:
    """Representation of a VCP (Virtual Control Panel) capability for a VDU."""
    vcp_code: str
    name: str
    vcp_type: str | None = None
    values: List | None = None
    causes_config_change: bool = False
    icon_source: bytes | None = None
    enabled: bool = False
    can_transition: bool = False
    retry_setvcp: bool = True

    def __post_init__(self):
        self.retry_setvcp = self.retry_setvcp and not self.causes_config_change  # Safe to repeat set on error
        # For non-continuous types of VCP (VCP types SNC or CNC). Also for special cases, such as restricted brightness ranges.
        self.values = [] if self.values is None else self.values

    def property_name(self) -> str:
        return re.sub('[^A-Za-z0-9_-]', '-', self.name).lower()

    def translated_name(self):  # deal with ddcutil returning mixed caps without losing the caps if possible
        tr_key = self.name.lower()
        tr_result = tr(tr_key)  # translations are keyed on lowercase
        return tr_result if tr_key != tr_result else self.name  # Use original name if not translated


class DdcutilServiceNotFound(Exception):
    pass


class DdcutilDisplayNotFound(Exception):
    pass


class VcpOrigin(Enum):  # Cause of a VCP value change
    NORMAL = 0  # Change generated internally within vdu_controls.
    TRANSIENT = 1  # Intermediate VDU VCP change as a result of vdu_controls transitioning to a new value
    EXTERNAL = 2  # Detected a change of value that must have been done externally to this vdu_controls run.


VcpValue = namedtuple('VcpValue', ['current', 'max', 'vcp_type'])  # A getvcp command returns these three things


class Ddcutil:
    """Interface to the abstracted ddcutil service"""
    vcp_write_counters: Dict[str, int] = {}

    def __init__(self, common_args: List[str] | None = None, prefer_dbus_client: bool = True,
                 connected_vdus_changed_callback: Callable | None = None) -> None:
        super().__init__()
        self.common_args = common_args
        self.ddcutil_emulators_by_edid: Dict[str, DdcutilEmulatorImpl] = {}
        self.ddcutil_impl: DdcutilDBusImpl | DdcutilExeImpl  # The service-interface implementations are duck-typed.
        if prefer_dbus_client:
            try:
                self.ddcutil_impl = DdcutilDBusImpl(self.common_args, callback=connected_vdus_changed_callback)
            except DdcutilServiceNotFound:
                log_warning("Failed to detect D-Bus ddcutil-service, falling back to the ddcutil command.")
                prefer_dbus_client = False

        if not prefer_dbus_client:  # dbus not preferred or dbus failed to initialize
            self.ddcutil_impl = DdcutilExeImpl(self.common_args)

        self.supported_codes: Dict[str, str] | None = None
        self.vcp_type_map: Dict[Tuple[str, str], str] = {}
        self.edid_txt_map: Dict[str, str] = {}
        self.ddcutil_version: Tuple[int, ...] = (0, 0, 0)  # Initial version for bootstrapping
        self.version_suffix = ''
        version_info = self.ddcutil_impl.get_ddcutil_version_string()
        if version_match := re.match(r'[a-z]* ?([0-9]+).([0-9]+).([0-9]+)-?([^\n]*)', version_info):
            self.ddcutil_version = tuple(int(i) for i in version_match.groups()[0:3])
            self.version_suffix = version_match.groups()[3]
        # self.version = (1, 2, 2)  # for testing for 1.2.2 compatibility
        log_info(f"ddcutil version {self.ddcutil_version} "
                 f"{self.version_suffix}(dynamic-sleep={self.ddcutil_version >= (2, 0, 0)}) "
                 f"- interface {self.ddcutil_impl.get_interface_version_string()}")

    def ddcutil_version_info(self) -> Tuple[str, str]:
        return self.ddcutil_impl.get_interface_version_string(), self.ddcutil_impl.get_ddcutil_version_string()

    def add_ddcutil_emulator(self, emulator_executable: str, common_args: List[str] | None = None):
        log_info(f"add_ddcutil_emulator: {emulator_executable} {common_args}")
        try:
            custom_imp = DdcutilEmulatorImpl(emulator_executable, common_args)
            for attr in custom_imp.detect(1):
                log_info(f"add_ddcutil_emulator: VDU edid={attr.edid_txt}")
                self.ddcutil_emulators_by_edid[attr.edid_txt] = custom_imp
        except Exception as e:
            log_error(f"add_ddcutil_emulator exception: {e}")

    def _impl(self, edid: str):
        if emulator_impl := self.ddcutil_emulators_by_edid.get(edid):  # edid is for a virtual implementation
            return emulator_impl  # A virtual ddcutil implementation - probably a laptop panel
        return self.ddcutil_impl  # Use real implementation

    def refresh_connection(self):
        self.ddcutil_impl.refresh_connection()
        for emulator_impl in self.ddcutil_emulators_by_edid.values():
            emulator_impl.refresh_connection()

    def set_sleep_multiplier(self, vdu_number: str, sleep_multiplier: float | None):
        try:
            edid = self.get_edid_txt(vdu_number)
            self._impl(edid).set_sleep_multiplier(edid, sleep_multiplier)
        except ValueError as e:
            if str(e).find('com.ddcutil.DdcutilService.Error.MultiplierLocked') > 0:
                log_warning(f"Ignoring: {e}")
            else:
                raise

    def set_vdu_specific_args(self, vdu_number: str, extra_args: List[str]):
        edid = self.get_edid_txt(vdu_number)
        self._impl(edid).set_vdu_specific_args(edid, extra_args)

    def get_edid_txt(self, vdu_number: str) -> str:
        return self.edid_txt_map.get(vdu_number, vdu_number)  # no edid probably means a simulated VDU

    def get_write_count(self, vdu_number: str) -> int:
        if edid_txt := self.get_edid_txt(vdu_number):
            return Ddcutil.vcp_write_counters.get(edid_txt, 0)
        return 0

    def detect_vdus(self) -> List[Tuple[str, str, str, str]]:
        """Return a list of (vdu_number, desc) tuples."""
        result_list = []
        vdu_list = self.ddcutil_impl.detect(0)
        for emulator_impl in self.ddcutil_emulators_by_edid.values():
            vdu_list += emulator_impl.detect(1)
        # Going to get rid of anything that is not a-z A-Z 0-9 as potential rubbish
        rubbish = re.compile('[^a-zA-Z0-9]+')
        # This isn't efficient, it doesn't need to be, so I'm keeping re-defs close to where they are used.
        key_prospects: Dict[Tuple[str, str], Tuple[str, str]] = {}
        for vdu in vdu_list:
            vdu_number = str(vdu.display_number)
            log_debug(f"checking possible IDs for display {vdu_number}") if log_debug_enabled else None
            model_name = rubbish.sub('_', vdu.model_name)
            manufacturer = rubbish.sub('_', vdu.manufacturer_id)
            serial_number = rubbish.sub('_', vdu.serial_number)
            bin_serial_number = str(vdu.binary_serial_number)
            man_date = ''  # TODO rubbish.sub('_', ds_parts.get('Manufacture year', ''))
            i2c_bus_id = ''  # TODO ds_parts.get('I2C bus', '').replace("/dev/", '').replace("-", "_")
            edid = vdu.edid_txt
            # check for duplicate edid, any duplicate will use the display Num
            if edid is not None and edid not in self.edid_txt_map.values():
                self.edid_txt_map[vdu_number] = edid
            for candidate in serial_number, bin_serial_number, man_date, i2c_bus_id, f"DisplayNum{vdu_number}":
                if candidate.strip() != '':
                    possibly_unique = (model_name, candidate)
                    if possibly_unique in key_prospects:  # Not unique - it has already been encountered.
                        log_info(f"Ignoring non-unique key {possibly_unique[0]}_{possibly_unique[1]}"
                                 f" - it matches displays {vdu_number} and {key_prospects[possibly_unique][0]}")
                        del key_prospects[possibly_unique]
                    else:
                        key_prospects[possibly_unique] = vdu_number, manufacturer
        # Try and pin down a unique id that won't change even if other monitors are turned off. Ideally, this should
        # yield the same result for the same monitor - DisplayNum is the worst for that, so it's the fallback.
        key_already_assigned = {}
        for model_and_main_id, vdu_number_and_manufacturer in key_prospects.items():
            vdu_number, manufacturer = vdu_number_and_manufacturer
            if vdu_number not in key_already_assigned:
                model_name, main_id = model_and_main_id
                log_debug(
                    f"Unique key for {vdu_number=} {manufacturer=} is ({model_name=} {main_id=})") if log_debug_enabled else None
                result_list.append((vdu_number, manufacturer, model_name, main_id))
                key_already_assigned[vdu_number] = 1
        # result_list.append(("3", "maker_y", "model_z", "1234")) # For testing bad VDUs:
        return result_list

    def query_capabilities(self, vdu_number: str) -> str:
        edid_txt = self.get_edid_txt(vdu_number)
        model, mccs_major, mccs_minor, _, features, full_text = self._impl(edid_txt).get_capabilities(edid_txt)
        if full_text:  # The service supplies pre-assembled capabilities text.
            return full_text
        capability_text = f"Model: {model}\nMCCS version: {mccs_major}.{mccs_minor}\nVCP Features:\n"
        for feature_id, feature in features.items():
            feature_code = f"{int.from_bytes(feature_id, 'big'):02X}"
            feature_name = feature[0]
            feature_values = feature[2]
            capability_text += f"   Feature: {feature_code} ({feature_name})\n"
            if len(feature_values) != 0:
                if all(value == '' for value in feature_values.values()):
                    capability_text += "      Values:"
                    for value_id in feature_values.keys():
                        capability_text += f" {int.from_bytes(value_id, 'big'):02X}"
                    capability_text += " (interpretation unavailable)\n"
                else:
                    capability_text += "      Values:\n"
                    for value_id, value_name in feature_values.items():
                        value_code = f"{int.from_bytes(value_id, 'big'):02X}"
                        capability_text += f"         {value_code}: {value_name}\n"
        return capability_text

    def get_type(self, vdu_number: str, vcp_code: str) -> str | None:  # may not be needed with a dbus implementation
        edid_txt = self.get_edid_txt(vdu_number)
        vcp_type_key = (edid_txt, vcp_code)
        if type_str := self.vcp_type_map.get(vcp_type_key):
            return type_str
        is_complex, is_continuous = self._impl(edid_txt).get_type(edid_txt, int(vcp_code, 16))
        type_str = CONTINUOUS_TYPE if is_continuous else (COMPLEX_NON_CONTINUOUS_TYPE if is_complex else SIMPLE_NON_CONTINUOUS_TYPE)
        self.vcp_type_map[vcp_type_key] = type_str
        return type_str

    def set_vcp(self, vdu_number: str, vcp_code: str, new_value: int, retry_on_error: bool = False) -> None:
        """Send a new value to a specific VDU and vcp_code."""
        edid_txt = self.get_edid_txt(vdu_number)
        impl = self._impl(edid_txt)
        for attempt_count in range(DDCUTIL_RETRIES):
            try:
                impl.set_vcp(edid_txt, int(vcp_code, 16), new_value)
                Ddcutil.vcp_write_counters[edid_txt] = Ddcutil.vcp_write_counters.get(edid_txt, 0) + 1
                log_debug(f"set_vcp: {vdu_number=} {vcp_code=} {new_value=}")
                return
            except (subprocess.SubprocessError, DdcutilDisplayNotFound, ValueError) as e:
                if not retry_on_error or attempt_count + 1 == DDCUTIL_RETRIES:
                    raise e
            time.sleep(attempt_count * 0.25)

    def vcp_info(self) -> str:
        """Returns info about all codes known to ddcutil, whether supported or not."""
        return DdcutilExeImpl([]).vcp_info()

    def get_supported_vcp_codes_map(self) -> Dict[str, str]:
        """Returns a map of descriptions keyed by vcp_code, the codes that ddcutil appears to support."""
        if self.supported_codes is not None:
            return self.supported_codes
        self.supported_codes = {}
        info = self.vcp_info()
        code_definitions = info.split("\nVCP code ")
        for code_def in code_definitions[1:]:
            lines = code_def.split('\n')
            vcp_code, vcp_name = lines[0].split(': ', 1)
            ddcutil_feature_subsets = None
            for line in lines[2:]:
                line = line.strip()
                if line.startswith('ddcutil feature subsets:'):
                    ddcutil_feature_subsets = line.split(": ", 1)
            if ddcutil_feature_subsets is not None:
                if vcp_code not in self.supported_codes:
                    self.supported_codes[vcp_code] = vcp_name
        return self.supported_codes

    def get_vcp_values(self, vdu_number: str, vcp_code_list: List[str]) -> List[VcpValue]:
        values_dict: Dict[str, VcpValue | None] = {vcp_code: None for vcp_code in vcp_code_list}
        edid_txt = self.get_edid_txt(vdu_number)
        impl = self._impl(edid_txt)
        # Try a few times in case there is a glitch due to a monitor being turned-off/on or slow to respond
        for attempt_count in range(DDCUTIL_RETRIES):
            values_list = impl.get_vcp_values(edid_txt, [int(vcp, 16) for vcp in vcp_code_list])
            for vcp, value, maxv, _ in values_list:
                vcp_code = f'{vcp:02X}'
                vcp_type = self.get_type(vdu_number, vcp_code)
                values_dict[vcp_code] = VcpValue(value, maxv, vcp_type)
            if None not in values_dict.values():
                break  # Got all values - OK to stop, otherwise try again
        for vcp_code, value in values_dict.items():
            if value is None:  # If all attempts failed, the values_dict will be missing one or more values.
                raise ValueError(f"getvcp: display-{vdu_number} - failed to obtain value for vcp_code {vcp_code:02X}")
        return list(values_dict.values())  # if we reach here all values will be present (none are None).


class DdcEventType(Enum):  # Has to correspond to what the service supports
    UNKNOWN = -1
    DPMS_AWAKE = 0
    DPMS_ASLEEP = 1
    DISPLAY_CONNECTED = 2
    DISPLAY_DISCONNECTED = 3


class DdcutilExeImpl:
    _VCP_CODE_REGEXP = re.compile(r"^VCP ([0-9A-F]{2}) ")  # VCP 2-digit-hex
    _C_PATTERN = re.compile(r'([0-9]+) ([0-9]+)')  # Match Continuous-Type getvcp result
    _SNC_PATTERN = re.compile(r'x([0-9a-f]+)')  # Match Simple Non-Continuous-Type getvcp result
    _CNC_PATTERN = re.compile(r'x([0-9a-f]+) x([0-9a-f]+) x([0-9a-f]+) x([0-9a-f]+)')  # Match Complex Non-Continuous-Type result
    _SPECIFIC_VCP_VALUE_PATTERN_CACHE: Dict[int, re.Pattern] = {}
    DetectedAttributes = namedtuple("DetectedAttributes", ('display_number', 'usb_bus', 'usb_device',
                                                           'manufacturer_id', 'model_name', 'serial_number',
                                                           'product_code', 'edid_txt', 'binary_serial_number'))

    def __init__(self, common_args: List[str] | None):
        self.vdu_sleep_multiplier: Dict[str, float] = {}
        self.extra_args: Dict[str, List[str]] = {}
        self.common_args = [arg for arg in os.getenv('VDU_CONTROLS_DDCUTIL_ARGS', default='').split() if arg != '']
        if common_args:
            self.common_args += common_args
        self.ddcutil_access_lock = Lock()
        self.vcp_type_map: Dict[int, str] = {}
        self.ddcutil_version: Tuple[int, ...] = (0, 0, 0)
        self.ddcutil_version_string = "0.0.0"
        self.version_suffix = ''
        self.ddcutil_exe = 'ddcutil'
        self.vdu_map_by_edid: Dict[str, Tuple] = {}

    def refresh_connection(self):
        pass

    def set_sleep_multiplier(self, edid_txt: str, sleep_multiplier: float):
        self.vdu_sleep_multiplier[edid_txt] = sleep_multiplier

    def set_vdu_specific_args(self, edid_txt: str, extra_args: List[str]):
        self.extra_args[edid_txt] = extra_args

    def _get_vdu_human_name(self, edid_txt: str):
        if vdu := self.vdu_map_by_edid.get(edid_txt):
            return f"display-{vdu.display_number} {vdu.model_name}"
        return f"Unknown-display {edid_txt:.30}..."

    def _format_args_diagnostic(self, args: List[str]):
        return ' '.join([arg if len(arg) < 30 else arg[:30] + "..." for arg in args])

    def __run__(self, *args, edid_txt: str | None = None) -> subprocess.CompletedProcess:
        if edid_txt:
            edid_args = ["--edid", edid_txt] if edid_txt else []
            multiplier = self.vdu_sleep_multiplier.get(edid_txt, None)
            multiplier_args = ["--sleep-multiplier", f"{multiplier:4.2f}"] if multiplier else []
        else:
            edid_args = []
            multiplier_args = []
        extra_args = self.extra_args.get(edid_txt, []) if edid_txt else []
        log_id = self._get_vdu_human_name(edid_txt) if (edid_txt and log_debug_enabled) else ''
        syslog_args = []
        if self.ddcutil_version[0] >= 2:
            if log_to_syslog and '--syslog' not in args:
                syslog_args = ['--syslog', 'DEBUG' if log_debug_enabled else 'ERROR']
        process_args = [self.ddcutil_exe] + self.common_args + multiplier_args + syslog_args + extra_args + list(args) + edid_args
        try:
            with self.ddcutil_access_lock:
                now = time.time()
                result = subprocess.run(process_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                elapsed = time.time() - now
                # Shorten EDID to 30 characters when logging it (it will be the only long argument)
                log_debug(f"subprocess result: success {log_id} [{self._format_args_diagnostic(result.args)}] "
                          # f"{process_args=} "
                          f"rc={result.returncode} elapsed={elapsed:.2f} "
                          f"stdout={result.stdout.decode('utf-8', errors='surrogateescape')}") if log_debug_enabled else None
        except subprocess.SubprocessError as spe:
            error_text = spe.stderr.decode('utf-8', errors='surrogateescape')
            if error_text.lower().find("display not found") >= 0:  # raise DdcutilDisplayNotFound and stay quiet
                log_debug("subprocess result: display-not-found ", log_id, self._format_args_diagnostic(process_args),
                          f"stderr='{error_text}', exception={str(spe)}", trace=True) if log_debug_enabled else None
                raise DdcutilDisplayNotFound(' '.join(args)) from spe
            log_debug("subprocess result: error ", log_id, self._format_args_diagnostic(process_args),
                      f"stderr='{error_text}', exception={str(spe)}", trace=True) if log_debug_enabled else None
            raise
        return result

    def vcp_info(self) -> str:
        """Returns info about all codes known to ddcutil, whether supported or not."""
        return self.__run__('--verbose', 'vcpinfo').stdout.decode('utf-8', errors='surrogateescape')

    def get_ddcutil_version_string(self) -> str:
        version_info = self.__run__('--version').stdout.decode('utf-8', errors='surrogateescape')
        if version_match := re.match(r'[a-z]+ ([0-9]+).([0-9]+).([0-9]+)-?([^\n]*)', version_info):
            self.ddcutil_version = tuple(int(i) for i in version_match.groups()[0:3])
            self.version_suffix = version_match.groups()[3]
            self.ddcutil_version_string = \
                f"{self.ddcutil_version[0]}.{self.ddcutil_version[1]}.{self.ddcutil_version[2]} {self.version_suffix}"
        return self.ddcutil_version_string

    def get_interface_version_string(self) -> str:
        return "Command Line - ddcutil"

    def _parse_edid(self, display_str: str) -> str | None:
        if edid_match := re.search(r'EDID hex dump:\n[^\n]+(\n([ \t]*[+]0).+)+', display_str):
            edid = "".join(re.findall('((?: [0-9a-f][0-9a-f]){16})', edid_match.group(0))).replace(' ', '')
            log_debug(f"{edid=}") if log_debug_enabled else None
            return edid
        log_error(f"Failed to parse edid in {display_str=}")
        return None

    def detect(self, flags: int) -> List[Tuple[Any, ...]]:
        args = ['detect', '--verbose', ]
        result_list: List[Tuple[Any, ...]] = []
        result = self.__run__(*args)
        # Going to get rid of anything that is not a-z A-Z 0-9 as potential rubbish
        rubbish = re.compile('[^a-zA-Z0-9]+')
        # This isn't efficient, it doesn't need to be, so I'm keeping re-defs close to where they are used.
        for display_str in re.split("\n\n", result.stdout.decode('utf-8', errors='surrogateescape')):
            if display_match := re.search(r'Display ([0-9]+)', display_str):
                vdu_number = display_match.group(1)
                log_debug(f"checking possible IDs for display {vdu_number}") if log_debug_enabled else None
                ds_parts = {fm.group(1).strip(): fm.group(2).strip()
                            for fm in re.finditer(r'[ \t]*([^:\n]+):[ \t]+([^\n]*)', display_str)}  # Create dict {name:value} pairs
                model_name = rubbish.sub('_', ds_parts.get('Model', 'unknown_model'))
                manufacturer = rubbish.sub('_', ds_parts.get('Mfg id', 'unknown_mfg'))
                serial_number = rubbish.sub('_', ds_parts.get('Serial number', ''))
                bin_serial_number = rubbish.sub('_', ds_parts.get('Binary serial number', '').split('(')[0].strip())
                man_date = rubbish.sub('_', ds_parts.get('Manufacture year', ''))
                i2c_bus_id = ds_parts.get('I2C bus', '').replace("/dev/", '').replace("-", "_")
                edid_txt = self._parse_edid(display_str)
                if not edid_txt:
                    log_warning(f"DdcutilExeImpl: failed to parse edid from '{display_str}'")
                vdu_attributes = DdcutilExeImpl.DetectedAttributes(vdu_number, '', '', manufacturer, model_name, serial_number, '',
                                                                   edid_txt, bin_serial_number)
                result_list.append(vdu_attributes)
                self.vdu_map_by_edid[edid_txt] = vdu_attributes
        return result_list

    def get_capabilities(self, edid_txt: str) -> Tuple[
            str, int, int, Dict[bytes, str], Dict[bytes, Tuple[bytes, str, Dict[bytes, str]]], str]:
        result = self.__run__('capabilities', edid_txt=edid_txt)
        capability_text = result.stdout.decode('utf-8', errors='surrogateescape')
        return '', 0, 0, {}, {}, capability_text

    def get_type(self, edid_txt: str, vcp_code_int: int) -> Tuple[bool, bool] | None:  # edid_txt isn't currently used/supported
        type_code = self.vcp_type_map.get(vcp_code_int)
        if type_code is None:
            return False, False
        is_complex = type_code == COMPLEX_NON_CONTINUOUS_TYPE
        is_continuous = type_code == CONTINUOUS_TYPE
        return is_complex, is_continuous

    def set_vcp(self, edid_txt: str, vcp_code_int: int, new_value_int: int) -> None:
        vcp_code = f"{vcp_code_int:02X}"
        new_value = f"x{new_value_int:X}"
        self.__run__('setvcp', vcp_code, new_value, edid_txt=edid_txt)

    def get_vcp_values(self, edid_txt: str, vcp_code_int_list: List[int]) -> List[Tuple[int, int, int, str]]:
        if self.ddcutil_version > (1, 3, 0):
            return self._get_vcp_values_implementation(edid_txt, vcp_code_int_list)
        else:
            return [self._get_vcp_values_implementation(edid_txt, [cd])[0] for cd in vcp_code_int_list]

    def _get_vcp_values_implementation(self, edid_txt: str, vcp_code_list: List[int]) -> List[Tuple[int, int, int, str]]:
        # Try a few times in case there is a glitch due to a monitor being turned-off/on or slow to respond
        args = ['--brief', 'getvcp'] + [f"{c:02X}" for c in vcp_code_list]
        results_dict: Dict[int, VcpValue | None] = {vcp_code: None for vcp_code in vcp_code_list}  # Force vcp_code_list ordering
        for attempt_count in range(DDCUTIL_RETRIES):
            try:
                from_ddcutil = self.__run__(*args, edid_txt=edid_txt)
                for line in from_ddcutil.stdout.split(b"\n"):
                    line_utf8 = line.decode('utf-8', errors='surrogateescape') + '\n'
                    if vcp_code_match := DdcutilExeImpl._VCP_CODE_REGEXP.match(line_utf8):
                        vcp_code = int(vcp_code_match.group(1), 16)
                        results_dict[vcp_code] = self.__parse_vcp_value(vcp_code, line_utf8)
                for vcp_code, vcp_value in results_dict.items():
                    if vcp_value is None:
                        raise ValueError(f"getvcp: {self._get_vdu_human_name(edid_txt)}"
                                         f" - failed to obtain value for vcp_code {vcp_code:02X}")
                return [(vcp_code, v.current, v.max, v.vcp_type) for vcp_code, v in results_dict.items()]
            except (subprocess.SubprocessError, ValueError, DdcutilDisplayNotFound):
                if attempt_count + 1 == DDCUTIL_RETRIES:  # Don't log here, it creates too much noise in the logs
                    raise  # Too many failures, pass the buck upstairs
            time.sleep(attempt_count * 0.25)
        raise ValueError(f"Exceeded {DDCUTIL_RETRIES} attempts to get vcp values.")

    def __parse_vcp_value(self, vcp_code: int, result: str) -> VcpValue | None:
        if not (specific_vcp_value_pattern := DdcutilExeImpl._SPECIFIC_VCP_VALUE_PATTERN_CACHE.get(vcp_code, None)):
            specific_vcp_value_pattern = re.compile(r'VCP ' + f"{vcp_code:02X}" + r' ([A-Z]+) (.+)\n')
            DdcutilExeImpl._SPECIFIC_VCP_VALUE_PATTERN_CACHE[vcp_code] = specific_vcp_value_pattern
        if value_match := specific_vcp_value_pattern.match(result):
            type_indicator = value_match.group(1)
            self.vcp_type_map[vcp_code] = type_indicator
            if type_indicator == CONTINUOUS_TYPE:
                if c_match := DdcutilExeImpl._C_PATTERN.match(value_match.group(2)):
                    return VcpValue(int(c_match.group(1)), int(c_match.group(2)), CONTINUOUS_TYPE)
            elif type_indicator == SIMPLE_NON_CONTINUOUS_TYPE:
                if snc_match := DdcutilExeImpl._SNC_PATTERN.match(value_match.group(2)):
                    return VcpValue(int(snc_match.group(1), 16), 0, SIMPLE_NON_CONTINUOUS_TYPE)
            elif type_indicator == COMPLEX_NON_CONTINUOUS_TYPE:
                if cnc_match := DdcutilExeImpl._CNC_PATTERN.match(value_match.group(2)):
                    return VcpValue(int(cnc_match.group(3), 16) << 8 | int(cnc_match.group(4), 16), 0, COMPLEX_NON_CONTINUOUS_TYPE)
            else:
                raise TypeError(f'Unsupported VCP type {type_indicator} vcp_code {vcp_code}')
        raise ValueError(f"VDU vcp_code {vcp_code} failed to parse vcp value '{result}'")


class DdcutilEmulatorImpl(DdcutilExeImpl):

    def __init__(self, ddcutil_exe: str, common_args: List[str] | None = None):
        super().__init__(common_args)
        self.ddcutil_exe = ddcutil_exe


class DdcutilDBusImpl(QObject):
    RETURN_RAW_VALUES = 2
    _metadata_cache: Dict[Tuple[str, int], Tuple[bool, bool]] = {}
    _current_connected_displays_changed_handler: Callable | None = None  # Only one instance and listener should exist at a time
    _current_service_initialization_handler: Callable | None = None  # Only one instance and listener should exist at a time
    DetectedAttributes = namedtuple("DetectedAttributes", "uninitialized")  # will be redefined during initialization

    def __init__(self, common_args: List[str] | None = None, callback: Callable | None = None):
        super().__init__()
        self.dbus_interface_name = os.environ.get('DDCUTIL_SERVICE_INTERFACE_NAME', default="com.ddcutil.DdcutilInterface")
        env_args = [arg for arg in os.getenv('VDU_CONTROLS_DDCUTIL_ARGS', default='').split() if arg != '']
        self.common_args = env_args + common_args if common_args else []
        self.service_access_lock = Lock()
        self.listener_callback: Callable | None = callback
        self.dbus_timeout_millis = int(os.getenv("VDU_CONTROLS_DBUS_TIMEOUT_MILLIS", default='10000'))
        self._status_values: Dict[int, str] = {}
        for try_count in range(1, 5):  # Approximating an infinite loop
            self.ddcutil_proxy, self.ddcutil_props_proxy = self._connect_to_service()
            if len(self.common_args) != 0:  # have to restart with the common_args, wait and connect again
                try:
                    log_info(f"Restarting dbus service with common args {self.common_args}")
                    self._validate(self.ddcutil_proxy.call("Restart", " ".join(self.common_args),
                                                           QDBusArgument(0, intV(QMetaType.Type.UInt)), QDBusArgument(0, intV(QMetaType.Type.UInt))))
                    time.sleep(2)  # Should be enough time
                    log_info("Reconnecting after dbus service restart.")
                    self.ddcutil_proxy, self.ddcutil_props_proxy = self._connect_to_service() # connect again
                except (ValueError, DdcutilDisplayNotFound):
                    log_warning(f"Failed to restart with common_args {self.common_args} on try {try_count}")
            # Retrieve the attributes returned by detect and also use the retrieval as a self check
            self_check_op = self.ddcutil_props_proxy.call("Get", self.dbus_interface_name, "AttributesReturnedByDetect")
            if self_check_op.errorName():
                log_error(f'Sanity check try {try_count}: {self.dbus_interface_name} failed: {self_check_op.errorMessage()}')
            else:
                DdcutilDBusImpl.DetectedAttributes = namedtuple("DetectedAttributes", self_check_op.arguments()[0])
                self.vdu_map_by_edid: Dict[str, Tuple] = {}
                break
            if try_count >= 4:  # Give up
                self._connect_to_service(disconnect=True)  # disconnect handler references to facilitate garbage collection
                raise DdcutilServiceNotFound(
                    f"Error contacting D-Bus service {self.dbus_interface_name} {self_check_op.errorMessage()}")
            log_info("looping")
            time.sleep(2)  # Try again

    def set_sleep_multiplier(self, edid_txt: str, sleep_multiplier: float):
        with self.service_access_lock:
            self._validate(self.ddcutil_proxy.call("SetSleepMultiplier", -1, edid_txt,
                                                   QDBusArgument(sleep_multiplier, intV(QMetaType.Type.Double)),
                                                   QDBusArgument(0, intV(QMetaType.Type.UInt))))

    def set_vdu_specific_args(self, vdu_number: str, extra_args: List[str]):
        pass  # TODO not implemented

    def _connect_to_service(self, disconnect=False) -> Tuple[QDBusInterface, QDBusInterface] | Tuple[None, None]:
        dbus_service_name = os.environ.get('DDCUTIL_SERVICE_NAME', default="com.ddcutil.DdcutilService")
        dbus_object_path = os.environ.get('DDCUTIL_SERVICE_OBJECT_PATH', default="/com/ddcutil/DdcutilObject")
        session_bus = QDBusConnection.connectToBus(QDBusConnection.BusType.SessionBus, "session")
        ddcutil_dbus_iface = QDBusInterface(
            dbus_service_name, dbus_object_path, self.dbus_interface_name, connection=session_bus)
        # Properties are available via a separate interface with "Get" and "Set" methods
        ddcutil_dbus_props = QDBusInterface(
            dbus_service_name, dbus_object_path, "org.freedesktop.DBus.Properties", connection=session_bus)
        session_bus.registerObject("/", self)
        # Clear handlers belonging to old instance
        if DdcutilDBusImpl._current_connected_displays_changed_handler:  # clear previous handler that belonged to old instance.
            session_bus.disconnect(dbus_service_name, dbus_object_path, self.dbus_interface_name,
                                   "ConnectedDisplaysChanged", DdcutilDBusImpl._current_connected_displays_changed_handler)
        DdcutilDBusImpl._current_connected_displays_changed_handler = None
        if DdcutilDBusImpl._current_service_initialization_handler:  # clear previous handler that belonged to old instance.
            session_bus.disconnect(dbus_service_name, dbus_object_path, self.dbus_interface_name,
                                   "ServiceInitialized", DdcutilDBusImpl._current_service_initialization_handler)
            DdcutilDBusImpl._current_service_initialization_handler = None
        if disconnect:
            return None, None
        # Connect new handlers - bind receiving slots to our new handlers
        DdcutilDBusImpl._current_service_initialization_handler = self._service_initialization_handler
        session_bus.connect(dbus_service_name, dbus_object_path, self.dbus_interface_name,
                            "ServiceInitialized", DdcutilDBusImpl._current_service_initialization_handler)
        session_bus.connect(dbus_service_name, dbus_object_path, self.dbus_interface_name,
                            "ConnectedDisplaysChanged", self._connected_displays_changed_handler)
        DdcutilDBusImpl._current_connected_displays_changed_handler = self._connected_displays_changed_handler
        ddcutil_dbus_iface.setTimeout(self.dbus_timeout_millis)
        # This is intended to provide the user with an easy way enable or disable events in the server.
        log_info(f"Remotely configuring ddcutil-service ServiceEmitSignals={self.listener_callback is not None}")
        ddcutil_dbus_props.call("Set",
                                "com.ddcutil.DdcutilInterface",
                                "ServiceEmitSignals",
                                QDBusVariant(QDBusArgument(self.listener_callback is not None, intV(QMetaType.Type.Bool))))
        return ddcutil_dbus_iface, ddcutil_dbus_props

    def refresh_connection(self):
        self_check_op = self.ddcutil_props_proxy.call("Get", self.dbus_interface_name, "ServiceInterfaceVersion")
        if self_check_op.errorName():  # Only reconnect if something appears to be wrong
            log_error(f'refresh_connection: check of {self.dbus_interface_name} failed: {self_check_op.errorMessage()}')
            self.ddcutil_proxy, self.ddcutil_props_proxy = self._connect_to_service()

    @pyqtSlot(QDBusMessage)
    def _service_initialization_handler(self, message: QDBusMessage):
        log_info(f"Received service_initialized D-Bus signal {message.arguments()=} {id(self)=}")  # check old instances... id()
        with self.service_access_lock:
            if self.listener_callback:  # In case the service has restarted
                self.ddcutil_props_proxy.call("Set",
                                              "com.ddcutil.DdcutilInterface",
                                              "ServiceEmitSignals",
                                              QDBusVariant(QDBusArgument(True, intV(QMetaType.Type.Bool))))
                self.listener_callback('', -1, 0)

    @pyqtSlot(QDBusMessage)
    def _connected_displays_changed_handler(self, message: QDBusMessage):
        log_info(f"Received display_change D-Bus signal {message.arguments()=} {id(self)=}")  # check old instances id()
        if self.listener_callback:
            self.listener_callback(*message.arguments())

    def get_ddcutil_version_string(self) -> str:
        return self._validate(self.ddcutil_props_proxy.call("Get", self.dbus_interface_name, "DdcutilVersion"))[0]

    def get_interface_version_string(self) -> str:
        return self._validate(self.ddcutil_props_proxy.call(
            "Get", self.dbus_interface_name, "ServiceInterfaceVersion"))[0] + " (D-Bus ddcutil-service - libddcutil)"

    def _get_status_values(self) -> Dict[int, str]:
        if len(self._status_values) == 0:
            self._status_values = self._validate(self.ddcutil_props_proxy.call("Get", self.dbus_interface_name, "StatusValues"))[0]
        return self._status_values

    def detect(self, flags: int) -> List[Tuple[Any, ...]]:
        with self.service_access_lock:
            result = self.ddcutil_proxy.call("Detect", QDBusArgument(flags, intV(QMetaType.Type.UInt)))
            vdu_list: List[Tuple[Any, ...]] = [DdcutilDBusImpl.DetectedAttributes(*vdu) for vdu in self._validate(result)[1]]
            self.vdu_map_by_edid = {vdu.edid_txt: vdu for vdu in vdu_list}
            return vdu_list

    def get_capabilities(self, edid_txt: str) -> Tuple[
            str, int, int, Dict[bytes, str], Dict[bytes, Tuple[str, str, Dict[bytes, str]]], str]:
        with self.service_access_lock:
            model, mccs_major, mccs_minor, commands, capabilities = \
                self._validate(self.ddcutil_proxy.call(
                    "GetCapabilitiesMetadata", -1, edid_txt, QDBusArgument(0, intV(QMetaType.Type.UInt))))
            return model, int.from_bytes(mccs_major, 'big'), int.from_bytes(mccs_minor, 'big'), commands, capabilities, ''

    def get_type(self, edid_txt: str, vcp_code_int: int) -> Tuple[bool, bool]:
        key = (edid_txt, vcp_code_int)
        if key in DdcutilDBusImpl._metadata_cache:
            return DdcutilDBusImpl._metadata_cache[key]
        with self.service_access_lock:
            _, _, _, _, _, is_complex, is_continuous = self._validate(self.ddcutil_proxy.call(
                "GetVcpMetadata", -1, edid_txt, QDBusArgument(vcp_code_int, intV(QMetaType.Type.UChar)), QDBusArgument(0, intV(QMetaType.Type.UInt))))
            DdcutilDBusImpl._metadata_cache[key] = (is_complex, is_continuous)
            return is_complex, is_continuous

    def set_vcp(self, edid_txt: str, vcp_code_int: int, new_value_int: int) -> None:
        with self.service_access_lock:
            self._validate(self.ddcutil_proxy.call("SetVcp", -1, edid_txt,
                                                   QDBusArgument(vcp_code_int, intV(QMetaType.Type.UChar)),
                                                   QDBusArgument(new_value_int, intV(QMetaType.Type.UShort)),
                                                   QDBusArgument(0, intV(QMetaType.Type.UInt))))

    def get_vcp_values(self, edid_txt: str, vcp_code_int_list: List[int]) -> List[Tuple[int, int, int, str]]:
        vcp_code_array = QDBusArgument()
        vcp_code_array.beginArray(intV(QMetaType.Type.UChar))
        for vcp_code_int in vcp_code_int_list:
            vcp_code_array.add(QDBusArgument(vcp_code_int, intV(QMetaType.Type.UChar)))
        vcp_code_array.endArray()
        with self.service_access_lock:
            raw = self._validate(self.ddcutil_proxy.call(
                "GetMultipleVcp", -1, edid_txt, vcp_code_array, QDBusArgument(DdcutilDBusImpl.RETURN_RAW_VALUES,
                                                                              intV(QMetaType.Type.UInt))))[0]
            return [(int.from_bytes(vcp, 'big'), value, maximum, text_val) for vcp, value, maximum, text_val in raw]

    def _validate(self, result: QDBusMessage) -> List:
        if result.errorName():
            raise ValueError(f"D-Bus error {result.errorName()}: {result.errorMessage()}")
        result_arg_list = result.arguments()
        if len(result_arg_list) >= 2:  # Normal retrieval calls return at least three items
            status, message = result.arguments()[-2:]  # last two are always DDC status and message
            if status != 0:
                formatted_message = f"D-Bus  {status=}: {message}"
                log_debug(formatted_message) if log_debug_enabled else None
                if self._get_status_values().get(status, "DDCRC_INVALID_DISPLAY") == "DDCRC_INVALID_DISPLAY":
                    raise DdcutilDisplayNotFound(formatted_message)
                raise ValueError(formatted_message)
            return result_arg_list[:-2]  # results with status and message stripped out.
        return result_arg_list  # Must be something like a property retrieval, just return as is


def si(widget: QWidget, icon_number: QStyle.StandardPixmap) -> QIcon:  # Qt bundled standard icons (which are themed)
    return widget.style().standardIcon(icon_number)


@dataclass
class GeoLocation:
    latitude: float
    longitude: float
    place_name: str | None

    def __eq__(self, other) -> bool:
        if other is None:
            return False
        if not isinstance(other, GeoLocation):
            return NotImplemented  # don't attempt to compare against unrelated types
        return self.latitude == other.latitude and self.longitude == other.longitude and \
            self.place_name == other.place_name


class DialogSingletonMixin:
    """
    A mixin that can augment a QDialog or QMessageBox with code to enforce a singleton UI.
    For example, it is used so that only one settings editor can be active at a time.
    """
    _dialogs_map: Dict[str, DialogSingletonMixin] = {}

    def __init__(self) -> None:
        """Registers the concrete class as a singleton, so it can be reused later."""
        super().__init__()
        class_name = self.__class__.__name__
        if class_name in DialogSingletonMixin._dialogs_map:
            raise TypeError(f"ERROR: More than one instance of {class_name} cannot exist.")
        log_debug(f'SingletonDialog created for {class_name}') if log_debug_enabled else None
        DialogSingletonMixin._dialogs_map[class_name] = self

    def closeEvent(self, event) -> None:
        """Subclasses that implement their own closeEvent must call this closeEvent to deregister the singleton"""
        class_name = self.__class__.__name__
        log_debug(f"SingletonDialog remove {class_name} "
                  f"registered={class_name in DialogSingletonMixin._dialogs_map}") if log_debug_enabled else None
        if class_name in DialogSingletonMixin._dialogs_map:
            del DialogSingletonMixin._dialogs_map[class_name]
        event.accept()

    def make_visible(self) -> None:
        """ If the dialog exists(), call this to make it visible by raising it.
        Internal, used by the class method show_existing_dialog()"""
        self.show()  # type: ignore
        self.raise_()  # type: ignore
        self.activateWindow()  # type: ignore

    @classmethod
    def show_existing_dialog(cls: Type) -> None:
        """If the dialog exists(), call this to make it visible by raising it."""
        class_name = cls.__name__
        log_debug(f'SingletonDialog show existing {class_name}') if log_debug_enabled else None
        DialogSingletonMixin._dialogs_map[class_name].make_visible()

    @classmethod
    def exists(cls: Type) -> bool:
        """Returns true if the dialog has already been created."""
        class_name = cls.__name__
        log_debug(f"SingletonDialog exists {class_name} "
                  f"{class_name in DialogSingletonMixin._dialogs_map}") if log_debug_enabled else None
        return class_name in DialogSingletonMixin._dialogs_map

    @classmethod
    def get_instance(cls: Type) -> DialogSingletonMixin | None:
        return DialogSingletonMixin._dialogs_map.get(cls.__name__)


class ClickableSlider(QSlider):  # loosely based on https://stackoverflow.com/a/29639127/609575

    def mousePressEvent(self, event: QMouseEvent | None):  # On mouse click, set value to the value at the click position
        if event:
            self.setValue(QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), event.pos().x(), self.width()))
        super().mousePressEvent(event)


class LineEditAll(QLineEdit):  # On mouse click, select the entire text - Make it easier to over-type
    def __init__(self, *args):
        super().__init__(*args)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.selectAll()


# Enabling this would enable anything supported by ddcutil - but that isn't safe for the hardware
# given the undocumented settings that appear to be available and the sometimes dodgy VDU-vendor DDC
# implementations.  Plus, the user might not be able to reset to factory for some of them?
SUPPORT_ALL_VCP = False

BRIGHTNESS_VCP_CODE = BRIT = '10'
CONTRAST_VCP_CODE = CONT = '12'
CON = CONTINUOUS_TYPE  # Shorter abbreviation
SNC = SIMPLE_NON_CONTINUOUS_TYPE
CNC = COMPLEX_NON_CONTINUOUS_TYPE

# Maps of controls supported by name on the command line and in config files.
SUPPORTED_VCP_BY_CODE: Dict[str, VcpCapability] = {
    **{code: VcpCapability(code, name, retry_setvcp=False)
       for code, name in (Ddcutil().get_supported_vcp_codes_map().items() if SUPPORT_ALL_VCP else [])},
    **{
        BRIT: VcpCapability(BRIT, QT_TR_NOOP('brightness'), CON, icon_source=BRIGHTNESS_SVG, enabled=True, can_transition=True),
        CONT: VcpCapability(CONT, QT_TR_NOOP('contrast'), CON, icon_source=CONTRAST_SVG, enabled=True, can_transition=True),
        '62': VcpCapability('62', QT_TR_NOOP('audio volume'), CON, icon_source=VOLUME_SVG, can_transition=True),
        '8D': VcpCapability('8D', QT_TR_NOOP('audio mute'), SNC, icon_source=VOLUME_SVG),
        '8F': VcpCapability('8F', QT_TR_NOOP('audio treble'), CON, icon_source=VOLUME_SVG, can_transition=True),
        '91': VcpCapability('91', QT_TR_NOOP('audio bass'), CON, icon_source=VOLUME_SVG, can_transition=True),
        '64': VcpCapability('91', QT_TR_NOOP('audio mic volume'), CON, icon_source=VOLUME_SVG, can_transition=True),
        '60': VcpCapability('60', QT_TR_NOOP('input source'), SNC, causes_config_change=True),
        'D6': VcpCapability('D6', QT_TR_NOOP('power mode'), SNC, causes_config_change=True),
        'CC': VcpCapability('CC', QT_TR_NOOP('OSD language'), SNC),
        '14': VcpCapability('14', QT_TR_NOOP('color preset'), SNC),
        '0C': VcpCapability('0C', QT_TR_NOOP('color temperature'), CON, icon_source=COLOR_TEMPERATURE_SVG, enabled=True),
    }}

SUPPORTED_VCP_BY_PROPERTY_NAME = {c.property_name(): c for c in SUPPORTED_VCP_BY_CODE.values()}


class WorkerThread(QThread):
    finished_work_qtsignal = pyqtSignal(object)

    def __init__(self, task_body: Callable[[WorkerThread], None], task_finished: Callable[[WorkerThread], None] | None = None,
                 loop: bool = False) -> None:
        super().__init__()
        # init should always be initiated from the GUI thread to grant the worker's __init__ easy access to the GUI thread.
        log_debug(f"WorkerThread: init {self.__class__.__name__} from {thread_pid()=}") if log_debug_enabled else None
        self.stop_requested = False
        self.task_body = task_body
        self.task_finished = task_finished
        self.loop = loop
        if self.task_finished is not None:
            self.finished_work_qtsignal.connect(self.task_finished)
        self.vdu_exception: VduException | None = None

    def run(self) -> None:  # called by QThread start(), or call it directly to run synchronously in an existing thread.
        # Long-running task, runs in a separate thread
        class_name = self.__class__.__name__
        try:
            log_debug(f"WorkerThread: {class_name=} running in {thread_pid()=} {self.task_body}") if log_debug_enabled else None
            while not self.stop_requested:
                self.task_body(self)  # Pass self so body can access context
                if not self.loop:
                    break
        except VduException as e:
            self.vdu_exception = e
        log_debug(f"WorkerThread: {class_name=} finished {thread_pid()=}") if log_debug_enabled else None
        self.finished_work_qtsignal.emit(self)  # Pass self so body can access context

    def stop(self) -> None:
        log_debug(f"WorkerThread: stop requested {thread_pid()=} {self.task_body}") if log_debug_enabled else None
        self.stop_requested = True
        while self.isRunning():
            time.sleep(0.1)

    def doze(self, seconds: float, sleep_unit: float = 0.5):
        while seconds >= sleep_unit and not self.stop_requested:
            time.sleep(sleep_unit)
            seconds -= sleep_unit
        if not self.stop_requested:
            if seconds > 0.1:
                time.sleep(seconds)


class SchedulerJobType(Enum):
    RESTORE_PRESET = 1
    SCHEDULE_PRESETS = 2


# QTimer replacement - hibernation-tolerant scheduling at specific YYYYMMDD HHMM.
# After hibernation, overdue events will trigger immediately.
class SchedulerJob:  # designed to resemble a QTimer, which it was written to replace

    def __init__(self, when: datetime, job_type: SchedulerJobType, run_callable: Callable, skip_callabled: Callable | None = None):
        assert when.tzinfo is not None
        self.when = when.replace(second=0, microsecond=0)
        self.run_callable = run_callable
        self.skip_callable = skip_callabled
        self.job_type = job_type
        self.has_run = False
        self.attempts = 0
        ScheduleWorker.get_instance().add(self)

    def remaining_time(self):
        return (self.when - zoned_now()).seconds if ScheduleWorker.get_instance().is_supervising(self) else -1

    def run_job(self):
        try:
            self.attempts += 1
            self.run_callable()
        finally:
            self.has_run = True

    def dequeue(self):
        ScheduleWorker.get_instance().remove(self)

    def requeue(self):
        assert not ScheduleWorker.get_instance().is_supervising(self)
        self.has_run = False
        ScheduleWorker.get_instance().add(self)

    def __lt__(self, other: SchedulerJob):
        return self.when < other.when

    def __str__(self):
        return f"[{self.job_type=} {self.when=:%Y-%m-%d %H:%M:%S} {self.attempts=} {self.has_run=}]"


# Worker that runs SchedulerJobs - hibernation-tolerant scheduling at specific YYYYMMDD HHMM.
# (An implementation based on sched.scheduler might also work - but the following is definitely going to work cross platform)
class ScheduleWorker(WorkerThread):
    _instance: ScheduleWorker | None = None
    _scheduler_lock = threading.RLock()

    @staticmethod
    def get_instance():
        with ScheduleWorker._scheduler_lock:
            if ScheduleWorker._instance is None or ScheduleWorker._instance.isFinished():
                ScheduleWorker._instance = ScheduleWorker()
                ScheduleWorker._instance.start()
            return ScheduleWorker._instance

    @staticmethod
    def shutdown():
        with ScheduleWorker._scheduler_lock:
            if ScheduleWorker._instance is not None and ScheduleWorker._instance.isRunning():
                ScheduleWorker._instance._remove_all()
                ScheduleWorker._instance.stop()

    @staticmethod
    def check():
        with ScheduleWorker._scheduler_lock:
            if ScheduleWorker._instance and ScheduleWorker._instance.isRunning():
                log_info(f"Scheduler: off-schedule check requested (queue len={len(ScheduleWorker._instance.pending_jobs_list)})")
                ScheduleWorker._instance._cycle()

    @staticmethod
    def dequeue_all(job_type: SchedulerJobType | None = None):
        with ScheduleWorker._scheduler_lock:
            if ScheduleWorker._instance:
                ScheduleWorker._instance._remove_all(job_type)

    @staticmethod
    def is_running() -> bool:
        with ScheduleWorker._scheduler_lock:
            return ScheduleWorker._instance and ScheduleWorker._instance.isRunning()

    def __init__(self) -> None:
        super().__init__(self.task_body, None, True)
        self.pending_jobs_list: List[SchedulerJob] = []

    def task_body(self, _: WorkerThread):
        self._cycle()
        now = datetime.now()  # want just over the next minute boundary e.g. 13:45:05
        sleep_seconds = ((now + timedelta(seconds=60 + 30)).replace(second=5, microsecond=0) - now).seconds
        self.doze(sleep_seconds)  # Have to wake every minute in case PC-sleep or hibernate has occurred.

    def _cycle(self):
        with ScheduleWorker._scheduler_lock:
            local_now = zoned_now()
            run_now: Dict[SchedulerJobType, SchedulerJob] = {}
            for job in self.pending_jobs_list:
                if job.when <= local_now:  # Eligible to run now
                    self.pending_jobs_list.remove(job)
                    if not job.has_run:  # Only the most recent of each type should run
                        if existing_job := run_now.get(job.job_type, None):
                            if job.when > existing_job.when:
                                existing_job.skip_callable()
                                run_now[job.job_type] = job
                            else:
                                job.skip_callable()
                        else:
                            run_now[job.job_type] = job
            for job in run_now.values():
                log_debug(f"Scheduler: Starting {job=!s} queued={len(self.pending_jobs_list)}") if log_debug_enabled else None
                job.run_job()

    def add(self, job: SchedulerJob) -> SchedulerJob:
        with ScheduleWorker._scheduler_lock:
            assert job not in self.pending_jobs_list
            self.pending_jobs_list.append(job)
            log_debug(f"Scheduler: added {job=!s} queued={len(self.pending_jobs_list)}") if log_debug_enabled else None
            return job

    def remove(self, job: SchedulerJob):
        with ScheduleWorker._scheduler_lock:
            if job in self.pending_jobs_list:
                self.pending_jobs_list.remove(job)
                log_debug(f"Scheduler: removed {job=!s} queued={len(self.pending_jobs_list)}") if log_debug_enabled else None

    def _remove_all(self, job_type: SchedulerJobType | None = None):
        with ScheduleWorker._scheduler_lock:
            for job in [j for j in self.pending_jobs_list if job_type is None or j.job_type == job_type]:
                self.remove(job)
            log_debug(f"Scheduler: remove type {job_type!s} ({len(self.pending_jobs_list)} remain)") if log_debug_enabled else None

    def is_supervising(self, job: SchedulerJob):
        return job in self.pending_jobs_list


class ConfIni(configparser.ConfigParser):
    """ConfigParser is a little messy, and its class name is a bit misleading, wrap it and bend it to our needs."""

    def __init__(self) -> None:
        super().__init__(interpolation=None)
        if not self.has_section(ConfSec.METADATA_SECTION):
            self.add_section(ConfSec.METADATA_SECTION)

    def data_sections(self) -> List:  # Section other than metadata and DEFAULT - real data.
        return [s for s in self.sections() if s != configparser.DEFAULTSECT and s != ConfSec.METADATA_SECTION]

    def get_version(self) -> Tuple:
        if version := self.get(*ConfOpt.METADATA_VERSION_OPTION.conf_id, fallback=None):
            try:
                return tuple(int(i) for i in version.split('.'))
            except ValueError:
                log_error(f"Illegal version number {version} should be i.j.k where i, j and k are integers.", trace=True)
        return 1, 6, 0

    def save(self, config_path) -> None:
        if not config_path.parent.is_dir():
            os.makedirs(config_path.parent)
        with open(config_path, 'w', encoding="utf-8") as config_file:
            self[ConfOpt.METADATA_VERSION_OPTION.conf_section][ConfOpt.METADATA_VERSION_OPTION.conf_name] = VDU_CONTROLS_VERSION
            self[ConfOpt.METADATA_TIMESTAMP_OPTION.conf_section][ConfOpt.METADATA_TIMESTAMP_OPTION.conf_name] = str(zoned_now())
            self.write(config_file)
        log_info(f"Wrote config to {config_path.as_posix()}")

    def duplicate(self, new_ini=None) -> ConfIni:
        if new_ini is None:
            new_ini = ConfIni()
        for section in self.sections():
            if section != configparser.DEFAULTSECT and section != ConfSec.METADATA_SECTION:
                new_ini.add_section(section)
            for option in self[section]:
                new_ini[section][option] = self[section][option]
        return new_ini

    def diff(self, other: ConfIni, vdu_settings_only: bool = False) -> Dict[Tuple[str, str], str]:
        values = []
        for subject in (self, other):
            sections = set(subject.sections()) - {configparser.DEFAULTSECT, ConfSec.METADATA_SECTION}
            if vdu_settings_only:
                sections -= {'preset'}
            values.append([(section, option, value) for section in sections for option, value in subject[section].items()])
        differences = list(set(values[0]) ^ set(values[1]))
        return {(section, option): value for section, option, value in differences}

    @staticmethod
    def get_path(config_name: str) -> Path:
        return CONFIG_DIR_PATH.joinpath(config_name + '.conf')


class ConfType:  # Supported types constants (in Python 3.11 this could be a StrEnum)
    BOOL = 'bool'
    FLOAT = 'float'
    CSV = 'csv'
    LONG_TEXT = 'long_text'
    TEXT = 'text'
    LOCATION = 'location'
    PATH = 'path'


class ConfSec:  # Data section constants (in Python 3.11 this could be a StrEnum)
    METADATA_SECTION = QT_TR_NOOP("metadata")  # INI version tracking section
    VDU_CONTROLS_GLOBALS = QT_TR_NOOP('vdu-controls-globals')
    VDU_CONTROLS_WIDGETS = QT_TR_NOOP('vdu-controls-widgets')
    DDCUTIL_PARAMETERS = QT_TR_NOOP('ddcutil-parameters')
    DDCUTIL_CAPABILITIES = QT_TR_NOOP('ddcutil-capabilities')
    UNKNOWN_SECTION = QT_TR_NOOP('unknown')


class ConfOpt(Enum):  # An Enum with tuples for values is used for convenience for scope/iteration

    @staticmethod  # Tricky way of creating a tuple with default values for some tuple members.
    def _def(cname: str, section: str = ConfSec.VDU_CONTROLS_GLOBALS, conf_type: str = ConfType.BOOL, default: str | None = None,
             global_allowed: bool = True, restart: bool = False, cmdline_arg: str = 'DEFAULT', tip: str = '',
             related: str = '', requires: str = '') -> Tuple[str, str, str, str, str | None, bool, str, str, str, bool]:
        return cname, section, cmdline_arg, conf_type, default, restart, tip, related, requires, global_allowed

    SPLASH_SCREEN_ENABLED = _def(cname=QT_TR_NOOP('splash-screen-enabled'), default='yes', cmdline_arg='splash',
                                 tip=QT_TR_NOOP('enable the startup splash screen'))
    SYSTEM_TRAY_ENABLED = _def(cname=QT_TR_NOOP('system-tray-enabled'), default="no", restart=True,
                               tip=QT_TR_NOOP('start up in the system tray'), related='hide-on-focus-out')
    HIDE_ON_FOCUS_OUT = _def(cname=QT_TR_NOOP('hide-on-focus-out'), default="no", restart=False,
                             tip=QT_TR_NOOP('minimize the main window automatically on focus out'))
    SMART_WINDOW = _def(cname=QT_TR_NOOP('smart-window'), default="yes",
                        tip=QT_TR_NOOP('smart main window placement and geometry (X11 and XWayland)'), restart=True)
    SMART_USES_XWAYLAND = _def(cname=QT_TR_NOOP('smart-uses-xwayland'), default="yes", restart=True,
                               tip=QT_TR_NOOP('if smart-window is enabled, use Xwayland in Wayland'))
    PREFER_QT6 = _def(cname=QT_TR_NOOP('prefer-qt6'), default="true", cmdline_arg='DISALLOWED',
                        tip=QT_TR_NOOP('Prefer Qt6 over Qt5 (if both are installed)'), restart=True)
    MONOCHROME_TRAY_ENABLED = _def(cname=QT_TR_NOOP('monochrome-tray-enabled'), default="no", restart=False,
                                   tip=QT_TR_NOOP('monochrome dark themed system tray'))
    MONO_LIGHT_TRAY_ENABLED = _def(cname=QT_TR_NOOP('mono-light-tray-enabled'), default="no", restart=False,
                                   tip=QT_TR_NOOP('monochrome light themed system tray'))
    PROTECT_NVRAM_ENABLED = _def(cname=QT_TR_NOOP('protect-nvram'), default="yes", restart=True,
                                 tip=QT_TR_NOOP('alter options and defaults to minimize VDU NVRAM writes'))
    ORDER_BY_NAME = _def(cname=QT_TR_NOOP('order-by-name'), default="no",
                         tip=QT_TR_NOOP('order lists and tabs by vdu-name'))
    LUX_OPTIONS_ENABLED = _def(cname=QT_TR_NOOP('lux-options-enabled'), default="yes", restart=True,
                               tip=QT_TR_NOOP('enable light metering options'))
    LUX_TRAY_ICON = _def(cname=QT_TR_NOOP('lux-tray-icon'), default="yes", restart=False,
                         tip=QT_TR_NOOP('enable lux light-level system-tray icon'))
    SCHEDULE_ENABLED = _def(cname=QT_TR_NOOP('schedule-enabled'), default='yes', tip=QT_TR_NOOP('enable preset schedule'))
    WEATHER_ENABLED = _def(cname=QT_TR_NOOP('weather-enabled'), default='yes', tip=QT_TR_NOOP('enable weather lookups'))
    DBUS_CLIENT_ENABLED = _def(cname=QT_TR_NOOP('dbus-client-enabled'), default="yes",
                               tip=QT_TR_NOOP('use the D-Bus ddcutil-server if available'))
    DBUS_EVENTS_ENABLED = _def(cname=QT_TR_NOOP('dbus-events-enabled'), default="yes",
                               tip=QT_TR_NOOP('enable D-Bus ddcutil-server events'), requires='dbus-client-enabled')
    SYSLOG_ENABLED = _def(cname=QT_TR_NOOP('syslog-enabled'), default="no",
                          tip=QT_TR_NOOP('divert diagnostic output to the syslog'))
    DEBUG_ENABLED = _def(cname=QT_TR_NOOP('debug-enabled'), default="no", tip=QT_TR_NOOP('output extra debug information'))
    WARNINGS_ENABLED = _def(cname=QT_TR_NOOP('warnings-enabled'), default="no",
                            tip=QT_TR_NOOP('popup warnings if a VDU lacks an enabled control'))
    TRANSLATIONS_ENABLED = _def(cname=QT_TR_NOOP('translations-enabled'), default="no", restart=True,
                                tip=QT_TR_NOOP('enable language translations, currently not updated (no known users)'))
    LOCATION = _def(cname=QT_TR_NOOP('location'), conf_type=ConfType.LOCATION, tip=QT_TR_NOOP('latitude,longitude'))
    DDCUTIL_EMULATOR = _def(cname=QT_TR_NOOP('ddcutil-emulator'), conf_type=ConfType.PATH,
                            tip=QT_TR_NOOP('additional command-line ddcutil emulator for a laptop panel'))
    SLEEP_MULTIPLIER = _def(cname=QT_TR_NOOP('sleep-multiplier'), section=ConfSec.DDCUTIL_PARAMETERS, conf_type=ConfType.FLOAT,
                            tip=QT_TR_NOOP('ddcutil --sleep-multiplier (0.1 .. 2.0, default none)'))
    DDCUTIL_EXTRA_ARGS = _def(cname=QT_TR_NOOP('ddcutil-extra-args'), section=ConfSec.DDCUTIL_PARAMETERS, conf_type=ConfType.TEXT,
                              tip=QT_TR_NOOP('ddcutil extra arguments (default none)'))
    VDU_NAME = _def(cname=QT_TR_NOOP('vdu-name'), section=ConfSec.VDU_CONTROLS_WIDGETS, conf_type=ConfType.TEXT,
                    global_allowed=False, cmdline_arg='DISALLOWED', tip=QT_TR_NOOP('Name to display for this VDU'))
    ENABLE_VCP_CODES = _def(cname=QT_TR_NOOP('enable-vcp-codes'), section=ConfSec.VDU_CONTROLS_WIDGETS, conf_type=ConfType.CSV,
                            cmdline_arg='DISALLOWED', tip=QT_TR_NOOP('CSV list of VCP Hex-code capabilities to enable'))
    CAPABILITIES_OVERRIDE = _def(cname=QT_TR_NOOP('capabilities-override'), section=ConfSec.DDCUTIL_CAPABILITIES,
                                 conf_type=ConfType.LONG_TEXT, cmdline_arg='DISALLOWED')
    METADATA_VERSION_OPTION = _def(cname=QT_TR_NOOP('version'), section=ConfSec.METADATA_SECTION,
                                 conf_type=ConfType.BOOL, cmdline_arg='DISALLOWED')
    METADATA_TIMESTAMP_OPTION = _def(cname=QT_TR_NOOP('timestamp'), section=ConfSec.METADATA_SECTION,
                                 conf_type=ConfType.BOOL, cmdline_arg='DISALLOWED')
    UNKNOWN = _def(cname="UNKNOWN", section=ConfSec.UNKNOWN_SECTION, conf_type=ConfType.BOOL, cmdline_arg='DISALLOWED', tip='')

    def __init__(self, conf_name: str, section: str, cmdline_arg: str, conf_type: str, default: str | None,
                 restart_required: bool, help_text: str, related: str, requires: str, global_allowed):
        self.conf_name = conf_name
        self.conf_section = section
        self.conf_type = conf_type
        self.conf_id = self.conf_section, self.conf_name
        self.restart_required = restart_required
        self.help = help_text
        self.cmdline_arg = self.conf_name.replace("-enabled", "") if cmdline_arg == 'DEFAULT' else cmdline_arg
        self.cmdline_var = None if self.cmdline_arg == "DISALLOWED" else self.conf_name.replace('-enabled', '').replace('-', '_')
        self.default_value = default
        self.related = related
        self.requires = requires
        self.global_allowed = global_allowed

    def add_cmdline_arg(self, parser: argparse.ArgumentParser) -> None:
        if self.cmdline_arg != "DISALLOWED":
            if self.conf_type == ConfType.BOOL:  # Store strings for bools, allows us to differentiate yes/no and not supplied.
                parser.add_argument(f"--{self.cmdline_arg}", dest=self.cmdline_var, action='store_const', const='yes',
                                    help=self.help + ' ' + (tr('(default)') if self.default_value == 'yes' else ''))
                parser.add_argument(f"--no-{self.cmdline_arg}", dest=self.cmdline_var, action='store_const', const='no',
                                    help=tr('(default)') if self.default_value == 'no' else '')
            elif self.conf_type == ConfType.FLOAT:
                parser.add_argument(f"--{self.cmdline_arg}", type=float, default=self.default_value, help=self.help)
            else:
                parser.add_argument(f"--{self.cmdline_arg}", type=str, default=self.default_value, help=self.help)


class VduControlsConfig:
    """
    A vdu_controls config that can be read or written from INI style files by the standard configparser package.
    Includes a method that can fold in values from command line arguments parsed by the standard argparse package.
    """

    def __init__(self, config_name: str, default_enabled_vcp_codes: List | None = None, main_config: bool = False) -> None:
        self.config_name = config_name
        self.ini_content = ConfIni()

        if main_config:
            self.ini_content[ConfSec.VDU_CONTROLS_GLOBALS] = {}
            for option in ConfOpt:  # Add in options for all supported controls
                if option.conf_section == ConfSec.VDU_CONTROLS_GLOBALS:
                    default_str = str(option.default_value) if option.default_value is not None else ''
                    self.ini_content.set(*option.conf_id, default_str)

        self.ini_content[ConfSec.VDU_CONTROLS_WIDGETS] = {}
        self.ini_content[ConfSec.DDCUTIL_PARAMETERS] = {}
        self.ini_content[ConfSec.DDCUTIL_CAPABILITIES] = {}

        for item in SUPPORTED_VCP_BY_CODE.values():
            self.ini_content[ConfSec.VDU_CONTROLS_WIDGETS][item.property_name()] = 'yes' if item.enabled else 'no'

        self.ini_content.set(*ConfOpt.ENABLE_VCP_CODES.conf_id, '')
        if not main_config:
            self.ini_content.set(*ConfOpt.VDU_NAME.conf_id, '')
        self.ini_content.set(*ConfOpt.SLEEP_MULTIPLIER.conf_id, str('0.0'))
        self.ini_content.set(*ConfOpt.DDCUTIL_EXTRA_ARGS.conf_id, '')
        self.ini_content.set(*ConfOpt.CAPABILITIES_OVERRIDE.conf_id, '')

        if default_enabled_vcp_codes is not None:
            for code in default_enabled_vcp_codes:
                if code in SUPPORTED_VCP_BY_CODE:
                    self.enable_supported_vcp_code(code)
                else:
                    self.enable_unsupported_vcp_code(code)
        self.file_path: Path | None = None

    def get_conf_option(self, section_name: str, option_name: str) -> ConfOpt:
        for option in ConfOpt:  # Inefficient, but a small number of iterations
            if option.conf_section == section_name and option.conf_name == option_name:
                return option
        return ConfOpt.UNKNOWN

    def restrict_to_actual_capabilities(self, supported_by_this_vdu: Dict[str, VcpCapability]) -> None:
        for option_name in self.ini_content[ConfSec.VDU_CONTROLS_WIDGETS]:
            if self.get_conf_option(ConfSec.VDU_CONTROLS_WIDGETS, option_name).conf_type == ConfType.BOOL:
                if option_name in SUPPORTED_VCP_BY_PROPERTY_NAME and \
                        SUPPORTED_VCP_BY_PROPERTY_NAME[option_name].vcp_code not in supported_by_this_vdu:
                    del self.ini_content[ConfSec.VDU_CONTROLS_WIDGETS][option_name]
                    log_debug(f"Removed {self.config_name} {option_name} - not supported by VDU") if log_debug_enabled else None
                elif option_name.startswith('unsupported-') and option_name[len('unsupported-'):] not in supported_by_this_vdu:
                    del self.ini_content[ConfSec.VDU_CONTROLS_WIDGETS][option_name]
                    log_debug(f"Removed {self.config_name} {option_name} - not supported by VDU") if log_debug_enabled else None

    def get_vdu_preferred_name(self):
        custom_name = self.ini_content.get(*ConfOpt.VDU_NAME.conf_id, fallback=None)
        return custom_name if custom_name is not None and custom_name.strip() != '' else self.config_name

    def is_set(self, option: ConfOpt, fallback=False) -> bool:
        return self.ini_content.getboolean(option.conf_section, option.conf_name, fallback=fallback)

    def set_option_from_args(self, option: ConfOpt, arg_values: Dict[str, Any]):
        if option.cmdline_var is not None and option.cmdline_var in arg_values and arg_values[option.cmdline_var] is not None:
            str_value = str(arg_values[option.cmdline_var])
            if str_value != self.ini_content[option.conf_section][option.conf_name]:
                log_warning(f"command-line {option.cmdline_arg}={str_value} overrides {option.conf_section}.{option.conf_name}="
                            f"{self.ini_content[option.conf_section][option.conf_name]} (in {self.file_path})")
                self.ini_content[option.conf_section][option.conf_name] = str_value

    def get_sleep_multiplier(self, fallback: float | None = None) -> float | None:
        value = self.ini_content.getfloat(*ConfOpt.SLEEP_MULTIPLIER.conf_id, fallback=0.0)
        return fallback if math.isclose(value, 0.0) else value

    def get_ddcutil_extra_args(self, fallback: List[str] | None = None) -> List[str]:
        fallback = [] if fallback is None else fallback
        value = self.ini_content.get(*ConfOpt.DDCUTIL_EXTRA_ARGS.conf_id, fallback=None)
        return fallback if value is None or value.strip() == '' else value.split()

    def get_capabilities_alt_text(self) -> str:
        return self.ini_content.get(*ConfOpt.CAPABILITIES_OVERRIDE.conf_id)

    def set_capabilities_alt_text(self, alt_text: str) -> None:
        self.ini_content.set(*ConfOpt.CAPABILITIES_OVERRIDE.conf_id, alt_text)

    def enable_supported_vcp_code(self, vcp_code: str) -> None:
        self.ini_content[ConfSec.VDU_CONTROLS_WIDGETS][SUPPORTED_VCP_BY_CODE[vcp_code].property_name()] = 'yes'

    def enable_unsupported_vcp_code(self, vcp_code: str) -> None:
        self.ini_content[ConfSec.VDU_CONTROLS_WIDGETS][f'unsupported-{vcp_code}'] = 'yes'

    def disable_supported_vcp_code(self, vcp_code: str) -> None:
        self.ini_content[ConfSec.VDU_CONTROLS_WIDGETS][SUPPORTED_VCP_BY_CODE[vcp_code].property_name()] = 'no'

    def get_all_enabled_vcp_codes(self) -> List[str]:  # Not very efficient
        enabled_vcp_codes = []
        for control_name, control_def in SUPPORTED_VCP_BY_PROPERTY_NAME.items():
            if self.ini_content[ConfSec.VDU_CONTROLS_WIDGETS].getboolean(control_name, fallback=False):
                enabled_vcp_codes.append(control_def.vcp_code)
        enable_codes_str = self.ini_content.get(*ConfOpt.ENABLE_VCP_CODES.conf_id, fallback='')
        for vcp_code in enable_codes_str.split(","):
            if code := vcp_code.strip().upper():
                if code not in enabled_vcp_codes:
                    enabled_vcp_codes.append(code)
                else:
                    log_warning(f"supported enabled vcp_code {code} is redundantly listed "
                                f"in enabled_vcp_codes ({enable_codes_str})")
        return enabled_vcp_codes

    def get_location(self) -> GeoLocation | None:
        try:
            spec = self.ini_content.get(*ConfOpt.LOCATION.conf_id, fallback=None)
            if spec is None or spec.strip() == '':
                return None
            parts = spec.split(',')
            return GeoLocation(float(parts[0]), float(parts[1]), None if len(parts) < 3 else parts[2])
        except ValueError as ve:
            log_error("Problem with geolocation:", ve)
            return None

    def parse_file(self, config_path: Path) -> None:
        """Parse config values from file"""
        self.file_path = config_path
        basename = os.path.basename(config_path)
        config_text = Path(config_path).read_text()
        log_info("Using config file '" + config_path.as_posix() + "'")
        if re.search(r'(\[ddcutil-capabilities])|(\[ddcutil-parameters])|(\[vdu-controls-\w])', config_text) is None:
            log_info(f"Old style config file {basename} overrides ddcutils capabilities")
            self.ini_content.set(*ConfOpt.CAPABILITIES_OVERRIDE.conf_id, config_text)
            return
        self.ini_content.read_string(config_text)
        # Manually extract the text preserving meaningful indentation
        preserve_indents_match = re.search(
            r'\[ddcutil-capabilities](?:.|\n)*\ncapabilities-override[ \t]*[:=]((.*)(\n[ \t].+)*)', config_text)
        alt_text = preserve_indents_match.group(1) if preserve_indents_match is not None else ''
        # Remove excess indentation while preserving the minimum existing indentation.
        alt_text = inspect.cleandoc(alt_text)
        self.ini_content.set(*ConfOpt.CAPABILITIES_OVERRIDE.conf_id, alt_text)

    def reload(self) -> None:
        log_info(f"Reloading config: {self.file_path}")
        if self.file_path:
            for section in list(self.ini_content.data_sections()):
                self.ini_content.remove_section(section)
            self.parse_file(self.file_path)

    def debug_dump(self) -> None:
        origin = 'configuration' if self.file_path is None else os.path.basename(self.file_path)
        for section in self.ini_content.sections():
            for option in self.ini_content[section]:
                log_debug(f"config: {origin} [{section}] {option} = {self.ini_content[section][option]}")

    def write_file(self, config_path: Path, overwrite: bool = False) -> None:
        """Write the config to a file.  Used for creating initial template config files."""
        self.file_path = config_path
        if config_path.exists():
            if not config_path.is_file() or not overwrite:
                log_error(f"{config_path.as_posix()} exists, remove the file if you really want to replace it.")
                return
        log_info(f"Creating new config file {config_path.as_posix()}")
        self.ini_content.save(config_path)

    def parse_global_args(self, args=None) -> argparse.Namespace:
        """Parse command line arguments and integrate the results into this config"""
        if args is None:
            args = sys.argv[1:]
        parser = argparse.ArgumentParser(
            description=textwrap.dedent(f"""
            {APPNAME}
              Uses ddcutil to issue Display Data Channel (DDC) Virtual Control Panel (VCP) commands.
              Controls DVI/DP/HDMI/USB connected monitors (but not builtin laptop displays)."""),
            formatter_class=argparse.RawTextHelpFormatter)
        parser.epilog = textwrap.dedent("""
            As well as command line arguments, individual VDU controls and optimisations may be
            specified in monitor specific configuration files, see --detailed-help for details.

            See the --detailed-help for important licencing information.
            """)
        parser.add_argument('--detailed-help', default=False, action='store_true', help='Detailed help (in markdown format).')
        parser.add_argument('--about', default=False, action='store_true', help='info about vdu_controls')
        parser.add_argument('--show', default=[], action='append',
                            choices=[vcp.property_name() for vcp in SUPPORTED_VCP_BY_CODE.values()],
                            help='show specified control only (--show may be specified multiple times)')
        parser.add_argument('--hide', default=[], action='append',
                            choices=[vcp.property_name() for vcp in SUPPORTED_VCP_BY_CODE.values()],
                            help='hide/disable a control (--hide may be specified multiple times)')
        parser.add_argument('--enable-vcp-code', type=str, action='append',
                            help='enable controls for an unsupported vcp-code hex value (maybe specified multiple times)')
        for option in ConfOpt:
            if option.cmdline_arg is not None:
                option.add_cmdline_arg(parser)
        parser.add_argument('--create-config-files', action='store_true',
                            help="create template config files, one global file and one for each detected VDU.")
        parser.add_argument('--install', action='store_true',
                            help="installs the vdu_controls in the current user's path and desktop application menu.")
        parser.add_argument('--uninstall', action='store_true',
                            help='uninstalls the vdu_controls application menu file and script for the current user.')
        parsed_args = parser.parse_args(args=args)
        if parsed_args.install:
            install_as_desktop_application()
            sys.exit()
        if parsed_args.uninstall:
            install_as_desktop_application(uninstall=True)
            sys.exit()
        if parsed_args.detailed_help:
            print(__doc__)
            sys.exit()

        arg_values = vars(parsed_args)
        for option in ConfOpt:
            if option.cmdline_arg is not None:
                self.set_option_from_args(option, arg_values)
        if len(parsed_args.show) != 0:
            for control_def in SUPPORTED_VCP_BY_CODE.values():
                if control_def.property_name() in parsed_args.show:
                    self.enable_supported_vcp_code(control_def.vcp_code)
                else:
                    self.disable_supported_vcp_code(control_def.vcp_code)
        if len(parsed_args.hide) != 0:
            for control_def in SUPPORTED_VCP_BY_CODE.values():
                if control_def.property_name() in parsed_args.hide:
                    self.disable_supported_vcp_code(control_def.vcp_code)
        if parsed_args.enable_vcp_code is not None:
            for code in parsed_args.enable_vcp_code:
                self.enable_unsupported_vcp_code(code)

        return parsed_args


class VduControllerAsyncSetter(WorkerThread):  # Used to decouple the set-vcp from the GUI

    def __init__(self):
        super().__init__(task_body=self._async_setvcp_task_body, task_finished=None, loop=True)
        self._async_setvcp_queue: queue.Queue = queue.Queue()
        # limit set_vcp to a sustainable interval - KDE powerdevil recommendation - 0.5s, ddcui 1.0 seconds
        self._idle_seconds = float(os.getenv("VDU_CONTROLS_UI_IDLE_SECS", '0.5'))
        log_info(f"env VDU_CONTROLS_UI_IDLE_SECS={self._idle_seconds}")

    def _async_setvcp_task_body(self, _: WorkerThread):
        latest_pending = {}  # Handle bursts of UI setvcp requests, filtering out repeats for the same feature.
        while not self._async_setvcp_queue.empty():  # Keep going while there is something in the queue
            try:
                # print(f"{self._async_setvcp_queue.qsize()=}")
                controller, vcp_code, value, origin = self._async_setvcp_queue.get_nowait()
                key = (controller, vcp_code)
                if log_debug_enabled:
                    log_debug(f"UI discard earlier op on {controller.vdu_number=} {vcp_code=}") if key in latest_pending else None
                latest_pending[key] = (value, origin)  # keep the latest for each controller+vcp_code.
                self._async_setvcp_queue.task_done()
            except queue.Empty:
                pass
            if latest_pending and self._async_setvcp_queue.empty():  # some setvcp requests are pending,
                self.doze(self._idle_seconds)  # wait a bit in case more arrive - might be dragging a slider or spinning a spinner
        if latest_pending:  # nothing more has arrived, if any setvcp requests are pending, set for real now
            for (controller, vcp_code), (value, origin) in latest_pending.items():
                if controller.values_cache.get(vcp_code, None) != value:
                    log_debug(f"UI set {controller.vdu_number=} {vcp_code=} {value=} {origin}") if log_debug_enabled else None
                    controller.set_vcp_value(vcp_code, value, origin, asynchronous_caller=True)
                else:
                    log_debug(f"UI nochange {controller.vdu_number=} {vcp_code=} {value=} {origin}") if log_debug_enabled else None
        else:
            self.doze(self._idle_seconds)

    def queue_setvcp(self, controller: VduController, vcp_code: str, value: int, origin: VcpOrigin):
        self._async_setvcp_queue.put((controller, vcp_code, value, origin))


class VduController(QObject):
    """
    Holds model+controller specific to an individual VDU including a map of its capabilities. A model object in
    MVC speak.

    The model configuration can optionally be read from an INI-format config file held in $HOME/.config/vdu-control/

    Capabilities are either extracted from ddcutil output or read from the INI-format files.  File read
    capabilities are provided so that the output from "ddcutil --display N capabilities" can be corrected (because
    it is sometimes incorrect due to sloppy implementation by manufacturers). For example, my LG monitor reports
    two Display-Port inputs, and it only has one.
    """

    NORMAL_VDU = 0
    IGNORE_VDU = 1
    ASSUME_STANDARD_CONTROLS = 2
    DISCARD_VDU = 3
    _RANGE_PATTERN = re.compile(r'Values:\s+([0-9]+)..([0-9]+)')
    _FEATURE_PATTERN = re.compile(r'([0-9A-F]{2})\s+[(]([^)]+)[)]\s(.*)', re.DOTALL | re.MULTILINE)
    _LIMITED_RANGE_KEY = "%%RANGE%%"  # A key internal to vdu_controls for storing Range n..m values.
    _FORCE_REFRESH_NAME_SUFFIX = "*refresh*"

    vcp_value_changed_qtsignal = pyqtSignal(str, str, int, VcpOrigin, bool)
    _async_setvcp_exception_qtsignal = pyqtSignal(str, int, VcpOrigin, Exception)

    _async_setvcp_task: VduControllerAsyncSetter | None = None

    def __init__(self, vdu_number: str, vdu_model_name: str, serial_number: str, manufacturer: str,
                 default_config: VduControlsConfig, ddcutil: Ddcutil,
                 vdu_exception_handler: Callable, remedy: int = 0) -> None:
        super().__init__()
        self.no_longer_in_use = False
        if vdu_model_name.strip() == '':  # laptop monitors can sneak through with no model_name
            vdu_model_name = "Unknown"
        self.vdu_stable_id = VduStableId(proper_name(vdu_model_name, serial_number))
        log_info(f"Initializing controls for {vdu_number=} {vdu_model_name=} {self.vdu_stable_id=}")
        self.vdu_number = vdu_number
        self.model_name = vdu_model_name
        self.serial_number = serial_number
        self.manufacturer = manufacturer
        self.ddcutil = ddcutil
        self.vdu_exception_handler = vdu_exception_handler

        def _handle_async_setvcp_exception(vcp_code: str, value: int, origin: VcpOrigin, e: VduException):
            if self.vdu_exception_handler(e, True):
                self.set_vcp_value_asynchronously(vcp_code, value, origin)

        self._async_setvcp_exception_qtsignal.connect(_handle_async_setvcp_exception)
        if VduController._async_setvcp_task is None or VduController._async_setvcp_task.isFinished():
            VduController._async_setvcp_task = VduControllerAsyncSetter()
            VduController._async_setvcp_task.start()

        self.vdu_model_id = proper_name(vdu_model_name.strip())
        self.capabilities_text: str | None = None
        self.config = None
        self.values_cache: Dict[str, int] = {}
        self.ignore_vdu = remedy == VduController.IGNORE_VDU
        default_sleep_multiplier: float | None = default_config.get_sleep_multiplier(fallback=None)
        enabled_vcp_codes = default_config.get_all_enabled_vcp_codes()
        for config_name in (self.vdu_stable_id, self.vdu_model_id):  # Allow for shared single model file (not encouraged).
            config_path = ConfIni.get_path(config_name)
            log_debug("checking for config file '" + config_path.as_posix() + "'") if log_debug_enabled else None
            if os.path.isfile(config_path) and os.access(config_path, os.R_OK):
                self.config = VduControlsConfig(config_name)
                self.config.parse_file(config_path)
                if default_config.is_set(ConfOpt.DEBUG_ENABLED):
                    self.config.debug_dump()
                enabled_vcp_codes = self.config.get_all_enabled_vcp_codes()
                self.capabilities_text = self.config.get_capabilities_alt_text()  # cached, possibly edited, ddc capabilities
                self.ignore_vdu = self.ignore_vdu or self.capabilities_text == '' or self.capabilities_text == IGNORE_VDU_MARKER_STR
                if not self.ignore_vdu:
                    if multiplier := self.config.get_sleep_multiplier(fallback=default_sleep_multiplier):
                        self.ddcutil.set_sleep_multiplier(vdu_number, multiplier)
                    self.ddcutil.set_vdu_specific_args(vdu_number, self.config.get_ddcutil_extra_args(fallback=None))
                break
        if not self.capabilities_text:
            if remedy == VduController.DISCARD_VDU:
                self.capabilities_text = IGNORE_VDU_MARKER_STR
                log_info(f"Capabilities override set to ignore VDU {vdu_number=} {vdu_model_name=} {self.vdu_stable_id=}")
            elif remedy == VduController.IGNORE_VDU:
                self.capabilities_text = ''
            elif remedy == VduController.ASSUME_STANDARD_CONTROLS:
                enabled_vcp_codes = ASSUMED_CONTROLS_CONFIG_VCP_CODES
                self.capabilities_text = ASSUMED_CONTROLS_CONFIG_TEXT
            else:
                self.capabilities_text = ddcutil.query_capabilities(vdu_number)
            self.ignore_vdu = self.capabilities_text == '' or self.capabilities_text == IGNORE_VDU_MARKER_STR
        # print(f"{self.capabilities_text}")
        self.capabilities_supported_by_this_vdu = self._parse_capabilities(self.capabilities_text)
        # Find those capabilities supported by this VDU AND enabled in the GUI:
        self.enabled_capabilities = [c for c in self.capabilities_supported_by_this_vdu.values() if c.vcp_code in enabled_vcp_codes]
        if self.config is None:  # In memory only config - in case it's needed by a future config editor
            self.config = VduControlsConfig(self.vdu_stable_id,
                                            default_enabled_vcp_codes=[c.vcp_code for c in self.enabled_capabilities])
            self.config.set_capabilities_alt_text(self.capabilities_text)
        self.config.restrict_to_actual_capabilities(self.capabilities_supported_by_this_vdu)
        if remedy == VduController.DISCARD_VDU:
            self.write_template_config_files()  # Persist the discard

    def write_template_config_files(self) -> None:
        """Write template config files to $HOME/.config/vdu_controls/"""
        config_name = self.vdu_stable_id
        save_config_path = ConfIni.get_path(config_name)
        config = VduControlsConfig(config_name, default_enabled_vcp_codes=[c.vcp_code for c in self.enabled_capabilities])
        config.set_capabilities_alt_text(self.capabilities_text if self.capabilities_text is not None else '')
        config.write_file(save_config_path)
        self.config = config

    def get_vdu_preferred_name(self, upper: bool = False) -> str:
        return self.config.get_vdu_preferred_name().upper() if upper else self.config.get_vdu_preferred_name()

    def get_full_id(self) -> Tuple[str, str, str, str]:
        """Return a tuple that defines this VDU: (vdu_number, manufacturer, model, serial-number)."""
        return self.vdu_number, self.manufacturer, self.model_name, self.serial_number

    def get_vcp_values(self, vcp_codes: List[str]) -> List[VcpValue]:
        try:
            if len(vcp_codes) == 0:
                return []
            # raise subprocess.SubprocessError("get_attributes")  # for testing
            values = self.ddcutil.get_vcp_values(self.vdu_number, vcp_codes)
            for vcp_code, vcp_value in zip(vcp_codes, values):
                value = vcp_value.current
                cached_value = self.values_cache.get(vcp_code, None)
                if value != cached_value:
                    self.values_cache[vcp_code] = value
                    if cached_value is not None:  # Not just initialization, but an actual change...
                        if log_debug_enabled:
                            log_debug(
                                f"get_vcp signals vcp_value_changed: {self.vdu_stable_id} {vcp_code=} {value} {VcpOrigin.EXTERNAL}")
                        self.vcp_value_changed_qtsignal.emit(self.vdu_stable_id, vcp_code, value, VcpOrigin.EXTERNAL,
                                                             self.capabilities_supported_by_this_vdu[vcp_code].causes_config_change)
            return values
        except (subprocess.SubprocessError, ValueError, TimeoutError, DdcutilDisplayNotFound) as e:
            raise VduException(vdu_description=self.get_vdu_preferred_name(), vcp_code=",".join(vcp_codes), exception=e,
                               operation="get_vcp_values") from e

    def set_vcp_value(self, vcp_code: str, value: int, origin: VcpOrigin = VcpOrigin.NORMAL,
                      asynchronous_caller: bool = False) -> None:
        if self.no_longer_in_use:
            log_info(f"Expired controller discards set_vcp_value({vcp_code=}, {value=}, {origin=}) {asynchronous_caller=}")
            return
        try:
            # raise subprocess.SubprocessError("set_attribute")  # for testing
            retry_on_error = vcp_code in SUPPORTED_VCP_BY_CODE and SUPPORTED_VCP_BY_CODE[vcp_code].retry_setvcp
            self.ddcutil.set_vcp(self.vdu_number, vcp_code, value, retry_on_error=retry_on_error)
            self.values_cache[vcp_code] = value
            if log_debug_enabled:
                log_debug(f"set_vcp signals vcp_value_changed: {self.vdu_stable_id} {vcp_code=} {value} {origin}")
            self.vcp_value_changed_qtsignal.emit(self.vdu_stable_id, vcp_code, value, origin,
                                                 self.capabilities_supported_by_this_vdu[vcp_code].causes_config_change)
        except (subprocess.SubprocessError, ValueError, TimeoutError, DdcutilDisplayNotFound) as e:
            vdu_exception = VduException(vdu_description=self.get_vdu_preferred_name(), vcp_code=vcp_code, exception=e,
                                         operation="set_vcp_value")
            if not asynchronous_caller:
                raise vdu_exception from e
            self._async_setvcp_exception_qtsignal.emit(vcp_code, value, origin, vdu_exception)

    def set_vcp_value_asynchronously(self, vcp_code: str, value: int, origin: VcpOrigin = VcpOrigin.NORMAL) -> None:
        # Queue the change for the queue processing thread - avoids blocking the GUI.
        VduController._async_setvcp_task.queue_setvcp(self, vcp_code, value, origin)

    def get_range_restrictions(self, vcp_code, fallback: Tuple[int, int] | None = None) -> Tuple[int, int] | None:
        if vcp_code in self.capabilities_supported_by_this_vdu:
            range_restriction = self.capabilities_supported_by_this_vdu[vcp_code].values  # will always be a list
            if len(range_restriction) != 0:
                return int(range_restriction[1]), int(range_restriction[2])
        return fallback

    def get_write_count(self):
        return self.ddcutil.get_write_count(self.vdu_number) if self.ddcutil else 0

    def _parse_capabilities(self, capabilities_text=None) -> Dict[str, VcpCapability]:
        """Return a map of vpc capabilities keyed by vcp code."""

        if capabilities_text == "Ignore VDU":
            return {}

        def _parse_values(values_str: str) -> List[str]:
            values_list = []
            if stripped := values_str.strip():
                lines_list = stripped.split('\n')
                if len(lines_list) == 1:
                    if range_match := VduController._RANGE_PATTERN.match(lines_list[0]):
                        values_list = [VduController._LIMITED_RANGE_KEY, range_match.group(1), range_match.group(2)]
                    else:
                        space_separated = lines_list[0].replace('(interpretation unavailable)', '').strip().split(' ')
                        values_list = [(v.upper(), 'unknown ' + v) for v in space_separated[1:]]
                else:
                    values_list = [(key.upper(), desc.strip()) for key, desc in (v.strip().split(":", 1) for v in lines_list[1:])]
            return values_list

        feature_map = {}
        for feature_text in capabilities_text.split(' Feature: '):
            if feature_match := VduController._FEATURE_PATTERN.match(feature_text):
                vcp_code = feature_match.group(1)
                vcp_name = feature_match.group(2)
                if requires_refresh := vcp_name.lower().endswith(VduController._FORCE_REFRESH_NAME_SUFFIX):
                    vcp_name = vcp_name.replace(VduController._FORCE_REFRESH_NAME_SUFFIX, "")
                values = _parse_values(feature_match.group(3))
                # Guess type from existence or not of value list
                if len(values) == 0:
                    vcp_type = CONTINUOUS_TYPE
                    if vcp_code in SUPPORTED_VCP_BY_CODE:  # Override if we know better
                        vcp_type = SUPPORTED_VCP_BY_CODE[vcp_code].vcp_type
                elif values[0] == VduController._LIMITED_RANGE_KEY:  # Special internal hacked config spec to specify range
                    vcp_type = CONTINUOUS_TYPE
                else:  # two-byte or one-byte continuous type - cannot always trust the VDU metadata on this.
                    try:  # See whether the max is really contained within one byte:
                        max_value = max([int(v, 16) for v, _ in values])
                        vcp_type = COMPLEX_NON_CONTINUOUS_TYPE if max_value > 0xff else SIMPLE_NON_CONTINUOUS_TYPE
                    except ValueError:
                        vcp_type = COMPLEX_NON_CONTINUOUS_TYPE  # Assume two byte

                capability = VcpCapability(vcp_code, vcp_name, vcp_type=vcp_type, values=values, icon_source=None,
                                           can_transition=vcp_type == CONTINUOUS_TYPE, causes_config_change=requires_refresh)
                feature_map[vcp_code] = capability
        return {**{k: feature_map[k] for k in (BRIGHTNESS_VCP_CODE, CONTRAST_VCP_CODE) if k in feature_map},  # Put B&C first
                **{k: v for k, v in feature_map.items() if k not in (BRIGHTNESS_VCP_CODE, CONTRAST_VCP_CODE)}}


class SubWinDialog(QDialog):  # Fix for gnome: QDialog must be a subwindow, otherwise it will always stay on top of other windows.

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.WindowType.SubWindow if is_gnome_desktop() else Qt.WindowType.Window)


class StdButton(QPushButton):  # Reduce some repetitiveness in the code

    def __init__(self, icon: QIcon | None = None, title: str = '', clicked: Callable | None = None, auto_default=True,
                 tip: str | None = None, flat: bool = False, margins: bool = True, icon_size: QSize | None = None):
        super().__init__()
        self.setIcon(icon) if icon else None
        self.setIconSize(icon_size) if icon_size else None
        self.setText(title) if title else None
        self.clicked.connect(clicked) if clicked else None
        self.setToolTip(tip) if tip else None
        self.setFlat(flat)
        self.setContentsMargins(0, 0, 0, 0) if not margins else None
        self.setAutoDefault(auto_default)


class SettingsDialog(SubWinDialog, DialogSingletonMixin):
    """
    Application Settings Editor, edits a default global settings file, and a settings file for each VDU.
    The files are in INI format.  Internally, the settings are VduControlsConfig wrappers around the standard class ConfigIni.
    """

    @staticmethod
    def invoke(default_config: VduControlsConfig, vdu_config_list: List[VduControlsConfig], change_callback: Callable) -> None:
        SettingsDialog.show_existing_dialog() if SettingsDialog.exists() else SettingsDialog(default_config,
                                                                                             vdu_config_list, change_callback)

    @staticmethod
    def reconfigure_instance(vdu_config_list: List[VduControlsConfig]) -> None:
        SettingsDialog.get_instance().reconfigure(vdu_config_list) if SettingsDialog.exists() else None

    def __init__(self, default_config: VduControlsConfig, vdu_config_list: List[VduControlsConfig], change_callback) -> None:
        super().__init__()
        self.setWindowTitle(tr('Settings'))
        self.setLayout(widget_layout := QVBoxLayout())
        self.tabs_widget = QTabWidget(self)
        widget_layout.addWidget(self.tabs_widget)
        self.editor_tab_list: List[SettingsEditorTab] = []
        self.bottom_status_bar = QStatusBar()
        self.tab_ops = QFrame(self)  # Groups operations that target the current tab
        self.tab_ops.setLayout(tab_ops_layout := QHBoxLayout())
        self.tab_ops_label = QLabel('')
        tab_ops_layout.addWidget(self.tab_ops_label)
        self.change_callback = change_callback

        def _tab_restore_defaults() -> None:
            self.tabs_widget.currentWidget().restore_application_defaults()

        self.tab_restore_defaults_button = StdButton(icon=si(self, StdPixmap.SP_DialogDiscardButton), title=(tr('Defaults')),
                                                     clicked=_tab_restore_defaults)
        tab_ops_layout.addWidget(self.tab_restore_defaults_button)

        def _tab_revert_current_tab() -> None:
            self.tabs_widget.currentWidget().revert_changes()

        self.tab_revert_button = StdButton(icon=si(self, StdPixmap.SP_DialogResetButton), title=(tr('Revert')),
                                           clicked=_tab_revert_current_tab)
        tab_ops_layout.addWidget(self.tab_revert_button)

        def _tab_save_current_tab() -> None:
            self.tabs_widget.currentWidget().save()

        self.tab_save_button = StdButton(icon=si(self, StdPixmap.SP_DriveFDIcon), title=(tr('Save')), clicked=_tab_save_current_tab)
        tab_ops_layout.addWidget(self.tab_save_button)

        self.bottom_status_bar.addPermanentWidget(self.tab_ops, 0)
        self.bottom_status_bar.addPermanentWidget(QLabel('                    '))

        save_all_button = StdButton(icon=si(self, StdPixmap.SP_DriveFDIcon), title=(tr("Save All")),
                                    clicked=(partial(self.save_all, True)))
        self.bottom_status_bar.addPermanentWidget(save_all_button, 0)

        quit_button = StdButton(icon=si(self, StdPixmap.SP_DialogCloseButton), title=(tr("Close")), clicked=self.close)
        self.bottom_status_bar.addPermanentWidget(quit_button, 0)

        widget_layout.addWidget(self.bottom_status_bar)

        def _tab_changed(index: int) -> None:
            self.update_tab_ops(self.tabs_widget.widget(index))

        self.tabs_widget.currentChanged.connect(_tab_changed)

        self.resize(npx(1900), npx(1000))
        self.setMinimumSize(npx(1024), npx(800))
        self.reconfigure([default_config, *vdu_config_list])
        self.make_visible()
        
    def status_message(self, message: str, msecs: int = 0):  # Display a message on the visible tab.
        self.bottom_status_bar.showMessage(message, msecs)

    def sizeHint(self):
        return QSize(npx(1700), npx(1000))

    def update_tab_ops(self, tab: SettingsEditorTab) -> None:
        self.tab_ops_label.setText(tr('{}: ').format(tab.preferred_name))
        self.tab_ops.setToolTip(tr('{}: {}').format(tab.preferred_name, tab.config_path.as_posix()))
        self.tab_save_button.setToolTip(tr('Save {} to \n{}').format(tab.preferred_name, tab.config_path.as_posix()))
        self.tab_revert_button.setToolTip(tr('Revert {} from \n{}').format(tab.preferred_name, tab.config_path.as_posix()))
        self.tab_restore_defaults_button.setToolTip(
            tr('Remove {}\nand restore {} to application defaults').format(tab.config_path.as_posix(), tab.preferred_name))

    def reconfigure(self, config_list: List[VduControlsConfig]) -> None:
        for config in config_list:
            vdu_label = config.get_vdu_preferred_name()
            conf_key = ConfIni.get_path(config.config_name)
            if tabs_found := [tab for tab in self.editor_tab_list if tab.config_path == conf_key]:
                assert len(tabs_found) == 1
                tab = tabs_found[0]
            else:
                tab = SettingsEditorTab(self, config, self.change_callback, parent=self.tabs_widget)
                tab.save_all_clicked_qtsignal.connect(self.save_all)  # type: ignore
                self.tabs_widget.addTab(tab, vdu_label)
                self.editor_tab_list.append(tab)
            tab.set_preferred_name(vdu_label)
            self.tabs_widget.setTabText(self.tabs_widget.indexOf(tab), vdu_label)
            if tab == self.tabs_widget.currentWidget():
                self.update_tab_ops(tab)
            if config.file_path:
                self.tabs_widget.setTabToolTip(self.tabs_widget.indexOf(tab), config.file_path.as_posix())

    def cross_validate(self) -> int:
        labels_in_use = {'vdu_controls': 'vdu_controls globals'}
        for tab in self.editor_tab_list:
            if vdu_label := tab.ini_editable.get(*ConfOpt.VDU_NAME.conf_id, fallback=None):
                if existing_use := labels_in_use.get(vdu_label, None):
                    return MBox(MIcon.Critical, msg=tr("Cannot save <tt>{}</tt>").format(tab.config_path.name),
                                info=tr("Duplicate VDU label: <i>{}</i><hr/>Alter the label for {} or {} and try again.").format(
                                    vdu_label, tab.config_path.stem, existing_use),
                                buttons=MBtn.Close | MBtn.Discard, default=MBtn.Close).exec()
                else:
                    labels_in_use[vdu_label] = tab.config_path.stem
        return MBtn.Ok

    def save_all(self, warn_if_nothing_to_save: bool = True) -> int:
        what_changed: Dict[str, str] = {}
        try:
            nothing_to_save = True
            self.setEnabled(False)
            save_order = self.editor_tab_list[1:] + [self.editor_tab_list[0]]  # Main config last, it may cause a restart of the app
            for editor in save_order:
                if editor.is_unsaved():
                    nothing_to_save = False
                    if editor.save(what_changed=what_changed, warn_if_no_changes=False) == MBtn.Cancel:
                        return MBtn.Cancel
            if warn_if_nothing_to_save and nothing_to_save:
                if MBox(MIcon.Critical, msg=tr("Nothing needs saving. Do you wish to save anyway?"),
                        buttons=MBtn.Yes | MBtn.No, default=MBtn.No).exec() == MBtn.Yes:
                    for editor in save_order:
                        if editor.save(force=True, what_changed=what_changed, warn_if_no_changes=False) == MBtn.Cancel:
                            return MBtn.Cancel
        finally:
            self.setEnabled(True)
            if len(what_changed) > 0:
                self.change_callback(what_changed)
        return MBtn.Ok

    def closeEvent(self, event) -> None:
        if self.save_all(warn_if_nothing_to_save=False) == MBtn.Cancel:
            event.ignore()
        else:
            super().closeEvent(event)


class SettingsEditorTab(QWidget):
    """A tab corresponding to a settings file, generates UI widgets for each tab based on what's in the config. """
    save_all_clicked_qtsignal = pyqtSignal()

    def __init__(self, editor_dialog: SettingsDialog, vdu_config: VduControlsConfig, change_callback: Callable,
                 parent: QTabWidget) -> None:
        super().__init__(parent=parent)
        widget_map = {ConfType.BOOL: SettingsEditorBooleanWidget, ConfType.FLOAT: SettingsEditorFloatWidget,
                      ConfType.LONG_TEXT: SettingsEditorLongTextWidget, ConfType.TEXT: SettingsEditorTextWidget,
                      ConfType.CSV: SettingsEditorCsvWidget, ConfType.LOCATION: SettingsEditorLocationWidget,
                      ConfType.PATH: SettingsEditorPathWidget, }
        content = QWidget()
        content_layout = QVBoxLayout()
        content.setLayout(content_layout)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content)
        self.setLayout(widget_layout := QVBoxLayout())
        widget_layout.addWidget(scroll_area)

        self.change_callback = change_callback
        self.unsaved_changes_map: Dict[Tuple[str, str], str] = {}
        self.config_path = ConfIni.get_path(vdu_config.config_name)
        self.ini_before = vdu_config.ini_content
        self.ini_editable = self.ini_before.duplicate()
        self.field_list: List[SettingsEditorFieldBase] = []
        self.editor_dialog = editor_dialog
        self.preferred_name = vdu_config.get_vdu_preferred_name()

        def _field(widget: SettingsEditorFieldBase) -> QWidget:
            self.field_list.append(widget)
            return widget

        for section_name in self.ini_editable.data_sections():
            title = tr(section_name).replace('-', ' ')
            content_layout.addWidget(QLabel(f"<b>{title}</b>"))
            bool_count = 0
            booleans_grid: QGridLayout | None = None  # Only create when bool_count > 0
            grid_columns = 5  # booleans are counted and laid out according to grid_columns.
            for option_name in self.ini_editable[section_name]:
                try:
                    option_def = vdu_config.get_conf_option(section_name, option_name)
                    # If it's unknown, it's probably a boolean switch for a VCP code
                    if section_name != ConfSec.VDU_CONTROLS_GLOBALS or option_def != ConfOpt.UNKNOWN:
                        if option_def.conf_type == ConfType.BOOL:
                            if bool_count == 0:  # Need to create a grid now
                                booleans_grid = QGridLayout()
                                booleans_grid.setVerticalSpacing(0)
                                booleans_panel = QWidget()
                                booleans_panel.setLayout(booleans_grid)
                                content_layout.addWidget(booleans_panel)
                            booleans_grid.addWidget(
                                _field(
                                    SettingsEditorBooleanWidget(self, option_name, section_name,
                                                                option_def.help, option_def.related, option_def.requires)),
                                bool_count // grid_columns, bool_count % grid_columns)
                            bool_count += 1
                        else:
                            content_layout.addWidget(_field(widget_map[option_def.conf_type](self, option_name, section_name, option_def.help)))
                except ValueError:  # Probably an old no-longer-valid option, or a typo.
                    log_warning(f"Ignoring invalid option name {option_name} in {section_name}")

    def set_preferred_name(self, label_str):
        self.preferred_name = label_str

    def save(self, force: bool = False, what_changed: Dict[str, str] | None = None, warn_if_no_changes: bool = True) -> int:
        # what_changed is an output parameter, if passed, it will be updated with what has changed.
        if self.is_unsaved() or force:
            try:
                self.setEnabled(False)  # Saving may take a while, give some feedback by disabling and enabling when done
                answer = SettingsDialog.get_instance().cross_validate()
                if answer == MBtn.Ok:
                    msg = (tr('Update existing {}?') if self.config_path.exists() else tr("Create new {}?")).format(
                        self.config_path.as_posix())
                    answer = MBox(MIcon.Question, msg=msg, buttons=MBtn.Save | MBtn.Cancel | MBtn.Discard, default=MBtn.Save).exec()
                if answer == MBtn.Save:
                    message = tr("Saving {} ...").format(self.config_path.name)
                    self.editor_dialog.status_message(message, 0)
                    QApplication.processEvents()
                    self.ini_editable.save(self.config_path)
                    flag_qt_version_preference(self.ini_editable)
                    self.ini_before = self.ini_editable.duplicate()  # Saved ini becomes the new "before"
                    if what_changed is None:  # Not accumulating what has changed, implement change now.
                        self.change_callback(self.unsaved_changes_map)
                    else:  # Accumulating what has changed, just add to the dictionary.
                        what_changed.update(self.unsaved_changes_map)
                    self.unsaved_changes_map = {}
                    message1 = tr("Saved {}").format(self.config_path.name)
                    self.editor_dialog.status_message(message1, 3000)
                elif answer == MBtn.Discard:
                    self.revert_changes()
                return answer
            finally:
                self.setEnabled(True)
        elif warn_if_no_changes:
            MBox(MIcon.Critical, msg=tr('No unsaved changes for {}.').format(self.config_path.name), buttons=MBtn.Ok).exec()
        return MBtn.Cancel

    def reset(self) -> None:
        for field in self.field_list:
            field.reset()

    def revert_changes(self) -> None:
        if self.is_unsaved():
            self.editor_dialog.status_message(tr("Discarded changes to {}").format(self.config_path.name), 3000)
            self.ini_editable = self.ini_before.duplicate()  # Revert
        else:
            self.editor_dialog.status_message(tr("Nothing to discard").format(self.config_path.name), 3000)
        self.reset()

    def restore_application_defaults(self):
        if MBox(MIcon.Critical,
                msg=tr("Are you sure you want to restore {} to application defaults?").format(self.preferred_name),
                info=tr("The file {} will be renamed to {}.old").format(self.config_path.name, self.config_path.stem),
                buttons=MBtn.Yes | MBtn.No, default=MBtn.No).exec() == MBtn.No:
            return
        if self.config_path.exists():
            self.config_path.rename(Path(self.config_path.parent, self.config_path.stem + 'old'))
        self.change_callback(None)

    def is_unsaved(self) -> bool:
        if self.config_path.exists():
            self.unsaved_changes_map = self.ini_editable.diff(self.ini_before)
            return len(self.unsaved_changes_map) > 0
        self.unsaved_changes_map = {}
        return True


class SettingsEditorFieldBase(QWidget):
    def __init__(self, section_editor: SettingsEditorTab, option: str, section: str, tooltip: str) -> None:
        super().__init__()
        self.section_editor = section_editor
        self.section = section
        self.option = option
        self.tip_text = tooltip
        self.has_error = False
        self.setToolTip(tr(tooltip)) if tooltip != '' else None

    def translate_option(self) -> str:
        return translate_option(self.option)


class SettingsEditorBooleanWidget(SettingsEditorFieldBase):
    def __init__(self, section_editor: SettingsEditorTab, option: str, section: str,
                 tooltip: str, related: str, requires: str) -> None:
        super().__init__(section_editor, option, section, tooltip)
        self.setLayout(widget_layout := QHBoxLayout())
        # Squish up, save space, stay closer to parent label
        widget_layout.setContentsMargins(widget_layout.contentsMargins().left(), 0, widget_layout.contentsMargins().right(), 0)
        checkbox = QCheckBox(self.translate_option())
        checkbox.setChecked(section_editor.ini_editable.getboolean(section, option))

        def _toggled(is_checked: bool) -> None:
            section_editor.ini_editable[section][option] = 'yes' if is_checked else 'no'
            if related:
                MBox(MIcon.Information, msg=tr("You may also wish to set\n{}").format(tr(related)), buttons=MBtn.Ok).exec()
            if is_checked and requires:
                MBox(MIcon.Information, msg=tr("You will also need to set\n{}").format(tr(requires)), buttons=MBtn.Ok).exec()

        checkbox.toggled.connect(_toggled)
        widget_layout.addWidget(checkbox)
        self.checkbox = checkbox

    def reset(self) -> None:
        self.checkbox.setChecked(self.section_editor.ini_before.getboolean(self.section, self.option))


class SettingsEditorLineBase(SettingsEditorFieldBase):
    def __init__(self, section_editor: SettingsEditorTab, option: str, section: str, tooltip: str) -> None:
        super().__init__(section_editor, option, section, tooltip)
        self.editor_layout = QHBoxLayout()
        self.editor_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.setLayout(self.editor_layout)
        self.text_label = QLabel(self.translate_option())
        self.editor_layout.addWidget(self.text_label)
        self.text_input = QLineEdit()
        self.validator: QValidator | None = None
        self.valid_palette = self.text_input.palette()
        self.error_palette = self.text_input.palette()
        self.error_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.red)
        self.error_palette.setColor(QPalette.ColorRole.Window, Qt.GlobalColor.red)
        self.text_input.inputRejected.connect(partial(self.set_error_indication, True))
        self.text_input.textEdited.connect(partial(self.set_error_indication, False))
        self.text_input.editingFinished.connect(self.editing_finished)
        self.editor_layout.addWidget(self.text_input)

    def editing_finished(self) -> None:
        text = self.text_input.text()
        if self.validator is not None:
            self.has_error = self.validator.validate(text, 0)[0] != QValidator.State.Acceptable
            self.set_error_indication(self.has_error)
        if not self.has_error:
            internal_value = str(text)  # Why did I do this - is text not really a string?
            if not self.has_error:
                self.section_editor.ini_editable[self.section][self.option] = internal_value

    def set_error_indication(self, has_error: bool) -> None:
        self.has_error = has_error
        self.text_input.setPalette(self.error_palette if has_error else self.valid_palette)

    def reset(self) -> None:
        self.text_input.setText(self.section_editor.ini_before[self.section][self.option])
        self.editing_finished()


class SettingsEditorFloatWidget(SettingsEditorFieldBase):
    def __init__(self, section_editor: SettingsEditorTab, option: str, section: str, tooltip: str) -> None:
        super().__init__(section_editor, option, section, tooltip)
        self.setLayout(widget_layout := QHBoxLayout())
        widget_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.text_label = QLabel(self.translate_option())
        widget_layout.addWidget(self.text_label)
        self.spinbox = QDoubleSpinBox()
        self.spinbox.setRange(0.0, 4.0)  # TODO this should be looked up in the metadata
        self.spinbox.setSingleStep(0.1)
        try:
            value = float(section_editor.ini_editable[section][option])
        except ValueError:  # Just in case - rather not fall over
            value = 0.0
        self.spinbox.setValue(value)
        widget_layout.addWidget(self.spinbox)

        def _spinbox_value_changed() -> None:
            section_editor.ini_editable[section][option] = locale.delocalize(f"{self.spinbox.value():.2f}")

        self.spinbox.valueChanged.connect(_spinbox_value_changed)

    def reset(self) -> None:
        self.spinbox.setValue(float(self.section_editor.ini_before.get(self.section, self.option)))


class SettingsEditorCsvWidget(SettingsEditorLineBase):
    def __init__(self, section_editor: SettingsEditorTab, option: str, section: str, tooltip: str) -> None:
        super().__init__(section_editor, option, section, tooltip)
        # TODO - should probably also allow spaces as well as commas, but the regexp is getting a bit tricky?
        # Validator matches CSV of two digit hex or the empty string.
        self.validator = QRegularExpressionValidator(QRegularExpression(r"^([0-9a-fA-F]{2}([ \t]*,[ \t]*[0-9a-fA-F]{2})*)|$"))
        self.text_input.setText(section_editor.ini_editable[section][option])


class LatitudeLongitudeValidator(QRegularExpressionValidator):

    def __init__(self) -> None:
        super().__init__(QRegularExpression(r"^([+-]*[0-9.,]+[,;][+-]*[0-9.,]+)([,;]\w+)?|$",
                                            QRegularExpression.PatternOption.UseUnicodePropertiesOption))

    def validate(self, text: str | None, pos: int) -> Tuple[QValidator.State, str, int]:
        result = super().validate(text, pos)
        if result[0] == QValidator.State.Acceptable:
            if text:
                try:
                    lat, lon = [float(i) for i in text.split(',')[:2]]
                    if -90.0 <= lat <= 90.0:
                        if -180.0 <= lon <= 180.0:
                            return QValidator.State.Acceptable, text, pos
                    return QValidator.State.Invalid, text, pos
                except ValueError:
                    return QValidator.State.Intermediate, text, pos
        return result


class SettingsEditorLocationWidget(SettingsEditorLineBase):
    def __init__(self, section_editor: SettingsEditorTab, option: str, section: str, tooltip: str) -> None:
        super().__init__(section_editor, option, section, tooltip)
        self.text_input.setFixedWidth(npx(500))
        self.text_input.setMaximumWidth(npx(500))
        self.text_input.setMaxLength(250)
        self.validator = LatitudeLongitudeValidator()
        self.text_input.setText(section_editor.ini_editable[section][option])
        self.text_input.setToolTip(tr("Latitude,Longitude for solar elevation calculations."))

        def _detection_location() -> None:
            if data_csv := self.location_dialog():
                self.text_input.setText(data_csv)
                self.editing_finished()

        detect_location_button = StdButton(title=tr("Detect"), clicked=_detection_location,
                                           tip=tr("Detect location by querying this desktop's external IP address."))
        self.editor_layout.addWidget(detect_location_button)
        self.editor_layout.addStretch(1)

    def retrieve_ipinfo(self) -> Mapping:
        #  https://stackoverflow.com/a/55432323/609575
        from urllib.request import urlopen
        from json import load
        with urlopen(IP_ADDRESS_INFO_URL) as res:
            return load(res)

    def location_dialog(self) -> str | None:
        if MBox(MIcon.Question, msg=tr('Query {} to obtain information based on your IP-address?').format(IP_ADDRESS_INFO_URL),
                buttons=MBtn.Yes | MBtn.No).exec() == MBtn.Yes:
            try:
                ipinfo = self.retrieve_ipinfo()
                msg = f"{tr('Use the following info?')}\n" f"{ipinfo['loc']}\n" + \
                      ','.join([ipinfo[key] for key in ('city', 'region', 'country') if key in ipinfo])
                details = f"Queried {IP_ADDRESS_INFO_URL}\n" + \
                          '\n'.join([f"{name}: {value}" for name, value in ipinfo.items()])
                if MBox(MIcon.Information, msg=msg, details=details, buttons=MBtn.Yes | MBtn.No).exec() == MBtn.Yes:
                    data = ipinfo['loc']
                    for key in ('city', 'region', 'country'): # Get location name for weather lookups.
                        if key in ipinfo:
                            data = data + ',' + ipinfo[key]
                            break
                    return data
            except (URLError, KeyError) as e:
                MBox(MIcon.Critical, msg=tr("Failed to obtain info from {}: {}").format(IP_ADDRESS_INFO_URL, e)).exec()
        return ''


class SettingsEditorLongTextWidget(SettingsEditorFieldBase):
    def __init__(self, section_editor: SettingsEditorTab, option: str, section: str, tooltip: str) -> None:
        super().__init__(section_editor, option, section, tooltip)
        layout = QVBoxLayout()
        self.setLayout(layout)
        text_label = QLabel(self.translate_option())
        layout.addWidget(text_label)
        text_editor = QPlainTextEdit(section_editor.ini_editable[section][option])

        def _text_changed() -> None:
            section_editor.ini_editable[section][option] = text_editor.toPlainText().strip()

        text_editor.textChanged.connect(_text_changed)
        layout.addWidget(text_editor)
        self.text_editor = text_editor

    def reset(self) -> None:
        self.text_editor.setPlainText(self.section_editor.ini_before[self.section][self.option])


class SettingsEditorTextWidget(SettingsEditorLongTextWidget):

    def __init__(self, section_editor: SettingsEditorTab, option: str, section: str, tooltip: str) -> None:
        super().__init__(section_editor, option, section, tooltip)
        self.setMaximumHeight(native_font_height(scaled=3))


class SettingsEditorPathValidator(QValidator):

    def validate(self, text, pos):
        if text.strip():
            if not Path(text).exists() or not Path(text).is_file():
                MBox(MIcon.Critical, msg=tr("The selected file does not exist or is not an ordinary file.")).exec()
                return QValidator.State.Invalid, text, pos
            elif not os.access(text, os.X_OK):
                MBox(MIcon.Critical, msg=tr("The selected file lacks execute permission.")).exec()
                return QValidator.State.Invalid, text, pos
        return QValidator.State.Acceptable, text, pos


class SettingsEditorPathWidget(SettingsEditorLineBase):

    def __init__(self, section_editor: SettingsEditorTab, option: str, section: str, tooltip: str) -> None:
        super().__init__(section_editor, option, section, tooltip)
        self.text_input.setText(section_editor.ini_editable[section][option])

        def _choose_emulator(index: int) -> None:
            current_path = self.text_input.text()
            new_path = FasterFileDialog.getOpenFileName(
                self, tr("Select: {}").format(tr(self.text_label.text())), current_path,
                qdir_filter=QDir.Filter.Files | QDir.Filter.Readable | QDir.Filter.Executable)[0]
            self.text_input.setText(new_path)
            self.editing_finished()

        self.editor_layout.addWidget(StdButton(si(self, StdPixmap.SP_DriveFDIcon), clicked =_choose_emulator))
        self.validator = SettingsEditorPathValidator()


    def editing_finished(self) -> None:
        super().editing_finished()
        if not self.has_error and self.text_input.text().strip() != '':
            if self.section_editor.ini_editable[self.section][self.option] != self.section_editor.ini_before[self.section][
                self.option]:
                mb = MBox(MIcon.Information,
                          msg="If you've developed a <i>ddcutil-emulator</i> for integrating a non-DDC laptop-panels, "
                              "please consider contributing it to the <b>vdu_controls</b> project."
                              "<br/>_______________________________________________________________________________________</br>",
                          info="Submit feedback and contributions to<br/> "
                               "<a href='https://github.com/digitaltrails/vdu_controls/issues/44'>"
                               "https://github.com/digitaltrails/vdu_controls/issues/44</a><br/>"
                               "or by email to <a href='mailto:michael@actrix.gen.nz?subject=ddcutil-emulator'>"
                               "michael@actrix.gen.nz</a>.", buttons=MBtn.Close)
                mb.setTextFormat(Qt.TextFormat.AutoText)
                mb.exec()


class VduException(Exception):

    def __init__(self, vdu_description=None, vcp_code=None, exception=None, operation=None) -> None:
        super().__init__()
        self.vdu_description = vdu_description
        self.attr_id = vcp_code
        self.cause = exception
        self.operation = operation

    def is_display_not_found_error(self) -> bool:
        return self.cause is not None and isinstance(self.cause, DdcutilDisplayNotFound)

    def __str__(self) -> str:
        return f"VduException: {self.vdu_description} op={self.operation} attr={self.attr_id} {self.cause}"


class VduControlBase(QWidget):
    """Base GUI control for a DDC attribute."""

    _refresh_ui_view_in_gui_thread_qtsignal = pyqtSignal()

    def __init__(self, controller: VduController, vcp_capability: VcpCapability) -> None:
        """Construct the slider control and initialize its values from the VDU."""
        super().__init__()
        self.controller = controller
        self.vcp_capability = vcp_capability
        self.current_value: int | None = None
        # Using Qt signals to ensure GUI activity occurs in the GUI thread (this thread).
        self._refresh_ui_view_in_gui_thread_qtsignal.connect(self._refresh_ui_view_task)
        self.refresh_ui_only = False
        self.debug = False  # Local debug switch because this is very noisy and only needed rarely.

    def update_from_vdu(self, vcp_value: VcpValue):  # Used for updating from the results of get_attributes() -> List[VcpValue]
        if self.vcp_capability.vcp_type == SIMPLE_NON_CONTINUOUS_TYPE:  # Overrides metadata value-type, enforce simple
            self.current_value = 0x00ff & vcp_value.current  # Mask off high byte
        else:
            self.current_value = vcp_value.current
        self.refresh_ui_view()

    def set_value(self, new_value: int, origin: VcpOrigin = VcpOrigin.NORMAL) -> None:  # Used by controllers to alter physical VDU
        if self.controller.values_cache[self.vcp_capability.vcp_code] != new_value:
            self.controller.set_vcp_value(self.vcp_capability.vcp_code, new_value, origin)
            self.current_value = new_value
        self.refresh_ui_view()

    def ui_change_vdu_attribute(self, new_value: int) -> None:  # Used by UI controls to change values
        log_info("ui_change_vdu_attribute") if self.debug else None
        if self.refresh_ui_only:  # Called from a GUI control when it was already responding to a vdu attribute change.
            log_info(f"Skip change {self.refresh_ui_only=}") if self.debug else None
            return  # Avoid repeating a setvcp by skipping the physical change
        self.controller.set_vcp_value_asynchronously(self.vcp_capability.vcp_code, new_value, VcpOrigin.NORMAL)

    def get_current_text_value(self) -> str | None:  # Return text in correct base: continuous->base10 non-continuous->base16
        assert False, "subclass failed to implement get_current_text_value"

    def refresh_ui_view_implementation(self):  # Subclasses to implement
        assert False, "subclass failed to implement refresh_ui_view_implementation"

    def refresh_ui_view(self) -> None:
        if not is_running_in_gui_thread():
            self._refresh_ui_view_in_gui_thread_qtsignal.emit()
        else:
            self._refresh_ui_view_task()

    def _refresh_ui_view_task(self):
        try:
            self.refresh_ui_only = True  # Stop slider/widget changes from re-propagating changes to the VDU
            self.refresh_ui_view_implementation()
            QApplication.sendPostedEvents(self, 0)  # Flush any change events before resetting the flag
            QApplication.processEvents()  # Force the flushed events to be processed now
        finally:
            self.refresh_ui_only = False


class VduControlSlider(VduControlBase):
    """GUI control for a DDC continuously variable attribute. A compound widget with icon, slider, and text-field."""

    def __init__(self, controller: VduController, vcp_capability: VcpCapability) -> None:
        """Construct the slider control and initialize its values from the VDU."""
        super().__init__(controller, vcp_capability)
        layout = QHBoxLayout()
        self.setLayout(layout)
        self.svg_icon: QSvgWidget | None = None
        if (vcp_capability.vcp_code in SUPPORTED_VCP_BY_CODE
                and SUPPORTED_VCP_BY_CODE[vcp_capability.vcp_code].icon_source is not None):
            svg_icon = QSvgWidget()
            svg_icon.load(handle_theme(SUPPORTED_VCP_BY_CODE[vcp_capability.vcp_code].icon_source, polychrome_light_or_dark()))
            svg_icon.setFixedSize(native_font_height(scaled=1.8), native_font_height(scaled=1.8))
            svg_icon.setToolTip(vcp_capability.translated_name())
            self.svg_icon = svg_icon
            layout.addWidget(svg_icon)
        else:
            layout.addWidget(QLabel(tr(vcp_capability.name)))

        self.slider = slider = ClickableSlider()
        slider.setMinimumWidth(npx(200))
        self.range_restriction = vcp_capability.values
        if self.range_restriction and len(self.range_restriction) >= 2:  # Would > 2 be an error - don't worry about it
            slider.setRange(int(self.range_restriction[1]), int(self.range_restriction[2]))
        slider.setSingleStep(1)
        slider.setPageStep(10)
        slider.setTickInterval(10)
        slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        slider.setOrientation(Qt.Orientation.Horizontal)  # type: ignore
        slider.setTracking(False)  # Don't rewrite the ddc value too often - not sure of the implications
        layout.addWidget(slider)

        self.spinbox = QSpinBox()
        self.spinbox.setLineEdit(LineEditAll())
        if self.range_restriction and len(self.range_restriction) >= 2:  # >2 would be an error, but not serious
            int_min, int_max = int(self.range_restriction[1]), int(self.range_restriction[2])
            self.spinbox.setRange(int_min, int_max)
            self.slider.setRange(int_min, int_max)

        self.slider.setTracking(True)
        self.slider.valueChanged.connect(self.spinbox.setValue)
        self.spinbox.valueChanged.connect(self.slider.setValue)

        self.spinbox.setValue(slider.value())
        layout.addWidget(self.spinbox)

        def _slider_changed(value: int) -> None:
            self.current_value = value
            self.ui_change_vdu_attribute(value)

        slider.valueChanged.connect(_slider_changed)

    def update_from_vdu(self, vcp_value: VcpValue):
        if not self.range_restriction:
            int_max = int(vcp_value.max)
            self.spinbox.setRange(0, int_max)
            self.slider.setRange(0, int_max)
        super().update_from_vdu(vcp_value)

    def get_current_text_value(self) -> str | None:
        return str(self.current_value) if self.current_value is not None else None

    def refresh_ui_view_implementation(self) -> None:
        if self.current_value is not None:  # Copy the internally cached current value onto the GUI view.
            self.slider.setValue(clamp(int(self.current_value), self.slider.minimum(), self.slider.maximum()))

    def event(self, event: QEvent | None) -> bool:
        if event and event.type() == QEvent.Type.PaletteChange:  # PalletChange happens after the new style sheet is in use.
            icon_source = SUPPORTED_VCP_BY_CODE[self.vcp_capability.vcp_code].icon_source
            if icon_source is not None:
                assert self.svg_icon is not None  # Because it must have been loaded from source earlier
                self.svg_icon.load(handle_theme(icon_source, polychrome_light_or_dark()))
        return super().event(event)


class VduControlComboBox(VduControlBase):
    """GUI control for a DDC non-continuously variable attribute, one that has a list of choices."""

    def __init__(self, controller: VduController, vcp_capability: VcpCapability) -> None:
        super().__init__(controller, vcp_capability)
        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel(self.translate_label(vcp_capability.name)))
        self.combo_box = combo_box = QComboBox()
        layout.addWidget(combo_box)

        self.keys = []
        for value, desc in self.vcp_capability.values:
            self.keys.append(value)
            combo_box.addItem(self.translate_label(desc), value)

        def _index_changed(_: int) -> None:
            self.current_value = int(self.combo_box.currentData(), 16)
            if self.validate_value() >= 0:
                self.ui_change_vdu_attribute(self.current_value)

        combo_box.currentIndexChanged.connect(_index_changed)

    def translate_label(self, source: str) -> str:
        canonical = source.lower()
        maybe = tr(canonical)
        result = maybe if maybe != canonical else source
        return ' '.join(w[:1].upper() + w[1:] for w in result.split())  # Default to capitalized version of each word

    def get_current_text_value(self) -> str | None:
        return f"{self.current_value:02X}" if self.current_value is not None else None

    def refresh_ui_view_implementation(self) -> None:
        """Copy the internally cached current value onto the GUI view."""
        value_index = self.validate_value()
        if value_index >= 0:
            self.combo_box.setCurrentIndex(value_index)

    def validate_value(self) -> int:
        value = self.get_current_text_value()
        if value is None:
            return -1
        if value not in self.keys:
            self.keys.append(self.current_value)
            self.combo_box.addItem('UNKNOWN-' + value, self.current_value)
            self.combo_box.model().item(self.combo_box.count() - 1).setEnabled(False)
            MBox(MIcon.Critical,
                 msg=tr("Display {vnum} {vdesc} feature {code} '({cdesc})' has an undefined value '{value}'. "
                        "Valid values are {valid}.").format(
                     vdesc=self.controller.get_vdu_preferred_name(), vnum=self.controller.vdu_number,
                     code=self.vcp_capability.vcp_code, cdesc=self.vcp_capability.name,
                     value=value, valid=self.keys),
                 info=tr('If you want to extend the set of permitted values, you can edit the metadata '
                         'for {} in the settings panel.  For more details see the man page concerning '
                         'VDU/VDU-model config files.').format(self.controller.get_vdu_preferred_name())).exec()
            return -1
        return self.keys.index(value)


class VduControlPanel(QWidget):
    """Widget that contains all the controls for a single VDU (monitor/display)."""

    def __init__(self, controller: VduController, vdu_exception_handler: Callable) -> None:
        super().__init__()
        layout = QVBoxLayout()
        self.label = QLabel(tr('Monitor {}: {}').format(controller.vdu_number, controller.get_vdu_preferred_name()))
        layout.addWidget(self.label)
        self.controller: VduController = controller
        self.vcp_controls: List[VduControlBase] = []
        self.vdu_exception_handler = vdu_exception_handler

        for capability in controller.enabled_capabilities:
            control = None
            if capability.vcp_type == CONTINUOUS_TYPE:
                try:
                    control = VduControlSlider(controller, capability)
                except ValueError as valueError:
                    MBox(MIcon.Critical, msg=str(valueError)).exec()
            elif capability.vcp_type in (SIMPLE_NON_CONTINUOUS_TYPE, COMPLEX_NON_CONTINUOUS_TYPE):
                try:
                    control = VduControlComboBox(controller, capability)
                except ValueError as valueError:
                    MBox(MIcon.Critical, msg=valueError.args[0],
                         info=tr('If you want to extend the set of permitted values, see the man page concerning '
                                 'VDU/VDU-model config files.').format(capability.vcp_code, capability.name)).exec()
            else:
                raise TypeError(f'No GUI support for VCP type {capability.vcp_type} for vcp_code {capability.vcp_code}')
            if control is not None:
                layout.addWidget(control)
                self.vcp_controls.append(control)

        if len(self.vcp_controls) != 0:
            self.setLayout(layout)

        self.update_stats()
        try:
            self.refresh_from_vdu()
        except VduException as e:
            self.vdu_exception_handler(e)

    def get_control(self, vcp_code: str) -> VduControlBase | None:
        return next((c for c in self.vcp_controls if c.vcp_capability.vcp_code == vcp_code), None)

    def refresh_from_vdu(self) -> None:
        """Tell the control widgets to get fresh VDU data (maybe called from a task thread, so no GUI operations here)."""
        if values := self.controller.get_vcp_values([control.vcp_capability.vcp_code for control in self.vcp_controls]):
            for control, value in zip(self.vcp_controls, values):
                control.update_from_vdu(value)

    def number_of_controls(self) -> int:
        """Return the number of VDU controls.  Might be zero if initialization discovered no controllable attributes."""
        return len(self.vcp_controls)

    def is_preset_active(self, preset: Preset) -> bool:
        vdu_section = self.controller.vdu_stable_id
        if vdu_section == proper_name(preset.name):
            return False  # ignore VDU initialization-presets
        count = 0
        preset_ini = preset.preset_ini
        for control in self.vcp_controls:
            if control.vcp_capability.property_name() in preset_ini[vdu_section]:
                # Prior to version vdu_controls 1.21 we stored lower, but ddcutil expects upper
                if control.get_current_text_value() != preset_ini[vdu_section][control.vcp_capability.property_name()].upper():
                    return False  # immediately fail if even one value differs
                count += 1
        return count > 0  # true unless no values were tested.

    def update_stats(self):
        name, sid = self.controller.get_vdu_preferred_name(), self.controller.vdu_stable_id
        self.label.setToolTip(tr("{}\nSet-VCP writes: {}").format(sid if id == name else f"{name}\n({sid})",
                                                                  self.controller.get_write_count()))


class Preset:
    """A config/ini file of user-created settings presets - such as Sunny, Cloudy, Night, etc."""

    def __init__(self, name) -> None:
        self.name = name
        self.path = ConfIni.get_path(proper_name('Preset', name))
        self.preset_ini = ConfIni()
        self.scheduler_job: SchedulerJob | None = None
        self.schedule_status = PresetScheduleStatus.UNSCHEDULED
        self.elevation_time_today: datetime | None = None
        self.in_transition_step = 0

    def get_title_name(self) -> str:
        return self.name

    def get_icon_path(self) -> Path | None:
        if self.preset_ini.has_section("preset"):
            path_text = self.preset_ini.get("preset", "icon", fallback=None)
            return Path(path_text) if path_text else None
        return None

    def create_icon(self, theme_type: ThemeType = ThemeType.UNDECIDED) -> QIcon:
        icon_path = self.get_icon_path()
        if theme_type == ThemeType.UNDECIDED:
            theme_type = polychrome_light_or_dark()
        if icon_path and icon_path.exists():
            return create_icon_from_path(icon_path, theme_type)
        else:
            # Only room for two letters at most - use first and last if more than one word.
            full_acronym = [word[0] for word in re.split(r"[ _-]", self.name) if word != '']
            abbreviation = full_acronym[0] if len(full_acronym) == 1 else full_acronym[0] + full_acronym[-1]
            return create_icon_from_text(abbreviation, theme_type)

    def load(self) -> ConfIni:
        if self.path.exists():
            log_debug(f"Reading preset file '{self.path.as_posix()}'") if log_debug_enabled else None
            preset_text = Path(self.path).read_text()
            preset_ini = ConfIni()
            preset_ini.read_string(preset_text)
        else:
            preset_ini = ConfIni()
        self.preset_ini = preset_ini
        return self.preset_ini

    def save(self) -> None:
        self.preset_ini.save(self.path)

    def delete(self) -> None:
        log_info(f"Deleting preset file '{self.path.as_posix()}'")
        self.remove_elevation_trigger()
        if self.path.exists():
            os.remove(self.path.as_posix())

    def get_brightness(self, vdu_stable_id: VduStableId) -> int:
        if vdu_stable_id in self.preset_ini:
            return self.preset_ini.getint(vdu_stable_id, 'brightness', fallback=-1)
        return -1

    def get_vdu_sids(self):
        return [section_name for section_name in self.preset_ini.data_sections() if section_name != 'preset']

    def get_solar_elevation(self) -> SolarElevationKey | None:
        if elevation_spec := self.preset_ini.get('preset', 'solar-elevation', fallback=None):
            solar_elevation = parse_solar_elevation_ini_text(elevation_spec)
            return solar_elevation
        return None

    def get_at_time(self) -> datetime | None:
        if at_time_spec := self.preset_ini.get('preset', 'at-time', fallback=None):
            return datetime.combine(datetime.today(), datetime.strptime(at_time_spec, "%H:%M").time()).astimezone()
        return None

    def get_solar_elevation_abbreviation(self) -> str:
        if elevation := self.get_solar_elevation():
            result = format_solar_elevation_abbreviation(elevation)
            if self.elevation_time_today:
                result += f" {TIME_CLOCK_SYMBOL} {self.elevation_time_today.strftime('%H:%M')}"
            else:
                # Not possible today - sun doesn't get that high
                result += ' ' + TOO_HIGH_SYMBOL
            if self.get_weather_restriction_filename() is not None:
                result += ' ' + WEATHER_RESTRICTION_SYMBOL
            result += ' ' + self.schedule_status.symbol()
            return result
        if at_time := self.get_at_time():
            return f" {TIME_CLOCK_SYMBOL} {at_time.strftime('%H:%M')} " + self.schedule_status.symbol()
        return ''

    def get_schedule_description(self) -> str:
        if not ScheduleWorker.is_running():
            return tr("(Schedule is disabled in Settings)")
        result = suffix = basic_desc = weather_suffix = ''
        if elevation := self.get_solar_elevation():
            basic_desc = SUN_SYMBOL + " " + format_solar_elevation_description(elevation)
            weather_fn = self.get_weather_restriction_filename()
            weather_suffix = tr(" (subject to {} weather)").format(
                Path(weather_fn).stem.replace('_', ' ')) if weather_fn is not None else ''
            if at_time := self.elevation_time_today:
                suffix = ''
            elif ScheduleWorker.is_running():
                suffix = tr("the sun does not rise this high today")
        elif at_time := self.get_at_time():
            basic_desc = TIME_CLOCK_SYMBOL
        # This might not work too well in translation - rethink?
        if at_time:
            if self.scheduler_job and self.scheduler_job.remaining_time() > 0:
                template = tr("{} later today at {}") + weather_suffix
            elif at_time < zoned_now():
                template = tr("{} earlier today at {}") + weather_suffix + f" ({tr(self.schedule_status.description())})"
            else:
                template = tr("{} suspended for {}")
            result = template.format(basic_desc, f"{at_time.replace(second=0, microsecond=0):%H:%M}")
        result = result + ' ' + suffix
        return result

    def get_daylight_factor(self) -> float | None:
        if self.preset_ini.get('preset', 'daylight-factor', fallback=None):
            return self.preset_ini.getfloat('preset', 'daylight-factor', fallback=None)
        return None

    def get_transition_type(self) -> PresetTransitionFlag:
        return parse_transition_type(self.preset_ini.get('preset', 'transition-type', fallback="NONE"))

    def get_step_interval_seconds(self) -> int:
        return self.preset_ini.getint('preset', 'transition-step-interval-seconds', fallback=0)

    def schedule(self, when_today: datetime, run_action: Callable, skip_action: Callable | None = None, overdue: bool = False):
        self.scheduler_job = SchedulerJob(when_today, SchedulerJobType.RESTORE_PRESET, partial(run_action, self),
                                          partial(skip_action, self) if skip_action else None)
        if not overdue:
            self.elevation_time_today = when_today
            self.schedule_status = PresetScheduleStatus.SCHEDULED
        log_info(f"Scheduled preset '{self.name}' for {when_today} in "
                 f"{round(self.scheduler_job.remaining_time() / 60)} minutes {self.get_solar_elevation()} {overdue=}")

    def remove_elevation_trigger(self, quietly: bool = False) -> None:
        if self.scheduler_job:
            log_info(f"Preset timer and schedule status cleared for '{self.name}'") if not quietly else None
            self.scheduler_job.dequeue()
            self.scheduler_job = None
        if self.elevation_time_today is not None:
            self.elevation_time_today = None
        self.schedule_status = PresetScheduleStatus.UNSCHEDULED

    def toggle_timer(self) -> None:
        if self.elevation_time_today and self.elevation_time_today > zoned_now():
            if self.scheduler_job is not None:
                if self.scheduler_job.remaining_time() > 0:
                    log_info(f"Preset scheduled timer cleared for '{self.name}'")
                    self.scheduler_job.dequeue()
                    self.schedule_status = PresetScheduleStatus.SUSPENDED
                else:
                    log_info(f"Preset scheduled timer restored for '{self.name}'")
                    self.scheduler_job.requeue()
                    self.schedule_status = PresetScheduleStatus.SCHEDULED

    def is_weather_dependent(self) -> bool:
        return self.get_weather_restriction_filename() is not None

    def check_weather(self, weather: WeatherQuery) -> bool:
        weather_restriction_filename = self.get_weather_restriction_filename()
        if weather.weather_code is None or weather_restriction_filename is None:
            return True
        path = Path(weather_restriction_filename)
        if not path.exists():
            log_error(f"Preset '{self.name}' missing weather requirements file: {weather_restriction_filename}")
            return True
        with open(path, encoding="utf-8") as weather_file:
            code_list = weather_file.readlines()
            for code_line in code_list:
                parts = code_line.split()
                if parts and weather.weather_code.strip() == parts[0]:
                    log_info(f"Preset '{self.name}' met {path.name} requirements. Current weather is: "
                             f"{weather.area_name} {weather.weather_code} {weather.weather_desc}")
                    return True
        log_info(f"Preset '{self.name}' failed {path.name} requirements. Current weather is: "
                 f"{weather.area_name} {weather.weather_code} {weather.weather_desc}")
        return False

    def get_weather_restriction_filename(self) -> str | None:
        weather_restriction_filename = \
            self.preset_ini.get('preset', 'solar-elevation-weather-restriction', fallback=None)
        return weather_restriction_filename


class ContextMenu(QMenu):
    PRESET_NAME_PROP = 'preset_name'
    PRESET_SHORTCUT_PROP = 'preset_shortcut'
    BUSY_DISABLE_PROP = 'busy_disable'
    ALT = 'Alt+{}'

    def __init__(self, app_controller: VduAppController, main_window_action, about_action, help_action, gray_scale_action,
                 lux_auto_action, lux_check_action, lux_meter_action, settings_action, presets_dialog_action, refresh_action,
                 quit_action, hide_shortcuts: bool, parent: QWidget) -> None:
        super().__init__(parent=parent)
        self.app_controller = app_controller
        self.reserved_shortcuts: List[str] = []
        self.hide_shortcuts = hide_shortcuts
        if main_window_action is not None:
            self._add_action(StdPixmap.SP_ComputerIcon, tr('&Control Panel'), main_window_action)
            self.addSeparator()
        self._add_action(StdPixmap.SP_ComputerIcon, tr('&Presets'), presets_dialog_action)
        self.presets_separator = self.addSeparator()  # Important for finding where to add a preset
        self._add_action(StdPixmap.SP_ComputerIcon, tr('&Grey Scale'), gray_scale_action)
        if lux_meter_action is not None:
            self.lux_auto_action = self._add_action(StdPixmap.SP_ComputerIcon, tr('&Auto/Manual'), lux_auto_action)
            self.lux_check_action = self._add_action(StdPixmap.SP_MediaSeekForward, tr('Lighting &Check'), lux_check_action)
            self._add_action(StdPixmap.SP_ComputerIcon, tr('&Light-Metering'), lux_meter_action)
        self._add_action(StdPixmap.SP_ComputerIcon, tr('&Settings'), settings_action, 'Ctrl+Shift+,')
        self._add_action(StdPixmap.SP_BrowserReload, tr('&Refresh'), refresh_action, QKeySequence.StandardKey.Refresh).setProperty(
            ContextMenu.BUSY_DISABLE_PROP, QVariant(True))
        self._add_action(StdPixmap.SP_MessageBoxInformation, tr('Abou&t'), about_action)
        self._add_action(StdPixmap.SP_DialogHelpButton, tr('&Help'), help_action, QKeySequence.StandardKey.HelpContents)
        self._add_action(StdPixmap.SP_DialogCloseButton, tr('&Quit'), quit_action, QKeySequence.StandardKey.Quit)
        self.reserved_shortcuts_basic = self.reserved_shortcuts.copy()
        self.auto_lux_icon: QIcon | None = None

    def _add_action(self, qt_icon_number: int, text: str, func: Callable, extra_shortcut: str | None = None) -> QAction:
        action = self.addAction(si(self, qt_icon_number), text, func)
        assert action is not None
        amp_pos =  text.find('&')
        shortcut_letter = text[amp_pos + 1].upper() if (0 <= amp_pos < len(text) - 1) else None
        if shortcut_letter is not None:
            log_debug(f"Reserve shortcut '{shortcut_letter}'") if log_debug_enabled else None
            if shortcut_letter in self.reserved_shortcuts:
                log_error(f"{shortcut_letter=} already in in {self.reserved_shortcuts=}")
            else:
                self.reserved_shortcuts.append(shortcut_letter)
                action.setShortcuts(self.shortcut_list(ContextMenu.ALT.format(shortcut_letter.upper()), extra_shortcut))
                action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        return action

    def get_preset_menu_action(self, name: str) -> QAction | None:
        for action in self.actions():
            if action.property(ContextMenu.PRESET_NAME_PROP) == name:
                return action
        return None

    def insert_preset_menu_action(self, preset: Preset, issue_update: bool = True) -> None:

        def _menu_restore_preset() -> None:
            self.app_controller.restore_named_preset(self.sender().property(ContextMenu.PRESET_NAME_PROP))

        assert preset.name
        shortcut = self.allocate_preset_shortcut(preset.name)
        action_name = shortcut.annotated_word if shortcut else preset.name
        action = self.addAction(preset.create_icon(), action_name, _menu_restore_preset)  # Have to add it, then move/insert it.
        assert action
        self.insertAction(self.presets_separator, action)  # Insert before the presets_separator
        action.setProperty(ContextMenu.BUSY_DISABLE_PROP, QVariant(True))
        action.setProperty(ContextMenu.PRESET_NAME_PROP, preset.name)
        if shortcut:
            action.setProperty(ContextMenu.PRESET_SHORTCUT_PROP, shortcut)
            action.setShortcuts(self.shortcut_list(ContextMenu.ALT.format(shortcut.letter.upper())))
            action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        else:
            log_warning(f"Failed to allocate shortcut for {preset.name} reserved shortcuts={self.reserved_shortcuts}")
        self.update() if issue_update else None

    def remove_preset_menu_action(self, name: str) -> None:
        if menu_action := self.get_preset_menu_action(name):
            shortcut = menu_action.property(ContextMenu.PRESET_SHORTCUT_PROP)
            if shortcut and shortcut in self.reserved_shortcuts:
                self.reserved_shortcuts.remove(shortcut.letter)
            self.removeAction(menu_action)
            self.update()

    def refresh_preset_menu(self, palette_change: bool = False, reorder: bool = False) -> None:
        changed = 0
        if reorder:  # Remove them all to get them reinserted, icons updated, names updated, etc.
            self.reserved_shortcuts = self.reserved_shortcuts_basic.copy()  # Reset shortcuts
            for action in self.actions():
                self.removeAction(action) if action.property(ContextMenu.PRESET_NAME_PROP) is not None else None
        for name, preset in self.app_controller.preset_controller.find_presets_map().items():
            menu_action = self.get_preset_menu_action(name)
            if menu_action is None or not menu_action.property(ContextMenu.PRESET_NAME_PROP):
                self.insert_preset_menu_action(preset, False)
                changed += 1
            elif palette_change:  # Must redraw icons in case desktop theme changed between light/dark.
                menu_action.setIcon(preset.create_icon())
                changed += 1
        self.update() if changed else None

    def indicate_preset_active(self, preset: Preset | None) -> None:
        changed = 0
        for action in self.actions():
            if action_preset_name := action.property(ContextMenu.PRESET_NAME_PROP):  # Mark active preset or un-mark previous active
                shortcut = action.property(ContextMenu.PRESET_SHORTCUT_PROP)
                suffix = (' ' + MENU_ACTIVE_PRESET_SYMBOL) if preset is not None and preset.name == action_preset_name else ''
                new_text = (shortcut.annotated_word if shortcut else action_preset_name) + suffix
                if new_text != action.text():
                    action.setText(new_text)
                    changed += 1
        self.update() if changed else None

    def indicate_busy(self, is_busy: bool = True) -> None:
        changed = 0
        for action in self.actions():
            if action.property(ContextMenu.BUSY_DISABLE_PROP):
                if (is_busy and action.isEnabled()) or (not is_busy and not action.isEnabled()):
                    action.setDisabled(is_busy)
                    changed += 1
        self.update() if changed else None

    def update_lux_auto_icon(self, icon: QIcon) -> None:
        if self.auto_lux_icon != icon:
            self.auto_lux_icon = icon
            self.lux_auto_action.setIcon(icon)
            self.update()

    def allocate_preset_shortcut(self, word: str) -> Shortcut | None:
        for letter in list(word):
            upper_letter = letter.upper()
            if upper_letter not in self.reserved_shortcuts:
                self.reserved_shortcuts.append(upper_letter)
                return Shortcut(letter=upper_letter, annotated_word=word[:word.index(letter)] + '&' + word[word.index(letter):])
        return None

    def shortcut_list(self, primary: str | QKeySequence, extra: str | QKeySequence | None = None) -> List[str | QKeySequence]:
        shortcuts = [primary] + ([extra] if extra else [])
        return ([''] + shortcuts) if self.hide_shortcuts else shortcuts  # Empty string causes shortcuts to be hidden.


class ToolButton(QToolButton):

    def __init__(self, svg_source: bytes, tip: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        if tip is not None:
            self.setToolTip(tip)
        self.svg_source = svg_source
        self.refresh_icon()

    def refresh_icon(self, svg_source: bytes | None = None) -> None:  # may refresh the theme (coloring light/dark) of the icon
        if svg_source is not None:  # Either a new icon or if None just a light/dark theme refresh
            self.svg_source = svg_source
        self.setIcon(create_icon_from_svg_bytes(self.svg_source))  # this may alter the SVG for light/dark theme


class VduPanelBottomToolBar(QToolBar):

    def __init__(self, tool_buttons: List[ToolButton], app_context_menu: ContextMenu, parent: VduControlsMainPanel) -> None:
        super().__init__(parent=parent)
        self.preset_edit_target: Preset | None = None
        self.tool_buttons = tool_buttons
        for button in self.tool_buttons:
            self.addWidget(button)
        self.setIconSize(QSize(native_font_height(), native_font_height()))
        self.progress_bar: QProgressBar | None = None
        self.status_area = QStatusBar()
        self.addWidget(self.status_area)
        self.menu_button = ToolButton(MENU_ICON_SOURCE, tr("Context and Preset Menu"), self)
        self.menu_button.setMenu(app_context_menu)
        self.menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.preset_action = self.addAction(QIcon(), "")
        assert self.preset_action
        self.preset_action.setVisible(False)

        def edit_current_preset():
            parent.main_controller.show_presets_dialog(self.preset_edit_target)

        self.preset_action.triggered.connect(edit_current_preset)
        self.addWidget(self.menu_button)
        self.installEventFilter(self)

    def eventFilter(self, target: QObject | None, event: QEvent | None) -> bool:
        # PalletChange happens after the new style sheet is in use.
        if event and event.type() == QEvent.Type.PaletteChange:
            for button in self.tool_buttons:
                button.refresh_icon()
            self.menu_button.refresh_icon()
        return super().eventFilter(target, event)

    def indicate_busy(self, is_busy: bool = True) -> None:
        if is_busy and self.progress_bar is None:
            self.status_area.clearMessage()
            self.progress_bar = QProgressBar(self)
            self.progress_bar.setTextVisible(False)  # Disable text percentage label on the spinner progress-bar
            self.progress_bar.setRange(0, 0)  # 0,0 causes the progress bar to pulsate left/right - used as a busy spinner.
            self.status_area.addWidget(self.progress_bar, 1)
            self.progress_bar.show()  # According to the Qt docs, this is necessary because removing it just hides it.
        elif self.progress_bar is not None:
            self.status_area.removeWidget(self.progress_bar)
            self.progress_bar = None
        QApplication.sendPostedEvents(self, 0)  # Flush any change events before resetting the flag
        QApplication.processEvents()  # Force the flushed events to be processed now

    def show_active_preset(self, preset: Preset | None) -> None:
        assert self.preset_action
        if preset is not None:
            self.preset_action.setToolTip(tr("{} preset").format(preset.get_title_name()))
            self.preset_action.setIcon(preset.create_icon())
            self.preset_action.setVisible(True)
            self.preset_edit_target = preset
        else:
            self.preset_action.setToolTip("")
            self.preset_action.setIcon(QIcon())
            self.preset_action.setVisible(False)
            self.preset_edit_target = None
        self.layout().update()


class VduControlsMainPanel(QWidget):
    """GUI for detected VDUs, it will construct and contain a control panel for each VDU."""

    vdu_vcp_changed_qtsignal = pyqtSignal(str, str, int, VcpOrigin, bool)

    def __init__(self) -> None:
        super().__init__()
        self.bottom_toolbar: VduPanelBottomToolBar | None = None
        self.refresh_data_task = None
        self.setObjectName("vdu_controls_main_panel")
        self.vdu_control_panels: Dict[str, VduControlPanel] = {}
        self.alert: QMessageBox | None = None
        self.main_controller: VduAppController | None = None

    def initialise_control_panels(self, main_controller: VduAppController,
                                  app_context_menu: ContextMenu, main_config: VduControlsConfig,
                                  tool_buttons: List[ToolButton], extra_controls: List[QWidget],
                                  splash_message_qtsignal: pyqtSignal) -> None:
        self.main_controller = main_controller

        if old_layout := cast(QVBoxLayout, self.layout()):  # Must be responding to a configuration change requiring re-layout.
            for i in range(0, old_layout.count()):  # Remove all existing widgets.
                item = old_layout.itemAt(i)
                if isinstance(item, QWidget):
                    old_layout.removeWidget(item)
                    item.deleteLater()
                elif isinstance(item, QWidgetItem):
                    old_layout.removeItem(item)
                    item.widget().deleteLater()
        controllers_layout = QVBoxLayout()
        controllers_layout.setSpacing(0)
        cl_margins = controllers_layout.contentsMargins()
        controllers_layout.setContentsMargins(cl_margins.left(), 0, cl_margins.right(), 0)
        self.setLayout(controllers_layout)

        warnings_enabled = main_config.is_set(ConfOpt.WARNINGS_ENABLED)
        self.vdu_control_panels.clear()
        for controller in self.main_controller.vdu_controllers_map.values():
            splash_message_qtsignal.emit(f"DDC ID {controller.vdu_number}\n{controller.get_vdu_preferred_name()}")
            vdu_control_panel = VduControlPanel(controller, self.show_vdu_exception)
            controller.vcp_value_changed_qtsignal.connect(self.vdu_vcp_changed_qtsignal)
            if vdu_control_panel.number_of_controls() != 0:
                self.vdu_control_panels[controller.vdu_stable_id] = vdu_control_panel
                controllers_layout.addWidget(vdu_control_panel)
            elif warnings_enabled:
                MBox(MIcon.Warning,
                     msg=tr('Monitor {} {} lacks any accessible controls.').format(controller.vdu_number,
                                                                                   controller.get_vdu_preferred_name()),
                     info=tr('The monitor will be omitted from the control panel.')).exec()

        controllers_layout.addStretch(0)
        for control in extra_controls:
            controllers_layout.addWidget(control, 0, Qt.AlignmentFlag.AlignBottom)

        if len(self.vdu_control_panels) == 0:
            no_vdu_widget = QWidget()
            no_vdu_layout = QHBoxLayout()
            no_vdu_widget.setLayout(no_vdu_layout)
            no_vdu_text = QLabel(tr('No controllable monitors found.\n'
                                    'Use the refresh button if any become available.\n'
                                    'Check that ddcutil and i2c are installed and configured.'))
            no_vdu_text.setAlignment(Qt.AlignmentFlag.AlignLeft)
            no_vdu_image = QLabel()
            no_vdu_image.setPixmap(QApplication.style().standardIcon(StdPixmap.SP_MessageBoxWarning).pixmap(QSize(64, 64)))
            no_vdu_image.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            no_vdu_layout.addSpacing(32)
            no_vdu_layout.addWidget(no_vdu_image)
            no_vdu_layout.addWidget(no_vdu_text)
            no_vdu_layout.addSpacing(32)
            controllers_layout.addWidget(no_vdu_widget)

        self.bottom_toolbar = VduPanelBottomToolBar(tool_buttons=tool_buttons, app_context_menu=app_context_menu, parent=self)
        controllers_layout.addWidget(self.bottom_toolbar, 0, Qt.AlignmentFlag.AlignBottom)

        def _open_context_menu(position: QPoint) -> None:
            assert app_context_menu is not None
            app_context_menu.exec(self.mapToGlobal(position))

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(_open_context_menu)

    def indicate_busy(self, is_busy: bool = True, lock_controls: bool = True) -> None:
        if self.bottom_toolbar is not None:
            self.bottom_toolbar.indicate_busy(is_busy)
        if lock_controls:
            for control_panel in self.vdu_control_panels.values():
                control_panel.setDisabled(is_busy)

    def is_preset_active(self, preset: Preset) -> bool:
        for section in preset.preset_ini:
            if section not in ('metadata', 'preset') and (panel := self.vdu_control_panels.get(section, None)):
                if not panel.is_preset_active(preset):
                    return False
        return True

    def show_active_preset(self, preset: Preset | None) -> None:
        if self.bottom_toolbar:
            self.bottom_toolbar.show_active_preset(preset)

    def show_vdu_exception(self, exception: VduException, can_retry: bool = False) -> bool:
        log_error(f"{exception.vdu_description} {exception.operation} {exception.attr_id} {exception.cause}")
        msg = tr("Set value: Failed to communicate with display {}").format(exception.vdu_description)
        if exception.is_display_not_found_error():
            info = tr('Monitor appears to be switched off or disconnected.')
        else:
            info = tr('Is the monitor switched off?') + '<br>' + tr('Is the sleep-multiplier setting too low?')
        if isinstance(exception.cause, subprocess.SubprocessError):
            details = exception.cause.stderr.decode('utf-8', errors='surrogateescape') + '\n' + str(exception.cause)
        else:
            details = str(exception.cause)
        if self.alert is not None:  # Dismiss any existing alert
            self.alert.done(MBtn.Close)
        self.alert = MBox(MIcon.Critical, msg=msg, info=info, details=details,
                          buttons=MBtn.Close | MBtn.Retry if can_retry else MBtn.Close,
                          default=MBtn.Retry if can_retry else MBtn.Close)
        self.alert.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        answer = self.alert.exec()
        self.alert = None
        return answer == MBtn.Retry

    def status_message(self, message: str, timeout: int):
        self.bottom_toolbar.status_area.showMessage(message, timeout) if self.bottom_toolbar else None

@dataclass
class BulkChangeItem:
    vdu_sid: VduStableId
    vcp_code: str
    final_value: int
    starting_value: int | None = None
    current_value: int | None = None
    transition: bool = False

class BulkChangeWorker(WorkerThread):
    progress_qtsignal = pyqtSignal(object)

    def __init__(self, name: str, main_controller: VduAppController,
                 progress_callable: Callable[[BulkChangeWorker], None],
                 finished_callable: Callable[[BulkChangeWorker], None],
                 step_interval: float = 0.0, ignore_others: bool = True, context: Any = None) -> None:
        super().__init__(task_body=self._perform_changes, task_finished=finished_callable)  # type: ignore
        log_debug(f"BulkChangeHandler: {name} init {ignore_others=}") if log_debug_enabled else None
        self.name = name
        self.ignore_others = ignore_others
        self.context = context
        self.start_time: datetime | None = None
        self.main_controller = main_controller
        self.progress_callable = progress_callable
        self.progress_qtsignal.connect(self.progress_callable)
        self.to_do_list: List[BulkChangeItem] = []
        self.step_interval = step_interval
        self.protect_nvram = self.main_controller.main_config.is_set(ConfOpt.PROTECT_NVRAM_ENABLED)
        self.change_count = 0
        self.total_elapsed_seconds = 0.0
        self.completed = False

    def add_item(self, item: BulkChangeItem):
        if self.protect_nvram or self.step_interval < 0.1:
            item.transition = False
        self.to_do_list.append(item)

    def _perform_changes(self, _: BulkChangeWorker):
        self.start_time = zoned_now()
        try:
            if any([item.current_value is None for item in self.to_do_list]):  # has parent filled out expected values.
                self._refresh_current_values_from_vdu()
            self._do_stepped_changes()  # transitions in a series of steps
            if not self.stop_requested:
                self._do_normal_changes()
                self.completed = len([item for item in self.to_do_list if item.current_value != item.final_value]) == 0
        finally:
            (_ :=self).total_elapsed_seconds = (self.start_time - zoned_now()).total_seconds()
            if log_debug_enabled:
                log_debug(f"BulkChangeWorker: {_.name} {_.completed=} {_.change_count=} {_.total_elapsed_seconds=:.3f}")

    def _do_normal_changes(self):
        for item in [item for item in self.to_do_list if not item.transition and item.current_value != item.final_value]:
            if self.stop_requested:
                break
            if item.final_value != item.current_value:
                self.main_controller.set_value(item.vdu_sid, item.vcp_code, item.final_value)
                item.current_value = item.final_value
                self.change_count += 1

    def _do_stepped_changes(self):
        while step_changes := [item for item in self.to_do_list if item.transition and item.current_value != item.final_value]:
            if self.stop_requested:
                break
            for item in step_changes:
                if self.stop_requested:
                    break
                diff = item.final_value - item.current_value
                step_size = max(5, abs(diff) // 2) # TODO find a good heuristic
                step = int(math.copysign(step_size, diff)) if abs(diff) > step_size else diff
                new_value = item.current_value + step
                origin = VcpOrigin.TRANSIENT if new_value != item.final_value else VcpOrigin.NORMAL
                self.main_controller.set_value(item.vdu_sid, item.vcp_code, new_value, origin)
                item.current_value = new_value
                self.change_count += 1
                # self.doze(0.1)  # TODO do we need to pause to let things settle?
            self.progress_qtsignal.emit(self)
            self.doze(self.step_interval)
            self._refresh_current_values_from_vdu()
            if self.stop_requested:
                    break

    def _refresh_current_values_from_vdu(self):
        log_debug(f"BulkChangeWorker {self.name} having to get current_values from VDU") if log_debug_enabled else None
        items_by_vdu: Dict[VduStableId, Dict[str: BulkChangeItem]] = {}
        for item in self.to_do_list:
            if item.vdu_sid not in items_by_vdu:
                items_by_vdu[item.vdu_sid] = {}
            items_by_vdu[item.vdu_sid][item.vcp_code] = item
        for vdu_sid, vdu_items_by_code in items_by_vdu.items():
            for vcp_code, vcp_value in self.main_controller.get_vdu_values(vdu_sid,
                                                                           [item.vcp_code for item in vdu_items_by_code.values()]):
                vdu_current_value = vcp_value.current
                item = vdu_items_by_code[vcp_code]
                if item.current_value is not None and item.current_value != vdu_current_value and not self.ignore_others:
                    log_warning(f"Interrupted bulk change {id=} "
                                f"something else changed the VDU: {vdu_current_value=} != {item.current_value=}")
                    self.stop_requested = True
                    break
                vdu_items_by_code[vcp_code].current_value = vdu_current_value

    def completed_items(self):
        return [item for item in self.to_do_list if item.current_value == item.final_value]


class PresetController:
    def __init__(self) -> None:
        self.presets: Dict[str, Preset] = {}

    def reinitialize(self):
        self.presets = {}

    def find_presets_map(self) -> Dict[str, Preset]:
        presets_still_present = []
        # Use a stable order for the files - alphabetical filename.
        for path_str in sorted(glob.glob(CONFIG_DIR_PATH.joinpath("Preset_*.conf").as_posix()), key=os.path.basename):
            preset_name = os.path.splitext(os.path.basename(path_str))[0].replace('Preset_', '').replace('_', ' ')
            if preset_name not in self.presets:
                preset = Preset(preset_name)
                preset.load()
                self.presets[preset_name] = preset
            presets_still_present.append(preset_name)
        for preset_name in list(self.presets.keys()):
            if preset_name not in presets_still_present:
                del self.presets[preset_name]
        # If Order_Presets.conf exists, reorder according to the CSV Preset names it holds.
        order_presets_path = CONFIG_DIR_PATH.joinpath("Order_Presets.conf")
        if order_presets_path.exists():
            ordering = order_presets_path.read_text().split(",")
            all_presets = list(self.presets.values())
            # Use the Preset-name's position in the Order_Presets.conf CSV as the key-value (or zero if not in the CSV)
            all_presets.sort(key=lambda obj: ordering.index(obj.name) if obj.name in ordering else 0)
            self.presets = {}
            for preset in all_presets:
                self.presets[preset.name] = preset
        return self.presets

    def save_order(self, ordering: List[str]) -> None:
        order_presets_path = CONFIG_DIR_PATH.joinpath("Order_Presets.conf")
        order_presets_path.write_text(','.join(ordering))

    def save_preset(self, preset: Preset) -> None:
        preset.save()
        self.presets[preset.name] = preset

    def delete_preset(self, preset: Preset) -> None:
        preset.delete()
        del self.presets[preset.name]

    def get_preset(self, preset_number: int) -> Preset | None:
        presets = self.find_presets_map()
        if preset_number < len(presets):
            return list(presets.values())[preset_number]
        return None


class FasterFileDialog(QFileDialog):  # Takes 5 seconds versus 30+ seconds for QFileDilog.getOpenFileName() on KDE.
    os.putenv('QT_LOGGING_RULES', 'kf.kio.widgets.kdirmodel.warning=false')  # annoying KDE message

    @staticmethod
    def getOpenFileName(parent: QWidget | None = None, caption: str = '', directory: str = '', filter_str: str = '',
                        initial_filter: str = '',
                        options: Any = QFileDialog.Option.ReadOnly,
                        qdir_filter: Any = QDir.Filter.AllEntries | QDir.Filter.AllDirs | QDir.Filter.Hidden | QDir.Filter.System) -> Tuple[str, str]:
        original_handler = QtCore.qInstallMessageHandler(lambda mode, context, message: None)
        try:  # Get rid of another annoying message: 'qtimeline::start: already running'
            dialog = QFileDialog(parent=parent, caption=caption, directory=directory, filter=filter_str)
            dialog.setOptions(options)
            dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
            dialog.setFilter(qdir_filter)
            return (dialog.selectedFiles()[0], filter) if dialog.exec() else ('', '')  # match QFileDilog.getOpenFileName()
        finally:
            QtCore.qInstallMessageHandler(original_handler)


MIcon = QMessageBox.Icon
MBtn = QMessageBox.StandardButton

class MBox(QMessageBox):

    def __init__(self, icon: QMessageBox.Icon, msg: str | None = None, info: str | None = None, details: str | None = None,
                 buttons: QMessageBox.StandardButton = MBtn.NoButton,
                 default: QMessageBox.StandardButton | None = None) -> None:
        super().__init__(icon, APPNAME, '', buttons=buttons)
        if RESIZABLE_MESSAGEBOX_HACK:
            self.setMouseTracking(True)
            self.setSizeGripEnabled(True)
        self.setDefaultButton(default) if default else None
        self.setText(msg) if msg else None
        self.setInformativeText(info) if info else None
        self.setDetailedText(details) if details else None

    def event(self, event: QEvent | None):
        # https://www.qtcentre.org/threads/24888-Resizing-a-MsgBox.p=251312#post251312
        # The "least evil" way to make MsgBox.resizable, by ArmanS
        result = super().event(event)
        if RESIZABLE_MESSAGEBOX_HACK and event:
            if event.type() == QEvent.Type.MouseMove or event == QEvent.Type.MouseButtonPress:
                self.setMaximumSize(npx(1200), npx(800))
                if text_edit_field := self.findChild(QTextEdit):
                    text_edit_field.setMaximumHeight(npx(600))
        return result


class PushButtonLeftJustified(QPushButton):
    def __init__(self, text: str | None = None, parent: QWidget | None = None, flat: bool = False) -> None:
        super().__init__(parent=parent)
        self.label = QLabel()
        self.setContentsMargins(npx(10), 0, npx(10), 0)  # Not sure if this helps
        self.setLayout(widget_layout := QVBoxLayout())
        widget_layout.addWidget(self.label)
        widget_layout.setContentsMargins(0, 0, 0, 0)  # Seems to fix top/bottom clipping on openbox and xfce
        self.setText(text) if text is not None else None
        self.setFlat(flat)

    def setText(self, text: str | None) -> None:
        self.label.setText(text)


class PresetItemWidget(QWidget):
    def __init__(self, preset: Preset, restore_action: Callable, save_action: Callable, delete_action: Callable,
                 edit_action: Callable, up_action: Callable, down_action: Callable, protect_nvram: bool):
        super().__init__()
        self.name = preset.name
        self.preset = preset
        line_layout = QHBoxLayout()
        line_layout.setSpacing(0)
        ll_margins = line_layout.contentsMargins()
        line_layout.setContentsMargins(ll_margins.left(), 0, ll_margins.right(), npx(1))  # Why?
        self.setLayout(line_layout)

        self.preset_name_button = PresetActivationButton(preset)
        line_layout.addWidget(self.preset_name_button)
        self.preset_name_button.clicked.connect(partial(edit_action, preset=preset))
        self.preset_name_button.setToolTip(tr('Activate this Preset and edit its options.'))
        self.preset_name_button.setAutoDefault(False)
        self.preset_name_button.setFixedSize(QSize(npx(300), native_font_height(scaled=1.5)))
        line_layout.addSpacing(npx(20))
        for button in (
                StdButton(icon=si(self, StdPixmap.SP_DriveFDIcon), tip=tr("Update this preset from the current VDU settings."),
                          clicked=partial(save_action, from_widget=self), flat=True),
                StdButton(icon=si(self, StdPixmap.SP_ArrowUp), tip=tr("Move up the menu order."),
                          clicked=partial(up_action, preset=preset, target_widget=self), flat=True),
                StdButton(icon=si(self, StdPixmap.SP_ArrowDown), tip=tr("Move down the menu order."),
                          clicked=partial(down_action, preset=preset, target_widget=self), flat=True),
                StdButton(icon=si(self, StdPixmap.SP_DialogDiscardButton), tip=tr('Delete this preset.'),
                          clicked=partial(delete_action, preset=preset, target_widget=self), flat=True)):
            button.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
            line_layout.addWidget(button)

        if not protect_nvram:
            preset_transition_button = PushButtonLeftJustified(flat=True)
            preset_transition_button.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
            width = QFontMetrics(preset_transition_button.font()).horizontalAdvance(">____99")
            preset_transition_button.setMaximumWidth(width + 5)
            preset_transition_button.setText(
                f"{preset.get_transition_type().abbreviation()}"
                f"{str(preset.get_step_interval_seconds()) if preset.get_step_interval_seconds() > 0 else ''}")
            if preset.get_step_interval_seconds() > 0:
                preset_transition_button.setToolTip(tr("Transition to {}, each step is {} seconds. {}").format(
                    preset.get_title_name(), preset.get_step_interval_seconds(), preset.get_transition_type().description()))
            else:
                preset_transition_button.setToolTip(tr("Transition to {}. {}").format(
                    preset.get_title_name(), preset.get_transition_type().description()))
            preset_transition_button.clicked.connect(partial(restore_action, preset=preset,
                                                             immediately=preset.get_transition_type() == PresetTransitionFlag.NONE))
            preset_transition_button.setAutoDefault(False)
            if preset.get_transition_type() == PresetTransitionFlag.NONE:
                preset_transition_button.setDisabled(True)
                preset_transition_button.setText('')
            line_layout.addWidget(preset_transition_button)

        line_layout.addSpacing(5)
        self.timer_control_button = PushButtonLeftJustified(parent=self, flat=True)
        self.timer_control_button.setAutoDefault(False)

        if preset.get_solar_elevation() is not None or preset.get_at_time() is not None:
            def _toggle_timer(_) -> None:
                preset.toggle_timer()
                self.update_timer_button()

            self.timer_control_button.clicked.connect(_toggle_timer)

        line_layout.addWidget(self.timer_control_button)
        self.update_timer_button()

    def update_timer_button(self):
        self.timer_control_button.setEnabled(
            self.preset.schedule_status in (PresetScheduleStatus.SCHEDULED, PresetScheduleStatus.SUSPENDED))
        if self.preset.schedule_status == PresetScheduleStatus.SCHEDULED:
            action_desc = tr("Press to skip: ")
        elif self.preset.schedule_status == PresetScheduleStatus.SUSPENDED:
            action_desc = tr("Press to re-enable: ")
        else:
            action_desc = ''
        tip_text = f"{action_desc} {self.preset.get_schedule_description()}"
        self.timer_control_button.setText(self.preset.get_solar_elevation_abbreviation())
        if tip_text.strip():
            self.timer_control_button.setToolTip(tip_text)

    def indicate_active(self, active: bool):
        weight = QFont.Weight.Bold if active else QFont.Weight.Normal
        font = self.preset_name_button.font()
        if font.weight() != weight:
            font.setWeight(weight)
            self.preset_name_button.setFont(font)


class PresetActivationButton(StdButton):
    def __init__(self, preset: Preset) -> None:
        super().__init__(icon=preset.create_icon(), icon_size=QSize(native_font_height(), native_font_height()),
                         title=preset.get_title_name(), tip=tr("Restore {} (immediately)").format(preset.get_title_name()))
        self.preset = preset

    def event(self, event: QEvent | None) -> bool:
        # PalletChange happens after the new style sheet is in use.
        if event and event.type() == QEvent.Type.PaletteChange:
            self.setIcon(self.preset.create_icon())
        return super().event(event)


class PresetIconPickerButton(StdButton):

    def __init__(self) -> None:
        super().__init__(icon_size=QSize(native_font_height(), native_font_height()),
                         clicked=self.choose_preset_icon_action,  flat=True, auto_default=False,
                         tip=tr('Choose a preset icon.'))
        self.setIcon(si(self, PresetsDialog.NO_ICON_ICON_NUMBER))
        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        self.last_selected_icon_path: Path | None = None
        self.last_icon_dir = Path.home()
        for path in STANDARD_ICON_PATHS:
            if path.exists():
                self.last_icon_dir = path
                break
        self.preset: Preset | None = None

    def set_preset(self, preset: Preset | None) -> None:
        self.preset = preset
        if preset is not None:
            self.last_selected_icon_path = preset.get_icon_path()
        if self.last_selected_icon_path is not None:
            self.last_icon_dir = self.last_selected_icon_path.parent
        self.update_icon()

    def choose_preset_icon_action(self) -> None:
        try:
            PresetsDialog.get_instance().setDisabled(True)
            PresetsDialog.get_instance().status_message(TIME_CLOCK_SYMBOL + ' ' + tr("Select an icon..."))
            QApplication.processEvents()
            icon_file = FasterFileDialog.getOpenFileName(self, tr('Icon SVG or PNG file'), self.last_icon_dir.as_posix(),
                                                         'SVG or PNG (*.svg *.png)')
            self.last_selected_icon_path = Path(icon_file[0]) if icon_file[0] != '' else None
            if self.last_selected_icon_path:
                self.last_icon_dir = self.last_selected_icon_path.parent
            self.update_icon()
        finally:
            PresetsDialog.get_instance().status_message('')
            PresetsDialog.get_instance().setDisabled(False)

    def update_icon(self) -> None:
        if self.last_selected_icon_path:
            self.setIcon(create_icon_from_path(self.last_selected_icon_path, polychrome_light_or_dark()))
        elif self.preset:
            self.setIcon(self.preset.create_icon(polychrome_light_or_dark()))
        else:
            self.setIcon(si(self, PresetsDialog.NO_ICON_ICON_NUMBER))

    def reset(self):
        self.last_selected_icon_path = None
        self.preset = None
        self.update_icon()

    def event(self, event: QEvent | None) -> bool:
        if event and event.type() == QEvent.Type.PaletteChange:  # PalletChange happens after the new style sheet is in use.
            self.update_icon()
        return super().event(event)


class WeatherQuery:

    def __init__(self, location: GeoLocation) -> None:
        self.location = location
        self.maximum_distance_km = int(os.getenv("VDU_CONTROLS_WEATHER_KM", default='200'))
        local_local = locale.getlocale()
        lang = local_local[0][:2] if local_local is not None and local_local[0] is not None else 'C'
        ascii_location = unicodedata.normalize('NFD', location.place_name).encode('ascii','ignore').decode("ascii")
        self.url = f"{WEATHER_FORECAST_URL}/{ascii_location}?" + urllib.parse.urlencode({'lang': lang, 'format': 'j1'})
        self.weather_data = None
        self.proximity_km = 0
        self.proximity_ok = True
        self.longitude = self.latitude = self.country_name = self.area_name = None
        self.cloud_cover = self.visibility = self.weather_desc = self.weather_code = None
        self.when: datetime | None = None

    def run_query(self) -> None:
        location_name = self.location.place_name
        local_local = locale.getlocale()
        lang = local_local[0][:2] if local_local is not None and local_local[0] is not None else 'C'
        if location_name is None or location_name.strip() == '':
            location_name = ''
        self.when = zoned_now()
        try:
            log_info(f"QueryWeather: {self.url}")
            with urllib.request.urlopen(self.url, timeout=15) as request:
                json_content = request.read()
                self.weather_data = json.loads(json_content)
                if self.weather_data is not None:
                    current_conditions = self.weather_data['current_condition'][0]
                    self.weather_code = current_conditions['weatherCode']
                    lang_key = f"lang_{lang}"
                    if lang_key in current_conditions:
                        self.weather_desc = current_conditions[lang_key][0]['value']
                    else:
                        self.weather_desc = current_conditions['weatherDesc'][0]['value']
                    self.visibility = current_conditions['visibility']
                    self.cloud_cover = current_conditions['cloudcover']
                    nearest_area = self.weather_data['nearest_area'][0]
                    self.area_name = nearest_area['areaName'][0]['value']
                    self.country_name = nearest_area['country'][0]['value']
                    self.latitude = nearest_area['latitude']
                    self.longitude = nearest_area['longitude']
                    self.proximity_km = round(spherical_kilometers(float(self.latitude), float(self.longitude),
                                                                   self.location.latitude, self.location.longitude))
                    self.proximity_ok = self.proximity_km <= self.maximum_distance_km
                    log_info(f"QueryWeather result: {self}")
                    return
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise ValueError(tr("Unknown location {}").format(location_name), tr("Please check Location in Settings")) from e
            raise ValueError(tr("Failed to get weather from {}").format(self.url), str(e)) from e
        except Exception as ue:
            # Can't afford to fall over because of a problem with a remote site
            raise ValueError(tr("Failed to get weather from {}").format(self.url), str(ue)) from ue
        raise ValueError(tr("Failed to get weather from {}").format(self.url))

    def __str__(self) -> str:
        if self.weather_data is None:
            return ""
        return f"{self.area_name}, {self.country_name}, {self.weather_desc} ({self.weather_code})," \
               f"cloud_cover {self.cloud_cover}, visibility {self.visibility}, location={self.latitude},{self.longitude}"


def weather_bad_location_dialog(weather) -> None:
    kilometres = weather.proximity_km
    use_km = QLocale.system().measurementSystem() == QLocale.MeasurementSystem.MetricSystem
    MBox(MIcon.Warning, msg=tr("The site {} reports your location as {}, {}, {},{} "
                              "which is about {} {} from the latitude and longitude specified in Settings."
                              ).format(WEATHER_FORECAST_URL, weather.area_name, weather.country_name, weather.latitude, weather.longitude,
                                       round(kilometres if use_km else kilometres * 0.621371), 'km' if use_km else 'miles'),
         info=tr("Please check the location specified in Settings."), details=f"{weather}").exec()


class PresetWeatherWidget(QWidget):
    default_weather_conditions = {
        CONFIG_DIR_PATH.joinpath('good.weather'): "113 Sunny\n116 Partly Cloudy\n119 Cloudy\n",
        CONFIG_DIR_PATH.joinpath('bad.weather'):
            "143 Fog\n179 Light Sleet Showers\n182 Light Sleet\n185 Light Sleet\n200 Thundery Showers\n227 "
            "Light Snow\n230 Heavy Snow\n248 Fog\n260 Fog\n266 Light Rain\n281 Light Sleet\n284 Light "
            "Sleet\n293 Light Rain\n296 Light Rain\n299 Heavy Showers\n302 Heavy Rain\n305 Heavy Showers\n308 "
            "Heavy Rain\n311 Light Sleet\n314 Light Sleet\n317 Light Sleet\n320 Light Snow\n323 Light Snow "
            "Showers\n326 Light Snow Showers\n329 Heavy Snow\n332 Heavy Snow\n335 Heavy Snow Showers\n338 "
            "Heavy Snow\n350 Light Sleet\n353 Light Showers\n356 Heavy Showers\n359 Heavy Rain\n362 Light "
            "Sleet Showers\n365 Light Sleet Showers\n368 Light Snow Showers\n371 Heavy Snow Showers\n374 "
            "Light Sleet Showers\n377 Light Sleet\n386 Thundery Showers\n389 Thundery Heavy Rain\n392 "
            "Thundery Snow Showers\n395 HeavySnowShowers\n",
        CONFIG_DIR_PATH.joinpath('all.weather'):
            "113 Sunny\n116 Partly Cloudy\n119 Cloudy\n122 Very Cloudy\n143 Fog\n176 Light Showers\n179 Light "
            "Sleet Showers\n182 Light Sleet\n185 Light Sleet\n200 Thundery Showers\n227 Light Snow\n230 Heavy "
            "Snow\n248 Fog\n260 Fog\n263 Light Showers\n266 Light Rain\n281 Light Sleet\n284 Light Sleet\n293 "
            "Light Rain\n296 Light Rain\n299 Heavy Showers\n302 Heavy Rain\n305 Heavy Showers\n308 Heavy "
            "Rain\n311 Light Sleet\n314 Light Sleet\n317 Light Sleet\n320 Light Snow\n323 Light Snow "
            "Showers\n326 Light Snow Showers\n329 Heavy Snow\n332 Heavy Snow\n335 Heavy Snow Showers\n338 "
            "Heavy Snow\n350 Light Sleet\n353 Light Showers\n356 Heavy Showers\n359 Heavy Rain\n362 Light "
            "Sleet Showers\n365 Light Sleet Showers\n368 Light Snow Showers\n371 Heavy Snow Showers\n374 "
            "Light Sleet Showers\n377 Light Sleet\n386 Thundery Showers\n389 Thundery Heavy Rain\n392 "
            "Thundery Snow Showers\n395 Heavy Snow Showers\n"}

    def __init__(self, location: GeoLocation | None, main_config: VduControlsConfig) -> None:
        super().__init__()
        self.location = location
        self.init_weather()
        self.main_config = main_config
        self.required_weather_filepath: Path | None = None
        self.setLayout(widget_layout := QVBoxLayout())
        self.label = QLabel(tr("Additional weather requirements"))
        self.label.setToolTip(tr("Weather conditions will be retrieved from {}").format(WEATHER_FORECAST_URL))
        widget_layout.addWidget(self.label)
        self.chooser = QComboBox()

        def _select_action(index: int) -> None:
            self.required_weather_filepath = self.chooser.itemData(index)
            if self.chooser.itemData(index) is None:
                self.info_label.setText('')
            else:
                assert self.location is not None
                self.verify_weather_location(self.location)
                path = self.chooser.itemData(index)
                if path.exists():
                    with open(path, encoding="utf-8") as weather_file:
                        code_list = weather_file.read()
                        self.info_label.setText(code_list)
                else:
                    self.chooser.removeItem(index)
                    self.chooser.setCurrentIndex(0)
            self.populate()

        self.chooser.currentIndexChanged.connect(_select_action)
        self.chooser.setToolTip(self.label.toolTip())
        widget_layout.addWidget(self.chooser)
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.populate()
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.info_label)
        scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        scroll_area.setWidgetResizable(True)
        widget_layout.addWidget(scroll_area)

    def init_weather(self) -> None:
        for condition_path, condition_content in PresetWeatherWidget.default_weather_conditions.items():
            if not condition_path.exists():
                with open(condition_path, 'w', encoding="utf-8") as weather_file:
                    log_info(f"Creating {condition_path.as_posix()}")
                    weather_file.write(condition_content)

    def verify_weather_location(self, location: GeoLocation) -> None:
        if not self.main_config.is_set(ConfOpt.WEATHER_ENABLED):
            return
        place_name = location.place_name if location.place_name is not None else 'IP-address'
        # Only do this check if the location has changed.
        vf_file_path = CONFIG_DIR_PATH.joinpath('verified_weather_location.txt')
        if vf_file_path.exists():
            with open(vf_file_path, encoding="utf-8") as vf:
                if vf.read() == place_name:
                    return
        try:
            log_info(f"Verifying weather location by querying {WEATHER_FORECAST_URL}.")
            weather = WeatherQuery(location)
            weather.run_query()
            if weather.proximity_ok:
                MBox(MIcon.Information,
                     msg=tr("Weather for {} will be retrieved from {}").format(place_name, WEATHER_FORECAST_URL)).exec()
                with open(vf_file_path, 'w', encoding="utf-8") as vf:
                    vf.write(place_name)
            else:
                weather_bad_location_dialog(weather)
        except ValueError as e:
            log_error(f"Failed to validate location: {e}", trace=True)
            MBox(MIcon.Critical, msg=tr("Failed to validate weather location: {}").format(e.args[0]), info=e.args[1]).exec()

    def populate(self) -> None:
        if self.chooser.count() == 0:
            self.chooser.addItem(tr("None"), None)
        existing_paths = [self.chooser.itemData(i) for i in range(1, self.chooser.count())]
        for path in sorted(CONFIG_DIR_PATH.glob("*.weather")):
            if path not in existing_paths:
                weather_name = path.stem.replace('_', ' ')
                self.chooser.addItem(weather_name, path)

    def get_required_weather_filepath(self) -> Path | None:
        return self.required_weather_filepath if self.required_weather_filepath is not None else None

    def set_required_weather_filepath(self, weather_filename: str | None) -> None:
        if weather_filename is None:
            self.required_weather_filepath = None
            self.chooser.setCurrentIndex(0)
            self.info_label.setText('')
            return
        self.required_weather_filepath = Path(weather_filename)
        for i in range(1, self.chooser.count()):
            if self.chooser.itemData(i).as_posix() == self.required_weather_filepath.as_posix():
                self.chooser.setCurrentIndex(i)
                return

    def update_location(self, location: GeoLocation) -> None:
        self.location = location
        self.verify_weather_location(self.location)


class PresetTransitionWidget(QWidget):

    def __init__(self) -> None:
        super().__init__()
        self.setToolTip(tr("Choose whether this Preset should transition when activated a particular way."))
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        layout.addWidget(QLabel(tr("Transition")), alignment=Qt.AlignmentFlag.AlignLeft)
        self.transition_type_widget = StdButton(title=PresetTransitionFlag.NONE.description())
        self.button_menu = QMenu()
        self.transition_type = PresetTransitionFlag.NONE
        self.is_setting = False

        for transition_type in PresetTransitionFlag.ALWAYS.component_values():
            action = QAction(transition_type.description(), self.button_menu)
            action.setData(transition_type)
            action.setCheckable(True)
            action.toggled.connect(self.update_value)
            self.button_menu.addAction(action)

        self.transition_type_widget.setMenu(self.button_menu)
        layout.addWidget(self.transition_type_widget, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addStretch(20)
        layout.addWidget(QLabel(tr("Transition step")), alignment=Qt.AlignmentFlag.AlignRight)
        self.step_seconds_widget = QSpinBox()
        self.step_seconds_widget.setRange(0, 60)
        layout.addWidget(self.step_seconds_widget, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(QLabel(tr("sec.")), alignment=Qt.AlignmentFlag.AlignRight)

    def update_value(self, checked: bool) -> None:
        if self.is_setting:
            return
        if checked:
            MBox(MIcon.Warning,
                 msg=tr('Transitions have been deprecated to minimize wear on VDU NVRAM.'),
                 info=tr('Transitions are slated for removal, please contact the developer if you wish to retain them.')).exec()
        for act in self.button_menu.actions():
            if act.isChecked():
                self.transition_type |= act.data()
            elif act.data() in self.transition_type:
                self.transition_type ^= act.data()
        self.transition_type_widget.setText(str(self.transition_type.description()))

    def set_transition_type(self, transition_type: PresetTransitionFlag) -> None:
        try:
            self.is_setting = True
            self.transition_type = transition_type
            for act in self.button_menu.actions():
                act.setChecked(self.transition_type & act.data())
            self.transition_type_widget.setText(str(self.transition_type.description()))
        finally:
            self.is_setting = False

    def set_step_seconds(self, seconds: int) -> None:
        self.step_seconds_widget.setValue(seconds)

    def get_transition_type(self) -> PresetTransitionFlag:
        return self.transition_type

    def get_step_seconds(self) -> int:
        return self.step_seconds_widget.value()


class PresetElevationChartWidget(QLabel):
    selected_elevation_qtsignal = pyqtSignal(object)

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(npx(300), npx(350))
        self.sun_image: QImage | None = None
        self.setMouseTracking(True)
        self.in_drag = False
        self.current_pos: QPoint | None = None
        self.cache_solar_by_elevation: Dict[SolarElevationKey, SolarElevationData] = {}
        self.elevation_key: SolarElevationKey | None = None
        self.location: GeoLocation | None = None
        self.elevation_steps: List[SolarElevationKey] = []
        for i in range(-19, 90):
            self.elevation_steps.append(SolarElevationKey(EASTERN_SKY, i))
        for i in range(90, -20, -1):
            self.elevation_steps.append(SolarElevationKey(WESTERN_SKY, i))
        self.noon_x: int = npx(100)
        self.noon_y: int = npx(25)
        self.horizon_y: int = npx(75)
        self.radius_of_deletion = npx(50)
        self.solar_max_t: datetime | None = None
        self.last_event_time = time.time()
        self.cache_key: Tuple[datetime, int, int, int] | None = None
        self.cache_curve_points: List[QPoint] = []

    def has_elevation_key(self, key: SolarElevationKey) -> bool:
        return key in self.elevation_steps

    def get_elevation_data(self, elevation_key: SolarElevationKey) -> SolarElevationData | None:
        assert self.cache_solar_by_elevation is not None
        return self.cache_solar_by_elevation[elevation_key] if elevation_key in self.cache_solar_by_elevation else None

    def set_elevation_key(self, elevation_key: SolarElevationKey | None) -> None:
        self.elevation_key = elevation_key
        self.create_plot()

    def configure_for_location(self, location: GeoLocation | None) -> None:
        self.location = location
        if location is not None:
            self.cache_key = None
            self.elevation_key = None
            self.create_plot()

    def _reverse_X(self, x: int) -> int:  # makes thinking right-to-left a bit easier. MAYBE
        return self.width() - x

    def create_plot(self) -> None:
        ev_key = self.elevation_key
        logical_width, logical_height = self.width(), self.height()
        origin_iy, range_iy = round(logical_height / 2), round(logical_height / 2.5)
        self.radius_of_deletion = round(range_iy * 0.8)
        self.horizon_y = origin_iy
        line_width = npx(4)
        thin_line_width = npx(2)
        dp_ratio = self.devicePixelRatio()
        pixmap = QPixmap(round(logical_width * dp_ratio), round(logical_height * dp_ratio))
        pixmap.setDevicePixelRatio(dp_ratio)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        def _reverse_x(x_val: int) -> int:  # makes thinking right-to-left a bit easier. MAYBE
            return logical_width - x_val

        painter.fillRect(0, 0, logical_width, origin_iy, QColor(0x5b93c5))
        painter.fillRect(0, origin_iy, logical_width, logical_height, QColor(0x7d5233))
        painter.setPen(QPen(Qt.GlobalColor.white, line_width))  # Horizon
        painter.drawLine(0, origin_iy, logical_width, origin_iy)

        _reverse_x = self._reverse_X

        if self.location is not None:
            self.refresh_day_cache(logical_width, origin_iy, range_iy)
            curve_points = self.cache_curve_points
            solar_noon_x, solar_noon_y = self.noon_x, self.noon_y,
            if ev_key and (solar_data := self.cache_solar_by_elevation.get(ev_key)):
                seconds_since_midnight = (solar_data.when - solar_data.when.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
                sun_plot_time = solar_data.when
                sun_plot_x = round(logical_width * seconds_since_midnight / (60.0 * 60.0 * 24.0))
                sun_height = math.sin(math.radians(90.0 - solar_data.zenith)) * range_iy
                sun_plot_y = origin_iy - round(sun_height)
            else:
                sun_plot_time = None
                sun_plot_x = self.noon_x
                sun_plot_y = self.noon_y

            # Draw an elevation curve for today from the accumulated plot points:
            painter.setPen(QPen(QColor(0xff965b), line_width))
            painter.drawPoints(QPolygon(curve_points))

            # Draw various annotations such the horizon-line, noon-line, E & W, and the current degrees:
            painter.setPen(QPen(Qt.GlobalColor.white, line_width))
            painter.drawLine(_reverse_x(0), origin_iy, _reverse_x(logical_width), origin_iy)
            painter.drawLine(_reverse_x(solar_noon_x), origin_iy, _reverse_x(solar_noon_x), 0)
            painter.setPen(QPen(Qt.GlobalColor.white, line_width))
            painter.setFont(QFont(QApplication.font().family(), pt := 18, QFont.Weight.Bold))
            painter.drawText(QPoint(_reverse_x((txt_margin := npx(25)) + pt), origin_iy - npx(32)), tr("E"))
            painter.drawText(QPoint(_reverse_x(logical_width - txt_margin), origin_iy - npx(32)), tr("W"))
            time_text = sun_plot_time.strftime("%H:%M") if sun_plot_time else "____"
            painter.drawText(_reverse_x(solar_noon_x + logical_width // 4), logical_height - npx(25),
                             f"{ev_key.elevation if ev_key else 0:3d}{DEGREE_SYMBOL} {time_text}")

            # Draw pie/compass angle
            if ev_key:
                angle_above_horz = ev_key.elevation if ev_key.direction == EASTERN_SKY else (180 - ev_key.elevation)  # anticlockwise from 0
            else:
                angle_above_horz = 180 + 19
            _, pos_as_radius = self.calc_angle_radius(self.current_pos) if self.current_pos else (0, 21)
            pie_width = pie_height = range_iy * 2
            span_angle = -(angle_above_horz + 19)  # From start angle spanning counterclockwise back toward the right to -19.
            painter.setPen(
                QPen(QColor(0xffffff if self.current_pos is None or self.in_drag or pos_as_radius > self.radius_of_deletion else 0xff0000),
                     2))
            painter.setBrush(QColor(255, 255, 255, 64))
            painter.drawPie(_reverse_x(solar_noon_x) - pie_width // 2, origin_iy - pie_height // 2, pie_width, pie_height,
                            angle_above_horz * 16, span_angle * 16)

            # Draw drag-dot
            painter.setFont(QFont(QApplication.font().family(), 8, QFont.Weight.Normal))
            if self.current_pos is not None or self.in_drag or pos_as_radius >= self.radius_of_deletion:
                painter.setPen(QPen(Qt.GlobalColor.red, npx(6)))
                painter.setBrush(Qt.GlobalColor.white)
                ddot_radians = math.radians(angle_above_horz if ev_key else -19)
                ddot_radius = npx(8)
                ddot_x = round(range_iy * math.cos(ddot_radians)) - ddot_radius
                ddot_y = round(range_iy * math.sin(ddot_radians)) + ddot_radius
                painter.drawEllipse(_reverse_x(solar_noon_x - ddot_x), origin_iy - ddot_y, ddot_radius * 2, ddot_radius * 2)
                if not self.in_drag:
                    painter.setPen(QPen(Qt.GlobalColor.black, 1))
                    painter.drawText(QPoint(_reverse_x(solar_noon_x - ddot_x) + npx(10), origin_iy - ddot_y - npx(5)), tr("Drag to change."))

            # Draw origin-dot
            painter.setPen(QPen(QColor(0xff965b), thin_line_width))
            if self.current_pos is not None and not self.in_drag:
                if pos_as_radius < self.radius_of_deletion:
                    painter.setPen(QPen(Qt.GlobalColor.black, npx(1)))
                    painter.drawText(QPoint(_reverse_x(solar_noon_x + 8) + npx(10), origin_iy - npx(8) - npx(5)),
                                     tr("Click to delete."))
                    painter.setPen(QPen(Qt.GlobalColor.red, thin_line_width))
            odot_radius = npx(8)
            painter.setBrush(painter.pen().color())
            painter.drawEllipse(_reverse_x(solar_noon_x + odot_radius), origin_iy - odot_radius, odot_radius * 2, odot_radius * 2)

            if ev_key:
                # Draw a line representing the slider degrees and Twilight indicator - may be higher than the sun for today:
                sky_line_y = origin_iy - round(math.sin(math.radians(ev_key.elevation)) * range_iy)
                if sky_line_y >= solar_noon_y:
                    sky_line_pen = QPen(Qt.GlobalColor.white, thin_line_width)
                else:
                    sky_line_pen = QPen(QColor(0xcccccc), thin_line_width)
                    sky_line_pen.setStyle(Qt.PenStyle.DotLine)
                painter.setPen(sky_line_pen)
                painter.setBrush(painter.pen().color())

                pyramid_base = npx(16)
                if ev_key.direction == EASTERN_SKY:  # Triangle pointing up
                    pyramid = [(-pyramid_base // 2, 0), (0, -pyramid_base), (pyramid_base // 2, 0)]
                    painter.drawLine(_reverse_x(0), sky_line_y, _reverse_x(solar_noon_x), sky_line_y)
                    painter.setPen(QPen(painter.pen().color(), 1))
                    painter.drawPolygon(
                        QPolygon([QPoint(_reverse_x(0 + npx(20) + tx), sky_line_y - npx(10) + ty) for tx, ty in pyramid]))
                else:  # Triangle pointing down
                    inverted_pyramid = [(-pyramid_base // 2, 0), (0, pyramid_base), (pyramid_base // 2, 0)]
                    painter.drawLine(_reverse_x(solar_noon_x), sky_line_y, _reverse_x(logical_width), sky_line_y)
                    painter.setPen(QPen(painter.pen().color(), 1))
                    painter.drawPolygon(
                        QPolygon([QPoint(_reverse_x(logical_width - npx(18)) + tx, sky_line_y + npx(10) + ty)
                                  for tx, ty in inverted_pyramid]))
                # Draw the sun
                painter.setPen(QPen(QColor(0xff4a23), line_width))
                if self.sun_image is None:
                    sun_image = create_image_from_svg_bytes(SUN_SVG.replace(SVG_LIGHT_THEME_COLOR, b"#fecf70"))
                    self.sun_image = sun_image.scaled(npx(sun_image.width()), npx(sun_image.height()))
                painter.drawImage(QPoint(_reverse_x(sun_plot_x) - self.sun_image.width() // 2,
                                         sun_plot_y - self.sun_image.height() // 2), self.sun_image)
        painter.end()
        self.setPixmap(pixmap)

    def refresh_day_cache(self, logical_width: int, origin_iy: int, range_iy: int) -> None:
        # Perform computations for today's curve and maxima.
        _reverse_x = self._reverse_X
        new_cache_key = ((zoned_now().replace(hour=0, minute=0, second=0, microsecond=0)), logical_width, origin_iy, range_iy)
        if self.cache_key and new_cache_key == self.cache_key:
            return
        log_debug(f"PresetElevationChartWidget: change of key values {new_cache_key=}, recalculating")
        self.cache_key = new_cache_key
        max_sun_height = npx(-90.0)
        solar_noon_x, solar_noon_y = 0, 0  # Solar noon
        curve_points = []

        def _create_curve(a, z, t):  # Gets called for every 1-minute point - to create a smooth curve.
            nonlocal max_sun_height, solar_noon_x, solar_noon_y
            second_of_day = (t - t.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
            x = round(logical_width * second_of_day / (60.0 * 60.0 * 24.0))
            sun_height = math.sin(math.radians(90.0 - z)) * range_iy
            y = origin_iy - round(sun_height)
            curve_points.append(QPoint(_reverse_x(x), y))  # Save the plot points to a list
            if sun_height > max_sun_height:
                max_sun_height = sun_height
                solar_noon_x, solar_noon_y = x, y
                self.solar_max_t = t

        self.cache_solar_by_elevation = create_elevation_map(zoned_now(),
                                                             latitude=self.location.latitude, longitude=self.location.longitude,
                                                             callback=_create_curve)
        self.noon_x = solar_noon_x
        self.noon_y = solar_noon_y
        self.cache_curve_points = curve_points

    def calc_angle_radius(self, pos: QPoint) -> Tuple[int, int]:
        x, y = pos.x(), pos.y()
        adjacent = x - self._reverse_X(self.noon_x)
        opposite = self.horizon_y - y
        angle = 90 if adjacent == 0 else round(math.degrees(math.atan(opposite / adjacent)))
        radius = round(math.sqrt(adjacent ** 2 + opposite ** 2))
        return angle, radius

    def update_current_pos(self, local_pos: QPoint) -> QPoint | None:
        self.current_pos = local_pos if (0 < local_pos.x() < self.width() and 0 <= local_pos.y() < self.height()) else None
        return self.current_pos

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        if event:
            if pos := self.update_current_pos(event.pos()):
                angle, radius = self.calc_angle_radius(pos)
                if radius <= self.radius_of_deletion:
                    self.set_elevation_key(None)
                    self.selected_elevation_qtsignal.emit(None)
                else:
                    self.in_drag = True
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent | None) -> None:
        if event:
            self.update_current_pos(event.pos())
            self.in_drag = False
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:
        if event:
            event.accept()
            if (now := time.time()) - self.last_event_time < 0.1:  # Prevent event overload on Qt6 kwin-wayland
                return
            self.last_event_time = now
            pos = self.update_current_pos(event.pos())
            if pos is not None and 0 <= pos.x() < self.width() and 0 <= pos.y() < self.height():
                angle, radius = self.calc_angle_radius(pos)
                if self.in_drag:
                    self.current_pos = pos
                    angle = -angle if pos.x() < self._reverse_X(self.noon_x) else angle
                    eastern = pos.x() >= self._reverse_X(self.noon_x)
                    key = SolarElevationKey(EASTERN_SKY if eastern else WESTERN_SKY, angle)
                    if not key in self.elevation_steps:
                        key = self.elevation_steps[0 if eastern else -1]
                    self.set_elevation_key(key)
                    self.selected_elevation_qtsignal.emit(key)
            self.create_plot()  # necessary to detect deletions


    def leaveEvent(self, event: QEvent | None) -> None:
        self.current_pos = None
        self.create_plot()
        super().leaveEvent(event)

class PresetDaylightFactorWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.setLayout(QHBoxLayout())
        self.df_checkbox = QCheckBox()
        self.df_label = QLabel(tr("Daylight-Factor"))
        self.df_input = QLineEdit()
        self.df_input.setValidator(QDoubleValidator())
        self.setEnabled(False)
        self.df_checkbox.toggled.connect(self.setEnabled)
        self.setToolTip(tr("Save the current semi-automatic Light-Metering Daylight-Factor (DF) as part of the Preset."))

        def df_init(state):
            if state == Qt.CheckState.Checked:
                if self.df_input.text() == '':
                    self.df_input.setText(f"{LuxMeterSemiAutoDevice.get_daylight_factor():.4f}")
            else:
                self.df_input.setText('')

        self.df_checkbox.stateChanged.connect(df_init)
        for widget in (self.df_checkbox, self.df_label, self.df_input):
            self.layout().addWidget(widget)

    def setEnabled(self, enabled):
        self.df_checkbox.setChecked(enabled)
        self.df_label.setEnabled(enabled)
        self.df_input.setEnabled(enabled)


class PresetScheduleAtWidgetBase(QWidget):  # Abstract

    def __init__(self, description: str):
        super().__init__()
        self.description = description
        self.all_schedule_chooser_widgets: List[PresetScheduleAtWidgetBase] = []

    def set_schedule_widgets(self, all_widgets: List[PresetScheduleAtWidgetBase]):
        self.all_schedule_chooser_widgets = all_widgets

    def clear_others(self, _ = None) -> bool:  # Only allow a Preset to be scheduled once.
        others = [w for w in self.all_schedule_chooser_widgets if w != self and w.is_set()]
        if others and MBox(MIcon.Question, msg=tr('Preset already scheduled. Clear existing {}?').format(others[0].description),
                           info=tr('Duplicate the preset if you need to schedule it more than once.'),
                           buttons=MBtn.Ok | MBtn.Cancel).exec() == MBtn.Cancel:
            return False
        for schedule_chooser in others:
            schedule_chooser.clear()
        return True

    def is_set(self) -> bool:  # Abstract
        return False

    def clear(self) -> None:  # Abstract
        pass

class PresetScheduleAtElevationWidget(PresetScheduleAtWidgetBase):
    _slider_select_elevation_qtsignal = pyqtSignal(object)

    def __init__(self, main_config: VduControlsConfig) -> None:
        super().__init__(description=tr("elevation-trigger"))
        self.elevation_key: SolarElevationKey | None = None
        self.location: GeoLocation | None = main_config.get_location()
        self.setLayout(main_layout := QVBoxLayout())
        self.title_prefix = tr("Trigger at solar elevation:")
        self.title_label = QLabel(self.title_prefix)
        self.title_label.setFixedHeight(native_font_height(scaled=1.5))  # Stop ascenders/descenders in Unicode from altering layout.
        self.title_label.setToolTip(tr("Trigger at a set solar elevation (sun angle at your geolocation and time)."))
        main_layout.addWidget(self.title_label)

        self.elevation_chart = PresetElevationChartWidget()
        self.elevation_chart.selected_elevation_qtsignal.connect(self.set_elevation_key)

        self.df_widget = PresetDaylightFactorWidget()

        self.slider_last_event_time = time.time()
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(-1)
        self.slider.setValue(-1)
        self.slider.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.slider.setTickInterval(5)
        self.slider.setTickPosition(QSlider.TickPosition.TicksAbove)
        self._slider_select_elevation_qtsignal.connect(self.set_elevation_key)

        bottom_layout = QHBoxLayout()
        main_layout.addLayout(bottom_layout)

        chart_and_slider_layout = QVBoxLayout()
        chart_and_slider_layout.addWidget(self.elevation_chart, 1)
        chart_and_slider_layout.addWidget(self.slider)
        chart_and_slider_layout.addWidget(self.df_widget, 0)
        bottom_layout.addLayout(chart_and_slider_layout, 1)

        self.weather_widget = PresetWeatherWidget(self.location, main_config)
        bottom_layout.addWidget(self.weather_widget, 0)
        self.configure_for_location(self.location)
        self.slider.valueChanged.connect(self.sliding)

        self.setMinimumWidth(npx(400))
        self.sun_image: QImage | None = None

    def is_set(self) -> bool:
        return self.elevation_key is not None

    def clear(self) -> None:
        self.set_elevation_key(None)

    def sliding(self) -> None:
        if (now := time.time()) - self.slider_last_event_time < 0.1:  # Prevent event overload on Qt6 kwin-wayland
            return
        self.slider_last_event_time = now
        value = self.slider.value()
        if value == -1:
            self._slider_select_elevation_qtsignal.emit(None)
            return
        chart = self.elevation_chart
        self._slider_select_elevation_qtsignal.emit(
            chart.elevation_steps[value] if 0 <= value < len(chart.elevation_steps) else None)

    def show_elevation_description(self) -> None:
        if self.elevation_key is None:
            self.title_label.setText(self.title_prefix)
            return
        elevation_data = self.elevation_chart.get_elevation_data(self.elevation_key)
        occurs_at = elevation_data.when if elevation_data is not None else None  # No elev data => sun doesn't rise this high today
        if occurs_at:
            when_text = tr("today at {}").format(occurs_at.strftime('%H:%M'))
        else:
            when_text = tr("the sun does not rise this high today")
        # https://en.wikipedia.org/wiki/Twilight
        if self.elevation_key.elevation < 1:
            if self.elevation_key.elevation >= -6:
                when_text += " " + (tr("dawn") if self.elevation_key.direction == EASTERN_SKY else tr("dusk"))
            elif self.elevation_key.elevation >= -18:  # Astronomical twilight
                when_text += " " + tr("twilight")
            else:
                when_text += " " + tr("nighttime")
        if elevation_data is not None and self.location:
            if lux := calc_solar_lux(elevation_data.when, self.location, 1.0):
                when_text += tr(" {:,} lux").format(lux)
        desc_text = "{} {} ({}, {})".format(
            self.title_prefix, format_solar_elevation_abbreviation(self.elevation_key), tr(self.elevation_key.direction), when_text)
        if desc_text != self.title_label.text():
            self.title_label.setText(desc_text)

    def configure_for_location(self, location: GeoLocation | None) -> None:
        self.elevation_chart.configure_for_location(location)
        self.location = location
        if location is None:
            self.title_label.setText(self.title_prefix + tr("location undefined (see settings)"))
            self.slider.setDisabled(True)
            return
        self.slider.setEnabled(True)
        self.slider.setMaximum(len(self.elevation_chart.elevation_steps) - 1)
        self.slider.setValue(-1)
        self.sliding()
        self.weather_widget.update_location(location)
        if self.elevation_chart.solar_max_t is not None:
            snt = self.elevation_chart.solar_max_t
            if snt.hour > (15 if snt.tzname() == 'CST' else 14) or snt.hour < 10:  # Solar midday seems too far from 12:00 midday.
                log_warning(f"Location {location.longitude},{location.latitude} and timezone {snt.tzname()} seem mismatched.")

    def resizeEvent(self, event: QResizeEvent | None) -> None:
        super().resizeEvent(event)
        self.elevation_chart.set_elevation_key(self.elevation_key)

    def set_elevation_from_text(self, elevation_text: str | None) -> None:
        if elevation_text is not None and elevation_text.strip() != '' and len(self.elevation_chart.elevation_steps) != 0:
            elevation_key = parse_solar_elevation_ini_text(elevation_text)
            if self.elevation_chart.has_elevation_key(elevation_key):
                self.set_elevation_key(elevation_key)
                return
        self.set_elevation_key(None)

    def set_elevation_key(self, elevation_key: SolarElevationKey | None) -> None:
        if elevation_key is not None:
            if self.clear_others():
                if self.elevation_chart.has_elevation_key(elevation_key):
                    self.elevation_key = elevation_key
                    self.slider.setValue(self.elevation_chart.elevation_steps.index(self.elevation_key))
                    self.slider.setToolTip(f"{self.elevation_key.elevation}{DEGREE_SYMBOL}")
                    self.elevation_chart.set_elevation_key(self.elevation_key)
                    self.weather_widget.setEnabled(True)
                    self.show_elevation_description()
                    return
        self.elevation_key = None
        self.slider.setValue(-1)
        self.elevation_chart.set_elevation_key(None)
        self.weather_widget.setEnabled(False)
        self.weather_widget.chooser.setCurrentIndex(0)
        self.show_elevation_description()

    def get_required_weather_filename(self) -> str | None:
        path = self.weather_widget.get_required_weather_filepath()
        return path.as_posix() if path else None

    def set_required_weather_filename(self, weather_filename: str | None) -> None:
        self.weather_widget.set_required_weather_filepath(weather_filename)

class PresetScheduleAtTimeWidget(PresetScheduleAtWidgetBase):

    class TimeFieldValidator(QValidator):

        def validate(self, text, pos):
            if len(text) < 4:
                return QValidator.State.Intermediate, text, pos
            state = QValidator.State.Invalid
            for acceptable_format in ['%H:%M', '%H%M']:
                try:
                    datetime.strptime(text, acceptable_format)
                    state = QValidator.State.Acceptable
                    break
                except ValueError:
                    pass
            return state, text, pos

    def __init__(self):
        super().__init__(description=tr("time-trigger"))
        self.setToolTip(tr("Trigger at the same time (hh:mm) each day."))
        self.setLayout(at_time_layout := QHBoxLayout())
        at_time_layout.addWidget(QLabel(tr("Trigger at time:")))
        self.editor_at_time_field = QLineEdit()
        self.editor_at_time_field.setValidator(PresetScheduleAtTimeWidget.TimeFieldValidator())
        at_time_layout.addWidget(self.editor_at_time_field)

        def clear_others_ask(_: str):
            if not self.clear_others():
                self.clear()

        self.editor_at_time_field.textChanged.connect(clear_others_ask)
        at_time_layout.addStretch(1)
        at_time_layout.setContentsMargins(0, 0, 0, 0)

    def is_set(self) -> bool:
        return len(self.text()) != 0

    def clear(self) -> None:
        if self.text():
            self.setText('')

    def setText(self, text: str) -> None:
        self.editor_at_time_field.setText(text)

    def text(self) -> str:
        if text := self.editor_at_time_field.text():
            if len(text) == 4:
                text = f"{text[:2]}:{text[2:]}"
        return text


class PresetsDialog(SubWinDialog, DialogSingletonMixin):  # TODO has become rather complex - break into parts?
    """A dialog for creating/updating/removing presets."""
    NO_ICON_ICON_NUMBER = StdPixmap.SP_ComputerIcon

    @staticmethod
    def invoke(main_controller: VduAppController, main_config: VduControlsConfig) -> None:
        PresetsDialog.show_existing_dialog() if PresetsDialog.exists() else PresetsDialog(main_controller, main_config)
        PresetsDialog.show_status_message('')

    @staticmethod
    def show_status_message(message: str = '', timeout: int = 0) -> None:
        if presets_dialog := PresetsDialog.get_instance():  # type: ignore
            if message != '':
                presets_dialog.status_message(message, timeout=timeout)
            elif not presets_dialog.main_config.is_set(ConfOpt.SCHEDULE_ENABLED):
                presets_dialog.status_message(
                    WARNING_SYMBOL + ' ' + tr('Preset scheduling is disabled in the Setting-Dialog.'))
            elif not presets_dialog.main_config.is_set(ConfOpt.WEATHER_ENABLED):
                presets_dialog.status_message(WARNING_SYMBOL + ' ' + tr('Weather lookup is disabled in the Setting-Dialog.'),
                                              timeout=60000)
            else:
                presets_dialog.status_message('')

    @staticmethod
    def reconfigure_instance() -> None:
        if presets_dialog := PresetsDialog.get_instance():  # type: ignore
            presets_dialog.reconfigure()

    @staticmethod
    def is_instance_editing() -> bool:
        if presets_dialog := PresetsDialog.get_instance():
            return presets_dialog.preset_name_edit.text() != ''
        return False

    @staticmethod
    def instance_indicate_active_preset(preset: Preset | None = None):
        if presets_dialog := PresetsDialog.get_instance():
            presets_dialog.indicate_active_preset(preset)

    @staticmethod
    def instance_edit_preset(preset: Preset | None = None):
        if presets_dialog := PresetsDialog.get_instance():
            presets_dialog.edit_preset(preset)

    def __init__(self, main_controller: VduAppController, main_config: VduControlsConfig) -> None:
        super().__init__()
        self.setWindowTitle(tr('Presets'))
        self.main_controller = main_controller
        self.main_config = main_config
        self.content_controls_map: Dict[Tuple[str, str], QCheckBox] = {}
        self.resize(npx(1800), npx(1200))
        self.setMinimumSize(npx(1350), npx(600))
        layout = QVBoxLayout()
        self.setLayout(layout)

        dialog_splitter = QSplitter()
        dialog_splitter.setOrientation(Qt.Orientation.Horizontal)
        dialog_splitter.setHandleWidth(npx(10))
        layout.addWidget(dialog_splitter, stretch=1)

        preset_list_panel = QGroupBox()
        preset_list_panel.setMinimumWidth(npx(550))
        preset_list_panel.setFlat(True)
        preset_list_layout = QVBoxLayout()
        preset_list_panel.setLayout(preset_list_layout)
        preset_list_title = QLabel(tr("Presets"))
        preset_list_title.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
        preset_list_layout.addWidget(preset_list_title)
        self.preset_widgets_scroll_area = QScrollArea(parent=self)
        preset_widgets_content = QWidget()
        self.preset_widgets_layout = QVBoxLayout()
        self.preset_widgets_layout.setSpacing(0)
        preset_widgets_content.setLayout(self.preset_widgets_layout)
        self.preset_widgets_scroll_area.setWidget(preset_widgets_content)
        self.preset_widgets_scroll_area.setWidgetResizable(True)
        preset_list_layout.addWidget(self.preset_widgets_scroll_area)
        dialog_splitter.addWidget(preset_list_panel)

        main_controller.refresh_preset_menu()
        self.base_ini = ConfIni()  # Create a temporary holder of preset values
        main_controller.populate_ini_from_vdus(self.base_ini)

        self.populate_presets_display_list()

        self.edit_panel = QWidget(parent=self)
        edit_panel_layout = QHBoxLayout()
        self.edit_panel.setLayout(edit_panel_layout)
        self.edit_panel.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))

        self.edit_choose_icon_button = PresetIconPickerButton()
        edit_panel_layout.addWidget(self.edit_choose_icon_button)

        self.preset_name_edit = QLineEdit()
        self.preset_name_edit.setToolTip(tr('Enter a new preset name.'))
        self.preset_name_edit.setClearButtonEnabled(True)
        self.preset_name_edit.textChanged.connect(self.change_edit_group_title)
        self.preset_name_edit.setValidator(QRegularExpressionValidator(QRegularExpression("[A-Za-z0-9][A-Za-z0-9_ .-]{0,60}")))

        self.vip_menu = QMenu()
        self.vip_menu.triggered.connect(self.vip_menu_triggered)
        edit_panel_layout.addWidget(self.preset_name_edit)
        self.vdu_init_button = ToolButton(VDU_CONNECTED_ICON_SOURCE, tr("Create VDU specific\nInitialization-Preset"), self)
        self.vdu_init_button.setMenu(self.vip_menu)
        self.vdu_init_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        edit_panel_layout.addWidget(self.vdu_init_button)

        self.editor_groupbox = QGroupBox()
        self.editor_groupbox.setFlat(True)
        self.editor_groupbox.setMinimumSize(npx(550), npx(768))
        self.editor_layout = QVBoxLayout()
        self.editor_layout.setSpacing(npx(20))
        self.editor_layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinimumSize)
        self.editor_title = QLabel(tr("New Preset:"))
        self.editor_title.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
        self.editor_layout.addWidget(self.editor_title)
        self.editor_groupbox.setLayout(self.editor_layout)

        self.editor_controls_widget = QScrollArea(parent=self)
        self.populate_editor_controls_widget()
        self.editor_layout.addWidget(self.edit_panel)

        self.controls_title_widget = self.editor_controls_prompt = QLabel(tr("Controls to include:"))
        self.controls_title_widget.setDisabled(True)
        self.editor_layout.addWidget(self.controls_title_widget)
        self.editor_layout.addWidget(self.editor_controls_widget)

        self.editor_transitions_widget = PresetTransitionWidget()
        if self.main_config.is_set(ConfOpt.PROTECT_NVRAM_ENABLED):
            self.editor_layout.addItem(QSpacerItem(1, 10))
        else:
            self.editor_layout.addWidget(self.editor_transitions_widget)

        self.editor_at_time_widget = PresetScheduleAtTimeWidget()
        self.editor_layout.addWidget(self.editor_at_time_widget)

        self.editor_at_elevation_widget = PresetScheduleAtElevationWidget(self.main_config)
        self.editor_layout.addWidget(self.editor_at_elevation_widget)

        possibles = [self.editor_at_time_widget, self.editor_at_elevation_widget]
        for schedule_choice_widget in possibles:
            schedule_choice_widget.set_schedule_widgets(possibles)

        dialog_splitter.addWidget(self.editor_groupbox)
        dialog_splitter.setCollapsible(0, False)
        dialog_splitter.setCollapsible(1, False)
        dialog_splitter.setSizes([preset_list_panel.minimumSize().width(), self.editor_groupbox.minimumSize().width()])

        self.status_bar = QStatusBar()

        def _revert_callable() -> None:
            preset_widget = self.find_preset_widget(self.preset_name_edit.text().strip())
            if preset_widget is None:
                self.preset_name_edit.setText('')
            else:
                self.edit_preset(preset_widget.preset)

        self.edit_clear_button = StdButton(icon=si(self, StdPixmap.SP_DialogCancelButton), title=tr('Clear'), clicked=self.reset_editor,
                                           tip=tr("Clear edits and enter a new preset using the defaults."))
        self.edit_save_button = StdButton(icon=si(self, StdPixmap.SP_DialogSaveButton), title=tr('Save'), clicked=self.save_preset,
                                          tip=tr("Save current VDU settings to Preset."))
        self.edit_revert_button = StdButton(icon=si(self, StdPixmap.SP_DialogResetButton), title=tr('Revert'), clicked=_revert_callable,
                                            tip=tr("Abandon edits, revert VDU and Preset settings."))
        self.close_button = StdButton(icon=si(self, StdPixmap.SP_DialogCloseButton), title=tr('Close'), clicked=self.close)
        for button in (self.edit_clear_button, self.edit_save_button, self.edit_revert_button, self.close_button):
            self.status_bar.addPermanentWidget(button)
        layout.addWidget(self.status_bar)

        self.edit_choose_icon_button.set_preset(None)
        self.editor_controls_widget.setDisabled(True)
        self.editor_at_time_widget.setDisabled(True)
        self.editor_transitions_widget.setDisabled(True)
        self.editor_at_elevation_widget.setDisabled(True)
        self.edit_save_button.setDisabled(True)
        self.edit_revert_button.setDisabled(True)

        self.indicate_active_preset(self.main_controller.which_preset_is_active())
        self.editor_controls_widget.adjustSize()
        self.make_visible()

    def sizeHint(self) -> QSize:
        return QSize(npx(1200), npx(768))

    def populate_presets_display_list(self) -> None:
        for i in range(self.preset_widgets_layout.count() - 1, -1, -1):  # Remove existing entries
            if item := self.preset_widgets_layout.itemAt(i):
                w = item.widget()
                if isinstance(w, PresetItemWidget):
                    self.preset_widgets_layout.removeWidget(w)
                    w.deleteLater()
                else:
                    self.preset_widgets_layout.removeItem(item)
        for preset_def in self.main_controller.preset_controller.find_presets_map().values():  # Populate new entries
            self.preset_widgets_layout.addWidget(self.create_preset_widget(preset_def))
        self.preset_widgets_layout.addStretch(1)

    def reconfigure(self) -> None:
        self.populate_presets_display_list()
        existing_content = self.editor_controls_widget.takeWidget()
        existing_content.deleteLater() if existing_content is not None else None
        self.base_ini = ConfIni()
        self.main_controller.populate_ini_from_vdus(self.base_ini)
        self.populate_editor_controls_widget()
        self.reset_editor()
        self.editor_at_elevation_widget.configure_for_location(self.main_config.get_location())

    def reset_editor(self):
        self.preset_name_edit.setText('')
        self.edit_choose_icon_button.reset()
        for checkbox in self.content_controls_map.values():
            checkbox.setChecked(True)

    def status_message(self, message: str, timeout: int = 0) -> None:
        self.status_bar.showMessage(message, msecs=3000 if timeout == -1 else timeout)

    def vip_menu_triggered(self, action: QAction):
        vdu_stable_id = action.data()
        if MBox(MIcon.Information, msg=tr('Create an initialization-preset for {}.').format(action.text()),
                info=tr('Initialization-presets are restored at startup or when ever the VDU is subsequently detected.'),
                buttons=MBtn.Ok | MBtn.Cancel).exec() == MBtn.Cancel:
            return
        self.preset_name_edit.setText(vdu_stable_id)
        for (section, option), checkbox in self.content_controls_map.items():
            checkbox.setChecked(section == vdu_stable_id)

    def find_preset_widget(self, preset_name: str) -> PresetItemWidget | None:
        for i in range(self.preset_widgets_layout.count()):
            w = self.preset_widgets_layout.itemAt(i).widget()
            if isinstance(w, PresetItemWidget) and w.name == preset_name:
                return w
        return None

    def indicate_active_preset(self, preset: Preset | None = None):
        self.preset_widgets_layout.findChildren(PresetItemWidget)
        for i in range(self.preset_widgets_layout.count()):
            if item := self.preset_widgets_layout.itemAt(i):
                w = item.widget()
                if isinstance(w, PresetItemWidget):
                    w.update_timer_button()
                    w.indicate_active(preset is not None and w.name == preset.name)

    def populate_editor_controls_widget(self):
        container = self.editor_controls_widget
        container.setMinimumHeight(native_font_height(scaled=6))  # making this too big throws the parent layout out of wack
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        self.content_controls_map = {}
        self.vip_menu.clear()  # VIP - VDU Initialization Preset
        for count, vdu_section_name in enumerate(self.base_ini.data_sections()):
            vdu_name = self.main_controller.get_vdu_preferred_name(vdu_section_name)
            if count > 0:
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setFrameShadow(QFrame.Shadow.Sunken)
                layout.addWidget(line)
            group_box = QGroupBox(vdu_name)
            group_box.setFlat(True)
            group_box.setToolTip(tr("Choose which settings to save for {}").format(vdu_name))
            group_layout = QHBoxLayout()
            group_box.setLayout(group_layout)
            for option in self.base_ini[vdu_section_name]:
                option_control = QCheckBox(translate_option(option))
                group_layout.addWidget(option_control)
                self.content_controls_map[(vdu_section_name, option)] = option_control
                option_control.setChecked(True)
            layout.addWidget(group_box)
            vip_action = QAction(f"{vdu_section_name} ({vdu_name})" if vdu_section_name != vdu_name else vdu_section_name,
                                 self.vip_menu)
            vip_action.setData(vdu_section_name)
            self.vip_menu.addAction(vip_action)
        container.setWidget(widget)

    def set_widget_values_from_preset(self, preset: Preset):
        self.preset_name_edit.setText(preset.name)
        self.edit_choose_icon_button.set_preset(preset)
        for key, item in self.content_controls_map.items():
            item.setChecked(preset.preset_ini.has_option(key[0], key[1]))
        if preset.preset_ini.has_section('preset'):
            self.editor_at_elevation_widget.clear()  # Clear both fields to stop any cross-field validation triggers.
            self.editor_at_time_widget.clear()
            self.editor_at_time_widget.setText(preset.get_at_time().strftime("%H:%M") if preset.get_at_time() else '')
            self.editor_at_elevation_widget.set_elevation_from_text(
                preset.preset_ini.get('preset', 'solar-elevation', fallback=None))
            self.editor_at_elevation_widget.set_required_weather_filename(
                preset.preset_ini.get('preset', 'solar-elevation-weather-restriction', fallback=None))
            self.editor_transitions_widget.set_transition_type(preset.get_transition_type())
            self.editor_transitions_widget.set_step_seconds(preset.get_step_interval_seconds())
            df = preset.get_daylight_factor()
            self.editor_at_elevation_widget.df_widget.setEnabled(df is not None)
            self.editor_at_elevation_widget.df_widget.df_input.setText(f"{df:.4f}" if df is not None else '')

    def has_changes(self, preset: Preset) -> bool:
        preset_ini_copy = preset.preset_ini.duplicate()
        self.populate_ini_from_gui(preset_ini_copy)  # get ini options from GUI checkbox and field values
        self.main_controller.populate_ini_from_vdus(preset_ini_copy, update_only=True)  # get current VDU values for ini options
        log_debug(f"has_changes {preset.preset_ini.diff(preset_ini_copy)=}") if log_debug_enabled else None
        return len(preset.preset_ini.diff(preset_ini_copy)) > 0

    def populate_ini_from_gui(self, preset_ini: ConfIni) -> None:  # initialise ini options based on GUI checkbox and field values
        for key, checkbox in self.content_controls_map.items():  # Populate ini options to indicate which settings need to be saved
            section, option = key
            if checkbox.isChecked():  # If this property is enabled, set its value
                if not preset_ini.has_section(section):
                    preset_ini.add_section(section)
                value = self.base_ini.get(section, option, fallback="%should not happen%")
                preset_ini.set(section, option, value)  # Just an initial value, it will be updated with the current VDU value later
            elif preset_ini.has_section(section) and preset_ini.has_option(section, option):
                preset_ini.remove_option(section, option)
        if not preset_ini.has_section('preset'):
            preset_ini.add_section('preset')
        if self.edit_choose_icon_button.last_selected_icon_path:
            preset_ini.set("preset", "icon", self.edit_choose_icon_button.last_selected_icon_path.as_posix())
        preset_ini.set('preset', 'at-time', self.editor_at_time_widget.text())
        preset_ini.set('preset', 'solar-elevation', format_solar_elevation_ini_text(self.editor_at_elevation_widget.elevation_key))
        if weather_filename := self.editor_at_elevation_widget.get_required_weather_filename():
            preset_ini.set('preset', 'solar-elevation-weather-restriction', weather_filename)
        elif preset_ini.get('preset', 'solar-elevation-weather-restriction', fallback=None):
            preset_ini.remove_option('preset', 'solar-elevation-weather-restriction')  # Remove existing restriction from ini
        preset_ini.set('preset', 'transition-type', str(self.editor_transitions_widget.get_transition_type()))
        preset_ini.set('preset', 'transition-step-interval-seconds', str(self.editor_transitions_widget.get_step_seconds()))
        preset_ini.set('preset', 'daylight-factor', str(self.editor_at_elevation_widget.df_widget.df_input.text()))

    def get_preset_widgets(self) -> List[PresetItemWidget]:
        return [self.preset_widgets_layout.itemAt(i).widget()
                for i in range(0, self.preset_widgets_layout.count() - 1)
                if isinstance(self.preset_widgets_layout.itemAt(i).widget(), PresetItemWidget)]

    def get_preset_names_in_order(self) -> List[str]:
        return [w.name for w in self.get_preset_widgets()]

    def add_preset_widget(self, preset_widget: PresetItemWidget) -> None:
        # Insert before trailing stretch item
        self.preset_widgets_layout.insertWidget(self.preset_widgets_layout.count() - 1, preset_widget)

    def up_action(self, preset: Preset, target_widget: QWidget) -> None:
        index = self.preset_widgets_layout.indexOf(target_widget)
        if index > 0:
            self.preset_widgets_layout.removeWidget(target_widget)
            self.preset_widgets_layout.insertWidget(index - 1, self.create_preset_widget(preset))
            target_widget.deleteLater()
            self.main_controller.save_preset_order(self.get_preset_names_in_order())
            self.preset_widgets_scroll_area.updateGeometry()

    def down_action(self, preset: Preset, target_widget: QWidget) -> None:
        index = self.preset_widgets_layout.indexOf(target_widget)
        if index < self.preset_widgets_layout.count() - 2:
            self.preset_widgets_layout.removeWidget(target_widget)
            self.preset_widgets_layout.insertWidget(index + 1, self.create_preset_widget(preset))
            target_widget.deleteLater()
            self.main_controller.save_preset_order(self.get_preset_names_in_order())
            self.preset_widgets_scroll_area.updateGeometry()

    def restore_preset(self, preset: Preset, immediately: bool = True) -> None:
        self.main_controller.restore_preset(preset, immediately=immediately)

    def delete_preset(self, preset: Preset, target_widget: QWidget) -> None:
        if MBox(MIcon.Question, msg=tr('Delete {}?').format(preset.name),
                buttons=MBtn.Ok | MBtn.Cancel, default=MBtn.Cancel).exec() == MBtn.Cancel:
            return
        self.main_controller.delete_preset(preset)
        self.preset_widgets_layout.removeWidget(target_widget)
        target_widget.deleteLater()
        self.main_controller.save_preset_order(self.get_preset_names_in_order())
        self.preset_name_edit.setText('')
        self.preset_widgets_scroll_area.updateGeometry()
        self.status_message(tr("Deleted {}").format(preset.name), timeout=-1)

    def change_edit_group_title(self) -> None:
        changed_text = self.preset_name_edit.text()
        if disable_controls := changed_text.strip() == "":
            self.edit_revert_button.setDisabled(True)
            self.editor_title.setText(tr("Create new preset:"))
            self.editor_controls_prompt.setText(tr("Controls to include:"))
        else:
            if self.find_preset_widget(changed_text):  # Already exists
                self.edit_revert_button.setDisabled(False)
                self.editor_title.setText(tr("Edit {}:").format(changed_text))
            else:
                self.edit_revert_button.setDisabled(True)
                self.editor_title.setText(tr("Create new preset:"))
            self.editor_controls_prompt.setText(tr("Controls to include in {}:").format(changed_text))
        self.editor_controls_widget.setDisabled(disable_controls)
        self.editor_transitions_widget.setDisabled(disable_controls)
        self.editor_at_time_widget.setDisabled(disable_controls)
        self.editor_at_elevation_widget.setDisabled(disable_controls)
        self.controls_title_widget.setDisabled(disable_controls)
        self.editor_transitions_widget.setDisabled(disable_controls)
        self.edit_save_button.setDisabled(disable_controls)
        self.edit_clear_button.setDisabled(disable_controls)

    def edit_preset(self, preset: Preset) -> None:

        def _begin_editing(worker: BulkChangeWorker | None = None) -> None:
            if worker is None or worker.completed:
                self.set_widget_values_from_preset(preset)
            else:
                self.status_message(tr(f"Failed to restore {preset.name} for editing."))
            self.setEnabled(True)

        if preset:
            self.setDisabled(True)  # Stop any editing until after the preset is restored.
            self.main_controller.restore_preset(preset, finished_func=_begin_editing, immediately=True)

    def save_preset(self, _: bool = False, from_widget: PresetItemWidget | None = None, quiet: bool = False) -> MBtn.Ok | MBtn.Cancel:
        preset: Preset | None = None
        widget_to_replace: PresetItemWidget | None = None
        if from_widget:  # A from_widget is requesting that the Preset's VDU current settings be updated.
            widget_to_replace = None  # Updating from widget, no change to icons or symbols, so no need to update the widget.
            preset = from_widget.preset  # Just update the widget's preset from the VDUs current settings
        elif preset_name := self.preset_name_edit.text().strip().replace('_', ' '):  # Saving from the save button, this may be new Preset or update.
            if widget_to_replace := self.find_preset_widget(preset_name):  # Already exists, update preset, replace widget
                preset = widget_to_replace.preset  # Use the widget's existing Preset.
            else:
                preset = Preset(preset_name)  # New Preset
        if preset is None or (quiet and not self.has_changes(preset)):  # Not found (weird), OR don't care if no changes made.
            return MBtn.Ok  # Nothing more to do, everything is OK

        preset_path = ConfIni.get_path(proper_name('Preset', preset.name))
        if preset_path.exists():  # Existing Preset
            if from_widget:  # The from_widget PresetWidget is initiating an update to the Preset from the VDUs settings.
                question = tr('Update existing {} preset with current monitor settings?').format(preset.name)
            else:  # The Preset Editor tab is modifying a Preset and it's PresetWidget.
                question = tr("Replace existing '{}' preset?").format(preset.name)
        else:  # New Preset
            question = tr("Save current edit?")
        answer = MBox(MIcon.Question, msg=question, buttons=MBtn.Save | MBtn.Discard | MBtn.Cancel, default=MBtn.Save).exec()
        if answer == MBtn.Discard:
            self.reset_editor()
            return MBtn.Ok
        elif answer == MBtn.Cancel:
            return MBtn.Cancel

        self.populate_ini_from_gui(preset.preset_ini)  # Initialises the options from the GUI, but does not get the VDU values.
        self.main_controller.populate_ini_from_vdus(preset.preset_ini, update_only=True)  # populate from VDU control values.

        if duplicated_presets := [other_preset for other_name, other_preset in self.main_controller.find_presets_map().items()
                                  if other_name != preset.name
                                     and preset.preset_ini.diff(other_preset.preset_ini, vdu_settings_only=True) == {}]:
            if MBox(MIcon.Warning, msg=tr("Duplicates existing Preset {}, save anyway?").format(duplicated_presets[0].name),
                    buttons=MBtn.Save | MBtn.Cancel, default=MBtn.Cancel).exec() == MBtn.Cancel:
                return MBtn.Cancel

        self.main_controller.save_preset(preset)

        if not from_widget:  # Which means the editor needs to update/create the PresetWidget, its icon, transition, weather, etc
            replacement_widget = self.create_preset_widget(preset)  # Create a new widget - an easy way to update the icon.
            if widget_to_replace:  # Existing widget need to update
                self.preset_widgets_layout.replaceWidget(widget_to_replace, replacement_widget)
                # The deleteLater removes the widget from the tree so that it is no longer findable and can be freed.
                widget_to_replace.deleteLater()
                self.make_visible()
            else:  # Must be a new Preset - create a new widget
                self.add_preset_widget(replacement_widget)
                self.main_controller.save_preset_order(self.get_preset_names_in_order())
                self.preset_widgets_scroll_area.ensureWidgetVisible(replacement_widget)
                QApplication.processEvents()  # TODO figure out why this does not work

        self.reset_editor()
        self.status_message(tr("Saved {}").format(preset.name), timeout=-1)
        return MBtn.Save

    def create_preset_widget(self, preset) -> PresetItemWidget:
        return PresetItemWidget(preset, restore_action=self.restore_preset, save_action=self.save_preset,
                                delete_action=self.delete_preset, edit_action=self.edit_preset,
                                up_action=self.up_action, down_action=self.down_action,
                                protect_nvram=self.main_config.is_set(ConfOpt.PROTECT_NVRAM_ENABLED))

    def event(self, event: QEvent | None) -> bool:
        # PalletChange happens after the new style sheet is in use.
        if event and event.type() == QEvent.Type.PaletteChange:
            self.repaint()
            self.vdu_init_button.refresh_icon()
        return super().event(event)

    def closeEvent(self, event) -> None:
        if self.save_preset(quiet=True) == MBtn.Cancel:
            event.ignore()
        else:
            self.reset_editor()
            super().closeEvent(event)


def exception_handler(e_type, e_value, e_traceback) -> None:
    """Overarching error handler in case something unexpected happens."""
    log_error("\n" + ''.join(traceback.format_exception(e_type, e_value, e_traceback)))
    MBox(MIcon.Critical, msg=tr('Error: {}').format(''.join(traceback.format_exception_only(e_type, e_value))),
         details=tr('Details: {}').format(''.join(traceback.format_exception(e_type, e_value, e_traceback)))).exec()


def create_pixmap_from_svg_bytes(svg_bytes: bytes) -> QPixmap:
    """There is no QIcon option for loading SVG from a string, only from a SVG file, so roll our own."""
    return QPixmap.fromImage(create_image_from_svg_bytes(svg_bytes))


def create_image_from_svg_bytes(svg_bytes) -> QImage:
    renderer = QSvgRenderer(svg_bytes)
    image = QImage(64, 64, QImage.Format.Format_ARGB32)
    image.fill(0x0)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    return image


svg_icon_cache: Dict[bytes, QIcon] = {}

def create_icon_from_svg_bytes(svg_bytes: bytes, theme_type: ThemeType = ThemeType.UNDECIDED) -> QIcon:
    """There is no QIcon option for loading SVG from a string, only from a SVG file, so roll our own."""
    if theme_type == ThemeType.UNDECIDED:
        theme_type = polychrome_light_or_dark()
    svg_bytes = handle_theme(svg_bytes, theme_type)
    if icon := svg_icon_cache.get(svg_bytes):
        return icon
    icon = QIcon(create_pixmap_from_svg_bytes(svg_bytes))
    svg_icon_cache[svg_bytes] = icon
    return icon


def handle_theme(svg_bytes: bytes, theme_type: ThemeType):
    assert theme_type != ThemeType.UNDECIDED
    if theme_type == ThemeType.MONOCHROME_LIGHT:
        return svg_bytes.replace(SVG_LIGHT_THEME_COLOR, b"#000000").replace(b"#ffffff", b"#000000")
    elif theme_type == ThemeType.MONOCHROME_DARK:
        return svg_bytes.replace(SVG_LIGHT_THEME_COLOR, b"#ffffff").replace(b"#000000", b"#ffffff")
    elif theme_type == ThemeType.POLYCHROME_LIGHT:
        return svg_bytes
    elif theme_type == ThemeType.POLYCHROME_DARK:
        return svg_bytes.replace(SVG_LIGHT_THEME_COLOR, SVG_DARK_THEME_COLOR)
    return svg_bytes

def create_icon_from_path(path: Path, theme_type: ThemeType) -> QIcon:
    if path.exists():
        if path.suffix == '.svg':
            with open(path, 'rb') as icon_file:
                icon_bytes = icon_file.read()
                icon = create_icon_from_svg_bytes(icon_bytes, theme_type)
        else:  # Hope the file contains something QIcon can cope with:
            icon = QIcon(path.as_posix())
        return icon
    # Copes with the case where the path has been deleted.
    return QApplication.style().standardIcon(StdPixmap.SP_MessageBoxQuestion)


def create_icon_from_text(text: str, theme_type: ThemeType) -> QIcon:
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    font = QApplication.font()
    font.setPixelSize(24)
    font.setWeight(QFont.Weight.Medium)
    painter.setFont(font)
    painter.setOpacity(1.0)
    if theme_type == ThemeType.MONOCHROME_LIGHT:
        painter.setPen(QColor("#000000"))
    elif theme_type == ThemeType.MONOCHROME_DARK:
        painter.setPen(QColor("#ffffff"))
    elif theme_type == ThemeType.POLYCHROME_DARK:
        painter.setPen(QColor(SVG_DARK_THEME_TEXT_COLOR.decode("utf-8")))
    else:  # default to a dark text color
        painter.setPen(QColor(SVG_LIGHT_THEME_TEXT_COLOR.decode("utf-8")))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignTop, text)
    painter.end()
    return QIcon(pixmap)


def create_decorated_app_icon(base_icon: QIcon, overlay_icon: QIcon | None = None,
                              left_indicator: QColor | None = None, right_indicator: QColor | None = None) -> QIcon:
    # Non-destructively overlay overlay_icon and indicators within a copy of base_icon.
    icon_size = QSize(64, 64)  # Everything is hard coded based on 64x64
    combined_pixmap = QPixmap(base_icon.pixmap(icon_size, QIcon.Mode.Normal, QIcon.State.On))
    painter = QPainter(combined_pixmap)
    if overlay_icon:
        overlay_pixmap = overlay_icon.pixmap(icon_size, QIcon.Mode.Normal, QIcon.State.On)
        painter.drawPixmap(16, 8, 32, 32, overlay_pixmap)
    painter.setPen(QPen(Qt.GlobalColor.black, 1, Qt.PenStyle.SolidLine))
    for i, led_color in enumerate((left_indicator, right_indicator)):
        if led_color:
            painter.setBrush(led_color)  # Each indicator resembles/simulates an LED embedded in the app icon.
            painter.drawEllipse(8 if i == 0 else 44, 32, 16, 16)
    painter.end()
    return QIcon(combined_pixmap)


def install_as_desktop_application(uninstall: bool = False) -> None:
    """Self install this script in the current Linux user's bin directory and desktop applications->settings menu."""
    desktop_dir = Path.home().joinpath('.local', 'share', 'applications')
    icon_dir = Path.home().joinpath('.local', 'share', 'icons')

    if not desktop_dir.exists():
        log_error(f"No desktop directory is present:{desktop_dir.as_posix()}"
                  " Cannot proceed - is this a non-standard desktop?")
        return

    bin_dir = Path.home().joinpath('bin')
    if not bin_dir.is_dir():
        log_warning(f"creating:{bin_dir.as_posix()}")
        os.mkdir(bin_dir)

    if not icon_dir.is_dir():
        log_warning("creating:{icon_dir.as_posix()}")
        os.mkdir(icon_dir)

    installed_script_path = bin_dir.joinpath("vdu_controls")
    desktop_definition_path = desktop_dir.joinpath("vdu_controls.desktop")
    icon_path = icon_dir.joinpath("vdu_controls.png")

    if uninstall:
        os.remove(installed_script_path)
        log_info(f"Removed {installed_script_path.as_posix()}")
        os.remove(desktop_definition_path)
        log_info(f"Removed {desktop_definition_path.as_posix()}")
        os.remove(icon_path)
        log_info(f"Removed {icon_path.as_posix()}")
        return

    if installed_script_path.exists():
        log_warning(f"reinstalling {installed_script_path.as_posix()}, assuming an upgrade is required.")

    source = open(__file__).read()
    source = source.replace("#!/usr/bin/python3", '#!' + sys.executable)
    log_info(f"Creating {installed_script_path.as_posix()}")
    open(installed_script_path, 'w').write(source)
    log_info(f"chmod u+rwx {installed_script_path.as_posix()}")
    os.chmod(installed_script_path, stat.S_IRWXU)

    if desktop_definition_path.exists():
        log_warning(f"Skipping installation of {desktop_definition_path.as_posix()}, it is already present.")
    else:
        log_info(f"Creating {desktop_definition_path.as_posix()}")
        desktop_definition = textwrap.dedent(f"""
            [Desktop Entry]
            Type=Application
            Exec={installed_script_path.as_posix()}
            Name={APPNAME}
            GenericName=DDC control panel for monitors
            Comment=Virtual Control Panel for externally connected VDUs
            Icon={icon_path.as_posix()}
            Categories=Qt;Settings;
            """)
        open(desktop_definition_path, 'w').write(desktop_definition)

    if icon_path.exists():
        log_warning(f"skipping installation of {icon_path.as_posix()}, it is already present.")
    else:
        log_info(f"Creating {icon_path.as_posix()}")
        get_splash_image().save(icon_path.as_posix())

    log_info(f"Installation complete. Your desktop->applications->settings should now contain {APPNAME}")


class LuxProfileWidget(QLabel):

    def __init__(self, lux_dialog: LuxDialog) -> None:
        super().__init__(parent=lux_dialog)
        self.lux_dialog = lux_dialog
        self.chart_changed_callback = lux_dialog.chart_changed_callback
        self.profiles_map = lux_dialog.lux_profiles_map
        self.preset_points = lux_dialog.preset_points
        self.main_controller: VduAppController = lux_dialog.main_controller
        self.vdu_chart_colors = self.lux_dialog.drawing_color_map
        self.range_restrictions = lux_dialog.range_restrictions_map  # Passed to chart
        self.current_lux = 0
        self.snap_to_margin = lux_dialog.lux_config.getint('lux-ui', 'snap-to-margin-pixels', fallback=4)
        self.current_vdu_sid = VduStableId('') if len(self.profiles_map) == 0 else list(self.profiles_map.keys())[0]
        self.x_origin, self.y_origin = 0, 0
        self.plot_width, self.plot_height = 0, 0
        self.setMouseTracking(True)  # Enable mouse move events so we can draw cross-hairs
        self.setMinimumWidth(npx(600))
        self.setMinimumHeight(npx(550))

    def resizeEvent(self, event: QResizeEvent | None) -> None:
        self.create_plot()

    def create_plot(self) -> None:
        dp_ratio = self.devicePixelRatio()
        pixmap = QPixmap(round(self.width() * dp_ratio), round(self.height() * dp_ratio))
        pixmap.setDevicePixelRatio(dp_ratio)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.plot_width, self.plot_height = self.width() - npx(200), self.height() - npx(170)
        self.x_origin, self.y_origin = npx(120), self.plot_height + npx(80)
        std_line_width = npx(4)
        interpolating = self.lux_dialog.is_interpolating()
        painter.fillRect(0, 0, self.width(), self.height(), QColor(0x5b93c5))
        painter.setPen(QPen(Qt.GlobalColor.white, std_line_width))
        painter.drawText(self.width() // 3, npx(30), tr("Lux Brightness Response Profiles"))

        tick_len = npx(5)
        painter.drawLine(self.x_origin, self.y_origin, self.x_origin + self.plot_width + 25, self.y_origin)  # Draw x-axis
        for lux in [0, 10, 100, 1_000, 10_000, 100_000]:  # Draw x-axis ticks
            x = self.x_from_lux(lux)
            painter.drawLine(self.x_origin + x, self.y_origin + tick_len, self.x_origin + x, self.y_origin - tick_len)
            painter.drawText(self.x_origin + x - npx(8) * len(str(lux)), self.y_origin + npx(40), str(lux))
        painter.drawText(self.x_origin + self.plot_width // 2 - len(str("Lux")), self.y_origin + npx(70), str("Lux"))

        painter.drawLine(self.x_origin, self.y_origin, self.x_origin, self.y_origin - self.plot_height)  # Draw y-axis
        for brightness in range(0, 101, 10):  # Draw y-axis ticks
            y = self.y_from_percent(brightness)
            painter.drawLine(self.x_origin - tick_len, self.y_origin - y, self.x_origin + tick_len, self.y_origin - y)
            painter.drawText(self.x_origin - npx(50), self.y_origin - y + npx(5), str(brightness))
        painter.save()
        painter.translate(self.x_origin - npx(70), self.y_origin - self.plot_height // 2 + npx(6) * len(tr("Brightness %")))
        painter.rotate(-90)
        painter.drawText(0, 0, tr("Brightness %"))
        painter.restore()

        if self.current_vdu_sid == '':  # Nothing to draw
            painter.end()
            self.setPixmap(pixmap)
            return

        min_v, max_v = self.range_restrictions.get(self.current_vdu_sid, (0, 100))  # Draw range restrictions (if not 0..100)
        if min_v > 0:
            painter.setPen(QPen(Qt.GlobalColor.red, std_line_width // 2, Qt.PenStyle.DashLine))
            cutoff = self.y_origin - self.y_from_percent(min_v)
            painter.drawLine(self.x_origin, cutoff, self.x_origin + self.plot_width + npx(25), cutoff)
        if max_v < 100:
            painter.setPen(QPen(Qt.GlobalColor.red, std_line_width // 2, Qt.PenStyle.DashLine))
            cutoff = self.y_origin - self.y_from_percent(max_v)
            painter.drawLine(self.x_origin, cutoff, self.x_origin + self.plot_width + npx(25), cutoff)

        point_markers = []  # Draw profile lines/histogram per vdu, current_profile last/on-top, collect point marker locations
        for vdu_sid, vdu_data in [(vid, data) for vid, data in self.profiles_map.items() if vid != self.current_vdu_sid] + \
                                 [(self.current_vdu_sid, self.profiles_map[self.current_vdu_sid])]:
            last_x, last_y = 0, 0
            if vdu_sid not in self.vdu_chart_colors:
                continue  # must have been turned off
            vdu_color_num = self.vdu_chart_colors[vdu_sid]
            vdu_line_color = QColor(vdu_color_num)
            histogram_bar_color = QColor(vdu_line_color)
            histogram_bar_color.setAlpha(50)
            for point_data in vdu_data:
                lux = point_data.lux
                brightness = point_data.brightness
                if brightness >= 0:
                    x = self.x_origin + self.x_from_lux(lux)
                    y = self.y_origin - self.y_from_percent(brightness)
                    if last_x and last_y:  # Join the previous and current point with a line
                        painter.setPen(QPen(vdu_line_color, std_line_width))
                        painter.drawLine(last_x, last_y, x, y)
                    if self.current_vdu_sid == vdu_sid:  # Special handling for the current/selected VDU
                        point_markers.append((point_data, x, y, lux, brightness, vdu_color_num))  # Save data for drawing markers
                    if last_x and last_y:  # draw a histogram-step, or if interpolating, the area under the line
                        painter.setBrush(histogram_bar_color)
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.drawPolygon(
                            QPolygon([QPoint(last_x, last_y), QPoint(x, y if interpolating else last_y),
                                      QPoint(x, self.y_origin), QPoint(last_x, self.y_origin), QPoint(last_x, last_y)]))
                    last_x, last_y = x, y
            if not interpolating and last_x and last_y:  # Show last step
                painter.fillRect(last_x, last_y, 15, self.y_origin - last_y, histogram_bar_color)

        for point_data, x, y, lux, brightness, vdu_color_num in point_markers:  # draw point-markers on top of lines and histograms
            if point_data.preset_name is None:  # Normal point
                marker_diameter = std_line_width * 4
                painter.setPen(QPen(QColor(vdu_color_num), std_line_width))
            else:  # Preset Point - fixed/non-deletable brightness level from Preset
                marker_diameter = std_line_width * 2
                painter.setPen(QPen(QColor(0xebfff9), std_line_width))
            painter.drawEllipse(x - marker_diameter // 2, y - marker_diameter // 2, marker_diameter, marker_diameter)

        pyramid_base = npx(16)
        pyramid = [(-pyramid_base // 2, 0), (0, -pyramid_base), (pyramid_base // 2, 0)]
        for preset_point in self.preset_points:  # for each Preset: draw a vertical-line and white-triangle below axis
            painter.setPen(QPen(Qt.GlobalColor.white, std_line_width // 2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.GlobalColor.white)
            x = self.x_origin + self.x_from_lux(preset_point.lux)
            painter.drawLine(x, self.y_origin, x, self.y_origin - self.plot_height)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(QPolygon([QPoint(x + tx, self.y_origin + npx(18) + ty) for tx, ty in pyramid]))

        lux_color = QColor(0xfeC053) # 0xfec053)
        if self.current_lux is not None:  # Draw a vertical-line at current lux
            painter.setPen(QPen(lux_color, npx(2)))  # fbc21b 0xffdd30 #fec053
            x_current_lux = self.x_origin + self.x_from_lux(self.current_lux)
            painter.drawLine(x_current_lux, self.y_origin + npx(10), x_current_lux, self.y_origin - self.plot_height - npx(10))
            for brightness in range(10, 101, 10):  # Draw y-axis ticks on lux current lux
                y = self.y_from_percent(brightness)
                painter.drawLine(x_current_lux - 2, self.y_origin - y, x_current_lux + 2, self.y_origin - y)
            trangle_h = npx(32)
            current_brightness_pointer = [(0, 0), (-trangle_h, trangle_h // 2), (-trangle_h, -trangle_h // 2)]
            # Indicate current brightness at current lux
            for vdu_sid, brightness in self.lux_dialog.current_brightness_map.items():
                if vdu_sid not in self.vdu_chart_colors:
                    continue  # must have been turned off
                vdu_color_num = self.vdu_chart_colors[vdu_sid]
                vdu_line_color = QColor(vdu_color_num)
                y = self.y_origin - self.y_from_percent(brightness)
                painter.setPen(QPen(Qt.GlobalColor.black, npx(1)))
                painter.setBrush(vdu_line_color)
                painter.drawPolygon(
                    QPolygon([QPoint(x_current_lux - 2 + tx // 2, y + 0 + ty // 2) for tx, ty in current_brightness_pointer]))

        marker_diameter = std_line_width * 4
        mouse_pos = self.mapFromGlobal(self.cursor().pos())  # Draw cross-hairs at mouse pos
        mouse_x, mouse_y, margin = mouse_pos.x(), mouse_pos.y(), self.snap_to_margin
        if margin <= mouse_x <= self.width() - margin and margin <= mouse_y <= self.height() - margin:
            x = clamp(mouse_x, self.x_origin, self.x_origin + self.plot_width)
            y = clamp(mouse_y, self.y_origin - self.plot_height, self.y_origin)
            match = self.find_close_to(x - self.x_origin, self.y_origin - y, self.current_vdu_sid)
            if match[0] is not None:  # Existing Point: snap to position for deleting the point under the mouse.
                x, y, lux, brightness, point_data = match[0] + self.x_origin, self.y_origin - match[1], match[2], match[3], match[4]
                point_preset_name = point_data.preset_name if point_data.preset_name is not None else ''
                if not point_preset_name:  # Existing normal point: cross-hairs, white for add, red for delete
                    painter.setPen(QPen(Qt.GlobalColor.red if match[0] is not None else Qt.GlobalColor.white, 2))
                    if match[0]:  # deletable: add a red circle
                        painter.setBrush(Qt.GlobalColor.white)
                        painter.drawEllipse(x - marker_diameter // 2, y - marker_diameter // 2, marker_diameter, marker_diameter)
                    painter.drawLine(self.x_origin, y, self.x_origin + self.plot_width + npx(5), y)
                    painter.drawLine(x, self.y_origin, x, self.y_origin - self.plot_height - npx(5))
                else:  # Existing Preset point: vertical line; plus removal hint, a red triangle below axis
                    painter.setPen(QPen(Qt.GlobalColor.red if mouse_y > self.y_origin else Qt.GlobalColor.white, 2))
                    painter.drawLine(x, self.y_origin, x, self.y_origin - self.plot_height - npx(5))
                    painter.setPen(QPen(Qt.GlobalColor.red, npx(2)))
                    painter.setBrush(Qt.GlobalColor.white)
                    painter.drawPolygon(QPolygon([QPoint(x + tx, self.y_origin + npx(18) + ty) for tx, ty in pyramid]))
                    if mouse_y > self.y_origin:  # Remove-Preset hint
                        painter.setPen(QPen(Qt.GlobalColor.black, npx(1)))
                        painter.drawText(x + npx(10), self.y_origin - npx(35), tr("Click remove preset at {} lux").format(lux))
            else:  # Potential new Point - show precise position for adding a new point
                lux, brightness = self.lux_from_x(x - self.x_origin), self.percent_from_y(y - self.y_origin)
                point_preset_name = ''
                painter.setPen(QPen(Qt.GlobalColor.white, npx(1)))
                painter.drawLine(self.x_origin, y, self.x_origin + self.plot_width + npx(5), y)
                painter.drawLine(x, self.y_origin, x, self.y_origin - self.plot_height - npx(5))
                if mouse_y > self.y_origin:  # Below axis, show a hint for adding a Preset point: draw a red triangle below axis
                    painter.setPen(QPen(Qt.GlobalColor.red, npx(2)))
                    painter.setBrush(Qt.GlobalColor.white)
                    painter.drawPolygon(QPolygon([QPoint(x + tx, self.y_origin + npx(18) + ty) for tx, ty in pyramid]))
                    painter.setPen(QPen(Qt.GlobalColor.black, npx(1)))
                    painter.drawText(x + 10, self.y_origin - npx(35), tr("Click to add preset at {} lux").format(lux))
            painter.setPen(QPen(Qt.GlobalColor.black, npx(1)))
            painter.drawText(x + 10, y - 10, f"{lux} lux, {brightness}% {point_preset_name}")  # Tooltip lux and percent

        painter.end()
        self.setPixmap(pixmap)

    def set_current_profile(self, name: VduStableId) -> None:
        self.current_vdu_sid = name
        self.create_plot()

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        if event:
            changed = False
            x = event.pos().x() - self.x_origin
            y = self.y_origin - event.pos().y()
            if event.button() == Qt.MouseButton.LeftButton:  # click along bottom (y=0) to attache presets
                changed = self.lux_point_edit(x, y) if y >= 0 else self.lux_preset_edit(x)
            if changed:
                self.show_changes()
        event.accept()

    def lux_point_edit(self, x, y) -> bool:
        assert self.current_vdu_sid != ''
        vdu_data = self.profiles_map[self.current_vdu_sid]
        _, _, existing_lux, existing_percent, existing_point = self.find_close_to(x, y, self.current_vdu_sid)
        if existing_lux is not None:  # Remove
            if existing_point.preset_name is None:
                vdu_data.remove(existing_point)
        else:  # Add
            percent = self.percent_from_y(y)
            lux = self.lux_from_x(x)
            vdu_data.append(LuxPoint(lux, percent))
            vdu_data.sort()
        return True

    def lux_preset_edit(self, x) -> bool:
        if point := self.find_preset_point_close_to(x):  # Delete
            self.preset_points.remove(point)
            for vdu_sid, profile in self.profiles_map.items():
                for profile_point in profile:
                    if profile_point == point:  # Note: these will not be the same object
                        if profile_point.preset_name and profile_point.brightness > 0:
                            # Convert to normal point - as a convenience for the user
                            profile_point.preset_name = None
                        else:  # Either an uncommitted LuxPoint or Preset without a brightness value, remove it.
                            profile.remove(profile_point)
                        break
            return True
        presets = self.main_controller.find_presets_map()
        if len(presets):
            ask_preset = QInputDialog()
            ask_preset.setComboBoxItems(list(presets.keys()))
            ask_preset.setOption(QInputDialog.InputDialogOption.UseListViewForComboBoxItems)
            if ask_preset.exec() == QInputDialog.DialogCode.Accepted:
                preset_name = ask_preset.textValue()
                if preset := self.main_controller.find_preset_by_name(preset_name):
                    point = LuxPoint(self.lux_from_x(x), -1, preset_name)
                    self.preset_points.append(point)
                    self.preset_points.sort()
                    for vdu_sid, profile in self.profiles_map.items():
                        preset_brightness = preset.get_brightness(vdu_sid) if preset is not None else -1
                        point = LuxPoint(self.lux_from_x(x), preset_brightness, preset_name)
                        profile.append(point)
                        profile.sort()
                    return True
        else:
            MBox(MIcon.Information, msg=tr("There are no Presets."), info=tr("Use the Presets Dialog to create some.")).exec()
        return False

    def show_changes(self, profile_changes=True) -> None:
        self.create_plot()
        if profile_changes:
            self.chart_changed_callback()

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:
        self.create_plot()

    def find_close_to(self, x: int, y: int, vdu_sid: VduStableId) -> Tuple:
        r = self.snap_to_margin
        for vdu_pd in self.profiles_map[vdu_sid]:
            existing_lux = vdu_pd.lux
            if vdu_pd.preset_name is None:
                existing_percent = vdu_pd.brightness
            else:
                if preset := self.main_controller.find_preset_by_name(vdu_pd.preset_name):
                    existing_percent = preset.get_brightness(vdu_sid)
                else:
                    continue  # Must have been deleted
            existing_x = self.x_from_lux(existing_lux)
            existing_y = self.y_from_percent(existing_percent)
            if existing_x - r <= x <= existing_x + r and (existing_y - r <= y <= existing_y + r or vdu_pd.preset_name is not None):
                return existing_x, existing_y, existing_lux, existing_percent, vdu_pd
        return None, None, None, None, None

    def find_preset_point_close_to(self, x: int) -> LuxPoint | None:
        for point in self.preset_points:
            point_x = self.x_from_lux(point.lux)
            if abs(point_x - x) <= self.snap_to_margin:
                return point
        return None

    def percent_from_y(self, y) -> int:
        percent = round(100.0 * abs(y) / self.plot_height)
        min_v, max_v = self.range_restrictions[self.current_vdu_sid]
        if percent > max_v:
            return max_v
        if percent < min_v:
            return min_v
        return percent

    def y_from_percent(self, percent) -> int:
        return round(self.plot_height * percent / 100)

    def lux_from_x(self, x) -> int:
        lux = 0 if x <= 0 else round(10.0 ** (math.log10(1) + (x / self.plot_width) * (math.log10(100_000) - math.log10(1))))
        if lux > 100_000:
            return 100_000
        return lux

    def x_from_lux(self, lux: int) -> int:
        return round((math.log10(lux) - math.log10(1)) / ((math.log10(100000) - math.log10(1)) / self.plot_width)) if lux > 0 else 0

@dataclass
class LuxGaugeHistory:
    lux: int
    when: datetime

class LuxGaugeWidget(QWidget):
    lux_changed_qtsignal = pyqtSignal(int)

    def __init__(self, parent: LuxDialog) -> None:
        super().__init__(parent=parent)
        self.max_history = 240
        self.history: List[LuxGaugeHistory | None] = [None] * (self.max_history // 10)
        self.sun_image = None
        self.lux_bar_color = QColor(0xfec053)
        self.white_line_color = w = QColor(0xfefefe)
        self.white_transparent_color = QColor(w.red(), w.green(), w.blue(), 30)
        self.orange_line_color = QColor(0xff8500)
        self.common_background_color = QColor(0x5b93c5)
        self.setLayout(widget_layout := QVBoxLayout())
        self.current_lux_display = QLabel()
        big_font = self.current_lux_display.font()
        big_font.setPointSize(big_font.pointSize() + 8)
        self.current_lux_display.setFont(big_font)
        widget_layout.addWidget(self.current_lux_display)
        self.plot_widget = QLabel()
        self.plot_widget.setFixedWidth(npx(340))
        self.plot_widget.setFixedHeight(npx(100))
        widget_layout.addWidget(self.plot_widget)
        self.current_meter: LuxMeterDevice | None = None
        self.stats_label = QLabel()
        self.help_text = tr("Left:\t Rolling display of metered lux (ML).\n"
                            "Right:\t 1) Estimated outside solar illumination (Eo) for\n"
                            "\t     the set geolocation for the current day.\n"
                            "\t 2) Estimated inside illumination (Ei = DF * Eo).\n"
                            "________________________________________________________________________________\n"
                            "Daylight Factor DF = ML/Eo\n"
                            "Eo = unit_constants * sin(radians(solar_altitude)) * 10 ** (-0.1 * air_mass)\n"
                            "Estimates of Ei are used by the semi-automatic metering option.")
        self.setToolTip(self.help_text)
        widget_layout.addWidget(self.stats_label)
        self.updates_enabled = True
        self.append_new_value(0)

    def mousePressEvent(self, a0):
        MBox(MIcon.Information, msg=self.help_text).exec()

    def append_new_value(self, lux: int) -> None:
        self.history = self.history[-self.max_history:]
        self.history.append(LuxGaugeHistory(lux, zoned_now()))
        if self.updates_enabled:
            self.current_lux_display.setText(tr("Lux: {}".format(lux)))
            self.update_plot()
            self.lux_changed_qtsignal.emit(lux)

    def update_plot(self):
        dp_ratio = self.devicePixelRatio()
        pixmap = QPixmap(round(self.plot_widget.width() * dp_ratio) , round(self.plot_widget.height() * dp_ratio))
        pixmap.setDevicePixelRatio(dp_ratio)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if QT5_QPAINTER_HIGH_QUALITY_ANTIALIASING:
            painter.setRenderHint(QT5_QPAINTER_HIGH_QUALITY_ANTIALIASING)
        plot_height = self.plot_widget.height()
        # Create a plot of recent historical lux readings.
        lux_plot_width = self.plot_widget.height()  # Square with height
        line_width = npx(4)
        thin_line_width = npx(2)

        painter.fillRect(0, 0, lux_plot_width, plot_height, self.common_background_color)
        painter.setPen(QPen(self.lux_bar_color, 1))
        most_recent_lux_xy = (None, None)  # draw pos of most recent
        for x, item in enumerate(self.history[-lux_plot_width:]):  # list position corresponds to x position
            if item:
                y = self._y_from_lux(item.lux, plot_height)
                painter.drawLine(x, plot_height, x, y)
                most_recent_lux_xy = (x, y)
            else:
                painter.drawLine(x, plot_height, x, self._y_from_lux(0, plot_height))
        if most_recent_lux_xy[0] is not None:
            painter.setPen(QPen(Qt.GlobalColor.red, 2))
            painter.drawLine(most_recent_lux_xy[0], plot_height, most_recent_lux_xy[0], most_recent_lux_xy[1])
        # Create plot of Eo (outside illumination) and Ei (inside illumination)
        margin = line_width
        painter.setPen(QPen(self.white_line_color, margin))
        painter.drawLine(lux_plot_width + margin // 2, plot_height, lux_plot_width + margin // 2, 0)
        df_plot_width = self.plot_widget.width() - lux_plot_width - margin
        minutes_per_point = (24 * 60) / df_plot_width
        df_plot_day = zoned_now().replace(hour=0, minute=0, second=0, microsecond=0)
        df_plot_left = lux_plot_width + margin #plot_width - df_plot_width - 30
        painter.fillRect(df_plot_left, 0, df_plot_left + df_plot_width, plot_height, self.common_background_color)
        # Plot the DF, Eo, Ei history as a block
        painter.setPen(QPen(self.lux_bar_color, 1))
        most_recent_df_xy = (None, None) # Indicate the last history position with a red dot
        most_recent_item = None
        for item in self.history:  # Block fill for history
            if item and item.when > df_plot_day:
                t = (item.when - df_plot_day).total_seconds() // 60
                i = int(df_plot_left + t // minutes_per_point)
                item_y_pos = self._y_from_lux(item.lux, plot_height)
                painter.drawLine(i, plot_height, i, item_y_pos)
                most_recent_df_xy = (i, item_y_pos)
                most_recent_item = item
        # Plot Eo and Ei
        eo_points = []
        ei_points = []
        painter.setPen(QPen(self.white_transparent_color, thin_line_width))
        t = df_plot_day + timedelta(minutes=0)
        df = LuxMeterSemiAutoDevice.get_daylight_factor()
        if location := LuxMeterSemiAutoDevice.get_location():
            for i in range(df_plot_left, df_plot_left + df_plot_width):
                eo_y = self._y_from_lux(calc_solar_lux(t, location, 1.0), plot_height * 10)  # scale * 10 for more accuracy
                eo_points.append(QPointF(i, eo_y / 10.0))  # scale down to floating-point precision drawing co-ordinates
                eo_x = self._y_from_lux(calc_solar_lux(t, location, df), plot_height * 10)
                ei_points.append(QPointF(i, eo_x / 10.0))  # scale down to floating-point precision drawing co-ordinates
                t += timedelta(minutes=minutes_per_point)
                painter.drawLine(i, plot_height, i, eo_y)  # Fill under eo line
            # Actually plot the two datasets
            painter.setPen(QPen(self.orange_line_color, thin_line_width * 3))
            painter.drawPolyline(eo_points)
            painter.setPen(QPen(self.white_line_color, thin_line_width * 3))
            painter.drawPolyline(ei_points)
        # Add text to the axis
        painter.setPen(QPen(self.white_line_color, thin_line_width))
        painter.setFont(QFont(QApplication.font().family(), fz := 5, QFont.Weight.Normal))
        middle = df_plot_left - margin // 2
        for i in (10, 100, 1_000, 10_000, 100_000):
            painter.drawLine(middle - line_width, y := self._y_from_lux(i, plot_height), middle + line_width, y)
            painter.drawText(QPointF(middle + npx(6), y + 4), str(i))
        # Draw hour ticks along the bottom
        tick_len = line_width * 2
        noon_tick_len = line_width * 4
        for hx in range((hw := 60 // round(minutes_per_point)), hw * 25, hw):
            painter.drawLine(x := df_plot_left + hx, plot_height, x, plot_height - (noon_tick_len if hx == (12 * hw) else tick_len))
        # Draw the sun
        if most_recent_df_xy and most_recent_item and most_recent_df_xy[0]:
            if self.sun_image is None:
                self.sun_image = create_image_from_svg_bytes(SUN_SVG.replace(SVG_LIGHT_THEME_COLOR, b"#feC053")).scaled(
                    npx(36), npx(36))
            t = (most_recent_item.when - df_plot_day).total_seconds() // 60
            i = int(df_plot_left + t // minutes_per_point)
            if location:
                sun_y = self._y_from_lux(calc_solar_lux(most_recent_item.when, location, 1.0), plot_height)
                if sun_y <= plot_height - self.sun_image.height() // 2 - 1:
                    painter.drawImage(QPoint(i - self.sun_image.width() // 2, sun_y - self.sun_image.height() // 2 - 1),
                                      self.sun_image)
        if most_recent_df_xy[0] is not None:
            painter.setPen(QPen(Qt.GlobalColor.red, thin_line_width))
            painter.drawLine(most_recent_df_xy[0], plot_height, most_recent_df_xy[0], most_recent_df_xy[1])
        # Draw dots at current points
        dot_size = line_width * 2
        half_dot_size = dot_size // 2
        for x, y in (most_recent_lux_xy, most_recent_df_xy):
            if x is not None and y is not None:
                painter.setPen(QPen(Qt.GlobalColor.red, half_dot_size))
                painter.setBrush(self.white_line_color)
                painter.drawEllipse(x - half_dot_size, y - half_dot_size, dot_size, dot_size)
        painter.end()  # End of plotting
        self.plot_widget.setPixmap(pixmap)
        # Add some text to the bottom
        if location:
            eo = calc_solar_lux(zoned_now(), location, 1.0)
            self.stats_label.setText(tr("Eo={:,} lux    DF={:,.4f}").format(eo, df))
        else:
            self.stats_label.setText(tr("Eo=?   DF=?   (location not set)"))

    def connect_meter(self, new_lux_meter: LuxMeterDevice | None) -> None:
        if self.current_meter:
            self.current_meter.new_lux_value_qtsignal.disconnect(self.append_new_value)
        self.current_meter = new_lux_meter
        if self.current_meter:
            self.current_meter.new_lux_value_qtsignal.connect(self.append_new_value)
            if new_lux_meter and new_lux_meter.has_manual_capability:
                if lux := new_lux_meter.get_value():
                    self.append_new_value(round(lux))
            self.enable_gauge(True)

    def enable_gauge(self, enable: bool = True) -> None:
        if enable:
            self.history = (self.history + [None] * 2)[-self.max_history:]  # Make a little gap in the history to show where we are
            self.update_plot()
        self.updates_enabled = enable

    def _y_from_lux(self, lux: int, required_height: int) -> int:
        return required_height - (
            round((math.log10(lux) - math.log10(1)) / ((math.log10(200000) - math.log10(1)) / required_height)) if lux > 0 else 0)


def lux_create_device(device_name: str) -> LuxMeterDevice:
    if device_name == LuxMeterSemiAutoDevice.device_name:
        return LuxMeterSemiAutoDevice()
    if not pathlib.Path(device_name).exists():
        raise LuxDeviceException(tr("Failed to set up {} - path does not exist.").format(device_name))
    if not os.access(device_name, os.R_OK):
        raise LuxDeviceException(tr("Failed to set up {} - no read access to device.").format({device_name}))
    if pathlib.Path(device_name).is_char_device():
        return LuxMeterSerialDevice(device_name)
    elif pathlib.Path(device_name).is_fifo():
        return LuxMeterFifoDevice(device_name)
    elif pathlib.Path(device_name).exists() and os.access(device_name, os.X_OK):
        return LuxMeterExecutableDevice(device_name)
    raise LuxDeviceException(tr("Failed to set up {} - not a recognized kind of device or not executable.").format(device_name))


class LuxMeterDevice(QObject):
    new_lux_value_qtsignal = pyqtSignal(int)

    def __init__(self, requires_worker: bool = True, manual: bool = False, semi_auto: bool = False) -> None:
        super().__init__()
        log_debug(f"LuxMeterDevice init {manual=} {semi_auto=}") if log_debug_enabled else None
        self.current_value: float | None = None
        self.requires_worker = requires_worker
        self.has_manual_capability = manual # Can be both manual and semi-automatic
        self.has_semi_auto_capability = semi_auto
        self.has_auto_capability = not self.has_manual_capability or self.has_semi_auto_capability
        if self.requires_worker:  # use a thread to prevent any blocking due to slow updating
            log_info(f"LuxMeterDevice: starting worker for {self.__class__}")
            self.worker = WorkerThread(task_body=self.update_from_worker_thread, task_finished=self.cleanup, loop=True)

    def get_value(self) -> float | None:  # an un-smoothed raw value - TODO should smoothing be moved here?
        if self.current_value is None and self.requires_worker:
            self.worker.start() if not self.worker.isRunning() else None
            while self.current_value is None and not self.worker.stop_requested:  # have to block on the first time through.
                time.sleep(0.1)
        return self.current_value

    def update_from_worker_thread(self, _: WorkerThread) -> None:  # Only for meters that have background workers.
        pass

    def set_current_value(self, new_value: float) -> None:
        self.current_value = max(new_value, 1.0)  # Never less than 1 - for safety - don't want to dim to zero.
        self.new_lux_value_qtsignal.emit(round(new_value))

    def cleanup(self, _: WorkerThread):
        pass

    def stop_metering(self) -> None:
        if self.requires_worker:
            self.worker.stop()

    def get_status(self) -> Tuple[bool, str]:  # True if OK, plus any message
        return True, ''


class LuxMeterFifoDevice(LuxMeterDevice):

    def __init__(self, device_name: str) -> None:
        super().__init__()
        self.device_name = device_name
        self.fifo: int | None = None
        self.buffer = b''

    def update_from_worker_thread(self, _: WorkerThread) -> None:
        try:
            if self.fifo is None:
                log_info(f"Initialising fifo {self.device_name} - waiting on fifo data.")
                self.fifo = os.open(self.device_name, os.O_RDONLY | os.O_NONBLOCK)
            while not self.worker.stop_requested and len(select.select([self.fifo], [], [], 1.0)[0]) == 1:
                byte = os.read(self.fifo, 1)
                if byte is None:
                    self.cleanup()  # Fifo has closed, maybe meter is resetting
                elif byte == b'\n':
                    if len(self.buffer) > 0:
                        self.set_current_value(float(self.buffer.decode()))
                        self.buffer = b''
                else:
                    self.buffer += byte
        except (OSError, ValueError) as se:
            self.cleanup()
            self.buffer = b''
            log_warning(f"Reopen and retry {self.device_name=} {self.buffer=}", se, trace=True)

    def cleanup(self, worker: WorkerThread | None = None):
        if self.fifo is not None:
            log_info("closing fifo")
            os.close(self.fifo)
            self.fifo = None


class LuxMeterExecutableDevice(LuxMeterDevice):

    def __init__(self, device_name: str) -> None:
        super().__init__()
        self.runnable = device_name
        self.sleep_time = float(os.getenv("LUX_METER_RUNNABLE_SLEEP", default='60.0'))

    def update_from_worker_thread(self, _: WorkerThread) -> None:
        try:
            result = subprocess.run([self.runnable], stdout=subprocess.PIPE, check=True)
            self.set_current_value(float(result.stdout))
        except (OSError, ValueError, subprocess.CalledProcessError) as se:
            log_warning(f"Error running {self.runnable}, will retry in {self.sleep_time} seconds", se, trace=True)
        self.worker.doze(self.sleep_time)  # Don't re-run too fast


class LuxMeterSerialDevice(LuxMeterDevice):

    def __init__(self, device_name: str) -> None:
        super().__init__()
        self.device_name = device_name
        self.serial_device = None
        self.line_matcher = re.compile(r'\A([0-9]+[.][0-9]+)\r\n\Z', re.DOTALL)  # Be precise to try and catch errors
        self.backoff_secs = self.initial_backoff_secs = 10
        try:
            self.serial_module = import_module('serial')
        except ModuleNotFoundError as mnf:
            raise LuxDeviceException(tr("The required pyserial serial-port module is not installed on this system.")) from mnf

    def update_from_worker_thread(self, _: WorkerThread) -> None:
        problem = None
        try:
            if self.serial_device is None:
                log_info(f"LuxMeterSerialDevice: Initialising character device {self.device_name}")
                self.serial_device = self.serial_module.Serial(self.device_name)
            if self.serial_device is not None:
                self.serial_device.reset_input_buffer()
                buffer = self.serial_device.read_until()
                decoded = buffer.decode('utf-8', errors='surrogateescape')
                if match := self.line_matcher.match(decoded):  # only accept correctly formatted output
                    self.set_current_value(float(match.group(1)))
                    self.backoff_secs = self.initial_backoff_secs
                else:
                    problem = f"value that failed to parse: {decoded.encode('unicode_escape')}"
            self.worker.doze(1.0)
        except (self.serial_module.SerialException, termios.error, FileNotFoundError, ValueError) as se:
            problem = se
        if problem:
            log_warning(f"Retry read of {self.device_name}, will reopen feed in {self.backoff_secs} seconds. Cause:", problem,
                        trace=True)
            self.cleanup()
            self.worker.doze(self.backoff_secs)
            self.backoff_secs = self.backoff_secs * 2 if self.backoff_secs < 300 else 300

    def cleanup(self, worker: WorkerThread | None = None):
        if self.serial_device is not None:
            log_debug("closing serial device") if log_debug_enabled else None
            self.serial_device.close()
            self.serial_device = None


class LuxMeterSemiAutoDevice(LuxMeterDevice):  # is both manual and automatic - semi-automatic
    obsolete_device_name = 'Slider-Control'
    device_name = 'solar-lux-calculator'
    location: GeoLocation | None = None
    daylight_factor: float | None = None

    def __init__(self) -> None:
        super().__init__(requires_worker=False, manual=True, semi_auto=True)
        self.current_value: float = LuxMeterSemiAutoDevice.get_stored_value()
        LuxMeterSemiAutoDevice.daylight_factor = None    # Force initilization from file
        _ = LuxMeterSemiAutoDevice.get_daylight_factor()

    def get_value(self) -> float | None:
        if location := LuxMeterSemiAutoDevice.get_location():
            if lux := calc_solar_lux(zoned_now(), location, LuxMeterSemiAutoDevice.get_daylight_factor()):
                self.set_current_value(lux)  # only set if in daylight
        return self.current_value

    def set_current_value(self, new_value: float) -> None:
        if (new_value := round(new_value)) != round(self.current_value):
            self.save_stored_value(new_value)
        super().set_current_value(new_value)

    def stop_metering(self) -> None:
        pass

    def get_status(self) -> Tuple[bool, str]:
        return (False, tr('No location defined.')) if self.location is None else super().get_status()

    @staticmethod
    def get_stored_value() -> float:
        persisted_path = CONFIG_DIR_PATH.joinpath("lux_manual_value.txt")
        if persisted_path.exists():
            try:
                return float(persisted_path.read_text())
            except ValueError:
                log_error(f"LuxSemiAuto: failed to parse stored lux value, removing {persisted_path.as_posix()}")
                persisted_path.unlink()
        return 1000.0

    @staticmethod
    def save_stored_value(new_value: float):
        if CONFIG_DIR_PATH.exists():
            CONFIG_DIR_PATH.joinpath("lux_manual_value.txt").write_text(str(round(new_value)))

    @staticmethod
    def get_daylight_factor() -> float:
        if LuxMeterSemiAutoDevice.daylight_factor is None:
            daylight_factor = 1.0
            persisted_path = CONFIG_DIR_PATH.joinpath("lux_daylight_factor.txt")
            if persisted_path.exists():
                try:
                    daylight_factor = float(persisted_path.read_text())
                except ValueError:
                    log_error(f"LuxSemiAuto: failed to parse daylight_factor, removing {persisted_path.as_posix()}")
                    persisted_path.unlink()
            else:
                log_error(f"LuxSemiAuto: {persisted_path.as_posix()} does not exist")
            log_debug(f'LuxSemiAuto: {daylight_factor=} ({persisted_path.as_posix()})') if log_debug_enabled else None
            LuxMeterSemiAutoDevice.daylight_factor = daylight_factor
        return LuxMeterSemiAutoDevice.daylight_factor

    @staticmethod
    def update_df_from_lux_value(new_lux_value: float, semi_auto_source: bool):
        if location := LuxMeterSemiAutoDevice.location:
            solar_lux = calc_solar_lux(zoned_now(), location, 1.0)
            if solar_lux > (0 if semi_auto_source else 1000):  # only for reasonable daylight lux levels or if the user is driving.
                daylight_factor =  new_lux_value / solar_lux
                LuxMeterSemiAutoDevice.set_daylight_factor(daylight_factor, internal=True, persist=semi_auto_source)

    @staticmethod
    def set_daylight_factor(daylight_factor: float, internal: bool = False, persist: bool = False):
        daylight_factor = round(daylight_factor, 4)
        if LuxMeterSemiAutoDevice.daylight_factor is None or abs(LuxMeterSemiAutoDevice.daylight_factor - daylight_factor) > 0.001:
            if persist:
                if CONFIG_DIR_PATH.exists():
                    persisted_path = CONFIG_DIR_PATH.joinpath("lux_daylight_factor.txt")
                    log_debug(f"LuxSemiAuto: save {daylight_factor=} to {persisted_path.as_posix()}") if log_debug_enabled else None
                persisted_path.write_text(f"{daylight_factor:.4f}")
            LuxMeterSemiAutoDevice.daylight_factor = daylight_factor
            if not internal:
                LuxDialog.reconfigure_instance()

    @staticmethod
    def get_location() -> GeoLocation | None:
        return LuxMeterSemiAutoDevice.location

    @staticmethod
    def set_location(location: GeoLocation | None):
        LuxMeterSemiAutoDevice.location = location


class LuxSmooth:
    def __init__(self, n: int, alpha: float = 0.5) -> None:
        self.length: int = n
        self.input: List[float] = []
        self.output: List[float] = []
        self.alpha: float = alpha

    def smooth(self, v: float) -> int:  # A low pass filter
        # The smaller the alpha, the more each previous value affects the following value. Smaller alpha results => more smoothing.
        # https://stackoverflow.com/questions/4611599/smoothing-data-from-a-sensor
        # https://en.wikipedia.org/wiki/Low-pass_filter#Simple_infinite_impulse_response_filter
        if len(self.input) == self.length:
            self.input.pop(0)
            self.output.pop(0)
        self.input.append(v)
        self.output.append(v)  # extend to same length - value will be overwritten if there is more than one sample.
        for i in range(1, len(self.input)):
            self.output[i] = self.output[i - 1] + self.alpha * (self.input[i] - self.output[i - 1])
        return round(self.output[-1])


class LuxStepStatus(Enum):
    ENCOUNTERED_ERROR = -2
    UNEXPECTED_CHANGE = -1
    FINISHED = 0,
    MORE_TO_DO = 1,


@dataclass
class LuxToDo:
    vdu_sid: VduStableId
    brightness: int
    preset_name: str | None
    current_brightness: int | None = None

class LuxAutoWorker(WorkerThread):  # Why is this so complicated?

    _lux_dialog_message_qtsignal = pyqtSignal(str, int, MsgDestination)

    def __init__(self, auto_controller: LuxAutoController, single_shot: bool) -> None:
        super().__init__(task_body=self._adjust_for_lux, task_finished=self._adjust_for_lux_finished)
        self.single_shot = single_shot  # Called for an on-demand single time assessment with immediate effect.
        self.main_controller = auto_controller.main_controller
        self.adjust_now_requested = False
        lux_config = auto_controller.get_lux_config()
        log_info(f"LuxAuto: lux-meter.interval-minutes={lux_config.get_interval_minutes()} {single_shot=}")
        self.sleep_seconds = lux_config.get_interval_minutes() * 60
        self.consecutive_error_count = 0

        def _get_prop(prop: str, fallback: bool | int | float | str) -> bool | int | float:
            op = {bool: lux_config.getboolean, int: lux_config.getint, float: lux_config.getfloat}[type(fallback)]
            value = op('lux-meter', prop, fallback=fallback)
            log_info(f"LuxAuto: lux-meter.{prop}={value}")
            return value

        samples_per_minute = _get_prop('samples-per-minute', fallback=3)
        self.sampling_interval_seconds = 60 // samples_per_minute
        self.smoother = LuxSmooth(_get_prop('smoother-n', fallback=5), alpha=_get_prop('smoother-alpha', fallback=0.5))
        self.interpolation_enabled = _get_prop('interpolate-brightness', fallback=True)
        self.sensitivity_percent = _get_prop('interpolation-sensitivity-percent', fallback=10)
        self.step_pause_millis = _get_prop('step-pause-millis', fallback=1000)
        self._lux_dialog_message_qtsignal.connect(LuxDialog.lux_dialog_message)
        self._lux_dialog_message_qtsignal.connect(self.main_controller.main_window.status_message)
        self.status_message(f"{TIMER_RUNNING_SYMBOL} 00:00", 0, MsgDestination.COUNTDOWN)

    def status_message(self, message: str, timeout: int = 0, destination: MsgDestination = MsgDestination.DEFAULT) -> None:
        self._lux_dialog_message_qtsignal.emit(message, timeout, destination)

    def _adjust_for_lux(self, _: WorkerThread) -> None:
        try:
            lux_auto_controller = self.main_controller.get_lux_auto_controller()
            # Give any previous thread a chance to exit, plus let the GUI and presets settle down
            self.doze(2) if not self.single_shot else None
            log_info(f"LuxAuto: monitoring commences {thread_pid()=}")
            assert lux_auto_controller is not None
            while not self.stop_requested:
                error_count = self.consecutive_error_count
                busy_main_controller = self.main_controller.busy_doing()
                if lux_meter := lux_auto_controller.lux_meter:
                    if (status := lux_meter.get_status())[0]:
                        if metered_lux := lux_meter.get_value():
                            if not busy_main_controller:
                                if to_do_list := self.assemble_required_work(lux_auto_controller, metered_lux,
                                                                             not lux_meter.has_manual_capability):
                                    self.do_work(to_do_list)
                    elif status[1]:
                        self.status_message(status[1], timeout=5000)
                    if self.single_shot:
                        break
                else:  # In-app config change - things are in a state of flux
                    log_error("Exiting, no lux meter available.")
                    break
                if error_count == self.consecutive_error_count:  # no change - must be OK now
                    log_debug("LuxAuto: clearing consecutive_error_count") if log_debug_enabled else None
                    self.consecutive_error_count = 0
                self.idle_sampling(lux_meter, busy_main_controller)  # Sleep and sample for rest of cycle
        finally:
            log_info(f"LuxAuto: exiting (stop_requested={self.stop_requested}) {thread_pid()=}")

    def assemble_required_work(self, lux_auto_controller: LuxAutoController, metered_lux: float, requires_smoothing) -> List[LuxToDo]:
        lux = self.smoother.smooth(metered_lux) if requires_smoothing else round(metered_lux)
        summary_text = self.lux_summary(metered_lux, lux)
        self.status_message(f"{SUN_SYMBOL} {summary_text} {PROCESSING_LUX_SYMBOL}", timeout=3000)
        to_do_list: List[LuxToDo] = []
        for vdu_sid in self.main_controller.get_vdu_stable_id_list():  # For each VDU, do one step of its profile
            if self.stop_requested:
                return []
            value_range = self.main_controller.get_range(vdu_sid, BRIGHTNESS_VCP_CODE, fallback=(0, 100))
            lux_profile = lux_auto_controller.get_lux_profile(vdu_sid, value_range)
            if to_do := self.determine_changes(vdu_sid, lux, lux_profile):
                to_do_list.append(to_do)
        self.assess_presets_collectively(to_do_list)
        return to_do_list

    def assess_presets_collectively(self, to_do_list: List[LuxToDo]) -> None:
         if to_do_list:  # See if all items are in agreement on whether a preset should be used
             for preset_name in [x.preset_name for x in to_do_list]:
                 if preset := self.main_controller.find_preset_by_name(preset_name):
                     sids_present = set(self.main_controller.get_vdu_stable_id_list())
                     sids_present_and_in_preset = sids_present.intersection(set(preset.get_vdu_sids()))
                     items_with_this_preset = [x for x in to_do_list if x.preset_name == preset_name]
                     sids_of_items_with_this_preset = set([x.vdu_sid for x in items_with_this_preset])
                     log_debug(f"LuxAuto: {sids_present_and_in_preset=} {sids_of_items_with_this_preset=}")
                     if sids_present_and_in_preset == sids_of_items_with_this_preset:
                         log_debug(f"LuxAuto: applying Preset {preset_name}")
                         for item in items_with_this_preset:
                             if (preset_brightness := preset.get_brightness(item.vdu_sid)) > 0:
                                 item.brightness = preset_brightness
                     else:
                         log_debug(f"LuxAuto: ignoring Preset {preset_name} doesn't match for all VDUs present.")
                         for item in items_with_this_preset:
                             item.preset_name = None
                 else:
                     log_debug(f"LuxAuto: ignoring Preset {preset_name} no longer exists.")

    def do_work(self, to_do_list: List[LuxToDo]):
        to_do_preset_names = []
        bulk_changer = BulkChangeWorker('LuxAutoBulk', main_controller=self.main_controller,
                                        progress_callable=self._to_do_progress, finished_callable=self._to_do_finished,
                                        step_interval=self.step_pause_millis / 1000.0, context=to_do_preset_names)
        for to_do in to_do_list:
            if to_do.brightness != -1:
                bulk_change_item = BulkChangeItem(to_do.vdu_sid, BRIGHTNESS_VCP_CODE, to_do.brightness,
                                                  current_value=to_do.current_brightness,
                                                  transition=True)  # only transitions if protect-nvram is False.
                bulk_changer.add_item(bulk_change_item)
            if to_do.preset_name and to_do.preset_name not in to_do_preset_names:
                to_do_preset_names.append(to_do.preset_name)
        bulk_changer.run()  # Call run instead of start; run in this thread instead of a new thread.

    def _to_do_progress(self, _: BulkChangeWorker):
        self.status_message(f"{SUN_SYMBOL} {STEPPING_SYMBOL}")

    def _to_do_finished(self, worker: BulkChangeWorker):
        if worker.completed:
            if to_do_preset_names := worker.context:
                self.doze(0.5)  # Give the user a chance to read messages
                for preset_name in to_do_preset_names:  # if a point had a Preset attached, activate it now
                    # Restoring the Preset's non-brightness settings. Invoke now, so it will happen in this thread's sleep period.
                    if preset := self.main_controller.find_preset_by_name(preset_name):  # Check that it still exists
                        log_debug(f"LuxAuto: restoring Preset {preset.name=}") if log_debug_enabled else None
                        self.main_controller.restore_preset(
                            preset, immediately=PresetTransitionFlag.SCHEDULED not in preset.get_transition_type(),
                            background_activity=True)
                    else:
                        log_debug("LuxAuto: Preset {preset.name} no longer exists - ignoring") if log_debug_enabled else None
                        self.main_controller.update_window_status_indicators()
        else:
            log_debug("LuxAuto: bulk worker failed to complete.") if log_debug_enabled else None
            self.status_message(f"{SUN_SYMBOL} {ERROR_SYMBOL} {RAISED_HAND_SYMBOL}")
            self.consecutive_error_count += 1

    def _adjust_for_lux_finished(self, _: WorkerThread) -> None:
        log_debug("LuxAuto: worker finished") if log_debug_enabled else None
        if self.vdu_exception:
            log_error(f"LuxAuto: exited with exception={self.vdu_exception}")

    def idle_sampling(self, lux_meter: LuxMeterDevice, busy_main_controller: str | None):
        seconds = 2 if self.consecutive_error_count == 1 else self.sleep_seconds
        log_debug(f"LuxAuto: sleeping {seconds=}") if log_debug_enabled else None
        if busy_main_controller:
            self.status_message(
                tr("Task waiting for {} to finish.").format(busy_main_controller), timeout=0, destination=MsgDestination.DEFAULT)
        for second in range(seconds, -1, -1):
            if busy_main_controller and not self.main_controller.busy_doing():
                break  # the main controller is no longer busy
            if self.stop_requested or self.adjust_now_requested:  # Respond to stop requests while sleeping
                self.adjust_now_requested = False
                break
            if not lux_meter.has_manual_capability:  # Update the smoother every n seconds, but not at the start or end of the period.
                if (0 < second < self.sleep_seconds) and second % self.sampling_interval_seconds == 0:
                    if metered_lux := lux_meter.get_value():  # Update the smoothing while sleeping
                        self.status_message(
                            f"{SUN_SYMBOL} {self.lux_summary(metered_lux, self.smoother.smooth(metered_lux))}", timeout=3000)
            self.status_message(f"{TIMER_RUNNING_SYMBOL} {second // 60:02d}:{second % 60:02d}", 0, MsgDestination.COUNTDOWN)
            self.doze(1)

    def determine_changes(self, vdu_sid: VduStableId, smoothed_lux: int, lux_profile: List[LuxPoint]) -> LuxToDo | None:
        previous_normal_point = matched_point = lower_point = LuxPoint(0, 0)
        proposed_brightness = 0
        # Update/bind the current Preset values onto the LuxPoints and wrap with min and max values.
        for profile_point in [LuxPoint(0, 0), *lux_profile, LuxPoint(100000, 100)]:
            # Moving up the lux steps, seeking the step below smoothed_lux
            if smoothed_lux > profile_point.lux:  # Possible result, there may be something higher, keep going...
                # if profile_point.brightness is -1, this is a Preset that doesn't change the VDU's brightness control
                if profile_point.brightness >= 0:  # else use existing result_brightness
                    proposed_brightness = profile_point.brightness
                matched_point = profile_point
            else:  # Step is too high, if interpolating check against the following point, if not, the previous match is the result.
                if self.interpolation_enabled:  # Only interpolate if lux is not an exact match and next_point has a brightness
                    if smoothed_lux != matched_point.lux and profile_point.brightness >= 0:
                        # if profile_point.brightness is -1, this is a Preset that doesn't change the VDU's brightness control
                        lower_point = matched_point if matched_point.brightness >= 0 else previous_normal_point
                        proposed_brightness = self.interpolate_brightness(smoothed_lux, lower_point, profile_point)
                break
            if profile_point.brightness > 0:
                previous_normal_point = profile_point
        try:
            preset_name = self.assess_preset_proximity(proposed_brightness, lower_point, matched_point, profile_point)
            current_brightness = self.main_controller.get_value(vdu_sid, BRIGHTNESS_VCP_CODE)
            diff = proposed_brightness - current_brightness
            if self.interpolation_enabled and preset_name is None and abs(diff) < self.sensitivity_percent:
                log_info(f"LuxAuto: {smoothed_lux=} {vdu_sid=} {current_brightness=} {proposed_brightness=} ignored, too small")
                self.status_message(f"{SUN_SYMBOL} {proposed_brightness}% {ALMOST_EQUAL_SYMBOL} {current_brightness}% {vdu_sid}",
                                    timeout=5000)
                return None
            if log_debug_enabled:
                log_debug(f"LuxAuto: {smoothed_lux=} {vdu_sid=} {current_brightness=}% {proposed_brightness=}% {preset_name=}")
            return LuxToDo(vdu_sid, proposed_brightness, preset_name, current_brightness)
        except VduException as e:
            self.consecutive_error_count += 1
            log_debug(f"LuxAuto: {self.consecutive_error_count=} error getting brightness: {e}") if log_debug_enabled else None
        return None

    def interpolate_brightness(self, smoothed_lux: int, current_point: LuxPoint, next_point: LuxPoint) -> int:

        def _x_from_lux(lux: int) -> float:
            return ((math.log10(lux) - math.log10(1)) / (math.log10(100000) - math.log10(1))) if lux > 0 else 0

        interpolated_brightness = float(current_point.brightness)
        x_smoothed = _x_from_lux(smoothed_lux)
        x_current_point = _x_from_lux(current_point.lux)
        x_next_point = _x_from_lux(next_point.lux)
        interpolated_brightness += (next_point.brightness - current_point.brightness) * (
                x_smoothed - x_current_point) / (x_next_point - x_current_point)
        return round(interpolated_brightness)

    def assess_preset_proximity(self, proposed_brightness: float,
                                previous_normal_point: LuxPoint, matched_point: LuxPoint, next_point: LuxPoint) -> str | None:
        # Brightness is a better indicator of nearness for deciding whether to activate a preset
        ordered = sorted([(abs(proposed_brightness - matched_point.brightness), matched_point),
                          (abs(proposed_brightness - previous_normal_point.brightness), previous_normal_point),
                          (abs(proposed_brightness - next_point.brightness), next_point)], key=lambda x: x[0])
        for diff, item in ordered:
            if diff < self.sensitivity_percent and (pick := item.preset_name):
                log_debug(f"LuxAuto: assess_preset_proximity {pick=}") if log_debug_enabled else None
                return pick
        return None

    def lux_summary(self, metered_lux: float, smoothed_lux: int) -> str:
        lux_int = round(metered_lux)  # 256 bit char in lux_summary_text can cause issues if stdout not utf8 (force utf8 for stdout)
        return f"{lux_int}{SMOOTHING_SYMBOL}{smoothed_lux} lux" if lux_int != smoothed_lux else f"{lux_int} lux"

    def stop(self) -> None:
        super().stop()
        assert is_running_in_gui_thread()
        self._lux_dialog_message_qtsignal.disconnect()
        log_info("LuxAuto: stopped on request")


@dataclass
class LuxPoint:
    lux: int
    brightness: int
    preset_name: str | None = None

    def __lt__(self, other) -> bool:  # Brightness doesn't matter for comparion purposes.
        return self.lux < other.lux

    def __eq__(self, other) -> bool:  # Brightness doesn't matter for comparion purposes.
        return self.lux == other.lux and self.preset_name == other.preset_name

    def __hash__(self):  # Brightness doesn't matter for comparion purposes.
        return hash((self.lux, self.preset_name))

    def __str__(self):
        return f"({self.lux} lux, {self.brightness}%, preset={self.preset_name})"


class LuxDeviceType(namedtuple('LuxDevice', 'name description'), Enum):
    SEMI_AUTO = "calculator", QT_TR_NOOP("Semi-automatic geolocated")
    ARDUINO = "arduino", QT_TR_NOOP("Arduino tty device")
    FIFO = "fifo", QT_TR_NOOP("Linux FIFO")
    EXECUTABLE = "executable", QT_TR_NOOP("Script/program")


class LuxConfig(ConfIni):

    def __init__(self) -> None:
        super().__init__()
        self.path = ConfIni.get_path('AutoLux')
        self.last_modified_time = 0.0
        self.cached_profiles_map: Dict[str, List[LuxPoint]] = {}

    def get_device_name(self) -> str:
        return self.get("lux-meter", "lux-device", fallback='')

    def get_preset_points(self) -> List[LuxPoint]:
        if self.has_option('lux-presets', 'lux-preset-points'):
            return [LuxPoint(lux, -1, name) for lux, name in literal_eval(self.get('lux-presets', 'lux-preset-points'))]
        return []

    def get_interval_minutes(self) -> int:
        return self.getint('lux-meter', 'interval-minutes', fallback=10)

    def is_auto_enabled(self) -> bool:
        return self.getboolean("lux-meter", "automatic-brightness", fallback=False)

    def load(self, force: bool = False) -> LuxConfig:
        self.cached_profiles_map.clear()
        if self.path.exists():
            if Path.stat(self.path).st_mtime > self.last_modified_time or force:
                log_info(f"Reading autolux file '{self.path.as_posix()}'")
                text = Path(self.path).read_text()
                self.read_string(text)
                self.last_modified_time = Path.stat(self.path).st_mtime
        for section_name in ['lux-meter', 'lux-profile', 'lux-ui', 'lux-presets']:
            if not self.has_section(section_name):
                self.add_section(section_name)
        return self


class LuxDialog(SubWinDialog, DialogSingletonMixin):

    @staticmethod
    def invoke(main_controller: VduAppController) -> None:
        LuxDialog.show_existing_dialog() if LuxDialog.exists() else LuxDialog(main_controller)

    @staticmethod
    def reconfigure_instance():
        if lux_dialog := LuxDialog.get_instance():  # type: ignore
            lux_dialog.reconfigure()

    @staticmethod
    def lux_dialog_message(message: str, timeout: int, destination: MsgDestination = MsgDestination.DEFAULT) -> None:
        if lux_dialog := LuxDialog.get_instance():  # type: ignore
            lux_dialog.status_message(message, timeout, destination)

    @staticmethod
    def lux_dialog_show_brightness(vdu_stable_id: VduStableId, brightness: int) -> None:
        if lux_dialog := LuxDialog.get_instance():  # type: ignore
            lux_dialog.current_brightness_map[vdu_stable_id] = brightness
            lux_dialog.profile_plot.show_changes(profile_changes=False)

    def __init__(self, main_controller: VduAppController) -> None:
        super().__init__()
        self.setWindowTitle(tr('Light-Metering'))
        self.main_controller: VduAppController = main_controller
        self.lux_profiles_map: Dict[VduStableId, List[LuxPoint]] = {}
        self.range_restrictions_map: Dict[VduStableId, Tuple[int, int]] = {}
        self.preset_points: List[LuxPoint] = []
        self.drawing_color_map: Dict[VduStableId, QColor] = {}
        self.current_brightness_map: Dict[VduStableId, int] = {}
        self.has_profile_changes = False
        self.setMinimumWidth(npx(950))
        self.path = ConfIni.get_path('AutoLux')
        self.device_name = ''
        self.lux_config = main_controller.get_lux_auto_controller().get_lux_config()

        self.setLayout(main_layout := QVBoxLayout())
        main_layout.addWidget(top_box := QWidget())
        top_box.setLayout(top_box_layout := QGridLayout())

        self.lux_gauge_widget = LuxGaugeWidget(self)

        top_box_layout.addWidget(self.lux_gauge_widget, 0, 0, 4, 2, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        existing_device = self.lux_config.get_device_name()
        existing_device_type = self.lux_config.get('lux-meter', 'lux-device-type', fallback='')
        self.meter_device_selector = QComboBox()
        for i, dev_type in enumerate(LuxDeviceType):
            if dev_type.name == existing_device_type:  # List existing device and device type, set it as selected.
                self.meter_device_selector.addItem(f"{tr(dev_type.description)}: {existing_device}", dev_type)
                self.meter_device_selector.setCurrentIndex(i)
            else:
                self.meter_device_selector.addItem(tr(dev_type.description), dev_type)  # List device type only.

        top_box_layout.addWidget(self.meter_device_selector, 0, 2, 1, 3)

        self.enabled_checkbox = QCheckBox(tr("Enable automatic brightness adjustment"))
        top_box_layout.addWidget(self.enabled_checkbox, 1, 2, 1, 3)

        self.interval_label = QLabel(tr("Adjustment interval minutes"))
        top_box_layout.addWidget(self.interval_label, 2, 2, 1, 2)

        self.interval_selector = QSpinBox()
        self.interval_selector.setMinimum(1)
        self.interval_selector.setMaximum(120)
        top_box_layout.addWidget(self.interval_selector, 2, 4, 1, 1)

        self.interpolate_checkbox = QCheckBox(tr("Interpolate brightness values"))
        top_box_layout.addWidget(self.interpolate_checkbox, 3, 2, 1, 3)
        self.setMinimumSize(top_box.minimumSize())

        self.profile_selector_widget = QListWidget(parent=self)
        self.profile_selector_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.profile_selector_widget.setSizeAdjustPolicy(QListWidget.SizeAdjustPolicy.AdjustToContents)
        self.profile_selector_widget.setFlow(QListWidget.Flow.LeftToRight)
        self.profile_selector_widget.setSpacing(0)
        self.profile_selector_widget.setMinimumHeight(native_font_height(scaled=1.4))

        main_layout.addWidget(self.profile_selector_widget, stretch=0)

        self.profile_plot = LuxProfileWidget(self)

        def _lux_changed(lux: int) -> None:
            if self.profile_plot:
                self.profile_plot.current_lux = lux
                self.profile_plot.create_plot()

        self.lux_gauge_widget.lux_changed_qtsignal.connect(_lux_changed)

        main_layout.addWidget(self.profile_plot, stretch=1)

        self.status_bar = QStatusBar()
        self.save_button = StdButton(icon=si(self, StdPixmap.SP_DriveFDIcon), title=tr("Save Profiles"), clicked=self.save_profiles,
                                     tip=tr("Apply and save profile-chart changes."))
        self.revert_button = StdButton(icon=si(self, StdPixmap.SP_DialogResetButton), title=tr("Revert Profiles"),
                                       clicked=self.reconfigure, tip=tr("Abandon profile-chart changes, revert to last saved."))
        quit_button = StdButton(icon=si(self, StdPixmap.SP_DialogCloseButton), title=tr("Close"), clicked=self.close)
        for button in (self.save_button, self.revert_button, quit_button):
            self.status_bar.addPermanentWidget(button, 0)

        self.status_layout = QHBoxLayout()
        main_layout.addLayout(self.status_layout)
        self.adjust_now_button = StdButton(clicked=self.main_controller.get_lux_auto_controller().adjust_brightness_now,
                                           tip=tr("Press to expire the timer and immediately evaluate brightness."))
        self.status_layout.addWidget(self.adjust_now_button, 0)
        self.adjust_now_button.hide()
        self.status_layout.addWidget(self.status_bar)

        def _choose_device(index: int) -> None:
            current_dev = self.lux_config.get('lux-meter', "lux-device", fallback=LuxMeterSemiAutoDevice.device_name)
            current_dev_type = self.lux_config.get('lux-meter', "lux-device-type", fallback=LuxDeviceType.SEMI_AUTO.name)
            new_dev_type = self.meter_device_selector.itemData(index)
            if new_dev_type == LuxDeviceType.SEMI_AUTO:
                new_dev_path = LuxMeterSemiAutoDevice.device_name
            elif new_dev_type in (LuxDeviceType.ARDUINO, LuxDeviceType.FIFO, LuxDeviceType.EXECUTABLE):
                if current_dev_type == new_dev_type.name:
                    default_file = current_dev
                else:
                    default_file = "/dev/arduino" if new_dev_type == LuxDeviceType.ARDUINO else Path.home().as_posix()
                new_dev_path = FasterFileDialog.getOpenFileName(
                    self, tr("Select: {}").format(tr(new_dev_type.description)), default_file)[0]
            if not self.validate_device(new_dev_path, required_type=new_dev_type):
                new_dev_path = ''
            if new_dev_path == '':  # Mothing selected, set back to what was in config
                for dev_num in range(self.meter_device_selector.count()):
                    config_device_type = self.lux_config.get('lux-meter', 'lux-device-type', fallback='')
                    if self.meter_device_selector.itemData(dev_num).name == config_device_type:
                        self.meter_device_selector.setCurrentIndex(dev_num)
            else:
                if new_dev_path != current_dev:
                    self.meter_device_selector.setItemText(index, tr(new_dev_type.description) + ': ' + new_dev_path)
                    self.lux_config.set('lux-meter', "lux-device", new_dev_path)
                    self.lux_config.set('lux-meter', "lux-device-type", new_dev_type.name)
                    self.lux_config.save(self.path)
                    self.apply_settings()
                    if (device := self.main_controller.get_lux_auto_controller().lux_meter) and device.has_auto_capability:
                        self.main_controller.get_lux_auto_controller().set_auto(True) # Enable auto if the meter is full auto or semi-auto
                    self.status_message(tr("Meter changed to {}.").format(new_dev_path))

        self.meter_device_selector.activated.connect(_choose_device)

        def _set_auto_monitoring(checked: int) -> None:
            enable = checked == intV(Qt.CheckState.Checked)
            if enable != self.lux_config.is_auto_enabled():
                self.lux_config.set('lux-meter', 'automatic-brightness', 'yes' if enable else 'no')
                self.adjust_now_button.setVisible(enable)
                self.apply_settings()

        self.enabled_checkbox.stateChanged.connect(_set_auto_monitoring)

        def _apply_interval(value: int) -> None:
            if self.interval_selector.value() == value and value != self.lux_config.get_interval_minutes():
                self.lux_config.set('lux-meter', 'interval-minutes', str(value))
                self.apply_settings()
                self.status_message(tr("Interval changed to {} minutes.").format(value))

        def _interval_selector_changed(value: int) -> None:
            if self.interval_selector.value() == value and value != self.lux_config.get_interval_minutes():
                QTimer.singleShot(1200, partial(_apply_interval, value))  # kind of like focus out, no change in a while

        self.interval_selector.valueChanged.connect(_interval_selector_changed)

        def _set_interpolation(checked: int) -> None:
            if checked == intV(Qt.CheckState.Checked):  # need to save setting if not already set
                if not self.lux_config.getboolean('lux-meter', 'interpolate-brightness', fallback=False):  # altering value
                    self.lux_config.set('lux-meter', 'interpolate-brightness', 'yes')
                    MBox(MIcon.Information, msg=tr('Interpolation may increase the number of writes to VDU NVRAM.'),
                         info=tr('Changes specified by each brightness-response curve will only be applied when they '
                                 'cross a minimum threshold (default {}%).\n\n'
                                 'When designing brightness-response curves, consider minimizing '
                                 'brightness changes to reduce wear on NVRAM.').format(10)).exec()
            elif self.lux_config.getboolean('lux-meter', 'interpolate-brightness', fallback=True):
                self.lux_config.set('lux-meter', 'interpolate-brightness', 'no')
            self.apply_settings()
            self.profile_plot.create_plot()

        self.interpolate_checkbox.stateChanged.connect(_set_interpolation)

        def _select_profile(index: int) -> None:
            if self.profile_plot is not None:
                profile_name = list(self.lux_profiles_map.keys())[index]
                self.profile_plot.set_current_profile(profile_name)
                self.status_message(tr("Editing profile {}").format(profile_name))
            data = self.profile_selector_widget.item(index).data(Qt.ItemDataRole.UserRole)
            if self.lux_config.get('lux-ui', 'selected-profile', fallback=None) != data:
                self.lux_config.set('lux-ui', 'selected-profile', data)
                self.apply_settings(requires_metering_restart=False)

        self.profile_selector_widget.currentRowChanged.connect(_select_profile)
        self.reconfigure()
        self.make_visible()

    def chart_changed_callback(self) -> None:
        self.has_profile_changes = True
        self.status_message(tr("Press Save-Profile to activate new profile."))
        self.save_button.setEnabled(True)
        self.revert_button.setEnabled(True)

    def reconfigure(self) -> None:
        assert self.profile_plot is not None
        # Make a copy of the config so the profile changes aren't applied until Apply is pressed.
        lux_auto_controller = self.main_controller.get_lux_auto_controller()
        self.lux_config = lux_auto_controller.get_lux_config().duplicate(LuxConfig())  # type: ignore
        self.device_name = self.lux_config.get("lux-meter", "lux-device", fallback='')
        log_debug("{self.lux_config.is_auto_enabled()=}") if log_debug_enabled else None
        self.enabled_checkbox.setChecked(self.lux_config.is_auto_enabled())
        self.interpolate_checkbox.setChecked(self.lux_config.getboolean('lux-meter', 'interpolate-brightness', fallback=False))
        self.has_profile_changes = False
        self.current_brightness_map.clear()
        self.save_button.setEnabled(False)
        self.revert_button.setEnabled(False)
        self.adjust_now_button.setText(f"{TIMER_RUNNING_SYMBOL} 00:00")
        self.adjust_now_button.setVisible(self.lux_config.is_auto_enabled())

        connected_id_list = []  # List of all currently connected VDUs
        for index, vdu_sid in enumerate(self.main_controller.get_vdu_stable_id_list()):
            value_range = (0, 100)
            if self.main_controller.is_vcp_code_enabled(vdu_sid, BRIGHTNESS_VCP_CODE):
                value_range = self.main_controller.get_range(vdu_sid, BRIGHTNESS_VCP_CODE, fallback=value_range)
                self.range_restrictions_map[vdu_sid] = value_range
                try:
                    self.current_brightness_map[vdu_sid] = self.main_controller.get_value(vdu_sid, BRIGHTNESS_VCP_CODE)
                except VduException as ve:
                    self.current_brightness_map[vdu_sid] = 0
                    log_warning("VDU may not be available:", str(ve), trace=True)
            # All VDUs have a profile, even if they have no brightness control - because a preset may be attached to a lux value.
            self.lux_profiles_map[vdu_sid] = lux_auto_controller.get_lux_profile(vdu_sid, value_range)
            connected_id_list.append(vdu_sid)
        self.preset_points.clear()  # Edit out deleted presets by starting from scratch
        for preset_point in self.lux_config.get_preset_points():
            if preset_point.preset_name is not None and self.main_controller.find_preset_by_name(preset_point.preset_name):
                self.preset_points.append(preset_point)

        self.interval_selector.setValue(self.lux_config.get_interval_minutes())
        existing_id_list = [item.data(Qt.ItemDataRole.UserRole) for item in self.profile_selector_widget.findItems('*', Qt.MatchFlag.MatchWildcard)]
        candidate_id = self.lux_config.get('lux-ui', 'selected-profile', fallback=None)
        if connected_id_list and (candidate_id is None or candidate_id not in connected_id_list):
            candidate_id = connected_id_list[0]
        try:
            self.profile_selector_widget.blockSignals(True) # Stop initialization from causing signal until all data is aligned.
            if connected_id_list != existing_id_list:  # List of connected VDUs has changed
                self.profile_selector_widget.clear()
                random.seed(int(self.lux_config.get("lux-ui", "vdu_color_seed", fallback='0x543fff'), 16))
                self.drawing_color_map.clear()
                for index, vdu_sid in enumerate(connected_id_list):
                    color = QColor.fromHsl(int(index * 137.508) % 255, random.randint(64, 128), random.randint(192, 200))
                    self.drawing_color_map[vdu_sid] = color
                    color_icon = create_icon_from_svg_bytes(SWATCH_ICON_SOURCE.replace(b"#ffffff", bytes(color.name(), 'utf-8')))
                    key_item = QListWidgetItem(color_icon, self.main_controller.get_vdu_preferred_name(vdu_sid))
                    key_item.setData(Qt.ItemDataRole.UserRole, vdu_sid)
                    self.profile_selector_widget.addItem(key_item)
                    if vdu_sid == candidate_id:
                        self.profile_selector_widget.setCurrentRow(index)
                        self.profile_plot.current_vdu_sid = candidate_id
                self.profile_selector_widget.setFixedHeight(
                    native_font_height(scaled=1.5) * (1 if len(connected_id_list) <= 3 else 5))
        finally:
            self.profile_selector_widget.blockSignals(False)
        self.configure_ui(lux_auto_controller.lux_meter)
        self.profile_plot.create_plot()
        lux_auto_controller.lux_meter.get_value() if lux_auto_controller.lux_meter else None  # prime the UI
        self.status_message('')

    def make_visible(self) -> None:
        self.lux_gauge_widget.enable_gauge(True)
        super().make_visible()

    def is_interpolating(self) -> bool:
        return self.interpolate_checkbox.isChecked()

    def validate_device(self, device, required_type: LuxDeviceType) -> bool:
        if required_type == LuxDeviceType.SEMI_AUTO:
            if self.main_controller.main_config.get_location() is None:
                MBox(MIcon.Critical, msg=tr("Cannot configure a solar lux calculator, no location is defined."),
                     info=tr("Please set a location in the main Settings-Dialog.")).exec()
                self.main_controller.edit_config(tab_number=0)
                return False
            MBox(MIcon.Information,
                 msg=tr("Semi-automatic lux adjustment: quick start instructions.\n"                      
                        "________________________________________________________________________________________\n\n"
                        "Use the ambient-light-level slider to set the current light level.\n\n"
                        "Starting from your chosen level, the application will adjust the light level\n"
                        "according to a trajectory based on the estimated sunlight for your location.\n\n"
                        "If conditions change, adjust the slider to alter the trajectory.\n\n"
                        "The trajectory is shown in the Light Metering Dialog, along with the estimate\n"
                        "of outdoor lux (Eo) and the Daylight-Factor (DF), the ratio of indoor to\n"
                        "outdoor lux.\n"),
                 details=tr("Estimation of indoor illumination (Ei) from solar illumination (Eo):\n"
                            "    Ei = DF * Eo\n"
                            "    DF = Ei / Eo\n"
                            "Ei:\tIndoor Illumination, from slider, or calculated automatically from Eo.\n"
                            "Eo:\tSolar/Outdoor Illumination, calculated from geolocation and datetime.\n"
                            "DF:\tDaylight factor, the ratio of indoor to outdoor illumination. Updated\n"
                            "\twhenever the Ambient Light Level slider is manually altered.")).exec()
            return True
        path = pathlib.Path(device)
        if ((required_type == LuxDeviceType.ARDUINO and path.is_char_device()) or
                (required_type == LuxDeviceType.FIFO and path.is_fifo()) or
                (required_type == LuxDeviceType.EXECUTABLE and path.exists() and os.access(device, os.X_OK))):
            if not os.access(device, os.R_OK):
                info = None
                if path.is_char_device() and path.group() != "root":
                    info = tr("You might need to be a member of the {} group.").format(path.group())
                MBox(MIcon.Critical, msg=tr("No read access to {}").format(device), info=info).exec()
                return False
        else:
            MBox(MIcon.Critical, msg=tr("Expecting {}, but {} was selected.").format(tr(required_type.description), device)).exec()
            return False
        return True

    def apply_settings(self, requires_metering_restart: bool = True) -> None:
        self.lux_config.save(self.path)
        if requires_metering_restart:
            self.main_controller.get_lux_auto_controller().initialize_from_config()  # Causes the LuxAutoWorker to restart
            self.lux_gauge_widget.connect_meter(None)
            meter_device = self.main_controller.get_lux_auto_controller().lux_meter
            self.configure_ui(meter_device)  # Use the new meter for a new lux-display metering thread

    def configure_ui(self, meter_device: LuxMeterDevice | None) -> None:
        if meter_device is not None:  # Set this up first because altering the checkboxes will cause events to use the outcome.
            self.lux_gauge_widget.connect_meter(meter_device)
        if meter_device is None or (meter_device.has_semi_auto_capability
                                    and self.main_controller.main_config.get_location() is None):
            self.enabled_checkbox.setChecked(False)
            self.enabled_checkbox.setEnabled(False)
            self.interval_label.setEnabled(False)
            self.status_message(tr("No metering device set."))
        else:
            self.enabled_checkbox.setEnabled(True)
            self.interval_label.setEnabled(True)

    def save_profiles(self) -> None:
        for vdu_sid, profile in self.profile_plot.profiles_map.items():
            data = [(lux_point.lux, lux_point.brightness) for lux_point in profile if lux_point.preset_name is None]
            self.lux_config.set('lux-profile', vdu_sid, repr(data))
        preset_data = [(lux_point.lux, lux_point.preset_name) for lux_point in self.profile_plot.preset_points]
        self.lux_config.set('lux-presets', 'lux-preset-points', repr(preset_data))
        self.apply_settings()
        self.has_profile_changes = False
        self.save_button.setEnabled(False)
        self.revert_button.setEnabled(False)

    def closeEvent(self, event) -> None:
        if self.has_profile_changes:
            answer = MBox(MIcon.Critical, msg=tr("There are unsaved profile changes?"),
                          buttons=MBtn.Save | MBtn.Discard | MBtn.Cancel, default=MBtn.Cancel).exec()
            if answer == MBtn.Save:
                self.save_profiles()
            elif answer == MBtn.Cancel:
                event.ignore()
                return
        self.lux_gauge_widget.enable_gauge(False)  # Stop updating the display
        super().closeEvent(event)

    def status_message(self, message: str, timeout: int = 0, destination: MsgDestination = MsgDestination.DEFAULT) -> None:
        if destination == MsgDestination.COUNTDOWN:
            if not self.adjust_now_button.isHidden():
                self.adjust_now_button.setText(message)
        else:
            self.status_bar.showMessage(message, timeout)
        QApplication.processEvents()  # force messages out


class LuxDeviceException(Exception):
    pass


class LuxAutoController:

    def __init__(self, main_controller: VduAppController) -> None:
        super().__init__()
        self.main_controller = main_controller
        self.lux_config = LuxConfig()
        self.lux_config.load()
        self.lux_meter: LuxMeterDevice | None = None
        self.lux_auto_brightness_worker: LuxAutoWorker | None = None
        self.lux_tool_button: ToolButton | None = None
        self.lux_lighting_check_button: ToolButton | None = None
        self.lux_slider: LuxAmbientSlider | None = None

    def create_tool_button(self) -> ToolButton:  # Used when the application UI has to reinitialize
        # Used when the application UI has to reinitialize
        self.lux_tool_button = ToolButton(AUTO_LUX_ON_SVG, tr("Toggle automatic light metered brightness adjustment"))
        return self.lux_tool_button

    def create_lighting_check_button(self) -> ToolButton:
        # Used when the application UI has to reinitialize
        self.lux_lighting_check_button = ToolButton(LIGHTING_CHECK_SVG, tr("Perform ambient lighting check now"))
        return self.lux_lighting_check_button

    def update_manual_meter(self, value: int):
        if self.is_auto_enabled() and not self.lux_meter.has_semi_auto_capability:  # goto manual unless on semi-auto
            self.set_auto(False)
        self.lux_meter.set_current_value(value)
        self.adjust_brightness_now()

    def update_manual_slider(self, value: int):
        if self.is_auto_enabled() and self.lux_slider:  # May not exist during initialization
            self.lux_slider.set_current_value(value)

    def create_manual_input_control(self) -> LuxAmbientSlider:
        if self.lux_slider is None:
            self.lux_slider = LuxAmbientSlider(self)
            self.lux_slider.new_lux_value_qtsignal.connect(self.update_manual_meter)

            def _toggle_lux_dialog():
                if LuxDialog.exists() and LuxDialog.get_instance().isVisible():
                    LuxDialog.get_instance().close()
                else:
                    LuxDialog.invoke(self.main_controller)

            self.lux_slider.status_icon_pressed_qtsignal.connect(_toggle_lux_dialog)
        return self.lux_slider

    def get_lux_zone(self) -> LuxZone | None:
        if self.lux_slider and self.lux_slider.current_zone:
            return self.lux_slider.current_zone
        return None

    def stop_worker(self):
        if self.lux_auto_brightness_worker is not None:
            self.lux_auto_brightness_worker.stop()
            self.lux_auto_brightness_worker = None

    def start_worker(self, single_shot: bool):
        if self.lux_config.is_auto_enabled() or single_shot:
            if self.lux_meter is not None:
                if self.lux_auto_brightness_worker is not None:
                    self.stop_worker()
                self.lux_auto_brightness_worker = LuxAutoWorker(self, single_shot)
                self.lux_auto_brightness_worker.start()
                try:
                    self.lux_meter.new_lux_value_qtsignal.connect(self.update_manual_slider, type=Qt.ConnectionType.UniqueConnection)
                except TypeError:
                    pass

    def initialize_from_config(self) -> None:
        assert is_running_in_gui_thread()
        self.lux_config.load()
        try:
            if self.lux_meter is not None:
                self.lux_meter.stop_metering()
            device_name = self.lux_config.get_device_name().strip()
            if not device_name or device_name == LuxMeterSemiAutoDevice.obsolete_device_name:
                device_name = LuxMeterSemiAutoDevice.device_name
            LuxMeterSemiAutoDevice.set_location(self.main_controller.main_config.get_location())
            self.lux_meter = lux_create_device(device_name)
            if self.lux_config.is_auto_enabled():
                log_info("Lux auto-brightness settings refresh - restart monitoring.")
                self.start_worker(single_shot=False)
            else:
                log_info("Lux auto-brightness settings refresh - monitoring is off.")
                self.stop_worker()
            self.main_controller.update_window_status_indicators()  # Refresh indicators immediately
        except LuxDeviceException as lde:
            log_error(f"Error setting up lux meter {lde}", trace=True)
            MBox(MIcon.Critical, msg=tr("Error setting up lux meter: {}").format(self.lux_config.get_device_name()),
                 info=str(lde)).exec()
        if self.lux_tool_button:
            self.lux_tool_button.refresh_icon(self.current_auto_svg())  # Refresh indicators immediately
        if self.lux_lighting_check_button:
            self.lux_lighting_check_button.refresh_icon(self.current_check_svg())

    def is_auto_enabled(self) -> bool:
        return self.lux_config is not None and self.lux_config.is_auto_enabled()

    def current_auto_svg(self) -> bytes:
        return AUTO_LUX_ON_SVG if self.is_auto_enabled() else AUTO_LUX_OFF_SVG

    def current_check_svg(self) -> bytes:
        return LIGHTING_CHECK_SVG if self.is_auto_enabled() else LIGHTING_CHECK_OFF_SVG

    def get_lux_config(self) -> LuxConfig:
        assert self.lux_config is not None
        return self.lux_config

    def toggle_auto(self) -> None:
        self.set_auto(not self.is_auto_enabled())

    def set_auto(self, enable: bool):
        assert self.lux_config is not None
        log_debug(f"LuxAutoController: set_auto {enable}")
        if enable:
            if self.lux_meter and self.lux_meter.has_semi_auto_capability and not self.main_controller.main_config.get_location():
                message = tr("Auto disabled, no location defined.")
                enable = False
            elif self.lux_config.is_auto_enabled():
                message = tr("Restarting automatic light metering.")
            else:
                message = tr("Switching to automatic light metering.")
            self.lux_config.set('lux-meter', 'automatic-brightness', 'yes' if enable else 'no')
        else:
            message = tr("Switching to manual input of ambient lux.")
            self.lux_config.set('lux-meter', 'automatic-brightness', 'no')
        self.lux_config.save(ConfIni.get_path('AutoLux'))
        self.main_controller.status_message(message, timeout=5000)
        LuxDialog.lux_dialog_message(message, timeout=5000)
        self.initialize_from_config()
        LuxDialog.reconfigure_instance()

    def adjust_brightness_now(self) -> None:
        if self.is_auto_enabled():
            if self.lux_auto_brightness_worker is not None:
                self.lux_auto_brightness_worker.adjust_now_requested = True
            else:
                log_error("adjust_brightness_now: No worker - unexpected - error?")
        else:
            self.start_worker(single_shot=True)

    def get_lux_profile(self, vdu_stable_id: VduStableId, brightness_range) -> List[LuxPoint]:
        if self.lux_config.has_option('lux-profile', vdu_stable_id):  # initialize removing duplicate points
            lux_points = list(set([LuxPoint(v[0], v[1]) for v in literal_eval(self.lux_config.get('lux-profile', vdu_stable_id))]))
        else:  # Create a default profile:
                min_v, max_v = (0, 100) if brightness_range is None else brightness_range
                defaults = [(0, 0.6), (100, 0.8), (1_000, 0.9), (10_000, 0.9), (100_000, 0.9)]
                lux_points = [LuxPoint(lux, min_v + round(r * (max_v - min_v))) for lux, r in defaults]
        if self.lux_config.has_option('lux-presets', 'lux-preset-points'):  # Merge in preset points
            merge_map = {point.lux: point for point in  lux_points}
            for preset_point in self.lux_config.get_preset_points():
                # Look up the Preset's brightness for this VDU - get value from the actual Preset.
                if preset := self.main_controller.find_preset_by_name(preset_point.preset_name):  # Drop any that no longer exist
                    if point := merge_map.get(preset_point.lux):
                        point.preset_name = preset_point.preset_name  # Merge both points
                    else:
                        merge_map[preset_point.lux] = preset_point  # Add this point on its own
                        point = preset_point
                    # Point brightness for this VDU will be -1 if this VDU's brightness-control doesn't participate in the Preset.
                    point.brightness = preset.get_brightness(vdu_stable_id)
            lux_points = list(merge_map.values())
            lux_points.sort()
        log_debug(f"LuxAuto: get_lux_profile({vdu_stable_id=}) => {lux_points=}") if log_debug_enabled else None
        return lux_points


LUX_SUNLIGHT_SVG = b"""<?xml version="1.0" encoding="utf-8"?>
<svg width="24px" height="24px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <style type="text/css" id="current-color-scheme"> .ColorScheme-Text { color:#232629; } </style>
    <g class="ColorScheme-Text" stroke="currentColor" stroke-linecap="round" stroke-width="1.25">
        <circle cx="12" cy="12" r="4" /> <line x1="3.5" y1="12" x2="5.5" y2="12" />
        <line x1="18.5" y1="12" x2="20.5" y2="12"/> <line x1="12" y1="3.5" x2="12" y2="5.5"/>
        <line x1="12" y1="18.5" x2="12" y2="20.5"/> <line x1="6" y1="6" x2="7.41" y2="7.41"/>
        <line x1="16.59" y1="16.59" x2="18.01" y2="18.01"/> <line x1="18" y1="6" x2="16.59" y2="7.41"/>
        <line x1="7.41" y1="16.59" x2="6" y2="18.01"/>
    </g>
</svg>"""

LUX_DAYLIGHT_SVG = b"""<?xml version="1.0" encoding="utf-8"?>
<svg width="24px" height="24px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <style type="text/css" id="current-color-scheme"> .ColorScheme-Text { color:#232629; } </style>
    <g class="ColorScheme-Text" stroke="currentColor" stroke-linecap="round" stroke-width="1.25">
        <path d="M6.5,11 a1,1 0 0,1 7,0 " /> <path d="M6.5,11 a1,1 0 0,0 0,6.5 " /> 
        <path d="M14,11 a1,1 0 0,1 0,6.5 " /> <path d="M7,17.5 l6.5,0" stroke-linecap="square"/> 
        <path d="M12.5,8 a1,1 0 0,1 5,4 "/> <path d="M15,10 m 0,-6 l 0,1.25"/>
        <path d="M15,10 m 3.5,-3.5 l 1,-1"/> <path d="M15,10 m -3.5,-3.5 l -1,-1"/>
        <path d="M15,10 m 3.5,3.5 l 1,1"/> <path d="M15,10 m 5,0 l 1.25,0"/>
    </g>
</svg>"""

LUX_OVERCAST_SVG = b"""<?xml version="1.0" encoding="utf-8"?>
<svg width="24px" height="24px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <style type="text/css" id="current-color-scheme"> .ColorScheme-Text { color:#232629; } </style>
    <g class="ColorScheme-Text" stroke="currentColor" stroke-linecap="round" stroke-width="1.25">
        <path d="M6.5,11 a1,1 0 0,1 7,0 " /> <path d="M6.5,11 a1,1 0 0,0 0,6.5 " />
        <path d="M14,11 a1,1 0 0,1 0,6.5 " /> <path d="M12.5,8.5 a1,1 0 0,1 5,-.5 " />
        <path d="M17.5,8.5 a1,1 0 0,1 0,5.5 " stroke-linecap="square"/>
        <path d="M7,17.5 l6.5,0" stroke-linecap="square"/>
    </g>
</svg>"""

LUX_TWILIGHT_SVG = b"""<?xml version="1.0" encoding="utf-8"?>
<svg width="24px" height="24px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <style type="text/css" id="current-color-scheme"> .ColorScheme-Text { color:#232629; } </style>
    <g class="ColorScheme-Text" stroke="currentColor" stroke-linecap="round" stroke-width="1.25">
        <path d="M8.25,15 A3.75,3.25 0 0,1 15.75,15 " stroke-linecap="square"/>
        <line x1="12" y1="7.5" x2="12" y2="9.5"/> <line x1="6" y1="10" x2="7.41" y2="11.41"/>
        <line x1="18" y1="10" x2="16.59" y2="11.41"/> <line x1="5" y1="17." x2="19" y2="17"/>
    </g>
</svg>"""

LUX_SUBDUED_SVG = b"""<?xml version="1.0" encoding="utf-8"?>
<svg width="24px" height="24px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <style type="text/css" id="current-color-scheme"> .ColorScheme-Text { color:#232629; } </style>
    <g class="ColorScheme-Text" stroke="currentColor" stroke-width="1.25" stroke-linecap="round">
        <circle cx="12" cy="11" r="4.5"/> <rect x="10" y="15.4" width="4" rx="1" ry="1" height="2.6"/>
        <line x1="4" y1="12" x2="5" y2="12" /> <line x1="19" y1="12" x2="20" y2="12"/>
        <line x1="12" y1="3" x2="12" y2="4"/> <line x1="5.75" y1="5.25" x2="6.75" y2="6.25"/>
        <line x1="18.5" y1="5.25" x2="17.5" y2="6.25"/>
    </g>
</svg>"""

LUX_DARK_SVG = b"""<?xml version="1.0" encoding="utf-8"?>
<!-- Copyright 2024 Michael Hamilton License Creative Commons - Attribution CC BY -->
<svg width="24px" height="24px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <style type="text/css" id="current-color-scheme"> .ColorScheme-Text { color:#232629; } </style>
    <g class="ColorScheme-Text" stroke="currentColor" stroke-linecap="round" stroke-width="1.25" 
       transform="translate(24, 24), scale(-1,-1)">
        <path d="M17.5 7.5   A6.25 6.25   0 1 0   16.5 16.5   5 5   0 1 1   17.5 7.5z"/>
    </g>
</svg>
"""


@dataclass
class LuxZone:
    name: str
    icon_svg: bytes
    min_lux: int
    max_lux: int
    icon_svg_lux: int
    column_span: int


class LuxAmbientSlider(QWidget):
    new_lux_value_qtsignal = pyqtSignal(int)
    status_icon_changed_qtsignal = pyqtSignal()
    status_icon_pressed_qtsignal = pyqtSignal()

    def __init__(self, controller: LuxAutoController) -> None:
        super().__init__()
        self.controller = controller
        self.in_flux = False
        self.zones = [  # Using col span as a hacky way to line up icons above the slider
            LuxZone(tr("Sunlight"), LUX_SUNLIGHT_SVG, 20_000, 100_000, 45_000, column_span=2),
            LuxZone(tr("Daylight"), LUX_DAYLIGHT_SVG, 5_000, 20_000, 6_000, column_span=2),
            LuxZone(tr("Overcast"), LUX_OVERCAST_SVG, 400, 5_000, 900, column_span=3),
            LuxZone(tr("Twilight"), LUX_TWILIGHT_SVG, 100, 400, 130, column_span=2),
            LuxZone(tr("Subdued"), LUX_SUBDUED_SVG, 15, 100, 20, column_span=3),
            LuxZone(tr("Dark"), LUX_DARK_SVG, 0, 15, 2, column_span=4), ]
        self.current_value = 10_000

        self.status_icon = StdButton(icon_size=QSize(native_font_height(scaled=1.8), native_font_height(scaled=1.8)), flat=True,
                                     clicked=self.status_icon_pressed_qtsignal)
        self.current_name: str | None = None
        self.current_zone: LuxZone | None = None

        top_layout = QVBoxLayout()
        self.setLayout(top_layout)
        top_layout.setSpacing(0)
        tl_margins = top_layout.contentsMargins()
        top_layout.setContentsMargins(tl_margins.left(), 0, tl_margins.right(), 0)
        top_layout.addWidget(QLabel(tr("Ambient Light Level (lux)")), alignment=Qt.AlignmentFlag.AlignBottom)

        input_panel = QWidget()
        input_panel_layout = QHBoxLayout()
        input_panel.setLayout(input_panel_layout)
        input_panel_layout.addWidget(self.status_icon)

        lux_slider_panel = QWidget()
        lux_slider_panel_layout = QGridLayout()
        lux_slider_panel.setLayout(lux_slider_panel_layout)

        self.slider = ClickableSlider()
        self.slider.setToolTip(tr("Ambient light level input (lux value)"))
        self.slider.setMinimumWidth(npx(200))
        self.slider.setRange(int(math.log10(1) * 1000), int(math.log10(100000) * 1000))
        self.slider.setSingleStep(1)
        self.slider.setPageStep(100)
        self.slider.setTickInterval(1000)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.setOrientation(Qt.Orientation.Horizontal)  # type: ignore
        self.slider.setTracking(False)  # Don't rewrite the ddc value too often - not sure of the implications
        lux_slider_panel_layout.addWidget(self.slider, 1, 0, 1, 15, alignment=Qt.AlignmentFlag.AlignTop)

        # A hacky way to get custom labels without redefining paint
        for col_num, span, value in ((0, 3, 1), (3, 3, 10), (6, 3, 100), (9, 3, 1000), (12, 3, 10000), (14, 1, 100000)):
            log10_button = QLabel(f"{value:2d}")
            app_font = QApplication.font()
            log10_button.setFont(QFont(app_font.family(), round(app_font.pointSize() * .66), QFont.Weight.Normal))
            lux_slider_panel_layout.addWidget(log10_button, 2, col_num, 1, span, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        input_panel_layout.addWidget(lux_slider_panel, stretch=100)

        self.lux_input_field = QSpinBox()
        self.lux_input_field.setLineEdit(LineEditAll())
        self.lux_input_field.setToolTip(tr("Ambient light level input (lux value)"))
        self.lux_input_field.setKeyboardTracking(False)
        self.lux_input_field.setRange(1, 100000)
        self.lux_input_field.setValue(self.current_value)
        input_panel_layout.addWidget(self.lux_input_field)

        top_layout.addWidget(input_panel, alignment=Qt.AlignmentFlag.AlignTop)

        def _lux_slider_change(new_value: int) -> None:
            real_value = round(10 ** (new_value / 1000))
            self.set_current_value(real_value, self.slider)
            self.new_lux_value_qtsignal.emit(real_value)

        self.slider.valueChanged.connect(_lux_slider_change)

        def _lux_slider_moved(new_value: int) -> None:
            new_lux_value = round(10 ** (new_value / 1000))
            self.set_current_value(new_lux_value, self.slider)

        self.slider.sliderMoved.connect(_lux_slider_moved)

        def _lux_input_field_changed() -> None:
            self.set_current_value(self.lux_input_field.value(), self.lux_input_field)

        self.lux_input_field.valueChanged.connect(_lux_input_field_changed)

        def _input_field_editing_finished():
            self.set_current_value(self.lux_input_field.value(), self.lux_input_field)

        self.lux_input_field.editingFinished.connect(_input_field_editing_finished)

        col = 0
        log10_icon_size = QSize(native_font_height(scaled=1), native_font_height(scaled=1))
        self.label_map: Dict[StdButton, bytes] = {}
        for zone in reversed(self.zones):
            log10_button = StdButton(icon=create_icon_from_svg_bytes(zone.icon_svg), icon_size=log10_icon_size,
                                     clicked=partial(self.lux_input_field.setValue, zone.icon_svg_lux), flat=True, tip=zone.name)
            lux_slider_panel_layout.addWidget(log10_button, 0, col, 1, zone.column_span, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
            self.label_map[log10_button] = zone.icon_svg
            col += zone.column_span

        self.set_current_value(controller.lux_meter.get_value() if controller.lux_meter else 1000)  # don't trigger side-effects.

    def set_current_value(self, value: int, source: QWidget | None = None) -> None:
        # log_debug("set_current_value ", value, source, self.in_flux)
        icon_changed = False
        if not self.in_flux and value != self.current_value:
            try:
                if source is None:
                    self.blockSignals(True)
                self.in_flux = True
                for zone in self.zones:
                    if zone.min_lux < value <= zone.max_lux:
                        if self.current_zone != zone:
                            self.current_zone = zone
                            self.status_icon.setIcon(create_icon_from_svg_bytes(zone.icon_svg))
                            self.status_icon.setToolTip(tr("Open/Close Light-Meter Dialog"))
                            icon_changed = True
                self.current_value = max(1, value)  # restrict to non-negative and something valid for log10
                if source != self.slider:
                    self.slider.setValue(round(math.log10(self.current_value) * 1000))
                if source != self.lux_input_field:
                    self.lux_input_field.setValue(self.current_value)
                # We can use values from non-semi-auto meters to calibrate the semi-auto-meter.
                semi_auto_source = self.controller.lux_meter and self.controller.lux_meter.has_semi_auto_capability
                if source == self.slider or source == self.lux_input_field or not semi_auto_source:
                    if location := self.controller.main_controller.main_config.get_location():
                        LuxMeterSemiAutoDevice.set_location(location)  # in case it's changed
                        LuxMeterSemiAutoDevice.update_df_from_lux_value(self.current_value, semi_auto_source)
            finally:
                self.in_flux = False
                if source is None:
                    self.blockSignals(False)
                if icon_changed:
                    self.status_icon_changed_qtsignal.emit()

    def event(self, event: QEvent | None) -> bool:
        if event and event.type() == QEvent.Type.PaletteChange:  # PalletChange happens after the new style sheet is in use.
            if self.current_zone:
                self.status_icon.setIcon(create_icon_from_svg_bytes(self.current_zone.icon_svg))
            for slider_button, svg_bytes in self.label_map.items():
                slider_button.setIcon(create_icon_from_svg_bytes(svg_bytes))
        return super().event(event)


class GreyScaleDialog(SubWinDialog):
    """Creates a dialog with a grey scale VDU calibration image.  Non-model. Have as many as you like - one per VDU."""

    # This stops garbage-collection of independent instances of this dialog until the user closes them.
    # If we don't do this, the dialog will disappear before it becomes visible. We could also pass a parent
    # which would achieve the same thing, but would alter where the dialog appears.
    _active_list: List[QDialog] = []

    def __init__(self) -> None:
        super().__init__()
        GreyScaleDialog._active_list.append(self)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setWindowTitle(tr('Grey Scale Reference'))
        self.setModal(False)
        svg_widget = QSvgWidget()
        svg_widget.renderer().load(GREY_SCALE_SVG)
        svg_widget.setMinimumSize(npx(600), npx(400))
        svg_widget.setToolTip(tr(
            'Grey Scale Reference for VDU adjustment.\n\n'
            'Set contrast toward the maximum (for HDR monitors\n'
            'try something lower such as 70%) and adjust brightness\n'
            'until as many rectangles as possible can be perceived.\n\n'
            'Use the content-menu to create additional charts and\n'
            'drag them onto each display.\n\nThis chart is resizable. '))
        layout.addWidget(svg_widget)
        close_button = StdButton(icon=si(self, StdPixmap.SP_DialogCloseButton), title=tr("Close"), clicked=self.hide)
        layout.addWidget(close_button, 0, Qt.AlignmentFlag.AlignRight)
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event) -> None:
        GreyScaleDialog._active_list.remove(self)
        event.accept()


class AboutDialog(QMessageBox, DialogSingletonMixin):

    @staticmethod
    def invoke(main_controller: VduAppController) -> None:
        if AboutDialog.exists():
            AboutDialog.get_instance().refresh_content()
            AboutDialog.show_existing_dialog()
        else:
            AboutDialog(main_controller)

    @staticmethod
    def refresh():
        if AboutDialog.exists() and AboutDialog.get_instance().isVisible():
            AboutDialog.get_instance().refresh_content()
        else:
            log_debug("About dialog - no refresh - not visible") if log_debug_enabled else None

    def __init__(self, main_controller: VduAppController) -> None:
        super().__init__()
        self.main_controller = main_controller
        self.refresh_content()
        self.setModal(False)
        self.show()
        self.raise_()
        self.activateWindow()

    def refresh_content(self):
        self.setWindowTitle(tr('About'))
        self.setTextFormat(Qt.TextFormat.AutoText)
        self.setText(tr('About vdu_controls'))
        path = find_locale_specific_file("about_{}.txt")
        if path:
            with open(path, encoding='utf-8') as about_for_locale:
                about_text = about_for_locale.read().format(
                    VDU_CONTROLS_VERSION=VDU_CONTROLS_VERSION, IP_ADDRESS_INFO_URL=IP_ADDRESS_INFO_URL,
                    WEATHER_FORECAST_URL=WEATHER_FORECAST_URL)
        else:
            about_text = ABOUT_TEXT
        if self.main_controller and self.main_controller.ddcutil:
            counts_str = ','.join((str(v) for v in Ddcutil.vcp_write_counters.values())) if len(Ddcutil.vcp_write_counters) else '0'
            about_text += (f"<hr><p><small>desktop: {os.environ.get('XDG_CURRENT_DESKTOP', default='unknown')}; "
                           f"platform: {os.environ.get('XDG_SESSION_TYPE', default='unknown')} "
                           f"({QApplication.platformName()}, qt-{QtCore.qVersion()});<br/>"
                           f"ddcutil-interface: {self.main_controller.ddcutil.ddcutil_version_info()[0]}; "
                           f"ddcutil: {self.main_controller.ddcutil.ddcutil_version_info()[1]} (writes: {counts_str});</small>")
        self.setInformativeText(about_text)
        self.setIcon(MIcon.Information)


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


class PresetScheduleStatus(Enum):
    UNSCHEDULED = 0, ' ', QT_TR_NOOP('unscheduled')
    # This hourglass character is too tall - it causes a jump when rendered - but nothing else is quite as appropriate.
    SCHEDULED = 1, TIMER_RUNNING_SYMBOL, QT_TR_NOOP('scheduled')
    SUSPENDED = 2, ' ', QT_TR_NOOP('suspended')
    SUCCEEDED = 3, SUCCESS_SYMBOL, QT_TR_NOOP('succeeded')
    SKIPPED_SUPERSEDED = 4, SKIPPED_SYMBOL, QT_TR_NOOP('skipped, superseded')
    WEATHER_CANCELLATION = 5, WEATHER_CANCELLATION_SYMBOL, QT_TR_NOOP('weather cancellation')

    def symbol(self) -> str:
        return self.value[1]

    def description(self) -> str:
        return self.value[2]

    def __str__(self) -> str:
        return str(self.value[0])


class PresetTransitionFlag(IntFlag):
    _ignore_ = ['abbreviations', 'descriptions']  # Seems very hacky

    NONE = 0
    SCHEDULED = 1
    MENU = 2
    SIGNAL = 4
    ALWAYS = 7

    abbreviations = {NONE: '', SCHEDULED: TIME_CLOCK_SYMBOL, MENU: MENU_SYMBOL,
                     SIGNAL: SIGNAL_SYMBOL, ALWAYS: TRANSITION_ALWAYS_SYMBOL}

    descriptions = {
        NONE: QT_TR_NOOP('Always immediately'), SCHEDULED: QT_TR_NOOP('Smoothly on solar/time'), MENU: QT_TR_NOOP('Smoothly on menu'),
        SIGNAL: QT_TR_NOOP('Smoothy on signal'), ALWAYS: QT_TR_NOOP('Always smoothly')}

    def abbreviation(self, abbreviations=abbreviations) -> str:  # Even more hacky
        if self.value in (PresetTransitionFlag.NONE, PresetTransitionFlag.ALWAYS):
            return abbreviations[self]
        return TRANSITION_SYMBOL + ''.join([abbreviations[component] for component in self.component_values()])

    def description(self, descriptions=descriptions) -> str:  # Yuck
        if self.value in (PresetTransitionFlag.NONE, PresetTransitionFlag.ALWAYS):
            return tr(descriptions[self])
        return ', '.join([tr(descriptions[component]) for component in self.component_values()])

    def component_values(self) -> list[PresetTransitionFlag]:
        # similar to Python 3.11 enum.show_flag_values(self) - list of power of two components for self
        return [option for option in PresetTransitionFlag if (option & (option - 1) == 0) and option != 0 and option in self]

    def __str__(self) -> str:
        assert self.name is not None  # TODO this failed once - get to repeat
        if self.value == PresetTransitionFlag.NONE:
            return self.name.lower()
        return ','.join([component.name.lower() for component in self.component_values()])  # type: ignore


def parse_transition_type(string_value: str) -> PresetTransitionFlag:
    transition_type = PresetTransitionFlag.NONE
    string_value = string_value.replace('schedule_or_signal', 'scheduled,signal')  # Backward compatible for unreleased 1.9.2
    for component_value in string_value.split(','):
        for option in PresetTransitionFlag:
            assert option.name is not None
            if component_value.lower() == option.name.lower():
                transition_type |= option
    return transition_type


@contextmanager  # https://stackoverflow.com/questions/31501487/non-blocking-lock-with-with-statement
def non_blocking_lock(lock: threading.RLock) -> threading.RLock:  # Provide a way to use a with-statement with non-blocking locks
    acquire_succeeded = lock.acquire(False)  # acquire_succeeded will be False if the lock is already locked.
    try:
        yield lock if acquire_succeeded else None  # return None to the with if the lock was not acquired
    finally:
        if acquire_succeeded:
            lock.release()


class VduAppController(QObject):  # Main controller containing methods for high level operations

    def __init__(self, main_config: VduControlsConfig) -> None:
        super().__init__()
        self.find_vdu_config_files()
        self.application_lock = threading.RLock()  # thread level, thread-safe, access lock
        self.main_config = main_config
        self.ddcutil: Ddcutil | None = None
        self.main_window: VduAppWindow | None = None
        self.vdu_controllers_map: Dict[VduStableId, VduController] = {}
        self.preset_controller = PresetController()
        self.detected_vdu_list: List[Tuple[str, str, str, str]] = []
        self.previously_detected_vdu_list: List[Tuple[str, str, str, str]] = []
        self.refresh_data_task: WorkerThread | None = None
        self.weather_query: WeatherQuery | None = None
        self.preset_transition_workers: List[BulkChangeWorker] = []  # Not sure if this actually needs to be a list.
        self.lux_auto_controller: LuxAutoController | None = LuxAutoController(self) if self.main_config.is_set(
            ConfOpt.LUX_OPTIONS_ENABLED) else None

        def respond_to_unix_signal(signal_number: int) -> None:
            if signal_number == signal.SIGHUP:
                self.start_refresh(external_event=True)
            elif PRESET_SIGNAL_MIN <= signal_number <= PRESET_SIGNAL_MAX:
                if preset := self.preset_controller.get_preset(signal_number - PRESET_SIGNAL_MIN):
                    immediately = PresetTransitionFlag.SIGNAL not in preset.get_transition_type()
                    log_info(f"Signaled for {preset.name=} {preset.get_transition_type()=} {immediately=} {thread_pid()=}")
                    # Signals occur outside the GUI thread - initiate the restore in the GUI thread
                    self.restore_preset(preset=preset, immediately=immediately, background_activity=True)
                else:
                    # Cannot raise a Qt alert inside the signal handler in case another signal comes in.
                    log_warning(f"ignoring {signal_number=}, no preset associated with that signal number.")

        global unix_signal_handler
        unix_signal_handler.received_unix_signal_qtsignal.connect(respond_to_unix_signal)

    def configure_application(self, main_window: VduAppWindow | None = None, check_schedule: bool = True):
        try:
            log_info(f"Configuring application (reconfiguring={main_window is None})...")
            for controller in self.vdu_controllers_map.values():
                controller.no_longer_in_use = True
            if main_window is not None:  # First time through
                assert self.main_window is None
                self.main_window = main_window
            if self.main_window.main_panel is not None:
                self.main_window.indicate_busy(True)
                QApplication.processEvents()
            log_debug("configure: try to obtain application_lock", trace=False) if log_debug_enabled else None
            with self.application_lock:
                log_debug("configure: holding application_lock") if log_debug_enabled else None
                ScheduleWorker.dequeue_all()
                if self.lux_auto_controller is not None:
                    self.lux_auto_controller.stop_worker()
                    self.lux_auto_controller.lux_slider = None
                self.stop_any_transitioning_presets()
                global log_to_syslog
                log_to_syslog = self.main_config.is_set(ConfOpt.SYSLOG_ENABLED)
                self.create_ddcutil()
                self.preset_controller.reinitialize()
                self.main_window.initialise_app_icon()
                self.main_window.create_main_control_panel()
                SettingsDialog.reconfigure_instance(self.get_vdu_configs())
                self.restore_vdu_initialization_presets()
                self.schedule_presets()
                ScheduleWorker.check() if check_schedule else None
            log_debug("configure: released application_lock") if log_debug_enabled else None
            if self.main_config.is_set(ConfOpt.LUX_OPTIONS_ENABLED):
                if self.lux_auto_controller is not None:
                    self.lux_auto_controller.initialize_from_config()
                    LuxDialog.reconfigure_instance()
            self.main_window.update_status_indicators()
        finally:
            if self.main_window is not None:
                self.main_window.indicate_busy(False)
        log_info("Completed configuring application")

    def stop_any_transitioning_presets(self):
        for running_worker in [worker for worker in self.preset_transition_workers if worker.isRunning()]:
            running_worker.stop()
            log_debug(f"Stop requested for {running_worker.name=} {running_worker.start_time=!s}")
        self.preset_transition_workers.clear()

    def create_ddcutil(self):

        if self.main_config.is_set(ConfOpt.DBUS_CLIENT_ENABLED) and self.main_config.is_set(ConfOpt.DBUS_EVENTS_ENABLED):

            def _vdu_connectivity_changed_callback(edid_encoded: str, event_type: int, flags: int):
                if not DdcEventType.UNKNOWN.value <= event_type <= DdcEventType.DISPLAY_DISCONNECTED.value:
                    log_warning(f"Connected VDUs event - unknown {event_type=} treating as DPMS_UNKNOWN.")
                    event_type = DdcEventType.UNKNOWN.value
                log_info(f"Connected VDUs event {DdcEventType(event_type)} {flags=} {edid_encoded:.30}...")
                if event_type == DdcEventType.DPMS_ASLEEP.value:
                    return  # Don't do anything, the VDUs are just asleep.
                self.start_refresh(external_event=True)

            change_handler = _vdu_connectivity_changed_callback
            log_debug("Enabled callback for VDU-connectivity-change D-Bus signals")
        else:
            change_handler = None  # This will force disabling the eventing/polling inside the server, not just the client.

        try:
            self.ddcutil = Ddcutil(common_args=self.main_config.get_ddcutil_extra_args(),
                                   prefer_dbus_client=self.main_config.is_set(ConfOpt.DBUS_CLIENT_ENABLED),
                                   connected_vdus_changed_callback=change_handler)
            if emulator := self.main_config.ini_content.get(ConfOpt.DDCUTIL_EMULATOR.conf_section,
                                                            ConfOpt.DDCUTIL_EMULATOR.conf_name, fallback=None):
                self.ddcutil.add_ddcutil_emulator(emulator, common_args=self.main_config.get_ddcutil_extra_args())
        except (subprocess.SubprocessError, ValueError, re.error, OSError, DdcutilServiceNotFound) as e:
            self.main_window.show_no_controllers_error_dialog(e)

    def detect_vdus(self) -> Tuple[List[Tuple[str, str, str, str]], Exception | None]:
        if self.ddcutil is None:
            return [], None
        ddcutil_problem = None
        try:
            self.detected_vdu_list = []
            log_debug("Detecting connected monitors, looping detection until it stabilizes.") if log_debug_enabled else None
            # Loop in case the session is initializing/restoring which can make detection unreliable.
            # Limit to a reasonable number of iterations.
            for i in range(1, 11):
                prev_num = len(self.detected_vdu_list)
                self.detected_vdu_list = self.ddcutil.detect_vdus()
                if prev_num == len(self.detected_vdu_list):
                    log_info(f"Number of detected monitors is stable at {len(self.detected_vdu_list)} (loop={i})")
                    break
                elif prev_num > 0:
                    log_info(f"Number of detected monitors changed from {prev_num} to {len(self.detected_vdu_list)} (loop={i})")
                time.sleep(1.5)
        except (subprocess.SubprocessError, ValueError, re.error, OSError) as e:
            log_error(e)
            ddcutil_problem = e
        self.previously_detected_vdu_list = self.detected_vdu_list
        return self.detected_vdu_list, ddcutil_problem

    def initialize_vdu_controllers(self) -> None:
        assert is_running_in_gui_thread()
        if self.ddcutil is None:
            return
        detected_vdu_list, ddcutil_problem = self.detect_vdus()
        self.vdu_controllers_map = {}
        main_panel_error_handler = self.main_window.get_main_panel().show_vdu_exception
        for vdu_number, manufacturer, model_name, vdu_serial in detected_vdu_list:
            controller = None
            while True:
                try:
                    controller = VduController(vdu_number, model_name, vdu_serial, manufacturer, self.main_config,
                                               self.ddcutil, main_panel_error_handler, VduController.NORMAL_VDU)
                except (subprocess.SubprocessError, ValueError, re.error, OSError, DdcutilDisplayNotFound) as e:
                    log_error(f"Problem creating controller for {vdu_number=} {model_name=} {vdu_serial=} exception={e}",
                              trace=True)
                    remedy = self.main_window.ask_for_vdu_controller_remedy(vdu_number, model_name, vdu_serial)
                    if remedy == VduController.NORMAL_VDU:
                        time.sleep(1.0)  # Slow things down in case something is wrong with the GUI or VDU interactions.
                        continue  # Loop and retry as a normal VDU
                    controller = VduController(vdu_number, model_name, vdu_serial, manufacturer, self.main_config,
                                               self.ddcutil, main_panel_error_handler, remedy)
                    controller.write_template_config_files()
                break  # Normally expect to just pass through the loop once
            if controller is not None:
                self.vdu_controllers_map[controller.vdu_stable_id] = controller
        if len(self.vdu_controllers_map) == 0:
            if self.main_config.is_set(ConfOpt.WARNINGS_ENABLED):
                self.main_window.show_no_controllers_error_dialog(ddcutil_problem)
        if self.main_config.is_set(ConfOpt.ORDER_BY_NAME):
            self.vdu_controllers_map = {
                c.vdu_stable_id: c for c in sorted(self.vdu_controllers_map.values(), key=VduController.get_vdu_preferred_name)}

    def settings_changed(self, changed_settings: List) -> None:
        if changed_settings is None:  # Special value - means settings have been reset/removed - needs restart.
            self.restart_application(tr("A settings reset requires vdu_controls to restart."))
            return
        for setting in ConfOpt:
            if setting.restart_required and (setting.conf_section, setting.conf_name) in changed_settings:
                self.restart_application(
                    tr("The change to the {} option requires vdu_controls to restart.").format(tr(setting.conf_name)))
                return
        self.main_config.reload()
        global log_debug_enabled
        global log_to_syslog
        log_to_syslog = self.main_config.is_set(ConfOpt.SYSLOG_ENABLED)
        log_debug_enabled = self.main_config.is_set(ConfOpt.DEBUG_ENABLED)
        log_info("Reconfiguring due to settings change.")
        self.configure_application()

    def edit_config(self, tab_number: int | None = None) -> None:
        SettingsDialog.invoke(self.main_config, self.get_vdu_configs(), self.settings_changed)
        SettingsDialog.get_instance().tabs_widget.setCurrentIndex(tab_number) if tab_number is not None else None

    def show_presets_dialog(self, preset: Preset | None = None) -> None:
        PresetsDialog.invoke(self, self.main_config)
        if preset:
            PresetsDialog.instance_edit_preset(preset)

    def get_vdu_configs(self) -> List[VduControlsConfig]:
        return [vdu.config for vdu in self.vdu_controllers_map.values() if vdu.config is not None]

    def create_config_files(self) -> None:
        for controller in self.vdu_controllers_map.values():
            controller.write_template_config_files()

    def lux_auto_action(self) -> None:
        if self.lux_auto_controller:
            try:
                self.main_window.setDisabled(True)
                self.lux_auto_controller.toggle_auto()
                self.main_window.update_status_indicators()
            finally:
                self.main_window.setDisabled(False)

    def lux_check_action(self) -> None:
        if self.lux_auto_controller and self.lux_auto_controller.is_auto_enabled():
            self.lux_auto_controller.adjust_brightness_now()

    def start_refresh(self, external_event: bool = False) -> None:

        def _update_from_vdu(worker: WorkerThread) -> None:
            if self.ddcutil is not None:
                with non_blocking_lock(self.application_lock) as acquired_lock:
                    if acquired_lock:  # If acquired_lock is not None, then we have successfully acquired the lock.
                        log_debug(f"_update_from_vdu: holding application_lock") if log_debug_enabled else None
                        try:
                            log_info(f"Refresh commences: {external_event=}") if log_debug_enabled else None
                            self.ddcutil.refresh_connection()
                            self.detected_vdu_list = self.ddcutil.detect_vdus()
                            self.restore_vdu_initialization_presets()
                            for control_panel in self.main_window.get_main_panel().vdu_control_panels.values():
                                if control_panel.controller.get_full_id() in self.detected_vdu_list:
                                    control_panel.refresh_from_vdu()
                        except (subprocess.SubprocessError, ValueError, re.error, OSError) as e:
                            if self.refresh_data_task.vdu_exception is None:
                                self.refresh_data_task.vdu_exception = VduException(vdu_description="unknown", operation="unknown",
                                                                                    exception=e)
                    else:
                        log_info(f"Application is already busy, can't do a refresh ({external_event=})")
                        worker.stop()  # Stop the thread - which also indicates we did not acquire the lock.
                        return  # Prevents logging unlock (because we don't have the lock if we reach here).
                log_debug(f"_update_from_vdu: released application_lock") if log_debug_enabled else None

        def _update_ui_view(worker: WorkerThread) -> None:
            # Invoke when the worker thread completes. Runs in the GUI thread and can refresh remaining UI views.
            if worker.stop_requested:
                return  # in this case, this means the worker never started anything
            try:  # No need for locking in here - running in the GUI thread effectively single threads the operation.
                assert self.refresh_data_task is not None and is_running_in_gui_thread()
                log_debug(f"Refresh - update UI view {external_event=}") if log_debug_enabled else None
                main_panel = self.main_window.get_main_panel()
                if self.refresh_data_task.vdu_exception is not None:
                    log_debug(f"Refresh - update UI view - exception {self.refresh_data_task.vdu_exception} {external_event=}")
                    if not external_event:
                        main_panel.show_vdu_exception(self.refresh_data_task.vdu_exception, can_retry=False)
                if len(self.detected_vdu_list) == 0 or self.detected_vdu_list != self.previously_detected_vdu_list or (
                        external_event and False):
                    log_info(f"Reconfiguring: detected={self.detected_vdu_list} previously={self.previously_detected_vdu_list}")
                    self.configure_application(check_schedule=False)  # May cause a further refresh?
                    self.previously_detected_vdu_list = self.detected_vdu_list
                ScheduleWorker.check()  # immediately active the currently applicable preset
                if self.lux_auto_controller:
                    if LuxDialog.exists():
                        LuxDialog.get_instance().reconfigure()  # Incase the number of connected monitors has changed.
                    if self.lux_auto_controller.is_auto_enabled():
                        self.lux_auto_controller.adjust_brightness_now()
            finally:
                self.main_window.indicate_busy(False)

        if not is_running_in_gui_thread():  # TODO this appears to never be true - remove???
            log_debug(f"Re-invoke start_refresh() in GUI thread {external_event=}") if log_debug_enabled else None
            self.main_window.run_in_gui_thread(partial(self.start_refresh, external_event))
            return
        self.refresh_data_task = WorkerThread(task_body=_update_from_vdu, task_finished=_update_ui_view)
        self.refresh_data_task.start()
        time.sleep(0.1)  # Sleep a bit to see if we acquire the application lock
        if not self.refresh_data_task.stop_requested:  # if the thread has already stopped, it never acquired the application_lock
            self.main_window.indicate_busy(True)  # Refresh has probably commenced, give the user some feedback

    def restore_preset(self, preset: Preset, finished_func: Callable[[BulkChangeWorker], None] | None = None,
                       immediately: bool = False, background_activity: bool = False, initialization_preset: bool = False) -> None:
        if initialization_preset:
            background_activity = True
            immediately = True
        elif self.main_config.is_set(ConfOpt.PROTECT_NVRAM_ENABLED):
            immediately = True
        # Starts the restore, but it will complete in the worker thread
        if not is_running_in_gui_thread():  # Transfer this request into the GUI thread
            log_debug(f"restore_preset: '{preset.name}' transferring task to GUI thread") if log_debug_enabled else None
            self.main_window.run_in_gui_thread(partial(self.restore_preset, preset, finished_func,
                                                       immediately, background_activity, initialization_preset))
            return

        log_debug(f"restore_preset: '{preset.name}' try to obtain application_lock", trace=False) if log_debug_enabled else None
        with self.application_lock:  # The lock prevents a transition firing when the GUI/app is reconfiguring

            def _update_progress(worker_thread: BulkChangeWorker) -> None:
                preset.in_transition_step += 1
                self.main_window.show_preset_status(
                    tr("Transitioning to preset {} (elapsed time {} seconds)...").format(
                        preset.name, f"{worker_thread.total_elapsed_seconds:.2f}"))
                #self.transitioning_dummy_preset.update_progress() if self.transitioning_dummy_preset else None
                self.main_window.update_status_indicators(preset)

            def _restore_finished_callback(worker_thread: BulkChangeWorker) -> None:
                # self.transitioning_dummy_preset = None
                if worker_thread.vdu_exception is not None and not background_activity:  # if it's a GUI request, ask about retry
                    if self.main_window.get_main_panel().show_vdu_exception(worker_thread.vdu_exception, can_retry=True):
                        self.restore_preset(preset, finished_func=finished_func, immediately=immediately)  # Try again, new thread
                        return  # Don't do anything more, the new thread will take over from here
                preset.in_transition_step = 0
                self.main_window.indicate_busy(False)
                if not initialization_preset:
                    if self.main_window.tray is not None:
                        self.main_window.refresh_tray_menu()
                    if worker_thread.completed:
                        with open(CURRENT_PRESET_NAME_FILE, 'w', encoding="utf-8") as cps_file:
                            cps_file.write(preset.name)
                        self.main_window.update_status_indicators(preset)
                        if worker_thread.change_count != 0:
                            self.main_window.show_preset_status(tr("Restored {} (elapsed time {} seconds)").format(
                                preset.name, f"{worker_thread.total_elapsed_seconds:.2f}"))
                            if (self.main_config.is_set(ConfOpt.PROTECT_NVRAM_ENABLED)
                                    and preset.get_transition_type() != PresetTransitionFlag.NONE):
                                log_warning(
                                    f"restore-preset: protect-nvram prevents '{preset.name}' from stepping, changes are immediate.")
                        else:
                            self.main_window.show_preset_status(tr("Already on Preset {} (no changes)").format(preset.name))
                        if df := preset.get_daylight_factor():
                            log_info(f"Daylight-Factor {df:.4f} read from Preset {preset.name}")
                            LuxMeterSemiAutoDevice.set_daylight_factor(df, persist=True)
                    else:  # Interrupted or exception:
                        self.main_window.update_status_indicators()
                        self.main_window.show_preset_status(tr("Interrupted restoration of {}").format(preset.name))
                if finished_func is not None:
                    finished_func(worker_thread)

            log_debug(f"restore_preset: '{preset.name}' holding application_lock", trace=False) if log_debug_enabled else None
            if not immediately:
                self.main_window.show_preset_status(tr("Transitioning to preset {}").format(preset.name))
                self.main_window.update_status_indicators(preset)  # TODO - create a transitioning indicator
            self.main_window.indicate_busy(True, lock_controls=immediately)
            preset.load()
            bulk_changer = BulkChangeWorker('RestorePreset', self, _update_progress, _restore_finished_callback,
                                      step_interval=0.0 if immediately else 5.0,
                                      ignore_others=initialization_preset, context=preset)
            for vdu_stable_id in self.get_vdu_stable_id_list():
                if vdu_stable_id in preset.preset_ini:
                    for vcp_capability in self.get_enabled_capabilities(vdu_stable_id):
                        property_name = vcp_capability.property_name()
                        if property_name in preset.preset_ini[vdu_stable_id]:
                            if vcp_capability.vcp_type == CONTINUOUS_TYPE:
                                final_value = preset.preset_ini.getint(vdu_stable_id, property_name)
                            else:
                                final_value = int(preset.preset_ini[vdu_stable_id][property_name], 16)
                            bulk_changer.add_item(BulkChangeItem(vdu_stable_id, vcp_capability.vcp_code, final_value,
                                                           transition=vcp_capability.can_transition))
            self.preset_transition_workers.append(bulk_changer)
            log_debug(f"restore_preset: '{preset.name}' handover to WorkerThread") if log_debug_enabled else None
            bulk_changer.start()
            if initialization_preset:  # Don't allow anything else until it's finished
                bulk_changer.wait()
        log_debug(f"restore_preset: '{preset.name}' released application_lock") if log_debug_enabled else None

    def restore_vdu_initialization_presets(self):
        # Find presets that match the name of each VDU name+serial and restore them...
        for stable_id in self.vdu_controllers_map.keys():
            for preset in self.preset_controller.find_presets_map().values():
                preset_proper_name = proper_name(preset.name)
                if stable_id == preset_proper_name:
                    log_info(f"Found initialization-preset for {stable_id}")

                    def _restored_initialization_preset(worker: BulkChangeWorker) -> None:
                        if worker.vdu_exception is not None:
                            log_error(f"Error during restoration of '{preset.name}'")
                            self.status_message(tr("Error during restoration preset {}").format(preset.name), timeout=5)
                            return
                        log_info(f"Restored initialization-preset '{worker.context.name}'")
                        message = tr("Restored Preset\n{}").format(worker.context.name)
                        self.status_message(message, timeout=5)
                        self.main_window.splash_message_qtsignal.emit(message)
                        time.sleep(1.0)  # Pause to give the message time to display - TODO find non-delaying solution
                        self.main_window.update_status_indicators()  # Refresh to restore other non-init preset icons

                    self.restore_preset(preset, finished_func=_restored_initialization_preset, initialization_preset=True)

    def schedule_create_timetable(self, start_of_day: datetime, location: GeoLocation) -> Dict[datetime, Preset]:
        log_debug(f"Create preset timetable for {start_of_day}") if log_debug_enabled else None
        timetable_for_day: Dict[datetime, Preset] = {}  # Create a timetable for the entire day from 00:00:00 to 23:59:59
        time_elevation_map = create_elevation_map(start_of_day, latitude=location.latitude, longitude=location.longitude)
        for preset in self.preset_controller.find_presets_map().values():
            if elevation_key := preset.get_solar_elevation():
                if elevation_data := time_elevation_map.get(elevation_key):
                    preset.elevation_time_today = elevation_data.when
                    timetable_for_day[elevation_data.when] = preset
                else:
                    log_debug(f"schedule_create_timetable: Skipped preset '{preset.name}' {elevation_key} degrees,"
                              " the sun does not reach that elevation today.")
            if at_time := preset.get_at_time():
                timetable_for_day[at_time] = preset
        return {when: preset for when, preset in sorted(list(timetable_for_day.items()))}

    def schedule_presets(self) -> None:
        assert is_running_in_gui_thread()
        location = self.main_config.get_location()
        if location and self.main_config.is_set(ConfOpt.SCHEDULE_ENABLED):
            log_debug("schedule_presets: try to obtain application_lock") if log_debug_enabled else None
            with self.application_lock:
                log_debug("schedule_presets: holding application_lock") if log_debug_enabled else None
                ScheduleWorker.dequeue_all(SchedulerJobType.RESTORE_PRESET)
                start_of_today = zoned_now(rounded_to_minute=True).replace(hour=0, minute=0)
                timetable_for_today = self.schedule_create_timetable(start_of_today, location)
                if len(timetable_for_today) > 0:  # Use the timetable to schedule jobs
                    now = zoned_now()
                    if future_presets := [(when, preset) for when, preset in timetable_for_today.items() if when > now]:
                        for when, preset in future_presets:  # Schedule future part of day
                            preset.schedule(when, self.activate_scheduled_preset_in_gui, self.skip_scheduled_preset)
                    # Schedule the preset that might apply right now, either the first overdue, or last from yesterday
                    if overdue_presets := [(when, preset) for when, preset in timetable_for_today.items() if when <= now]:
                        when_overdue, most_recent_overdue_preset = overdue_presets[-1]  # first is the most recently applicable
                        if most_recent_overdue_preset.schedule_status != PresetScheduleStatus.SUCCEEDED:  # not already run
                            most_recent_overdue_preset.schedule(when_overdue, self.activate_scheduled_preset_in_gui, overdue=True)
                        for when, preset in overdue_presets[:-1]:  # The rest have been superseded (if not already succeeded)
                            if preset.schedule_status != PresetScheduleStatus.SUCCEEDED:  # not already run
                                preset.schedule_status = PresetScheduleStatus.SKIPPED_SUPERSEDED
                                log_info(f"Skipped preset '{preset.name}', passed assigned-time (status={preset.schedule_status})")
                    else:  # Nothing overdue today, schedule the last from yesterday (assumed to be the last for today)
                        last_preset_yesterday = list(timetable_for_today.values())[-1]  # last for yesterday same as last for today
                        last_preset_yesterday.schedule(start_of_today, self.activate_scheduled_preset_in_gui, overdue=True)
                # set a timer to rerun this scheduler at the start of the next day.
                ScheduleWorker.dequeue_all(SchedulerJobType.SCHEDULE_PRESETS)
                tomorrow = zoned_now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                # tomorrow = zoned_now().replace(second=0, microsecond=0) + timedelta(minutes=2) # testing
                daily_schedule_job = SchedulerJob(tomorrow, SchedulerJobType.SCHEDULE_PRESETS,
                                                  partial(self.main_window.run_in_gui_thread, self.schedule_presets))
                log_info(f"Will update schedule for Presets at {tomorrow} "
                         f"(in {round(daily_schedule_job.remaining_time() / 60)} minutes)")
            log_debug("schedule_presets: released application_lock") if log_debug_enabled else None
        else:
            log_info(f"Scheduling is disabled or no location ({location=})")
            ScheduleWorker.shutdown()
        PresetsDialog.reconfigure_instance()

    def schedule_alteration(self, preset: Preset) -> None:
        location = self.main_config.get_location()
        if location and self.main_config.is_set(ConfOpt.SCHEDULE_ENABLED):
            log_debug("schedule_alteration: try to obtain application_lock") if log_debug_enabled else None
            with self.application_lock:
                log_debug("schedule_alteration: holding application_lock") if log_debug_enabled else None
                preset.remove_elevation_trigger(quietly=True)
                start_of_today = zoned_now(rounded_to_minute=True).replace(hour=0, minute=0)
                timetable_for_today = self.schedule_create_timetable(start_of_today, location)
                if when := next((t for t, p in timetable_for_today.items() if p == preset), None):
                    if when > zoned_now():  # if destined for the future, schedule it
                        preset.schedule(when, self.activate_scheduled_preset_in_gui, overdue=False)
            log_debug("schedule_alteration: released application_lock") if log_debug_enabled else None
        else:
            log_info(f"schedule_alteration: Scheduling is disabled or no location ({location=})")

    def activate_scheduled_preset_in_gui(self, preset):
        self.main_window.run_in_gui_thread(partial(self.activate_scheduled_preset, preset))

    def activate_scheduled_preset(self, preset: Preset, check_weather: bool = True, immediately: bool = False,
                                  activation_time: datetime | None = None) -> None:
        assert is_running_in_gui_thread()

        def _activation_feedback(msg: str):
            self.main_window.show_preset_status(f"{TIME_CLOCK_SYMBOL} " + tr("Preset {} activating at {}").format(
                preset.name, f"{activation_time:%H:%M}") + f" - {msg}")

        def _activation_finished(worker: BulkChangeWorker) -> None:
            assert preset.elevation_time_today is not None or preset.get_at_time() is not None
            attempts = preset.scheduler_job.attempts
            if worker.vdu_exception is not None:
                too_close = zoned_now() + timedelta(seconds=60)  # retry if more than a minute before any others
                for other in self.preset_controller.find_presets_map().values():  # Skip retry if another is due soon
                    if (other.name != preset.name
                            and preset.elevation_time_today is not None and other.elevation_time_today is not None
                            and preset.elevation_time_today < other.elevation_time_today <= too_close):
                        log_info(f"Schedule restoration skipped '{preset.name}', too close to {other.name}")
                        if not off_schedule:
                            preset.schedule_status = PresetScheduleStatus.SKIPPED_SUPERSEDED
                        _activation_feedback(tr("Skipped, superseded"))
                        return
                _activation_feedback(tr("Error, trying again in {} seconds").format(60))
                if attempts == 1:
                    log_warning(f"Error during restoration of '{preset.name}', retrying every {60} seconds.")
                preset.scheduler_job.requeue()  # retry - retain old schedule time to maintain proper schedule order.
                return
            if not off_schedule:
                preset.schedule_status = PresetScheduleStatus.SUCCEEDED
            self.main_window.update_status_indicators(preset)
            _activation_feedback(tr("Restored {}").format(preset.name))
            log_info(f"Restored preset '{preset.name}' on try {attempts}") if attempts > 1 else None

        if not self.main_config.is_set(ConfOpt.SCHEDULE_ENABLED):
            log_info(f"Schedule is disabled - not activating preset '{preset.name}'")
            return
        if activation_time is None:
            activation_time = zoned_now()
        if preset.elevation_time_today:
            off_schedule = activation_time < preset.elevation_time_today  # Too early, must be an off-schedule catchup from yesterday
        else:
            off_schedule = activation_time < preset.get_at_time()
        if preset.is_weather_dependent() and check_weather and self.main_config.is_set(ConfOpt.WEATHER_ENABLED):
            if not self.is_weather_satisfactory(preset):
                if not off_schedule:
                    preset.schedule_status = PresetScheduleStatus.WEATHER_CANCELLATION
                message = tr("Preset {} activation was cancelled due to weather at {}").format(
                    preset.name, activation_time.isoformat(' ', 'seconds'))
                self.main_window.show_preset_status(message)
                return
        if preset.scheduler_job.attempts == 1:
            log_info(f"Activating scheduled preset '{preset.name}' transition={immediately} {off_schedule=}")
        # Happens asynchronously in a thread
        self.restore_preset(preset, finished_func=_activation_finished,
                            immediately=immediately or PresetTransitionFlag.SCHEDULED not in preset.get_transition_type(),
                            background_activity=True)

    def skip_scheduled_preset(self, preset: Preset):
        assert is_running_in_gui_thread()
        preset.schedule_status = PresetScheduleStatus.SKIPPED_SUPERSEDED
        self.main_window.update_status_indicators(preset)

    def is_weather_satisfactory(self, preset, use_cache: bool = False) -> bool:
        try:
            if not use_cache or self.weather_query is None:
                if location := self.main_config.get_location():
                    self.weather_query = WeatherQuery(location)
                    self.weather_query.run_query()
                    if not self.weather_query.proximity_ok:
                        log_error(f"Preset '{preset.name}' weather location is {self.weather_query.proximity_km} km from "
                                  f"Settings Location, check settings.")
                        weather_bad_location_dialog(self.weather_query)
            if not preset.check_weather(self.weather_query):
                return False
        except ValueError as e:
            MBox(MIcon.Warning, msg=tr("Ignoring weather requirements, unable to query local weather: {}").format(str(e.args[0])),
                 info=e.args[1]).exec()
        return True

    def find_preset_by_name(self, preset_name: str) -> Preset | None:
        return self.preset_controller.find_presets_map().get(preset_name)

    def restore_named_preset(self, preset_name: str) -> None:
        if preset := self.find_preset_by_name(preset_name):
            # Transition immediately unless the Preset is required to ALWAYS transition.
            self.restore_preset(preset, immediately=PresetTransitionFlag.MENU not in preset.get_transition_type())

    def save_preset(self, preset: Preset) -> None:
        self.preset_controller.save_preset(preset)
        if self.main_window.app_context_menu.get_preset_menu_action(preset.name) is None:
            self.main_window.app_context_menu.insert_preset_menu_action(preset)
        self.main_window.update_status_indicators()
        preset.remove_elevation_trigger()
        self.schedule_alteration(preset)

    def save_preset_order(self, name_order: List[str]):
        self.preset_controller.save_order(name_order)
        self.refresh_preset_menu(reorder=True)

    def populate_ini_from_vdus(self, preset_ini: ConfIni, update_only: bool = False) -> None:
        for control_panel in self.main_window.get_main_panel().vdu_control_panels.values():
            vdu_section_name = control_panel.controller.vdu_stable_id
            if not preset_ini.has_section(vdu_section_name):
                preset_ini.add_section(vdu_section_name)
            for control in control_panel.vcp_controls:  # Fill out value for any options present in the preset_ini.
                if not update_only or preset_ini.has_option(vdu_section_name, control.vcp_capability.property_name()):
                    if control.current_value is not None:
                        preset_ini[vdu_section_name][control.vcp_capability.property_name()] = control.get_current_text_value()

    def delete_preset(self, preset: Preset) -> None:
        self.preset_controller.delete_preset(preset)
        self.main_window.app_context_menu.remove_preset_menu_action(preset.name)
        self.main_window.update_status_indicators()

    def refresh_preset_menu(self, reorder: bool = False):
        self.main_window.refresh_preset_menu(reorder=reorder)

    def which_preset_is_active(self) -> Preset | None:
        # See if we have a record of which was last active, and see if it still is active
        main_panel = self.main_window.get_main_panel()
        if CURRENT_PRESET_NAME_FILE.exists():
            with open(CURRENT_PRESET_NAME_FILE, encoding="utf-8") as cps_file:
                if preset_name := cps_file.read().strip():
                    preset = self.preset_controller.find_presets_map().get(preset_name)  # will be None if it has been deleted
                    if preset is not None and main_panel.is_preset_active(preset):
                        return preset
        # Guess by testing each possible preset against the current VDU settings
        for preset in self.preset_controller.find_presets_map().values():
            if main_panel.is_preset_active(preset):
                return preset
        return None

    def find_presets_map(self) -> Dict[str, Preset]:
        return self.preset_controller.find_presets_map()

    def get_lux_auto_controller(self) -> LuxAutoController:
        assert self.lux_auto_controller is not None
        return self.lux_auto_controller

    def get_vdu_stable_id_list(self) -> List[VduStableId]:
        return [stable_id for stable_id, vdu_controller in self.vdu_controllers_map.items() if not vdu_controller.ignore_vdu]

    def get_vdu_values(self, vdu_stable_id: VduStableId, vcp_codes: List[str] | None) -> List[Tuple[str, VcpValue]]:
        if controller := self.vdu_controllers_map.get(vdu_stable_id):
            if not vcp_codes:
                vcp_codes = [capability.vcp_code for capability in controller.enabled_capabilities]
            return [(code, value) for code, value in zip(vcp_codes, controller.get_vcp_values(vcp_codes))]
        return []

    def get_enabled_capabilities(self, vdu_stable_id: VduStableId) -> List[VcpCapability]:
        if controller := self.vdu_controllers_map.get(vdu_stable_id):
            return controller.enabled_capabilities
        return []

    def get_range(self, vdu_stable_id: VduStableId, vcp_code: str,
                  fallback: Tuple[int, int] | None = None) -> Tuple[int, int] | None:
        if controller := self.vdu_controllers_map.get(vdu_stable_id):
            return controller.get_range_restrictions(vcp_code, fallback)
        log_error(f"get_range: No controller for {vdu_stable_id}")
        return fallback

    def get_value(self, vdu_stable_id, vcp_code) -> int:
        if controller := self.vdu_controllers_map.get(vdu_stable_id):
            value = controller.get_vcp_values([vcp_code])
            if len(value) == 1:  # This could probably be an assertion
                return value[0].current
        log_error(f"get_value: No controller for {vdu_stable_id}")
        return 0

    def set_value(self, vdu_stable_id: VduStableId, vcp_code: str, value: int, origin: VcpOrigin = VcpOrigin.NORMAL):
        if panel := self.main_window.get_main_panel().vdu_control_panels.get(vdu_stable_id):
            if control := panel.get_control(vcp_code):
                control.set_value(value, origin)  # Apply to physical VDU
                return
        log_error(f"set_value: No controller for {vdu_stable_id=} {vcp_code=}")

    def is_vcp_code_enabled(self, vdu_stable_id, vcp_code: str) -> bool:
        if controller := self.vdu_controllers_map.get(vdu_stable_id):
            for capability in controller.enabled_capabilities:
                if capability.vcp_code == vcp_code:
                    return True
        return False

    def update_window_status_indicators(self, preset: Preset | None = None):
        if not is_running_in_gui_thread():
            self.main_window.run_in_gui_thread(partial(self.main_window.update_status_indicators, preset))

    def get_vdu_preferred_name(self, vdu_stable_id: VduStableId):
        if controller := self.vdu_controllers_map.get(vdu_stable_id):
            return controller.get_vdu_preferred_name()
        log_error(f"get_vdu_description: No controller for {vdu_stable_id}")
        return vdu_stable_id

    def busy_doing(self) -> str | None:
        return tr("Preset editing") if PresetsDialog.is_instance_editing() else None

    def find_vdu_config_files(self) -> List[Path]:
        found = []
        for conf_file in [f for f in sorted(CONFIG_DIR_PATH.glob('*_*_*.conf')) if f.is_file()]:
            conf = ConfIni()
            conf.read(conf_file.as_posix())
            if conf.has_section(ConfOpt.CAPABILITIES_OVERRIDE.conf_id[0]) and conf.get(*ConfOpt.CAPABILITIES_OVERRIDE.conf_id):
                found.append(conf_file)
        log_debug(f"find_vdu_config_files {found}")
        return found

    def status_message(self, message: str, timeout: int, destination: MsgDestination = MsgDestination.DEFAULT):
        self.main_window.status_message(message, timeout, destination)

    def restart_application(self, reason: str):
        # Force a restart of the application.  Some settings changes need this (for example, run in the system tray).
        MBox(MIcon.Warning, msg=reason, info=tr('When this message is dismissed, vdu_controls will restart.')).exec()
        self.main_window.app_save_window_state()
        QCoreApplication.exit(EXIT_CODE_FOR_RESTART)


class VduAppWindow(QMainWindow):
    splash_message_qtsignal = pyqtSignal(str)
    _run_in_gui_thread_qtsignal = pyqtSignal(object)

    def __init__(self, main_config: VduControlsConfig, main_controller: VduAppController) -> None:
        super().__init__()
        global gui_thread
        app = QApplication.instance()
        assert app
        gui_thread = app.thread()
        self.main_controller: VduAppController = main_controller
        self.setObjectName('main_window')
        self.qt_version_key = self.objectName() + "_qt_version"
        self.qt_geometry_key = self.objectName() + "_geometry"
        self.qt_state_key = self.objectName() + "_window_state"
        self.qt_settings = QSettings('vdu_controls.qt.state', 'vdu_controls')
        self.main_panel: VduControlsMainPanel | None = None
        self.scroll_area: QScrollArea | None = None
        self.main_config = main_config
        self.hide_shortcuts = True

        def _run_in_gui(task: Callable):
            log_debug(f"Running task in gui thread {repr(task)}") if log_debug_enabled else None
            task()  # Was using a partial, but it silently failed when task was a method with only self and no other arguments.

        self._run_in_gui_thread_qtsignal.connect(_run_in_gui)

        os_desktop = os.environ.get('XDG_CURRENT_DESKTOP', default='unknown').lower()
        use_gnome_like_tray = main_config.is_set(ConfOpt.SYSTEM_TRAY_ENABLED) and (is_gnome_desktop() or is_cosmic_desktop())
        log_info(f"{os_desktop=} {use_gnome_like_tray=}")  # Gnome tray doesn't provide a way to bring up the main app.

        global log_debug_enabled
        if log_debug_enabled:
            for screen in app.screens():
                log_info("Screen", screen.name())

        self.app_context_menu = ContextMenu(
            app_controller=main_controller,
            main_window_action=partial(self.show_main_window, True) if use_gnome_like_tray else None,
            about_action=partial(AboutDialog.invoke, self.main_controller),
            help_action=HelpDialog.invoke,
            gray_scale_action=GreyScaleDialog,
            lux_auto_action=self.main_controller.lux_auto_action if main_config.is_set(ConfOpt.LUX_OPTIONS_ENABLED) else None,
            lux_check_action=self.main_controller.lux_check_action if main_config.is_set(ConfOpt.LUX_OPTIONS_ENABLED) else None,
            lux_meter_action=partial(LuxDialog.invoke, self.main_controller) if main_config.is_set(
                ConfOpt.LUX_OPTIONS_ENABLED) else None,
            settings_action=self.main_controller.edit_config,
            presets_dialog_action=self.main_controller.show_presets_dialog,
            refresh_action=self.main_controller.start_refresh,
            quit_action=self.quit_app,
            hide_shortcuts=self.hide_shortcuts, parent=self)

        splash_pixmap = get_splash_image()
        splash = QSplashScreen(
            splash_pixmap.scaledToWidth(native_font_height(scaled=26)).scaledToHeight(native_font_height(scaled=13)),
            Qt.WindowType.WindowStaysOnTopHint) if main_config.is_set(ConfOpt.SPLASH_SCREEN_ENABLED) else None
        if splash is not None:
            splash.show()
            splash.raise_()  # Attempt to force it to the top with raise and activate
            splash.activateWindow()
        self.app_icon: QIcon | None = None
        self.tray_icon: QIcon | None = None
        self.initialise_app_icon(splash_pixmap)

        def f10_func():
            self.app_context_menu.exec(QCursor.pos())

        f10_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F10), self)  # New Qt standard shortcut for context menu.
        f10_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        f10_shortcut.activated.connect(f10_func)

        self.tray = None
        if main_config.is_set(ConfOpt.SYSTEM_TRAY_ENABLED):
            if not QSystemTrayIcon.isSystemTrayAvailable():
                log_warning("no system tray, waiting to see if one becomes available.")
                for _ in range(0, SYSTEM_TRAY_WAIT_SECONDS):
                    if QSystemTrayIcon.isSystemTrayAvailable():
                        break
                    time.sleep(0.25)  # TODO - at least use a constant
            if QSystemTrayIcon.isSystemTrayAvailable():
                log_info("Using system tray.")
                app.setQuitOnLastWindowClosed(False)  # This next call appears to be automatic on KDE, but not on gnome.
                self.tray = QSystemTrayIcon(parent=self)
                self.tray.setContextMenu(self.app_context_menu)
            else:
                log_error("no system tray - cannot run in system tray.")

        self.app_name = APPNAME
        app.setApplicationDisplayName(self.app_name)
        if QT5_USE_HIGH_DPI_PIXMAPS:
            app.setAttribute(QT5_USE_HIGH_DPI_PIXMAPS)  # Make sure all icons use HiDPI - toolbars don't by default, so force it.

        if splash is not None:
            splash.showMessage(tr('\n\nVDU Controls\nLooking for DDC monitors...\n'), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        def _splash_message_action(message) -> None:
            if splash is not None:
                log_info(f"splash_message: {repr(message)}")
                splash.showMessage(f"\n\n{APPNAME} {VDU_CONTROLS_VERSION}\n{message}", Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.splash_message_qtsignal.connect(_splash_message_action)

        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.main_controller.configure_application(self)

        self.inactive_pause_millis = int(os.environ.get('VDU_CONTROLS_INACTIVE_PAUSE_MILLIS', default='1200'))
        self.active_event_count = 0
        app.applicationStateChanged.connect(self.on_application_state_changed)
        self.installEventFilter(self)

        if self.tray is not None:
            self.hide()
            self.tray.activated.connect(partial(self.show_main_window, True))
            self.tray.show()
        else:
            self.show_main_window()

        if splash is not None:
            splash.finish(self)
            splash.deleteLater()
            splash = None

        if main_config.file_path is None or main_config.ini_content.get_version() < VDU_CONTROLS_VERSION_TUPLE:  # New version...
            release_alert = MBox(
                MIcon.Information,
                msg=RELEASE_ANNOUNCEMENT.format(WELCOME=tr(RELEASE_WELCOME), NOTE=tr(RELEASE_NOTE), VERSION=VDU_CONTROLS_VERSION),
                info=RELEASE_INFO, buttons=MBtn.Close)
            release_alert.setTextFormat(Qt.TextFormat.RichText)
            release_alert.exec()
            main_config.write_file(ConfIni.get_path('vdu_controls'), overwrite=True)  # Stops release notes from being repeated.

    def is_inactive(self):
        if QApplication.instance().applicationState() != Qt.ApplicationState.ApplicationInactive:
            return False
        for top_level_widget in QApplication.topLevelWidgets():  # Check if any dialogs are active
            if isinstance(top_level_widget, DialogSingletonMixin) or isinstance(top_level_widget, GreyScaleDialog):
                if top_level_widget.isVisible():
                    return False  # A dialog is showing - definitely active
        return True  # inactive and no dialogs are active

    def on_application_state_changed(self, _: Qt.ApplicationState):
        if self.main_config.is_set(ConfOpt.HIDE_ON_FOCUS_OUT):
            if self.is_inactive():
                # The user may be using the title-bar or window-edges to move/resize the window. Monitor for the lack of
                # move/resize events, treat that as a real focus out.  This is needed for gnome and xfce.
                self.active_event_count = 0  # Count the following move/resize events as evidence of titlebar edge-grab activity.

                def _hide_func():
                    if self.active_event_count == 0 and self.is_inactive():  # No moving/resizing activity and is_inactive().
                        self.hide() if self.tray else self.showMinimized()  # Probably safe to hide now

                QTimer.singleShot(self.inactive_pause_millis, _hide_func)  # wait N ms and see if any move/resize events occur.

    def eventFilter(self, target: QObject | None, event: QEvent | None) -> bool:
        # log_info(f"eventFilter {event.__class__.__name__} {event.type()}")
        if event and event.type() in (QEvent.Type.Move, QEvent.Type.Resize, QEvent.Type.WindowActivate):  # Still active if being moved or resized
            self.active_event_count += 1
        return super().eventFilter(target, event)

    def show_main_window(self, toggle: bool = False) -> None:
        if toggle and self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()  # Attempt to force it to the top with raise and activate
            self.activateWindow()

    def show(self):
        if self.main_config.is_set(ConfOpt.SMART_WINDOW):
            if not self.app_restore_window_state():  # No previous state or invalid
                self.adjustSize()
                self.app_decide_window_position()  # decide initial position relative to cursor
                self.app_save_window_state()
        super().show()

    def hide(self):
        if self.main_config.is_set(ConfOpt.SMART_WINDOW):
            if self.isVisible():  # Only save position if really on screen
                self.app_save_window_state()
        super().hide()

    def quit_app(self) -> None:
        self.app_save_window_state()
        QApplication.instance().quit()
        sys.exit(0)  # Just in case self.app.quit() errors

    def initialise_app_icon(self, splash_pixmap: QPixmap | None = None):
        global mono_light_tray
        self.app_icon = QIcon()
        self.app_icon.addPixmap(get_splash_image() if splash_pixmap is None else splash_pixmap)
        tray_theme_type = get_tray_theme_type(self.main_config)
        if CUSTOM_TRAY_ICON_FILE.exists() and os.access(CUSTOM_TRAY_ICON_FILE.as_posix(), os.R_OK):
            log_info(f"Loading custom app_icon: {CUSTOM_TRAY_ICON_FILE} {tray_theme_type=}")
            self.tray_icon = create_icon_from_path(CUSTOM_TRAY_ICON_FILE, tray_theme_type)
        elif tray_theme_type in (ThemeType.MONOCHROME_LIGHT, ThemeType.MONOCHROME_DARK):  # Special tray monochrome version
            log_info(f"Using monochrome app_icon: {tray_theme_type=}")
            self.tray_icon = create_icon_from_svg_bytes(MONOCHROME_APP_ICON, tray_theme_type)
        else:  # non-themed color icon based on the splash screen image
            self.tray_icon = self.app_icon

    def create_main_control_panel(self) -> None:
        # Call on initialization and whenever the number of connected VDUs changes.
        if self.main_panel is not None:
            self.main_panel.deleteLater()
            self.main_panel = None
        if self.scroll_area is not None:
            self.scroll_area.deleteLater()
            self.scroll_area = None
        self.main_panel = VduControlsMainPanel()
        self.main_controller.initialize_vdu_controllers()
        refresh_button = ToolButton(REFRESH_ICON_SOURCE, tr("Refresh settings from monitors"))
        refresh_button.pressed.connect(self.main_controller.start_refresh)
        tool_buttons = [refresh_button]
        extra_controls = []
        if self.main_controller.lux_auto_controller is not None:
            self.main_controller.lux_auto_controller.lux_config.load()  # may have changed
            if lux_auto_button := self.main_controller.lux_auto_controller.create_tool_button():
                lux_auto_button.pressed.connect(self.main_controller.lux_auto_action)
                tool_buttons.append(lux_auto_button)
            if lux_check_button := self.main_controller.lux_auto_controller.create_lighting_check_button():
                lux_check_button.pressed.connect(self.main_controller.lux_check_action)
                tool_buttons.append(lux_check_button)
            if lux_manual_input := self.main_controller.lux_auto_controller.create_manual_input_control():
                extra_controls.append(lux_manual_input)
            if lux_ambient_slider := self.main_controller.lux_auto_controller.lux_slider:
                lux_ambient_slider.status_icon_changed_qtsignal.connect(self.update_status_indicators)
        self.refresh_preset_menu()
        self.main_panel.initialise_control_panels(self.main_controller, self.app_context_menu, self.main_config,
                                                  tool_buttons, extra_controls, self.splash_message_qtsignal)
        # Wire-up after successful init to avoid deadlocks
        self.main_panel.vdu_vcp_changed_qtsignal.connect(self.respond_to_changes_handler)
        self.indicate_busy(True)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.main_panel)
        self.setCentralWidget(self.scroll_area)

        available_height = self.screen().availableGeometry().height() - npx(200)  # Minus allowance for panel/tray
        hint_height = self.main_panel.sizeHint().height()  # The hint is the actual required layout space
        hint_width = self.main_panel.sizeHint().width()
        log_debug(f"create_main_control_panel: {hint_height=} {available_height=} {self.minimumHeight()=}")
        if hint_height > available_height:
            log_debug(f"Main panel too high, adding scroll-area {hint_height=} {available_height=}") if log_debug_enabled else None
            self.setMaximumHeight(available_height)
            self.setMinimumWidth(hint_width + 20)  # Allow extra space for disappearing scrollbars
        else:  # Don't mess with the size unnecessarily - let the user determine it?
            self.setMinimumHeight(hint_height + 20)
            if hint_height != self.height():
                self.setMinimumWidth(self.width())
                self.adjustSize()
            self.setMinimumWidth(hint_width + 20)

        self.splash_message_qtsignal.emit(tr("Checking Presets"))

    def get_main_panel(self) -> VduControlsMainPanel:
        assert self.main_panel is not None
        return self.main_panel

    def indicate_busy(self, is_busy: bool, lock_controls: bool = True):
        if self.main_panel:
            self.main_panel.indicate_busy(is_busy, lock_controls)
        self.app_context_menu.indicate_busy(is_busy)

    def show_preset_status(self, message: str, timeout: int = 3000):
        PresetsDialog.show_status_message(message=message, timeout=timeout)
        self.status_message(message, timeout=timeout, destination=MsgDestination.DEFAULT)

    def update_status_indicators(self, preset: Preset|None = None, palette_change: bool = False) -> None:
        assert is_running_in_gui_thread()  # Boilerplate in case this is called from the wrong thread.
        if self.main_panel is None:  # On deepin 23, events can trigger this method before initialization is complete
            return
        title = self.app_name
        tray_embedded_icon = led1_color = led2_color = None
        if preset is None:  # Detects matching Preset based on current VDU control settings
            preset = self.main_controller.which_preset_is_active()
        if preset is None:  # Clears the indicators
            self.get_main_panel().show_active_preset(None)
            self.app_context_menu.indicate_preset_active(None)
            PresetsDialog.instance_indicate_active_preset(None)
        else:  # Set indicators to specific preset
            self.get_main_panel().show_active_preset(preset)
            self.app_context_menu.indicate_preset_active(preset)
            PresetsDialog.instance_indicate_active_preset(preset)
            title = f"{preset.get_title_name()} {PRESET_APP_SEPARATOR_SYMBOL} {title}"
            tray_embedded_icon = preset.create_icon(get_tray_theme_type(self.main_config))
            led1_color = PRESET_TRANSITIONING_LED_COLOR if preset.in_transition_step > 0 else None   # TODO transitioning indicator
        if self.main_controller.lux_auto_controller is not None:
            if self.main_controller.lux_auto_controller.is_auto_enabled():
                title = f"{tr('Auto')}/{title}"
                led2_color = AUTO_LUX_LED_COLOR
            menu_lux_icon = create_icon_from_svg_bytes(self.main_controller.lux_auto_controller.current_auto_svg())  # NB cache involved
            self.app_context_menu.update_lux_auto_icon(menu_lux_icon)  # Won't actually update if it hasn't changed
            if tray_embedded_icon is None and self.main_config.is_set(ConfOpt.LUX_TRAY_ICON):
                if zone := self.main_controller.lux_auto_controller.get_lux_zone():
                    tray_embedded_icon = create_icon_from_svg_bytes(zone.icon_svg, get_tray_theme_type(self.main_config))
                    title = title + '\n' + tr("Lighting: {}").format(zone.name.lower())

        if self.windowTitle() != title:  # Don't change if not needed - prevent flickering.
            self.setWindowTitle(title)
            QApplication.instance().setWindowIcon(create_decorated_app_icon(self.app_icon, tray_embedded_icon, led1_color, led2_color))
        if self.tray:
            self.tray.setToolTip(title)
            self.tray.setIcon(create_decorated_app_icon(self.tray_icon, tray_embedded_icon, led1_color, led2_color))
        if palette_change or preset is not None:
            self.refresh_preset_menu(palette_change=palette_change)

    def respond_to_changes_handler(self, vdu_stable_id: VduStableId, vcp_code: str, value: int, origin: VcpOrigin,
                                   causes_config_change: bool) -> None:
        # Update UI secondary displays
        AboutDialog.refresh()
        for panel in self.main_panel.vdu_control_panels.values():
            panel.update_stats()
        if causes_config_change and origin == VcpOrigin.NORMAL:  # only respond if this is an internally initiated change
            log_info(f"Must reconfigure due to change to: {vdu_stable_id=} {vcp_code=} {value=} {origin}")
            self.main_controller.configure_application()  # Special case, such as a power control causing the VDU to go offline.
            return
        log_debug(f"respond_to_changes_handler {vdu_stable_id=} {vcp_code=} {value=} {origin}") if log_debug_enabled else None
        if origin != VcpOrigin.TRANSIENT:  # Only want to indicate final status (not when just passing through a preset)
            self.update_status_indicators()
            if origin != VcpOrigin.EXTERNAL:
                self.status_message(SET_VCP_SYMBOL, timeout=500, destination=MsgDestination.DEFAULT)
        if self.main_config.is_set(ConfOpt.LUX_OPTIONS_ENABLED) and self.main_controller.lux_auto_controller is not None:
            if vcp_code == BRIGHTNESS_VCP_CODE:
                LuxDialog.lux_dialog_show_brightness(vdu_stable_id, value)

    def refresh_tray_menu(self) -> None:
        assert is_running_in_gui_thread()
        self.app_context_menu.update()

    def closeEvent(self, event) -> None:
        self.app_save_window_state()

    def app_save_window_state(self) -> None:
        if self.main_config.is_set(ConfOpt.SMART_WINDOW, fallback=True) and self.isVisible():
            log_debug(f"app_save_window_state: {self.pos()=} {self.geometry()=} {QtCore.qVersion()}") if log_debug_enabled else None
            self.qt_settings.setValue(self.qt_version_key, QtCore.qVersion())
            self.qt_settings.setValue(self.qt_geometry_key, self.saveGeometry())
            self.qt_settings.setValue(self.qt_state_key, self.saveState())

    def app_restore_window_state(self) -> bool:
        log_debug(f"app_restore_window_state")
        if not self.main_config.is_set(ConfOpt.SMART_WINDOW, fallback=True):
            return False
        if len(self.qt_settings.allKeys()) == 0:  # No previous state
            return False
        save_version_major = self.qt_settings.value(self.qt_version_key, '5').split('.', 1)[0]
        qt_version_major = QtCore.qVersion().split('.', 1)[0]
        if save_version_major != qt_version_major:
            log_warning(f"app_restore_window_state: cannot restore: {save_version_major=} != {qt_version_major=}")
            return False  # Different Qt versions - cannot restore size, layout/size/scaling might be different.
        if geometry := self.qt_settings.value(self.qt_geometry_key, None):
            self.restoreGeometry(geometry)
        if window_state := self.qt_settings.value(self.qt_state_key, None):
            self.restoreState(window_state)
        log_debug(f"app_restore_window_state: {self.pos()=} {self.geometry()=}") if log_debug_enabled else None
        return True


    def app_decide_window_position(self):
        # Guess a window position near the tray. Use the mouse/cursor-pos as a guess to where the
        # system tray is.  Under Linux Qt the position of the tray icon is reported as 0,0, so we can't use that.
        cursor_x, cursor_y = QCursor.pos().x(), QCursor.pos().y()
        app_width, app_height = self.geometry().width(), self.geometry().height()
        desktop_width, desktop_height = (self.screen().availableGeometry().width(),
                                         self.screen().availableGeometry().height())
        # The following calculations allow for the tray being on any edge of the desktop...
        margin = min(abs(desktop_height - cursor_y), abs(desktop_width - cursor_x), npx(100)) + npx(25) if self.tray else 0
        x = cursor_x - app_width - margin if cursor_x > app_width else cursor_x + margin
        y = cursor_y - app_height - margin if cursor_y > app_height else cursor_y + margin
        log_debug(f"decide_window_position: {x=} {y=} {app_width=} {app_height=} {cursor_x=} {cursor_y=} {margin=}")
        self.setGeometry(x, y, app_width, app_height)

    def status_message(self, message: str, timeout: int, destination: MsgDestination):
        assert (self.main_panel is not None)
        if not is_running_in_gui_thread():
            self.run_in_gui_thread(partial(self.status_message, message, timeout, destination))
        else:
            if destination == MsgDestination.DEFAULT:
                self.main_panel.status_message(message, timeout)
                QApplication.processEvents()  # Force the message out straight way.

    def event(self, event: QEvent | None) -> bool:
        # PalletChange happens after the new style sheet is in use.
        if event and event.type() == QEvent.Type.PaletteChange:
            log_info("PaletteChange event: New style sheet in use, update icons")
            self.initialise_app_icon()
            self.update_status_indicators(palette_change=True)
        return super().event(event)

    def refresh_preset_menu(self, palette_change: bool = False, reorder: bool = False):
        self.app_context_menu.refresh_preset_menu(palette_change=palette_change, reorder=reorder)

    def show_no_controllers_error_dialog(self, ddcutil_problem: Exception):
        log_error("No controllable monitors found.")
        if isinstance(ddcutil_problem, subprocess.SubprocessError):
            problem_text = ddcutil_problem.stderr.decode('utf-8', errors='surrogateescape') + '\n' + str(ddcutil_problem)
        else:
            problem_text = str(ddcutil_problem)
        log_error(f"Most recent error: {problem_text}".encode("unicode_escape").decode("utf-8"))
        MBox(MIcon.Critical, msg=tr('No controllable monitors found.'),
             info=tr("Is ddcutil or ddcutil-service installed and working?") + "\n\n" +
                  tr("Most recent error: {}").format(problem_text) + "\n" + '_' * 80).exec()

    def ask_for_vdu_controller_remedy(self, vdu_number: str, model_name: str, vdu_serial: str):
        msg = tr('Failed to obtain capabilities for monitor {} {} {}.').format(vdu_number, model_name, vdu_serial)
        info = tr('Cannot automatically configure this monitor.'
                  '\n You can choose to:'
                  '\n 1: Retry obtaining the capabilities.'
                  '\n 2: Temporarily ignore this monitor.'
                  '\n 3: Apply standard brightness and contrast controls.'
                  '\n 4: Permanently discard this monitor from use with vdu_controls.'
                  '\n\nPossibly just a timing error, maybe a retry will work\n(see Settings: sleep multiplier)\n\n')
        choice = MBox(MIcon.Critical, msg=msg, info=info, buttons=MBtn.Discard | MBtn.Ignore | MBtn.Apply | MBtn.Retry).exec()
        if choice == MBtn.Discard:
            MBox(MIcon.Information, msg=tr('Discarding {} monitor.').format(model_name),
                 info=tr('Remove "{}" from {} capabilities override to reverse this decision.').format(IGNORE_VDU_MARKER_STR,
                                                                                                       model_name)).exec()
            return VduController.DISCARD_VDU
        elif choice == MBtn.Ignore:
            MBox(MIcon.Information, msg=tr('Ignoring {} monitor for now.').format(model_name),
                 info=tr('Will retry when vdu_controls is next started')).exec()
            return VduController.IGNORE_VDU
        elif choice == MBtn.Apply:
            MBox(MIcon.Information, msg=tr('Assuming {} has brightness and contrast controls.').format(model_name),
                 info=tr('Wrote {} config files to {}.').format(model_name, CONFIG_DIR_PATH) +
                      tr('\nPlease check these files and edit or remove them if they '
                         'cause further issues.')).exec()
            return VduController.ASSUME_STANDARD_CONTROLS
        elif choice == MBtn.Retry:
            return VduController.NORMAL_VDU
        return VduController.IGNORE_VDU

    def run_in_gui_thread(self, task: Callable):
        self._run_in_gui_thread_qtsignal.emit(task)


class SignalWakeupHandler(QtNetwork.QAbstractSocket):
    # https://stackoverflow.com/a/37229299/609575
    # '''
    # Quoted here: The Qt event loop is implemented in C(++). That means, that while it runs and no Python code is
    # called (e.g. by a Qt signal connected to a Python slot), the signals are noted, but the Python signal handlers
    # aren't called.
    #
    # But, since Python 2.6 and in Python 3 you can cause Qt to run a Python function when a signal with a handler is
    # received using signal.set_wakeup_fd().
    #
    # This is possible because, contrary to the documentation, the low-level signal handler doesn't only set a flag
    # for the virtual machine, but it may also write a byte into the file descriptor set by set_wakeup_fd(). Python 2
    # writes a NUL byte, Python 3 writes the signal number.
    #
    # So by subclassing a Qt class that takes a file descriptor and provides a readReady() signal, like e.g.
    # QAbstractSocket, the event loop will execute a Python function every time a signal (with a handler) is received
    # causing the signal handler to execute nearly instantaneously without the need for timers:
    # '''

    received_unix_signal_qtsignal = pyqtSignal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(QtNetwork.QAbstractSocket.SocketType.UdpSocket, parent)
        self.old_fd = None
        self.wsock, self.rsock = socket.socketpair(type=socket.SOCK_DGRAM)  # Create a socket pair
        self.setSocketDescriptor(self.rsock.fileno())  # Let Qt listen on the one end
        self.wsock.setblocking(False)  # And let Python write on the other end
        self.old_fd = signal.set_wakeup_fd(self.wsock.fileno())
        # First Python code executed gets any exception from the signal handler, so add a do-nothing handler first
        self.readyRead.connect(lambda: None)
        self.readyRead.connect(self._readSignal)  # Second handler does the real handling

    def __del__(self) -> None:
        if self.old_fd is not None and signal is not None and signal.set_wakeup_fd is not None:
            signal.set_wakeup_fd(self.old_fd)  # Restore any old handler on deletion

    def _readSignal(self) -> None:
        # Read the written byte. Note: readyRead is blocked from occurring again until readData()
        # is called, so call it, even if you don't need the value.
        data = self.readData(1)
        signal_number = int(data[0])
        log_info("SignalWakeupHandler", signal_number)
        self.received_unix_signal_qtsignal.emit(signal_number)  # Emit a Qt signal for convenience


# FUNCTION TO COMPUTE SOLAR AZIMUTH AND ZENITH ANGLE
# Extracted from a larger gist by Antti Lipponen: https://gist.github.com/anttilipp/1c482c8cc529918b7b973339f8c28895
# which was translated to Python from http://www.psa.es/sdg/sunpos.htm
# Converted to only use the python math library (instead of numpy) by me for vdu_controls.
# Coding style also altered for use with vdu_controls.
def calc_solar_azimuth_zenith(localised_time: datetime, latitude: float, longitude: float) -> Tuple[float, float]:
    """Return azimuth degrees clockwise from true north and zenith in degrees from vertical direction."""

    utc_date_time = localised_time if localised_time.tzinfo is None else localised_time.astimezone(timezone.utc)
    # UTC from now on...
    hours, minutes, seconds = utc_date_time.hour, utc_date_time.minute, utc_date_time.second
    year, month, day = utc_date_time.year, utc_date_time.month, utc_date_time.day

    earth_mean_radius = 6371.01
    astronomical_unit = 149597890

    # Calculate the difference in days between the current Julian Day and JD 2451545.0, which is noon 1 January 2000 Universal Time

    # Calculate the time of the day in UT decimal hours
    decimal_hours = hours + (minutes + seconds / 60.) / 60.
    # Calculate current Julian Day
    aux1 = int((month - 14.) / 12.)
    aux2 = int((1461. * (year + 4800. + aux1)) / 4.) + int((367. * (month - 2. - 12. * aux1)) / 12.) - int(
        (3. * int((year + 4900. + aux1) / 100.)) / 4.) + day - 32075.
    julian_date = aux2 - 0.5 + decimal_hours / 24.
    # Calculate the difference between current Julian Day and JD 2451545.0
    elapsed_julian_days = julian_date - 2451545.0

    # Calculate ecliptic coordinates (ecliptic longitude and obliquity of the ecliptic in radians but
    # without limiting the angle to be less than 2*Pi (i.e., the result may be greater than 2*Pi)
    omega = 2.1429 - 0.0010394594 * elapsed_julian_days
    mean_longitude = 4.8950630 + 0.017202791698 * elapsed_julian_days  # Radians
    mean_anomaly = 6.2400600 + 0.0172019699 * elapsed_julian_days
    ecliptic_longitude = mean_longitude + 0.03341607 * math.sin(mean_anomaly) + 0.00034894 * math.sin(
        2. * mean_anomaly) - 0.0001134 - 0.0000203 * math.sin(omega)
    ecliptic_obliquity = 0.4090928 - 6.2140e-9 * elapsed_julian_days + 0.0000396 * math.cos(omega)

    # Calculate celestial coordinates (right ascension and declination) in radians but without limiting
    # the angle to be less than 2*Pi (i.e., the result may be greater than 2*Pi)
    sin_ecliptic_longitude = math.sin(ecliptic_longitude)
    dy = math.cos(ecliptic_obliquity) * sin_ecliptic_longitude
    dx = math.cos(ecliptic_longitude)
    right_ascension = math.atan2(dy, dx)
    if right_ascension < 0.0:
        right_ascension = right_ascension + 2.0 * math.pi
    declination = math.asin(math.sin(ecliptic_obliquity) * sin_ecliptic_longitude)

    # Calculate local coordinates ( azimuth and zenith angle ) in degrees
    greenwich_mean_sidereal_time = 6.6974243242 + 0.0657098283 * elapsed_julian_days + decimal_hours
    local_mean_sidereal_time = (greenwich_mean_sidereal_time * 15. + longitude) * (math.pi / 180.)
    hour_angle = local_mean_sidereal_time - right_ascension
    latitude_in_radians = latitude * (math.pi / 180.)
    cos_latitude = math.cos(latitude_in_radians)
    sin_latitude = math.sin(latitude_in_radians)
    cos_hour_angle = math.cos(hour_angle)
    zenith_angle = math.acos(cos_latitude * cos_hour_angle * math.cos(declination) + math.sin(declination) * sin_latitude)
    dy = -math.sin(hour_angle)
    dx = math.tan(declination) * cos_latitude - sin_latitude * cos_hour_angle
    azimuth = math.atan2(dy, dx)
    if azimuth < 0.0:
        azimuth += 2 * math.pi
    azimuth = azimuth / (math.pi / 180.)
    # Parallax Correction
    parallax = (earth_mean_radius / astronomical_unit) * math.sin(zenith_angle)
    zenith_angle = (zenith_angle + parallax) / (math.pi / 180.)
    # Return azimuth as a clockwise angle from true north
    return azimuth, zenith_angle


def true_noon(longitude, when: datetime) -> datetime:
    b = (360 / 365.25) * (when.timetuple().tm_yday - 81)  # Estimate the Equation of Time (in minutes)
    eot = 9.87 * math.sin(math.radians(2 * b)) - 7.53 * math.cos(math.radians(b)) - 1.5 * math.sin(math.radians(b))
    offset = 4 * longitude + eot   # Calculate the time offset from UTC (in minutes)
    true_noon_utc_minutes = 12 * 60 - offset  # Calculate true noon in UTC (12:00 UTC +/- offset)
    hours = int(true_noon_utc_minutes // 60)
    minutes = int(true_noon_utc_minutes % 60)
    when.replace(hour=hours, minute=minutes)
    return when


def calc_solar_lux(localised_time: datetime, location: GeoLocation, daylight_factor: float) -> int:
    # E. Elvegård and G. Sjöstedt, "The Calculation of Illumination from Sun and Sky," _Illuminating Engineering_, Apr. 1940.
    # [Illuminating Engineering Society, 100 Significant Papers](https://www.ies.org/research/publications/100-significant-papers/)
    latitude, longitude = location.latitude, location.longitude
    azimuth, zenith = calc_solar_azimuth_zenith(true_noon(longitude, localised_time), latitude, longitude)
    solar_altitude = 90 - zenith   # After sunset use
    if solar_altitude < 3:  # 3 degrees is a minimum, the functional limit for the algorithm
        return 0
    al_e8_illumination_unit = 77000  # E8 in Lux
    air_mass = 1.0 / math.cos(math.radians(zenith)) # approximation:  https://en.wikipedia.org/wiki/Air_mass_(solar_energy)
    solar_lux = 1.6 * al_e8_illumination_unit * math.sin(math.radians(solar_altitude)) * 10 ** (-0.1 * air_mass)
    illumination = int(daylight_factor * solar_lux)
    return illumination


# Spherical distance from https://stackoverflow.com/a/21623206/609575
def spherical_kilometers(lat1, lon1, lat2, lon2) -> float:
    p = math.pi / 180
    a = 0.5 - math.cos((lat2 - lat1) * p) / 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * (1 - math.cos((lon2 - lon1) * p)) / 2
    return 12742 * math.asin(math.sqrt(a))


def create_elevation_map(local_now: datetime, latitude: float, longitude: float,
                         callback: Callable[[float, float, datetime], None]
                                   | None = None) -> Dict[SolarElevationKey, SolarElevationData]:
    # Create a minute-by-minute map of today's SolarElevations.
    # For a given dict[SolarElevation], record the first minute it occurs.
    # Calls the callback for every 1 mimute point, not just each integer elevation.
    elevation_time_map = {}
    local_when = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    while local_when.day == local_now.day:
        a, z = calc_solar_azimuth_zenith(local_when, latitude, longitude)
        e = round(90.0 - z)
        key = SolarElevationKey(elevation=round(e), direction=(EASTERN_SKY if a < 180 else WESTERN_SKY))
        if key not in elevation_time_map:
            elevation_time_map[key] = SolarElevationData(azimuth=a, zenith=z, when=local_when)
        if callback:
            callback(a, z, local_when)
        local_when += timedelta(minutes=1)
    return elevation_time_map


def find_locale_specific_file(filename_template: str) -> Path | None:
    locale_name = QLocale.system().name()
    filename = filename_template.format(locale_name)
    for path in LOCALE_TRANSLATIONS_PATHS:
        full_path = path.joinpath(filename)
        log_debug(f"Checking for {locale_name} translation: {full_path}") if log_debug_enabled else None
        if full_path.exists():
            log_info(f"Found {locale_name} translation: {full_path}")
            return full_path
    return None


translator: QTranslator | None = None
ts_translations: Dict[str, str] = {}


def initialise_locale_translations(app: QApplication) -> None:
    # Has to be put somewhere it won't be garbage collected when this function goes out of scope.
    global translator
    translator = QTranslator()
    locale_name = QLocale.system().name()
    ts_path = find_locale_specific_file("{}.ts")
    qm_path = find_locale_specific_file("{}.qm")

    # If there is a .ts XML file in the path newer than the associated .qm binary file, load the messages
    # from the XML into a map and use them directly.  This is useful while developing and possibly useful
    # for users that want to do their own localization.
    if ts_path is not None and (qm_path is None or os.path.getmtime(ts_path) > os.path.getmtime(qm_path)):
        log_info(tr("Using newer .ts file {} translations from {}").format(locale_name, ts_path.as_posix()))
        import xml.etree.ElementTree as XmlElementTree
        global ts_translations
        if context := XmlElementTree.parse(ts_path).find('context'):
            for message in context.findall('message'):
                translation = message.find('translation')
                source = message.find('source')
                if translation is not None and source is not None and translation.text is not None and source.text is not None:
                    ts_translations[source.text] = translation.text
        log_info(tr("Loaded {} translations from {}").format(locale_name, ts_path.as_posix()))
        return
    if qm_path is not None:
        log_info(tr("Loading {} translations from {}").format(locale_name, qm_path.as_posix()))
        if translator.load(qm_path.name, qm_path.parent.as_posix()):
            app.installTranslator(translator)
            log_info(tr("Using {} translations from {}").format(locale_name, qm_path.as_posix()))


def main() -> None:
    # Allow control-c to terminate the program
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)  # Force UTF-8, just in case it isn't

    def signal_handler(x, y) -> None:
        log_info("Signal received", x, y)

    signal.signal(signal.SIGHUP, signal_handler)
    for i in range(PRESET_SIGNAL_MIN, PRESET_SIGNAL_MAX):
        signal.signal(i, signal_handler)

    sys.excepthook = exception_handler

    # This is supposed to set the locale for all categories to the user’s default setting.
    # This can error on some distros when the required language isn't installed, or if LANG
    # is set without also specifying the UTF-8 encoding, so LANG=da_DK might fail,
    # but LANG=da_DK.UTF-8 should work. For our purposes, failure is not important.
    try:
        locale.setlocale(locale.LC_ALL, '')
    except locale.Error:
        log_warning(f"Could not set the default locale - may not be an issue...", trace=True)

    main_config = VduControlsConfig('vdu_controls', main_config=True)
    default_config_path = ConfIni.get_path('vdu_controls')
    log_info("Looking for config file '" + default_config_path.as_posix() + "'")
    if Path.is_file(default_config_path) and os.access(default_config_path, os.R_OK):
        main_config.parse_file(default_config_path)

    if os.environ.get('XDG_SESSION_TYPE') != 'x11':  # If Wayland we can't do smart window placement - use XWayland
        if main_config.is_set(ConfOpt.SMART_WINDOW) and main_config.is_set(ConfOpt.SMART_USES_XWAYLAND):
            log_warning(f"{ConfOpt.SMART_WINDOW.conf_id}: Wayland disallows app window placement. Switching to XWayland.")
            force_xwayland()

    QGuiApplication.setDesktopFileName("vdu_controls")  # Wayland needs this set to find/use the app's desktop icon.
    # Call QApplication before parsing arguments, it will parse and remove Qt session restoration arguments.
    app = QApplication(sys.argv)
    log_info(f"{app.applicationName()=} {QApplication.instance().applicationName()=}")
    global unix_signal_handler
    unix_signal_handler = SignalWakeupHandler(app)

    log_info(f"{APPNAME} {VDU_CONTROLS_VERSION} {sys.argv[0]}  ")
    log_info(f"python-locale: {locale.getlocale()} Qt-locale: {QLocale.system().name()}")
    log_info(f"desktop: {os.environ.get('XDG_CURRENT_DESKTOP', default='unknown')}; "
             f"session-type: {os.environ.get('XDG_SESSION_TYPE', default='unknown')}; "
             f"platform: {QApplication.platformName()}; Qt: {QtCore.qVersion()}")
    log_info(f"app-style: {app.style().objectName()} (detected a {'dark' if is_dark_theme() else 'light'} theme)")

    args = main_config.parse_global_args()
    global log_debug_enabled
    global log_to_syslog
    log_info(f"Logging to {'syslog' if main_config.is_set(ConfOpt.SYSLOG_ENABLED) else 'stdout'}")
    log_to_syslog = main_config.is_set(ConfOpt.SYSLOG_ENABLED)
    log_debug_enabled = main_config.is_set(ConfOpt.DEBUG_ENABLED)
    if args.syslog:
        log_to_syslog = True
    if args.debug:
        main_config.debug_dump()
    if args.create_config_files:
        main_config.write_file(default_config_path)
    if args.install:
        install_as_desktop_application()
        sys.exit()
    if args.uninstall:
        install_as_desktop_application(uninstall=True)
        sys.exit()
    if args.detailed_help:
        print(__doc__)
        sys.exit()

    if main_config.is_set(ConfOpt.TRANSLATIONS_ENABLED):
        initialise_locale_translations(app)

    main_controller = VduAppController(main_config)
    VduAppWindow(main_config, main_controller)  # may need to assign this to a variable to prevent garbage collection?

    if args.about:
        AboutDialog.invoke(main_controller)
    if args.create_config_files:
        main_controller.create_config_files()

    rc = app.exec()
    log_info(f"App exit {rc=} {'EXIT_CODE_FOR_RESTART' if rc == EXIT_CODE_FOR_RESTART else ''}")
    if rc == EXIT_CODE_FOR_RESTART:
        reverse_force_xwayland()
        rc = 0
        log_info(f"Trying to restart - this only works if {app.arguments()[0]} is executable and on your PATH): ", )
        restart_status = QProcess.startDetached(app.arguments()[0], app.arguments()[1:])
        if not restart_status:
            MBox(MIcon.Critical, msg=tr("Restart of {} failed.  Please restart manually.").format(app.arguments()[0]),
                 info=tr("This is probably because {} is not executable or is not on your PATH.").format(app.arguments()[0]),
                 buttons=MBtn.Close).exec()
    sys.exit(rc)


# A fallback in case the hard coded splash screen PNG doesn't exist (which probably means KDE is not installed).
# Based on video-display.png from oxygen5-icon-theme-5: LGPL-3.0-only.
# Convert vdu_controls.png -depth 8 -colors 24 smallest.png; exiftool -all= smallest.png; base64 -w 120 smallest.png
FALLBACK_SPLASH_PNG_BASE64 = b"""
iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAMAAABrrFhUAAAAIGNIUk0AAHomAACAhAAA+gAAAIDoAAB1MAAA6mAAADqYAAAXcJy6UTwAAABLUExURQICAjE0
O76+wGttcSgrLgcICHd9gxscIRARFS1on2GKoUSS2Fes2UN60WGy4VKs5zd0y0Wc4zuK1j+V4ZOYnayvs7y/ws7R1P///6WsmEMAAAAHdFJOUwFgeb76L/4C
wkTRAAAAAWJLR0QYm2mFHgAAESFJREFUeNrtnYtaqzoQhbdCoR4qAYT6/m96yH1yg0wIBZX5zi7YVmX9s2YSAvX8+3fFFVdcccUVV1xxxRVXXHHFFVdccQWL
NzPe39198Nw7eO3d/j7P+9m36Pe+vxXvxksZfr753nkHJ7+o70nBv62eQ27nKPljUqgfA35ubf18EPpF/QzfL4sbQn9p6InQXQcAlCvCi6rijyyKQu7JqB0h
AmYditLznpLtl/EEirT0Qx/oA14EQEXOAJjywtVfSr4SAfw6AKD0wOBRRBsA63/7/fPBAhcG1X9UZTVnn+lnACo7DMFxAGoTAGQQbYG3jQawDnTNAUUQQKkL
CiCo73V9X1YeiNhGyAF8/KZIAvBfQ+PBgm+bpHionxIT4L1pv84Tnx+8NyABII46Idr20S6+mjGaDz4SnAyAKbK1XsuJoEkrgf0AtB4A8JnM+tEAit0BuPJY
QbQgcv6+cwBo9Y4n12z7iwEYOsGjEttakZX9CQCIvm4obJfitwGQ6QcQ1Au76z8UgBbDhbUQwIsMgAbwngsA16s6gCPS6Xz76D9sHiCEhBL+OgCPoxwgOSxa
fW/9hDwe3XEAFnv+ww8gr3wBoDxqFAAyvVoRBiA6pXqjng7JpwQ63NlgLgBi7BMcAjWwpp8QYu7YW03Cr14AqA8CYMx540ILcPJLDOXiCc/75G8U+o/pAcD4
Kfq9eRVStWL6LkLc9xMpPglAth4ANaENIDBwiVIk20LB4mtiOICYcdAw2EZO+sL61fFL4QS43+yE4BWde10CrwZgZx1TAlKQqm+gXttdCQew+LYlTrx+KmyJ
xnYAnnM93GkXGDBUMbB/2iMuAOoAzDxgewmYqjEAtM1l3RtNThNw+oPS3zomaJCrwpsA4CreMQABSbYmACYAqz+Esq8AYOYBAsB/6QBSCViDmwEBdH0g+bEu
XwDAl0AKAGzLcwvAEKZyTIw9Z+QnZA8ACSWQrFwWgM42HweA+IcpXTZF+lvJbwFgulnvc+8bAPSbVuW/EgB22uspACgdFIGSD7s+sMgygA53aSwZQNs+NgIw
6914NPtATOlbAHZtgvqcV5yGJepXptc+eLhIFqc9gRLYFUArT/rVLGArACDa84zRBdYDfXU4qQT0+E8eKfJbmOOHzrSp/mFVQrwDdm+Cuv5Jkv5WlTmBkwEt
3rXDWQAEFzex+g29louZ6dPk8ya4K4Bt838WZltzlGr3vxBAbBNsVe+jTkguAKDWUY9p+W70e58LtGr9l+nYov8BxIb9cDYAwAkkaQCUZ0H+TG/ofq8GkBxL
Lt9mf6p/LwB6WU5m0RSFBLDR52sOyD8TVGfjcggwAWB6wX7aeew3FSZqECRW+Sv9ERx2yjt76MlePYCoEaAVgx/MOWos2EU8ky6+2heAvginq58cWgC98UW/
UxMkcujTF+J09o8D0Pe988QeAAh0AfFVezSB7AZwkewG4CFGL6Tk3fX32gf9BgALJ0NET1pbd/wjiALYPftgInTPBgBco5VVb2naAOCRb07Ui0gEEFECrmCC
KwbfYW8B0AvRhn4K4J4XgFyWcwAgzwW9ItL1M+m9RNDvBYBfjWEzYCKuxUa4335BdI+coaY/vRXNx/2ecHn8v5B+ImcARKowEiprwZwZOmTIHjMA7n4XQNZR
QAFQ+k0A3BYy58R4l3qZtDkNwKwvc+8SyA1A9j/TAEpfa3CRguGWyPdlk98D7+/qAPpbOAPtfJhiRQMmXL1P2l5+lTOYB3pvNBzAPcM8AKxbAQBAJ2BiA1DO
yGj+Xpqe9/8wgHu2iRAxpz9atdCsDUCg/VtrhpjP+8RrekM+c8A9DwA+BPp7O7cFyLwn22o4zAbAKP+A/uGDf+x6IwAx/j+0XD26G1tzYmyohR1jm3JdBWED
NA0HICZCG5vg/Mvk8p+cAAHhqhmoKg8nejMAUfFs5FsC0MtPT+cAQKz5j1ICRgD5z2d9v2h7+SJKumF+OP0NyFcA3rc5ALKAw55WyRqAfyqfRX4IwIr8LA7Q
i+CtNLpvouPX33qlYMVr4QCBH0BjyJ+bIP+LHlsBtHwZ3JBmA0AoQYv3OGA19xIA+7suG0cBfiOnOAmE+o0RIL9+rQx6B0OAOQA1D6i9w6Bzp67m4BnxVkRh
9EPrr6U/6ID0iZC+S9d/hHpWiBAV+0aQ7wjts1hXPgeQYxgM6Neb6Pwj5PNGJ32ALH4RHRqAUwLsePa8gutlJM/y5RNo72sAqHnAW20CUHdpvgiArHf+AJ5b
kN77zW8CQDhgDgBA36G5zCAPINXwevOZZQBLBLoP/gepEJ8ehwCgtL31g0VdCWBdfKNOehYAoD8+rwDEl34agN4Y3/UlrVX1zXLhZwMQXfrJBuitfySi5Ymc
900MAWwJvLMFNAqAbL9Jz5tzF4D5ah/V9ZqY7CsAmHMBtoAGAOQ0QO9ewNcQIsf7OOM7AOJnghBAbOBd0usup9hEzfewBD67jxq3JLY3gF4u40gSxoQ3Rn4s
gM/PJADsj2TyJphdv1Db973ZC+JkC+m4EmAAcLfJKQds6uzBl+TcPnqoB+IRuf+Ue/iZ4B0LwK7moPd5j+/NcT6WQHzOqWwajSqBNACxsyAtR6a4B187Nlfv
iE9976xzrVT+p4g0ANgm6BvYVU939Men3GVgLfYFG5/Y49Ehb5F5Y4PmDCBaf6/X5w2lxAdAlQIWgzfbgyMfVr8EkHhtMFq/OZABjwf0o80v9X99NV9sMwxU
+jC44g3zawApi6JNnP6H9LT2vSf9KwvZy4lnD7P2Oaj6Wb4IX/bdkDNBxIURdTocWQDGdI54Jrxovxvp57lnELhqW/6npxAgAPxEiAGILwCwigMKIov+pufS
efobKVzqHzQAVfmN44CEGyRmAFFrt72SrCP8PrT5pW62Y/qeO0H3QbMD2A5IaYJRi7ce/dbt6qn6mWhe9wzDl1n4cjPIgW8FAOrSGJ8HxDig8Ry5hScNgMj8
l6ld2l8yGIZunue4Ve9zAKYEOACTQLSxVeZ7DQBtfd3xDf0879z3fLfr4ICXGYCpug/rJy4Cwwr4zDfSAVQ2IyBSL33AYAx81k/73yoA1CgAS6C3TnTgENcE
VJjX8qIBfHlCGX8wB0D2OGtbzn3qKMCvC3gUmwOcV7+pOF7/LHY2v1e+yrveNF3X0R3Z9haLAHtlSAEwRng144nIK3LaS6X2wez7gtZ+180lEOsA5M3SEAAx
5vmAQt8sqhJ3MS0D+FLG7y3pi/rnmOXPaaePXRSAhEtjAwCgbkciam9Nf9QK35cmYGV+WT4D0FAAn3QY6LpuBwCNMr8+dQWOaNYA8O9cNj7W+lJ8x/R/Mukg
Am7o0DdIKAf06kQP6OL5bxbVS6+QJfGBiNI/98BB6mezwSbsgmQHwGauAfCdFQNodmbBh8XH+H4WLwmIiRCfFXZwHdAPALceIEsA3o1rqYrQj0j9qnChG8wC
5KkAy/vCiYAEgJkH1LoEiHOeF5N/ghGPYaCGwXkc1AhkQ2BiQxMh7MmQBOAUN9ePNcCicKR6NhWaRXecAOuIqzPBhBIYgmqk/iayErIl3umE3PdiJATJ7ywA
/H9ShpwJLgEwt4vi8+vvlH6RewYAqLbHg9wAuO4mpg6WpScBEONAoylA0dwMnx4A+HOBYVX/KoCw+shRz2d9ioABaIB+oZo9On1Q3iCRB0CjL1DCfhANIKXp
GbnvOo5BzP04AqlfGaDLAKAJ6FcBQUTp50JSW5+QrsRbIU8JZC2o/Q7dA+qwAxzxCwDck/stfV9Ng4bB0v3ZuaWvKgMAQFwYCQLwXp5TAJoF/SL1m4Y9Zn1b
v6r9DpTBZwdLIx+ARfk2AZD41Kq3AMgScMwPuoGnLWZ0wHL6LQPwYt8qncv2V72UDaVLAHqbDsCp7WEIp9/uBQ3Iu8kARURUfjj7Lg1ZAHpHXhvcCMC5Gm1I
Zl81wCWDf7iLdcRK5j0eWAj0xVEBwEypAMBW7dlVK2MgtNGEhMWXhM795kA64M0HQF6RnYUPors1C/dsbSx8Od7n0S8XRJAl0DVymsfcPciLM1Q5TWWzFFvU
d0J8rvyrJhh/jxD93zFQACr7vXFlhpmgkTct5NPf5c99MoByBvAFP4jCD5Fv9KXLgP7EoY9Jz1n7GwEMvLO7CeVX7A0Asil8sdrYYH4+8mWVnwKANcFBKnMA
gER/KYcoUmj9XDhoALmDf2IkGYB9vOq8RrhBlQh8xAKIHPWPABA6bO8ruA7YDdYC1076UwEsn726ryCHgM5/fnciAKjQN65F217bf38ACU2wi1MCCWDc370i
968EgMy8KIDf5ABc5l+T+0QA9Q4A4Hn9i5y/AUCZFYCy+msrfxMAOhXORABIfr30QwC4B3CQ7g0AWA+YCYRicHaiDsPYfuiv6d6HDrhvhfqGD/tnf7j74P3I
iRADUH78okgBEAj+SXwepR3380aNuEHCBXD379v666NVriDI4oCF/JfMIPLXnZDG3gBEidxFmRwt9zAAoF2Eoqjm777TplGX94puKvpltXMT2RmA2yRDB1KN
1VRPxXif7tW8X033iW2K6SwAlBwEAP4H22Lyf6/q+3gvZ7VVOc5797Ge5VdFSffPAaBeA1C6BhCFDwGEIIzVnPtpfiynGUBZPmua+oo++2MAuA1A6L/LQlg4
kHqkGZ8Tf5/m0h/HuRLGsah+kAPKIABZAxLA8lhQzYrLufz31Z0CQBk92gDa+fLxzmksHRHr+i+bQNa3SAD/VjtgHID1bvjaKGP1/7vhO4DR+2pr8nyOKKMN
4CHAf4QxyEMSUQX/g/RTBG97RaECPFd5nswbOPl7RqVCN+U3/eTRh7d/jCoAAP3k0Ye3f0wqAAD+xJ8HQOPow7sA7A/g+ZyeE/0PAHiy+DMAngzAUw95BXuG
ETj68F4EwIpvtfdHATwvAH8JwHIcfXgXgAvABeACsG/ohs+CbcEwcPTh7R6376V4fp9n4WKnePPq1hG7dP1j412m2tT9dwAUft2qKxRHH+DeMTqSzfgTAJaG
wV+/JjYuyv8DAFbmQReA3z4VfFsF8ItnQrf3cVU+q4Li50G4FePzeyVC3Y9eDpGP0wjOEH4QpLdV9d9r0tW1MfmiZ57EF9RlnGnOOCHlU51jKCYvglOPF2+r
+pWscT0mi8AUKofzWGDVAJY8ezsp2SaK72kxxrO0gWK1AXgTbe5NnqpYAXCW84bbqgH8BFbje3UoOIcF1g0wJRH4XjTAeBoL3NaHwOdI/+HiuaxflMsZLFA8
+erO8ihA3xQzBKhOSU0T1K3iBBa4geF6gUBVTXJAXBdPDT5W7vDneffxFiisC93MDeALsfOcEYxgVhRSzl+o5jdr/WPgG05hgZv/Yi8Vbq39ieGe6gd63eTS
e+Xoq8/FzJ/GAsUTFxNXWFky2AdHKvUK6PVrFXOwBW7ThFDP64OntHLCqoXYlnnshDhw5hJa9ObdIOBsOTem/8UPGMdawFnfeTrncCuLwJNJID7xqnQOtUDc
Cg8uUPJpHGiB9QU+nPJY/VbzOM4COQ0QmfPR0z4Ps0BGA4wRbY8PFJUnjrJAFgNgK94XB1mA3eQ/pVLYLvtwCxjHOU3jGCcYPdBFxCEWKFaOnE9o5NwGHxX9
L0r+QRZIEZU58cdaAGllv8oUsb444hrB5L/XRSyCra+TouPJfqrvHGM+xX69/ttoHswOildIyN9P9w5YFri9jcaJzwsBMATGest0wOcib/SzpfSj3wcE/wsX
8lO77HOhRwC47ffxWuzHYm8HAGAEKIRDMdxkvF6/InCOOALAmQgcov9EBA7SfxICh6mXEDQJvmd+zZ645X9d7V5xxRVXXHHFFVdcccUVV1xxBTr+By2wdkDA
7ktNAAAAAElFTkSuQmCC
"""

if __name__ == '__main__':
    main()
