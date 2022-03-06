#
# spec file for vducontrols
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>.
#
# Contact:  m i c h a e l   @   a c t r i x   .   g e n   .   n z
#

Name: vdu_controls
Version: 1.6.0
Release: 0
License: GPL-3.0-or-later
BuildArch: noarch
URL: https://github.com/digitaltrails/vdu_controls
Group: System/GUI/Other
Summary: Visual Display Unit virtual control panel
Source0:        %{name}-%{version}.tar.gz

%if 0%{?suse_version} || 0%{?fedora_version}
Requires: ddcutil python38 python38-qt5
%endif

BuildRequires: coreutils

BuildRoot: %{_tmppath}/%{name}-%{version}-build
%description
vdu_controls is a virtual control panel for externally connected
VDU's (visual display units).  Controls are included for backlight
brightness, and contrast.  vdu_controls uses the ddcutil command
line utility to interact with external displays via VESA Display
Data Channel (DDC) Virtual Control Panel (VCP) standards.

%prep
%setup -q

%build

exit 0

%install
mkdir -p %{buildroot}/%{_bindir}
mkdir -p %{buildroot}/%{_datadir}/applications
mkdir -p %{buildroot}/%{_datadir}/man/man1
install vdu_controls.py  %{buildroot}/%{_bindir}/%{name}

cat > %{buildroot}/%{_datadir}/applications/%{name}.desktop <<'EOF'
[Desktop Entry]
Type=Application
Terminal=false
Exec=%{_bindir}/%{name}
Name=VDU Controls
GenericName=VDU controls
Comment=Virtual Control Panel for externally connected VDU's
Icon=preferences-desktop-display-color
Categories=Settings
EOF

gzip -c docs/_build/man/vdu_controls.1 > %{buildroot}/%{_datadir}/man/man1/%{name}.1.gz

%post


%files
%license LICENSE.md
%defattr(-,root,root)
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/man/man1/%{name}.1.gz

%changelog
* Mon Mar 07 2022 Michael Hamilton <michael@actrix.gen.nz>
- Let other processes trigger preset changes and settings refreshes via UNIX/Linux signals: : vdu_controls 1.6.0
* Sun Feb 27 2022 Michael Hamilton <michael@actrix.gen.nz>
- Cleanly handle monitors that do not respond to ddctuil commands: vdu_controls 1.5.9
* Sat Dec 04 2021 Michael Hamilton <michael@actrix.gen.nz>
- Check if a system tray is available before applying system_tray_enabled: vdu_controls 1.5.7
* Sat Nov 13 2021 Michael Hamilton <michael@actrix.gen.nz>
- Escape % characters in the metadata: vdu_controls 1.5.6
* Thu Nov 13 2021 Michael Hamilton <michael@actrix.gen.nz>
- Fix tray for some desktops. Combobox value enhanccments/fixes. Login-restart support: vdu_controls 1.5.5
* Thu Nov 08 2021 Michael Hamilton <michael@actrix.gen.nz>
- Detect and handle light/dark theme changes: vdu_controls 1.5.3
* Mon Oct 04 2021 Michael Hamilton <michael@actrix.gen.nz>
- Packaged for rpm vdu_controls: 1.5.2
