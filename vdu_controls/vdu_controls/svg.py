# SPDX-FileCopyrightText: 2021-2026 Michael Hamilton
# SPDX-License-Identifier: GPL-3.0-or-later
import re
from vdu_controls.qt_imports import QColor


MONOCHROME_APP_ICON = b"""
<svg viewBox="0 0 22 22" version="1.1" id="svg1" xmlns="http://www.w3.org/2000/svg">
  <defs id="defs3051"><style type="text/css" id="current-color-scheme">.ColorScheme-Text {color:#232629;}</style></defs>
  <path style="fill:currentColor;fill-opacity:1;stroke:none" class="ColorScheme-Text"
     d="m 3.012318,1.987629 -0.086226,13.98553 h 1 l 5.0022397,0.02464 -1e-7,2 -2.0022396,-0.02464 v 1 h 8.0000002 v -1 
     l -2.00224,-0.01232 -0.01232,-2 5.01456,0.01232 h 1 L 18.957944,2.0296853 17.989795,2.0050493 4.0174203,1.9774244 
     Z m 0.9927843,1.0339651 13.9651597,-0.01742 -0.01954,10.9465899 -14.0000001,0.02464 z" id="rect4211"/>
</svg>"""

FALLBACK_SPLASH_SVG = b"""
<svg viewBox="0 0 24 24" width="256" height="256" fill="none" xmlns="http://www.w3.org/2000/svg">
    <style type="text/css" id="current-color-scheme"> .ColorScheme-Text { color:#232629; } </style>
    <linearGradient id="screenGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#66c0f1" /> <!-- Start color (offset 0%) -->
      <stop offset="100%" stop-color="#3f7eed" />  <!-- End color (offset 100%) -->
    </linearGradient>
    <g class="ColorScheme-Text" stroke="currentColor" stroke-linecap="round" stroke-width="1.2" transform="">
        <rect x="2.5" y="3" width="19.25" height="15" fill="url(#screenGradient)" rx="1" ry="1"/>
        <path fill="None" d="M 3 17.5 L 21.5 17.5 M 8.5 20.5 L 15.75 20.5"/>
        <path stroke-width="2" stroke-linecap="square" fill="None" d="M 11 19 L 13 19"/>
    </g>
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
    <g class="ColorScheme-Text" stroke="currentColor" stroke-linejoin="round" stroke-linecap="round"  
       stroke-width="2" transform="">
        <path fill="None" d="M 20 18 L 1 18 1 5 20 5 20 18 M 6.5 21 L 15 21"/>
    </g>
</svg>
"""

PANEL_CONNECTED_ICON_SOURCE = b"""
<svg viewBox="0 0 24 24" width="24" height="24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <style type="text/css" id="current-color-scheme"> .ColorScheme-Text { color:#232629; } </style>
    <g class="ColorScheme-Text" stroke="currentColor" stroke-linejoin="round" stroke-linecap="round"  stroke-width="2" transform="">
        <path fill="None" d="M 20 18 L 1 18 1 5 20 5 20 18 M 1 21 L 20 21"/>
    </g>
</svg>
"""

VDU_POWER_ON_ICON_SOURCE = b"""
<svg viewBox="0 0 24 24" width="24" height="24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <style type="text/css" id="current-color-scheme"> .ColorScheme-Text { color:#232629; } </style>
    <g class="ColorScheme-Text" stroke="currentColor" stroke-linejoin="round" stroke-linecap="round" stroke-width="2" transform="">
        <path fill="None" d="M14 12 A 5 5 0 1 0 20 12 M 17 11 L 17 16.5 M 9 20 L 1 20 1 5 20 5 20 8"/>
    </g>
</svg>
"""

AMBIENT_PANEL_ICON_SOURCE = b"""
<svg viewBox="0 0 24 24" width="24" height="24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <style type="text/css" id="current-color-scheme"> .ColorScheme-Text { color:#232629; } </style>
    <g class="ColorScheme-Text" stroke="currentColor"  stroke-linejoin="round" stroke-linecap="round" stroke-width="2">
        <path fill="none" d="M9 20 L1 20 1 5 20 5 20 7" />
        <circle cx="17" cy="16" r="5" stroke="currentColor" fill="none" />
        <rect x="11" y="21.5" width="1" height="1" rx="5" ry="5" stroke-width="1" fill="currentColor" />
        <rect x="8.5" y="15.5" width="1" height="1" rx="5" ry="5" stroke-width="1" fill="currentColor" />
        <rect x="10.5" y="10" width="1" height="1" rx="5" ry="5" stroke-width="1" fill="currentColor" />
        <rect x="15.5" y="7.5" width="1" height="1" rx="5" ry="5" stroke-width="1" fill="currentColor" />
        <rect x="21.5" y="9" width="1" height="1" rx="5" ry="5" stroke-width="1" fill="currentColor" />
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
