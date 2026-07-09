#
# spec file for package vdu_controls
#
# Copyright (c) 2023 SUSE LLC
# Copyright (c) 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via https://bugs.opensuse.org/
#

Name:           vdu_controls
Version:        2.6.5
Release:        0
Summary:        Visual Display Unit virtual control panel
License:        GPL-3.0-or-later
Group:          System/GUI/Other
URL:            https://github.com/digitaltrails/vdu_controls
Source0:        https://github.com/digitaltrails/vdu_controls/archive/refs/tags/v%{version}.tar.gz#/%{name}-%{version}.tar.gz

# This forces the openSUSE macros to only target the main system interpreter
%define python_flavors python3
%define skip_python314 1
%define skip_python311 1

BuildRequires:  hicolor-icon-theme
BuildRequires:  python3-devel
BuildRequires:  python-rpm-macros
BuildArch:      noarch

%if 0%{?suse_version}
Requires:       ddcutil
Requires:       noto-sans-math-fonts
Requires:       noto-sans-symbols2-fonts
Requires:       python3 >= 3.9
Requires:       python3-qt6
Recommends:     ddcutil-service
Recommends:     python3-pyserial
Recommends:     python3-pyudev
Recommends:     brightnessctl
%endif

%if 0%{?fedora_version}
%define ext_man *
Requires:       ddcutil
Requires:       google-noto-sans-math-fonts
Requires:       google-noto-sans-symbols2-fonts
Requires:       python3-qt5
Suggests:       python3-pyserial
Suggests:       python3-pyudev
Suggests:       brightnessctl
%endif

%description
vdu_controls is a virtual control panel for externally connected
VDUs (visual display units).  Controls are included for backlight
brightness, and contrast.  vdu_controls uses the ddcutil command
line utility to interact with external displays via VESA Display
Data Channel (DDC) Virtual Control Panel (VCP) standards.

%prep
%autosetup

%build
# Nothing to build – we only copy source files.
# Translations are shipped as editable .ts files for end-user contributions.

%install
# Create the filesystem tree
install -d -m 0755 %{buildroot}%{_bindir} \
                   %{buildroot}%{_mandir}/man1/ \
                   %{buildroot}%{_datadir}/applications \
                   %{buildroot}%{_datadir}/%{name}/translations \
                   %{buildroot}%{_datadir}/%{name}/icons \
                   %{buildroot}%{_datadir}/%{name}/sample-scripts \
                   %{buildroot}%{_datadir}/icons/hicolor/256x256/apps \

# Copy the source package into the private app directory
cp -r src/vdu_controls %{buildroot}%{_datadir}/%{name}

# Copy other assets
install -m 0644 %{name}.desktop %{buildroot}%{_datadir}/applications/%{name}.desktop
install -m 0644 src/%{name}/resources/icons/app/%{name}.svg \
                    %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/%{name}.svg
install -m 0644 icons/* %{buildroot}%{_datadir}/%{name}/icons/
# Install .ts files, editable by end users, app has code to use them directly.
install -m 0644 translations/*.ts %{buildroot}%{_datadir}/%{name}/translations/
install -m 0755 sample-scripts/* %{buildroot}%{_datadir}/%{name}/sample-scripts/
install -m 0644 docs/_build/man/%{name}.1 %{buildroot}%{_mandir}/man1/

# Byte-compile everything in the private app directory
%{__python3} -m compileall -q -f %{buildroot}%{_datadir}/%{name}

# Install the wrapper script
install -p -m 0755 packaging/vdu_controls.wrapper %{buildroot}%{_bindir}/%{name}

# Fix shebang to exact Python version (for openSUSE strictness)
sed -i "s|/usr/bin/python3|/usr/bin/python%{python3_version}|" %{buildroot}%{_bindir}/%{name}

# Make it easy for the user to find a range of icons
%post
ln -s -f %{_datadir}/icons %{_datadir}/%{name}/icons/system-icons

%files
%license LICENSE.md
%dir %{_datadir}/%{name}
%dir %{_datadir}/%{name}/icons
%dir %{_datadir}/%{name}/translations
%dir %{_datadir}/%{name}/sample-scripts
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/256x256/apps/%{name}.svg
%{_mandir}/man1/%{name}.1*
%{_datadir}/%{name}/icons/*
%{_datadir}/%{name}/translations/*.ts
%{_datadir}/%{name}/sample-scripts/*
%{_datadir}/%{name}/vdu_controls

%ghost %{_datadir}/%{name}/icons/system-icons

%changelog