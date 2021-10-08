pkgname=vdu_controls
pkgver=1.5.2
pkgrel=1
pkgdesc="Visual Display Unit virtual control panel"
arch=('i686' 'x86_64')
url=""
license=('GPL-3.0-or-later')
groups=()
depends=('ddcutil' 'python' 'python-pyqt5')
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
md5sums=(f902fe85dbdb8d80a719d7e4c79c630b) #generate with 'makepkg -g'

build() {
    exit 0
}

package() {
    mkdir -p /usr/bin
    mkdir -p /usr/share/applications
    mkdir -p /usr/share/man/man1
    install vdu_controls.py  /usr/bin/%{name}

    cat > /usr/share/applications/%{name}.desktop <<'EOF'
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

    gzip -c docs/_build/man/vdu_controls.1 > /usr/share/man/man1/%{name}.1.gz

}