pkgname=vdu_controls
pkgver=2.2.0
pkgrel=1
pkgdesc="Visual Display Unit virtual control panel"
arch=('i686' 'x86_64')
url=""
license=('GPL-3.0-or-later')
groups=()
depends=('ddcutil' 'python' 'python-pyqt5' 'qt5-svg' 'python3-pyserial' 'noto-sans-math-fonts' 'noto-sans-symbols2-fonts')
makedepends=('coreutils')
optdepends=()
provides=()
conflicts=()
replaces=()
backup=()
options=()
install=
changelog=
source=($pkgname-$pkgver.tar.gz)
noextract=()
md5sums=(c422c415ea9e71275a79d7df35d0407c) #generate with 'makepkg -g'

build() {
    exit 0
}

package() {
    mkdir -p /usr/bin
    mkdir -p /usr/share/applications
    mkdir -p /usr/share/man/man1
    mkdir -p /usr/share/vdu_controls/icons
    ln -s /usr/share/icons /usr/share/vdu_controls/icons/system-icons
    mkdir -p /usr/share/vdu_controls/translations
    mkdir -p /usr/share/vdu_controls/sample-scripts
    install vdu_controls.py  /usr/bin/%{name}
    install -m644 icons/* /usr/share/vdu_controls/icons
    install -m644 translations/*.ts /usr/share/vdu_controls/translations
    install -m755 sample-scripts/* /usr/share/vdu_controls/sample-scripts

    cat > /usr/share/applications/%{name}.desktop <<'EOF'
[Desktop Entry]
Type=Application
Terminal=false
Exec=%{_bindir}/%{name}
Name=VDU Controls
GenericName=VDU controls
Comment=Virtual Control Panel for externally connected VDUs
Icon=preferences-desktop-display-color
Categories=Settings
EOF

    gzip -c docs/_build/man/vdu_controls.1 > /usr/share/man/man1/%{name}.1.gz
}
