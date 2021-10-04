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
Version: 1.5.0
Release: 0
License: GPL-3.0-or-later
BuildArch: noarch
URL: https://github.com/digitaltrails/vdu_controls
Group: System/GUI/Other
Summary: Visual Display Unit virtual control panel
Source0:        %{name}-%{version}.tar.gz
Requires: ddcutil python38 python38-qt5
BuildRequires: python3
BuildRequires: coreutils
%if 0%{?suse_version}
BuildRequires: update-desktop-files
%endif
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

%if 0%{?suse_version}
%suse_update_desktop_file %{name} Settings
%endif

gzip -c docs/_build/man/vdu_controls.1 > %{buildroot}/%{_datadir}/man/man1/%{name}.1.gz

%files
%license LICENSE.md
%defattr(-,root,root)
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/man/man1/%{name}.1.gz

%changelog

* Mon Oct 04 2021 Michael Hamilton <michael@actrix.gen.nz>
- Packaged for rpm
