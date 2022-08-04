#!/usr/bin/python3
import sys

"""
ddcutil_simulator
=================

For testing vdu_controls UI in different desktops in virtual environments.

The procedure for use would be similar to the following

   export PATH=~/bin:$PATH
   chmod u+x ~/script_location/ddcutil_simulator.py 
   ln -s ~/script_location/ddcutil_simulator.py ~/bin/ddcutil
   vdu_controls

ddcutil_simulator Copyright (C) 2022 Michael Hamilton
=====================================================

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, version 3.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
more details.

You should have received a copy of the GNU General Public License along
with this program. If not, see <https://www.gnu.org/licenses/>.

**Contact:**  m i c h a e l   @   a c t r i x   .   g e n   .   n z
"""

DETECT_RESULT = """Display 1
   I2C bus:  /dev/i2c-0
   Monitor:             HWP:HP ZR24w:CNT0000001

Display 2
   I2C bus:  /dev/i2c-3
   Monitor:             GSM:LG HDR 4K:

"""

CAPABILITIES_RESULTS = {
    "1": """Model: ZR24w
MCCS version: 2.2
VCP Features:
   Feature: 10 (Brightness)
   Feature: 12 (Contrast)
""",
    "2": """Model: Not specified
MCCS version: 2.1
VCP Features:
   Feature: 10 (Brightness)
   Feature: 12 (Contrast)
"""
}

GETVCP_RESULTS = {
    "1": {"10": "VCP 10 C 90 100", "12": "VCP 12 C 100 100"},
    "2": {"10": "VCP 10 C 13 100", "12": "VCP 12 C 60 100"}
}


def main():
    arg1 = sys.argv[1]

    if "--display" in sys.argv:
        display_num = sys.argv[sys.argv.index("--display") + 1]
    if "detect" in sys.argv:
        print(DETECT_RESULT)
    elif "capabilities" in sys.argv:
        print(CAPABILITIES_RESULTS[display_num])
    elif "setvcp" in sys.argv:
        pass
    elif "getvcp" in sys.argv:
        code = sys.argv[sys.argv.index("getvcp") + 1]
        print(GETVCP_RESULTS[display_num][code])


if __name__ == '__main__':
    main()
