<!-- 
SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
SPDX-License-Identifier: GPL-3.0-or-later
-->
# Changelog

## Unreleased <small>(master)</small>

- The Light-Metering-Dialog includes two profile starter-templates.
      One for older monitors and one for newer monitors.
- Tick marks on control-sliders are now optional, see Settings-Dialog -> tick-marks.
- vdu_controls now defaults to a _single-instance_ mode. Subsequent launches 
      focus the existing window. Uncheck the _single-instance_ option to override. 
      Contributed by Mohammed Elsayed Ahmed.
- An Online-Help button has been added to the Help-Dialog and About-Dialog.
- When parsing monitor metadata, if the same VCP-feature-code is 
    defined multiple times, the first definition is kept and any following 
    definitions are logged (rather than silently overwriting the first). 
    This allows some monitors with incorrect metadata to work out-of-the-box.
    Contributed by Mohammed Elsayed Ahmed.
- When parsing monitor metadata, well known "Continuous" VCP-feature 
    definitions, such as brightness, will always be regarded as "Continuous".
    Any attached 'Value:' metadata that implies otherwise will be ignored
    (with a warning logged).  Contributed by Mohammed Elsayed Ahmed.
    This allows some monitors with incorrect metadata to work out-of-the-box.
- A cascade-guard has been added to protect NVRAM from cascading writes  
    due to application, driver, or hardware bugs (or _cats on keyboards_).
    If the application or user sets a VDU feature more than 20 times in 65
    seconds, an error-popup blocks further attempts until dismissed.

- The required minimum python3 version has risen from 3.8 to 3.9.
- The ambient-light-level slider works even if location is not set.
- The ambient-light-level slider behaves better when dragged after sunset 
    and when dragged beyond the estimated solar lux level.
- The laptop-panel option now defaults to enabled.
- The Settings-Dialog global-options have been grouped under subheadings.
- The Settings-Dialog offers more popup-guidance on dependencies 
    between options.
- The layout of the Preset and Light-Metering dialogs better reflect
    the new style of the main panel.
- The system-tray icon is now primarily monochrome.
- The program-icon and splash-screen icons have been redesigned and 
    reimplemented as scalable vector graphics. The new program-icon is theme aware.
- The protect NVRAM option has been made mandatory.
- The weather related Preset settings are only visible when the weather option 
    is enabled.
- The script's source code has been refactored into multiple source files.
- The executable is now a Python _zipapp_ containing the source hierarchy.
- The included set of language-translations has been expanded. All of 
    the translations have been generated for testing purposes and may not 
    be accurate.  Layouts now correctly handle right-to-left langauages.

- The right-mouse action that could irretrievably hide the toolbar has been
    disabled.
- Numerous minor fixes.

## Version 2.6.0 <small>(2026-04-20)</small>
- Added laptop-panel support, see Setting option "laptop-panel-enabled".
    Requires the commonly available "brightnessctr" command to be installed.
- Udev is used to detect laptop brightness events, such as up/down function-keys and inactivity-dimming.
- The control-panel's icons/titles are now shortcuts to the relevant Settings tabs.  
- Fixed _Settings_ text-input line-height on small screens.
- Cosmetic fixes to icons and spacing in the main panel layout.
  
## Version 2.5.0 <small>(2026-04-07)</small>
- Visual refresh of the Main-panel. Inspired by [a recent fork](https://github.com/ViktorSharga/vdu_controls_vibecodedUI) 
    by @ViktorSharga.
- Added option "toolbar-at-top" to configure the top/bottom placement of the toolbar 
    in the main-window. Top placement is more Plasma-6-like and may also be useful
    when combined with top-located system-trays 
- Added option "separate-status-bar" to allow the main-window's status-bar to be 
    separated from its toolbar.  This may be useful when combined with "toolbar-at-top".
- Replaced QProgressBar with a more modern circular busy-spinner.
- Added a tooltip to the status-bar that shows the last 10 status messages.
- The main-menu now includes a Control-Panel menu-item on all desktops - previously it 
    was Gnome-only (for tray extensions), but Xfce's tray also needs it.
- Light-Metering window - corrected the horizontal tick mark placement on the sun-plot.
- Light-Metering window - added enlarged tick-marks to the sun-plot at 3,6,9,15,18,21 hours.
- Added option "tray-follows-theme" (default enabled) to invert the tray icon’s light/dark state
    when the desktop theme changes. It can be set for trays that flip-with the desktop or 
    flip-opposite to the desktop, or unset for trays don’t change at all (there isn't a 
    common way to detect tray-themes, so this cannot be automated).
- Internal code simplifications and cleanups.
  
## Version 2.4.3 <small>(2025-08-29)</small>
- Fix a rare TypeError when light metering.
- Some code cleanups for the splash screen.

## Version 2.4.2 <small>(2025-07-29)</small>
- Fix the Lux-Dialog's display of the Daylight-Factor for non semi-automatic metering.
- Make sure the tray-icon always shows the correct lux-level icon.
- Correct the lux-zone boundaries on the ambient slider.

## Version 2.4.1 <small>(2025-07-14)</small>
- Support PyQt6 before PyQt5 goes out of support.
- PyQt6 is used by default, with a fallback to PyQt5 should it not be available.
- Add the prefer-qt6 option to the Settings-Dialog, disable this option to force the use of PyQt5.
- Various changes to UI layouts to accommodate both Qt5 and Qt6 (including Qt6 High-DPI scaling).
- Minor alterations to the main-window layout to make the more spacious Qt6 styling more compact.
- Renamed the smart-uses-xcb option to smart-uses-xwayland.  This better reflects what the option does.
- Fixed smart-window preservation when the app was closed from the tray without ever showing the main window. 
- Fixed weather selection: automatically restore any missing weather definition files.
- Fixed initialization-preset error handling: fix a reference to an undefined variable.
- Only persist lux_daylight_factor if in semi-auto mode (stop hardware light metering overwriting the user's choice).
- Allow Presets to be scheduled for a set time each day.
- The DBus-events default setting has been corrected to true/enabled.
- Dragging the Preset-Dialog elevation to below the horizon now works properly (previously it was jerky).

## Version 2.4.0 <small>(2025-06-12)</small>
- Added the ability to estimate the solar-illumination for a given geolocation and time. 
- Added semi-automatic brightness adjustment proportional to geolocated solar-illumination.
- Ambient-light-level slider: when the slider is manually adjusted, it has the side-effect
    of determining the ratio of indoor-illumination/solar-illumination (the daylight-factor, DF).
- Light-Metering dialog: semi-automatic metering replaces manual metering.
- Light-Metering dialog: added a display of estimated outdoor-lux (Eo) and the current daylight-factor (DF).
- Light-Metering dialog: added a plot of the current day's estimated solar and indoor illumination.
- Light-Metering dialog: replaced the profile-selector combo-box with a list for easier accessibility.
- Light-Metering dialog: added the ability to dynamically adjust for display DPI.
- Presets-Dialog: added an option to save/restore the daylight-factor. This can be
    used to save daylight factors for various conditions, or to activate them at a solar-elevation.
- Settings-Dialog: disabling protect-nvam now works properly for adjustments due to light-metering.
- Duplicate Lux-profile points are filtered out to prevent confusing the UI and lux evaluation process.
- DBus ddcutil-service: altered the detection parameters to request only valid displays (prevents errors).
- Ambient-light brightness adjustment: prevent an infinite-loop if no brightness controls are enabled.
- Preset-restoration and ambient-light brightness-adjustment now share the same code for
    background operations.
- Model-only config files are no longer created, they're confusing and likely not used (they
    can still be created manually with a text editor).

## Version 2.3.0 <small>(2025-04-30)</small>
- Fix the doze function, this improves the responsiveness of all slider controls.
- Fix an infinite loop if menu->quit is used when the "Failed to obtain capabilities" dialog is showing.
- The Settings-Dialog has been reorganized to make it scrollable.
- When lux options are enabled, the tray will show the icon for current light-level (if no preset is active). 
- Renamed two light-light levels more appropriately (room becomes subdued, rise-set becomes twilight).
- Support a user-defined ddcutil-emulator executable for controlling laptop-panels 
    or other non-DDC-capable displays. A template sample emulator written in bash is included 
    as a DIY starter (sample-scripts/laptop-ddcutil-emulator.bash).
- Add smart-uses-xcb option to control the use of XWayland for the smart positioning of windows (defaults to yes).
- Fix title-bars on sub-windows in COSMIC. 
- The About-Dialog now includes some desktop and platform information.
  
## Version 2.2.0 <small>(2025-03-20)</small>
- Add a vdu-name option for assigning meaningful/user-friendly names to each VDU.
- Implement an order-by-name option that orders lists and tabs by VDU name.
- Hovering over a settings-dialog tab-name or save-button reveals the settings-filename as a tooltip. 
- If smart-window is enabled in a Wayland desktop, automatically use XWayland. (Wayland
    doesn't allow an application to precisely place it's own windows!)
- Altering the smart-window option now requires a restart (due to the Wayland/XWayland changes).
- The smart-window option save/restore of main-window has been made more consistent.
- The COSMIC desktop is treated as GNOME-like (the system-tray right-mouse menu includes a "control-panel" menu-item).  

## Version 2.1.4 <small>(2025-03-09)</small>
- Provide a setting for enabling dbus-events - ddcutil-service DPMS and hotplug detection. 
- Default the dbus-event setting to off, which is less troublesome for some VDUs/GPUs/drivers.

## Version 2.1.3 <small>(2025-02-19)</small>
- Fix the error-dialog option "Ignore-VDU" when ddcutil cannot communicate with a VDU.  
- Avoid abrupt U-turns in automatic brightness, don't reassess the lux level while making an adjustment.
- Update the EDID-parser to accept the command line output from ddcutil 2.2 (for those not using ddcutil-service).

## Version 2.1.2 <small>(2024-11-27)</small>
- Replace the Preset-scheduler with an implementation that remains accurate after PC-sleep/hibernation.
- Fix the day-rollover which was scheduling for the wrong day if triggered at 12:59:59. 
- When performing a set-vcp, don't increment the NVRAM write count if the VDU doesn't respond.
- When reconfiguring VDU controllers, discard pending VDU VCP changes from previous controllers. 
- Eliminate a potential for deadlock when handling change-events from ddcutil-service.
- Better handle ddcutil-service unexpected event types (don't raise an error dialog).
- The main window height will now automatically resize to accommodate the number of controls present.
- Toggling lux brightness-interpolation now immediately updates the profile-plot to reflect the change.
- Fix the Lux Dialog, it was turning off interpolation when first constructed.
  
## Version 2.1.1 <small>(2024-10-15)</small>
- Removed --dbus-signals-enabled. DBus signals are now always enabled when --dbus-client
    is enabled.
- Fix the active Preset icon display which was sometimes incorrect after DPMS-sleep or errors. 
- Fix a code regression when handling non-DDC-capable VDUs (fix status=-3020 exception).
- The About-Dialog now includes counts of per-VDU set_vcp/NVRAM-writes.
- Hovering over a VDU-name in the main-window reveals the write count for that VDU.
- Minor changes to reduce unnecessary work and improve log messages.

## Version 2.1.0 <small>(2024-09-28)</small>
- Preset _transitions_ have been deprecated.  All presets are now restored instantly no 
    matter how they have been set to transition.  The Preset-Dialog controls for assigning
    transitions have been hidden.   __All  transition related code may be removed in a future 
    version, please contact me or comment on issue #93 if you prefer transitions to be retained.__
- Transitions and related controls can be re-enabled by disabling `protect-nvram` in the _Settings-Dialog_. 
- To avoid unnecessary updates, preset restoration now queries the VDU's existing
    values. This may slow down preset restoration.
- Lux-metered auto adjustment has been defaulted to 10 minute intervals (up from 5).
- Color-Preset (VCP code 0x14) has been added to the list of standard controls.
- Added a VDU  ___Initializer-Preset___ feature to provide a replacement for dead NVRAM.
    This also provides a way to restore settings not persisted in VDU NVRAM.  A VDU's initializer-preset is 
    automatically run if the target VDU is present at startup or is subsequently detected.
    Any preset that has a name that matches a VDU model and serial-number will be treated
    as an Initializer-Preset. 
- The ___Preset-Dialog___ now includes a tool-button  to the right of the preset-name entry 
    that will create a VDU specific ___Initializer-Preset___.
  
## Version 2.0.4 <small>(2024-07-02)</small>
- The About-Dialog now refreshes the ddcutil version info on each invocation. 
- Increased dbus timeout to 10 seconds (in case numerous VDUs or errors slow down VDU detection).
- Dynamically enable a scroll-area when the main-panel exceeds the available screen height.
  
## Version 2.0.3 <small>(2024-05-08)</small>
- Reduce the number of writes to VDU NVRAM by sliders, spinners, and ambient brightness adjustments.
- Slider and spin-box controls now only update the VDU when adjustments become slow or stop (when 
      the control value remains constant for 0.5 seconds).
- Spin-Boxes now select the entire text on focus in (enables easier overtyping and decreases VDU updates).
- Ambient lighting initiated changes in brightness of up to 20% are applied without any transitional 
      steps (plus the existing code ignores updates of less than 10%). 
- Set the default ambient-light brightness adjustment-interval to 5 minutes.
- React to DPMS awake signal from ddcutil-service by re-assessing ambient brightness.
- Simplified locking and conformed to a locking hierarchy/protocol to avoid potential deadlocks.

## Version 2.0.2 <small>(2024-04-13)</small>
- Added a *refresh* annotation suffix for use with VCP-codes which cause multiple changes.
- Make manual adjustment of the ambient Light Level more accurate and responsive.
- Updates are sent to the VDU as sliders are dragged (rather than only on release).
- Fix exception on monitors that return invalid/unexpected combo-box VCP values.
- Fix exception on monitors with blank VCP value descriptions.
- When refresh is pressed, only auto adjust ambient brightness if auto-brightness is enabled.
- Don't automatically refresh on error, eliminate popup dialog loops.
- Eliminate deadlocks when exceptions occur.
- Cleanup the initialisation of the ddcutil-service connection.
- Add more caveats and limitations to the documentation.
- Fix manual ambient light slider when light meter is uninitialized.
- Promote Simple-Non-Continuous values whose metadata exceeds one-byte to two-byte Complex-NC.
  
## Version 2.0.1 <small>(2024-02-28)</small>
- Fix D-Bus client code for python versions prior to 3.11.
- Fix infinite-loop when altering an existing FIFO lux-meter in the Lux-Dialog.
- Fix the refresh of the Lux-Dialog meter-readout/plot when changing to a new meter.
- Apply context-aware defaults to the Lux-Dialog device file-chooser. 
- Improve/fix the handling of displays/laptop-displays that may be detected but lack proper DDC.
- Force the file-picker to always show devices and FIFOs - it wasn't showing then on some desktops.

## Version 2.0.0 <small>(2024-02-17)</small>
- Added an optional D-Bus interface to ddcutil for up to 10x faster response times.
- Added an immediate-lighting-check button and corresponding main-menu item (when lux-metering is enabled).
- Added an ambient-light-control for manual lux input, one slider to adjust brightness on all displays.
- Added more preset icons.

## Version 1.20.0 <small>(2023-10-25)</small>
- Added options monochrome-tray and mono-light-tray to enable a monochrome tray-icon (dark and light).
- Optional $HOME/.config/vdu_controls/tray_icon.svg overrides the normal tray icon.
- Improved the adjustment of icon/window dimensions by scaling them in respect to the user's default-font height.
- Remove adjust-for-dpi in favour of the above which automatically accounts for DPI.
- When a Preset is transitioning slowly (i.e. not immediately), the UI controls can be used to stop the transition.
- Considerable internal refactoring of option handling.

## Version 1.12.0 <small>(2023-10-17)</small>
- Added an F10_key context menu shortcut to all application windows (KDE accessibility standard).
- Set icon and pixmap sizes appropriately for Normal and High DPI (controlled by adjust-for-dpi) (issue #63).
- Icon/device-chooser-dialog: init-time reduced from 30 to 5 seconds for users with large home folders (issue #61).
- Improvements/Fixes to the vlux_meter.py sample-script and the related vdu_controls FIFO reader.
- Improved visibility of the app-icon's preset-transitioning indicator and auto-lux indicator.
- Increased contrast for generated text preset-abbreviation icons.
- Encode translations in plain text rather than escaped XML (for easier editing).

## Version 1.11.1 <small>(2023-09-21)</small>
- Fix Preset text size in tray icon.
- Fix occasional concurrency lockup issue in lux_metering.
- Update the Settings-Dialog when a new VDU becomes available.
- Light-metering: show both a lux-auto indicator (an orange "LED") AND the current preset (if any) in the app icon.
- Fix first time use crash (issue #60).
- Allow % in config files by turning off ConfigParser interpolation (issue #60).
## Version 1.11.0 <small>(2023-09-09)</small>
- Made vdu_controls ddcutil-2.0-ready.
- Added support for ddcutil versions earlier than 1.3 (issue #43, #53).
- Main-Window: added a hide-on-focus-out option to minimize the main window on focus out (issue #57).
- Main-Window: changed the layout to display brightness and contrast as the first two controls for each VDU.
- Main-Window: added jump to clicked value to sliders (issue #59).
- Main-Window: added a smart-main-window option to make main window placement and geometry preservation optional.
- Main-Window: the main window can now be raised above the other sub-windows (gnome issue only).
- Main-Window and Context Menu: added alt-key keyboard shortcuts (issue #13).
- main-menu: added an indicator mark suffix to the currently active Preset (if any) (issue #55).
- main-menu: made changes to Preset ordering propagate to the menu without requiring an application restart.
- Tray-Icon: made the app icon un-themed so that overlaid active Preset text/icon is more visible (issue #55).
- Settings-Dialog: added a Reset button to makes it possible to un-ignore a VDU (issue #51).
- Settings-Dialog: added tool-tips to main config-settings, made them consistent with command line help (issue #52).
- Presets-Dialog: combined the Activate and Edit buttons into one button (simpler and more intuitive).
- Presets-Dialog: made the dialog bold the text button of the currently active Preset (if any).
- Presets-Dialog: added code to detect and and warn of unsaved changes.
- Presets-Dialog: made the dialog lock out any scheduled or automatic VDU changes while a Preset is being edited.
- Preset-Dialog: supplied a starter set of Prest icons - a selection of KDE breeze5-icons (issue #56).
- Popup-Messages: made message box popups resizable for increased readability.
- Command-line: made config-settings and command-line arguments consistent, command line has precedence (issue #52).
- Command-line: fixed --sleep-multiplier so that it is actually applied (issue #54).
- Prevented potential crashes in the event of utf-8 decoding errors for EDIDs and capabilities (issue #49).
- Added logging of stack traces for some errors if debugging is set to on (issue #49).
- Improved the handling of ddcutil not found (issue #48).
- Refactored to improve maintainability and run-time efficiency (issue #52).
- Added Deepin 23 pyqt library compatibility.
- Numerous minor enhancements and fixes.
- An alpha release of vlux_meter.py, a system-tray webcam lux-meter, has been included in the sample scripts folder.
## Version 1.10.2 <small>(2023-05-26)</small>
- Fix Preset non-zero transition-step-seconds, so it works properly.
- Changing log-to-syslog or log-debug-enabled no longer requires a restart.
- Fix Lux Auto menu icon when starting with Auto disabled.
- Use the progress bar area on the main panel for status messages.
- Make auto brightness behave more predictably by removing unnecessary constraints on interpolation.
- Improve auto-lux/preset tray icon interaction - better reflect actions and current state.
## Version 1.10.1 <small>(2023-05-10)</small>
- Restore lux meter displayed-value when restoring LuxDialog window.
- Minor fixes to reduce and improve displayed and logged messages.
- Rollup release prior to downtime for ToTK
## Version 1.10.0 <small>(2023-05-04)</small>
- Added hardware lux metering options (GY30/BH1750+Arduino, UNIX-fifo, or executable-script).
- Added lux-to-brightness profiles per VDU.
- Added sample scripts for using a webcam to produce approximate lux values.
- Added an option to transition smoothly on UNIX signal.
- Replaced the transition combo-box with a button+checkboxes.
- Added drag-to-change, click-to-delete, to the elevation chart component.
- Added a setting to quickly disable weather and another for elevation-scheduling.
- Cleanup of thread handling - clarification of GUI/non-GUI thread operations.
- Reduced logging and eliminated popup dialogs when monitors are suspended or powered off.
## Version 1.9.2 <small>(2023-02-24)</small>
- Optional _Smooth Transitions_ for presets:
- The Presets Dialog now includes an option to set a Preset to _Transition Smoothly_.
- The tray, main panel, and Presets-Dialog indicate when a smooth transition is in progress.
- Transitions are performed by a non-GUI thread, the GUI remains accessible during smooth transitions.
- A smooth transition can be interrupted by moving the controls being transitioned or invoking a preset.
## Version 1.9.1 <small>(2023-02-04)</small>
- The text input to right of slider controls has been replaced with a SpinBox with up/down arrows.
- The main panel progress-bar spinner will now also display during preset-activation (in addition to displaying during refresh).
- Refresh and preset controls now lock during refresh and preset-activation (to prevent conflicting actions).
- The context menu and hamburger menu are now available during refresh (a subset of actions is available, such as help and about).
- The VDU `EDID` 128/256 byte identifier is now used internally to ensure the controls operate on the correct monitor.
- Build changes for submission to _OpenSUSE_  _Development_ and _Factory_ by @malcolmlewis.
- The thread handling and error handling has been cleaned up.
## Version 1.9.0 <small>(2023-01-23)</small>
- Bug fixes and speedy performance improvements:
- Speed up initialization and refresh by combining multiple ddcutil `getvcp` requests.
- Stop executing a `getvcp` precheck before each `setvcp`. 
- Fix repeat-initialisation bug in _main-menu Refresh_.
- Fix _Settings-Dialog_ text field validation, some errors were invisibly ignored.
- Fix _Settings-Dialog_ _Settings Enable VCP Codes_, they had stopped working.
- Fix the monitor specific sleep multipliers, they were not always being used.
- Treat all monitor detection situations as needing time to stabilise (helps in disconnect situations).
- Fix event handling so that tablet+pen input works on the main window.
- Default to a sleep-multiplier of 1.0 to support a wider range of monitors out of the box.
- V1.9.0 drops support for converting from v1.6.* config and preset files. To convert 
    from v1.6.* and earlier versions, follow these steps to download and run v1.8.3:
    ```
     % wget https://github.com/digitaltrails/vdu_controls/blob/v1.8.3/vdu_controls.py
     % python3 vdu_controls.py
    ```
    Alternatively, start fresh by moving or removing the old configs from `$HOME/.config/vdu_controls`.
## Version 1.8.3 <small>(2022-12-21)</small>
- Fix for a crash when the network is down and the weather site cannot be contacted. 
## Version 1.8.2 <small>(2022-11-27)</small>
- Solar elevation weather requirements.
- Locale language support and sample AI generated translations.
## Version 1.8.0 <small>(2022-11-06)</small>
- Presets can be scheduled to activate according to solar elevation at a given latitude and longitude.
## Version 1.7.2 <small>(2022-10-07)</small>
- Better handle monitors being powered off: on set-value errors, check what's connected. 
- The display ordering of presets can now be manually altered in the Presets dialog.
- Do not exit if no controllable monitor is found.
## Version 1.7.1 <small>(2022-09-25)</small>
- Refactoring in 1.7 broke the signal handling - incorporate fix from Mark Lowne. 
## Version 1.7.0 <small>(2022-08-20)</small>
- Presets can now optionally have icons which display in the menu and overlay the tray icon.
- The Preset-management dialog now includes an icon selection button.
## Version 1.6.11 <small>(2022-07-31)</small>
- Display current preset in window and tray title and detect if a preset is in use at startup.
## Version 1.6.10 1.6.9 <small>(2022-07-16)</small>
- Cope better with invalid slider values caused by a monitor being too slow/busy when responding.
- Wait for monitor detection to stabilise at session restoration (at login time).
## Version 1.6.8 <small>(2022-06-13)</small>
- Fix preset restore/save bug introduced in 1.6.7
## Version 1.6.7 <small>(2022-06-12)</small>
- Gnome system tray behaviour made consistent with gnome - when in gnome do as the gnomens do.
## Version 1.6.5 <small>(2022-06-11)</small>
- Widen handling of pare exceptions for VDU capabilities - catch more exceptions.
## Version 1.6.4 <small>(2022-04-13)</small>
- Wait for system tray to become available (for autostart Plasma Wayland).
- Enable HiDPI icons (for the bottom toolbar) - fix blurred toolbar icons on up-scaled desktops.
## Version 1.6.3 <small>(2022-04-09)</small>
- Added a hamburger menu as an obvious alternate path to the context menu.
- Minor cosmetic UI changes.
## Version 1.6.2 <small>(2022-04-09)</small>
- Added a Feature Values: min..max override to optionally restrict brightness and other sliders.
## Version 1.6.1 <small>(2022-03-14)</small>
- Alterations for Wayland compatibility (cosmetic)
## Version 1.6.0 <small>(2022-03-07)</small>
- Let other processes trigger vdu_controls preset changes and settings refreshes via UNIX/Linux signals.
## Version 1.5.2 <small>(2021-10-09)</small>
- ``vdu-controls`` is now feature complete in respect to my own requirements.
- Raise popup dialogs to the top (in case Qt renders them behind existing windows).
- Documentation tweaks.
## Version 1.5.1 <small>(2021-10-07)</small>
- New grey-scale reference chart for assistance with brightness and contrast adjustment.
- About/help/settings/presets dialogs are now singletons, only one of each can be visible.
## Version 1.5.0 <small>(2021-10-03)</small>
- New presets feature: easily switch between named presets such as *Night*, *Day*, *Overcast*, *Sunny*, 
-Photography*, and *Video*.
- ``Presets`` main-menu item for access to the new ``preset management widget``.
- Context menu shortcuts for quickly accessing presets.
- INI preset file format for ease of editing.
## Version 1.4.2
- Fix increasing indentation of multiline capabilities text on each config file save.
- Prune the VDU settings-editor control-list to only show controls supported by the VDU.
- Use grid layout in the ``settings`` editor.
## Version 1.4.1 <small>(2021-09-28)</small>
- Internal code cleanups after switching to INI config files (no functional changes).
- Updated the help.
## Version 1.4.0 <small>(2021-09-27)</small>
- Added global and VDU-specific INI style configuration files in `$HOME/.conf/vdu_controls/`.
- Added a GUI settings-editor as a `settings` menu-item in the main-menu.
## Version 1.3.1 <small>(2021-09-22)</small>
- A minor enhancement to ease installation on Ubuntu, create ``$HOME/bin`` if it doesn't exist. 
## Version 1.3.0 <small>(2021-09-16)</small>
- Add a CUSTOM::Sleep_Multiplier VDU config-file option to allow VDU specific sleep multipliers.
    This can be used to prevent the slowest VDU from dragging down response time for all connected VDUs.
- Added a main UI right-mouse action that makes the context menu available in the UI window.
- Added a help option to context menu, it displays a formatted version of the ``--detailed-help`` text.
- Added a ``--detailed-help`` command line option to extract the help from the script (in Markdown format).
## Version 1.2.2 <small>(2021-09-14)</small>
- Generalise and simplify the error handling changes initiated in v1.2.1.
## Version 1.2.1 <small>(2021-09-14)</small>
- Catch ddcutil error exit and offer to try a slower --sleep-multiplier
## Version 1.2 <small>(2021-09-13)</small>
- Better handle out of range values.
- Enable audio-mute,audio-treble,audio-bass,audio-mic-volume.
- Allow ddcutil to be anywhere on the user's PATH.
- Improve parsing to ignore laptop non-MCCS displays when present with external monitors. 
- Improve the documentation.
- Add an --about command line option and an "about" tray option.
## Version 1.0
- Initial Release


