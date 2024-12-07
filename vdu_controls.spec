#
# spec file for package vdu_controls
#
# Copyright (c) 2023 SUSE LLC
# Copyright (c) 2021-2023 Michael Hamilton <michael@actrix.gen.nz>
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
Version:        2.1.3
Release:        0
Summary:        Visual Display Unit virtual control panel
License:        GPL-3.0-or-later
Group:          System/GUI/Other
URL:            https://github.com/digitaltrails/vdu_controls
Source0:        https://github.com/digitaltrails/vdu_controls/archive/refs/tags/v%{version}.tar.gz#/%{name}-%{version}.tar.gz
BuildRequires:  coreutils
BuildRequires:  hicolor-icon-theme
BuildArch:      noarch
%if 0%{?suse_version}
Requires:       ddcutil
Requires:       noto-sans-math-fonts
Requires:       noto-sans-symbols2-fonts
Requires:       python3
Requires:       python3-qt5
Recommends:     ddcutil-service
Recommends:     python3-pyserial
%endif
%if 0%{?fedora_version}
%define ext_man *
Requires:       ddcutil
Requires:       google-noto-sans-math-fonts
Requires:       google-noto-sans-symbols2-fonts
Requires:       python3
Requires:       python3-qt5
Suggests:       python3-pyserial
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
#Just a placeholder, no build required.

%install
install -d -m 0755 %{buildroot}%{_bindir} \
                   %{buildroot}%{_mandir}/man1/ \
                   %{buildroot}%{_datadir}/applications \
                   %{buildroot}%{_datadir}/%{name}/translations \
                   %{buildroot}%{_datadir}/%{name}/icons \
                   %{buildroot}%{_datadir}/%{name}/sample-scripts \
                   %{buildroot}%{_datadir}/icons/hicolor/256x256/apps
install -m 0755 %{name}.py  %{buildroot}/%{_bindir}/%{name}
install -m 0644 %{name}.desktop %{buildroot}%{_datadir}/applications/%{name}.desktop
install -m 0644 %{name}.png %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/%{name}.png
install -m 0644 icons/* %{buildroot}%{_datadir}/%{name}/icons/
install -m 0644 translations/*.ts %{buildroot}%{_datadir}/%{name}/translations/
install -m 0644 translations/about_*.txt %{buildroot}%{_datadir}/%{name}/translations/
install -m 0755 sample-scripts/* %{buildroot}%{_datadir}/%{name}/sample-scripts/
install -m 0644 docs/_build/man/%{name}.1 %{buildroot}%{_mandir}/man1/

# This script is supposed to work with any python3 - so leave the shebang alone
# %%if 0%{?suse_version}
# %%python3_fix_shebang
# %%endif

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
%{_datadir}/icons/hicolor/256x256/apps/%{name}.png
%{_mandir}/man1/%{name}.1%{?ext_man}
%{_datadir}/%{name}/icons/*
%{_datadir}/%{name}/translations/da_DK.ts
%{_datadir}/%{name}/translations/fr_FR.ts
%{_datadir}/%{name}/translations/de_DE.ts
%{_datadir}/%{name}/translations/cs_CZ.ts
%{_datadir}/%{name}/translations/about_da_DK.txt
%{_datadir}/%{name}/translations/about_fr_FR.txt
%{_datadir}/%{name}/translations/about_de_DE.txt
%{_datadir}/%{name}/translations/about_cs_CZ.txt
%{_datadir}/%{name}/sample-scripts/lux-from-webcam.bash
%{_datadir}/%{name}/sample-scripts/lux-from-webcam.py
%{_datadir}/%{name}/sample-scripts/vlux_meter.py
%ghost %{_datadir}/%{name}/icons/system-icons

# Build service notes:
# 0) Build service page: https://build.opensuse.org/package/show/utilities/vdu_controls
# 1) branch the package (link on left margin of page)
# 2) upload/alter package files in branch (should be the github versions)
# 3) wait for builds to complete
# 4) when OK/finished/happy, submit
# 5) check assigned tasks: self approve submission and opt to remove branch
# 6) check build service page (above) has updated
# 7) wait for propagation to experimental package https://software.opensuse.org/package/vdu_controls
%changelog