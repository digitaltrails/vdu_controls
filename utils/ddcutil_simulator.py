#!/usr/bin/python3
import sys
from pathlib import Path

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

BASE_PATH = Path.home()

ANSWER_LINK = 'answer'

SIMULATOR_DATA_DIR = 'ddcutil_simulator_data'


def main():
    answer = ''
    display_num = 0

    arg1 = sys.argv[1]

    if "--display" in sys.argv:
        display_num = sys.argv[sys.argv.index("--display") + 1]

    if "--edid" in sys.argv:
        display_num = sys.argv[sys.argv.index("--edid") + 1][:20]

    if "detect" in sys.argv:
        answer_path = BASE_PATH / SIMULATOR_DATA_DIR / ANSWER_LINK / 'detect'
        print(f"answer_path={answer_path}")
        with open(answer_path, 'r') as answer_file:
            answer = answer_file.read()
    elif "capabilities" in sys.argv:
        answer_path = BASE_PATH / SIMULATOR_DATA_DIR / ANSWER_LINK / f'capabilities_{display_num}'
        print(f"answer_path={answer_path}")
        with open(answer_path, 'r') as answer_file:
            answer = answer_file.read()
    elif "setvcp" in sys.argv:
        pass
    elif "getvcp" in sys.argv:
        vcp_code = "_".join(sys.argv[sys.argv.index("getvcp") + 1:-2])
        answer_path = BASE_PATH / SIMULATOR_DATA_DIR / ANSWER_LINK / f'getvcp_{display_num}_{vcp_code}'
        print(f"answer_path={answer_path}")
        with open(answer_path, 'r') as answer_file:
            answer = answer_file.read()

    print(answer)


if __name__ == '__main__':
    main()
