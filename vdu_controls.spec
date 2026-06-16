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
BuildRequires:  coreutils
BuildRequires:  hicolor-icon-theme
BuildRequires:  python3-devel
BuildRequires:  python-rpm-macros
BuildArch:      noarch
%if 0%{?suse_version}
Requires:       ddcutil
Requires:       noto-sans-math-fonts
Requires:       noto-sans-symbols2-fonts
Requires:       python3 > 3.8
%if 0%{?sle_version} > 150000 && 0%{?is_opensuse}
Requires:       python3-qt5
%else
Requires:       python3-qt6
%endif
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
python%{python3_version} -m zipapp src -o %{name}.pyz -m %{name}_main:main -p "%{_bindir}/python%{python3_version}"

%install
install -d -m 0755 %{buildroot}%{_bindir} \
                   %{buildroot}%{_mandir}/man1/ \
                   %{buildroot}%{_datadir}/applications \
                   %{buildroot}%{_datadir}/%{name}/translations \
                   %{buildroot}%{_datadir}/%{name}/icons \
                   %{buildroot}%{_datadir}/%{name}/sample-scripts \
                   %{buildroot}%{_datadir}/icons/hicolor/256x256/apps
install -m 0755 %{name}.pyz  %{buildroot}/%{_bindir}/%{name}
install -m 0644 %{name}.desktop %{buildroot}%{_datadir}/applications/%{name}.desktop
install -m 0644 src/%{name}/resources/icons/app/%{name}.svg \
                    %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/%{name}.svg
install -m 0644 icons/* %{buildroot}%{_datadir}/%{name}/icons/
install -m 0644 translations/*.ts %{buildroot}%{_datadir}/%{name}/translations/
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
%{_datadir}/icons/hicolor/256x256/apps/%{name}.svg
%{_mandir}/man1/%{name}.1*
%{_datadir}/%{name}/icons/*
%{_datadir}/%{name}/translations/ar_SA.ts
%{_datadir}/%{name}/translations/da_DK.ts
%{_datadir}/%{name}/translations/de_DE.ts
%{_datadir}/%{name}/translations/es_ES.ts
%{_datadir}/%{name}/translations/fr_FR.ts
%{_datadir}/%{name}/translations/mi_NZ.ts
%{_datadir}/%{name}/translations/zh_CN.ts
%{_datadir}/%{name}/sample-scripts/lux-from-webcam.bash
%{_datadir}/%{name}/sample-scripts/lux-from-webcam.py
%{_datadir}/%{name}/sample-scripts/vlux_meter.py
%{_datadir}/%{name}/sample-scripts/laptop-ddcutil-emulator.bash
%ghost %{_datadir}/%{name}/icons/system-icons

%changelog
