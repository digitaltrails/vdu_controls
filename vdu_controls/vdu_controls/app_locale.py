# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

"""
This module defines our own tr() that matches what pylupdate5/6 is looking for.
If this method is ever renamed to something other than tr(), then you must
pass -ts-function=new_name to pylupdate5/6.

The Qt pylupdate5/6 utility extracts messages and context from Python source 
and creates or updates an XML .ts file containing all the tr and QT_TR_NOOP 
wrapped messages.  Read up on it for further info.  

Normal message are surrounded by tr("my message") where the context is
the name of the calling class (found by inspection).  For example, if
a class Foo calls tr("something"), tr will use Qt-inspect to find out
it's being called from an instance of Foo, the context will be "Foo".
Where the context cannot be found by inspection tr("my message", "MyContext") 
can be used to explicitly set the context.

Usage:
1) Generate template file from this code, for example, for French:
   ALWAYS BACKUP THE CURRENT .ts FILE BEFORE RUNNING AN UPDATE - it can go wrong!
       pylupdate5/6 vdu_controls.py -ts translations/fr_FR.ts
   where translations is a subdirectory of your current working directory.
2) Edit that using a text editor, an AI translator, or the linguist-qt5 utility.
   If using an editor, remove the 'type="unfinished"' as you complete each entry.
3) This tr() function can work directly from a .ts file.  The ts file
   should reside in $HOME/.config/vdu_controls/translations/ or
   /usr/share/vdu_controls/translations/.  The file should be named
   to match the local setting, for example fr_FR.ts, zh_CN.ts.
4) This is not necessary, but you can optionally us Qt5/Qt6 lrelease to
   convert the .ts to a binary .qm file.  For example lrelease zh_CN.ts
   will create zh_CH.qm. If a qm file and ts file are residient, the
   qm will be preferred.
4) Test using by setting LC_ALL for python and LANGUAGE for Qt
       LC_ALL=fr_FR LANGUAGE=fr_FR python3 vdu_controls/vdu_controls_main.py
   At startup the app will log several messages as it searches for translation files.

Completed .qm files can reside in $HOME/.config/vdu_controls/translations/
or  /user/share/vdu_controls/translations/

If the environment variable VDU_CONTROLS_DEVELOPER is set then a translations
folder in the current working directory will also be searched.  This makes
it possible to test development tweaks to translations without having to copy
them anywhere.
"""

import inspect
import os
from pathlib import Path
from typing import Dict, List
from importlib.resources import files as resources_files

from vdu_controls.constants import VDU_CONTROLS_DEVELOPER
from vdu_controls.qt_imports import QLocale, QTranslator, QApplication, QCoreApplication, Qt
import vdu_controls.logging as log

# Places in the filesystem:
DEVELOPER_TRANSLATIONS_PATH = Path.cwd() / 'translations'  # Developers current working folder - top of project
HOME_LOCAL_SHARE = Path.home() / ".local/share/vdu_controls"
USR_LOCAL_SHARE = Path('/usr/share/vdu_controls')

# Places in the filesystem or zipapp zip file.
APP_INTERNAL_RESOURCE_ROOT = resources_files() / 'resources'
APP_INTERNAL_DOCS_FOLDER = APP_INTERNAL_RESOURCE_ROOT / 'docs'

LOCALE_TRANSLATIONS_PATHS = ([ DEVELOPER_TRANSLATIONS_PATH ] if VDU_CONTROLS_DEVELOPER else []) + [
    HOME_LOCAL_SHARE / 'translations',
    USR_LOCAL_SHARE / 'translations',
    APP_INTERNAL_RESOURCE_ROOT / 'translations',
]


def available_translations() -> List[str]:
    filename_stem_pattern = "??_??"  # two letters, underscore, two letters
    extensions = ["ts", "qm"]
    language_codes = set()
    for dir_path in LOCALE_TRANSLATIONS_PATHS:
        log.info(f"Looking for translation files in {dir_path}")
        for ext in extensions:
            # Glob pattern: e.g., "??_??.ts"
            for file_path in dir_path.glob(f"{filename_stem_pattern}.{ext}"):
                log.info(f"Found translation file: {file_path}")
                language_codes.add(file_path.stem)  # stem is e.g., "fr_FR"
    return sorted(language_codes)  # sorted for consistent order


def find_locale_specific_file(filename: str) -> Path | None:
    """
    First look for a locale specific filename-??_??.suffix version in
      0. If env VDU_CONTROLS_DEVELOPER=yes first look in ./translations
      1. $HOME/.local/share/vdu_controls/translations
      2. /usr/share/vdu_controls/translations
      3. app-internal-resources/resources/translations
    """
    log.info(f"Looking for translation file {filename}")
    for path in LOCALE_TRANSLATIONS_PATHS:
        full_path = path.joinpath(filename)
        log.info(f"Checking for translation: {full_path}")
        if full_path.exists():
            log.info(f"Found translation: {full_path}")
            return full_path
    return None


def load_docs_text(filename: str) -> str:
    """
    First look for a locale specific filename-??_??.suffix using
    find_locale_specific_file("filename.suffix") if that fails
    look internally in vdu_controls/resources/docs/
    """
    # Check outside the application for something locale specific
    as_path = Path(filename)
    if translated_override := find_locale_specific_file(f"{as_path.stem}-{{}}{as_path.suffix}"):
        log.info(f"Loading translated resource {filename} from {translated_override.as_posix()}")
        return translated_override.read_text()

    # Check inside the application resources/docs/
    file_path = APP_INTERNAL_DOCS_FOLDER / filename
    if True or file_path.exists():
        log.info(f"Loading original resource from {file_path}")
        return file_path.read_text()
    log.error(f"Could not find resource {filename} or a translation of it anywhere")
    return ''


translator: QTranslator | None = None
ts_translations: Dict[str, str] = {}
translating_locale = ''


def get_locale_name():
    return QLocale.system().name()


def get_translating_locale():
    global translating_locale
    return translating_locale


def initialise_locale_translations(app: QApplication) -> None:

    # Has to be put somewhere it won't be garbage collected when this function goes out of scope.
    global translator
    translator = QTranslator()
    global ts_translations
    ts_translations = {}
    global translating_locale
    translating_locale = ''

    locale_name = get_locale_name()
    ts_path = find_locale_specific_file(f"{locale_name}.ts")
    qm_path = find_locale_specific_file(f"{locale_name}.qm")  # don't use qm files for now.

    # If there is a .ts XML file in the path newer than the associated .qm binary file, load the messages
    # from the XML into a map and use them directly.  This is useful while developing and possibly useful
    # for users that want to do their own localization.
    if ts_path is not None and (qm_path is None or os.path.getmtime(ts_path) > os.path.getmtime(qm_path)):
        log.info(tr("Using newer .ts file {0} translations from {1}").format(locale_name, ts_path.as_posix()))
        import xml.etree.ElementTree as XmlElementTree
        for context in XmlElementTree.parse(ts_path).findall('context'):
            context_name = context.findall('name')[0].text
            log.info(f"context: {context_name}")
            for message in context.findall('message'):
                translation = message.find('translation')
                source = message.find('source')
                if translation is not None and source is not None and translation.text is not None and source.text is not None:
                    ts_translations[(context_name, source.text)] = translation.text
        log.info(tr("Loaded {0} translations from {1}").format(locale_name, ts_path.as_posix()))
        translating_locale = locale_name
    elif qm_path is not None:
        log.info(tr("Loading {0} translation from {1}").format(locale_name, qm_path.as_posix()))
        if translator.load(qm_path.name, qm_path.parent.as_posix()):
            app.installTranslator(translator)
            log.info(tr("Using {0} translations from {1}").format(locale_name, qm_path.as_posix()))
            translating_locale = locale_name
    if translating_locale and QLocale.system().textDirection() == Qt.LayoutDirection.RightToLeft:
        log.info(f"Locale {locale_name} language is right-to-left - setting layout direction to right-to-left.")
        app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

def tr(source_text: str, context: str | None = None) -> str:
    """
    Match source_text (the original message) in respect to context.
    Context is the calling class name or "@default" otherwise.
    So if a class called Foo calls tr(), then "Foo" will be the
    context.
    """
    if context is None:
        # Try to find 'self' in the caller's local variables
        caller_frame = inspect.stack()[1].frame
        if 'self' in caller_frame.f_locals:
            context = caller_frame.f_locals['self'].__class__.__name__
        else:
            context = "@default" # "Global"  # Fallback if called from a plain function

    # If the source .ts file is newer, we load messages from the XML into ts_translations
    # and use the most recent translations. Using the .ts files in production may be a good
    # way to allow the users to help themselves.
    if ts_translations:
        if translated := ts_translations.get((context, source_text), None):
            return translated
    # the context @default is what is generated by pylupdate5 by default
    return QCoreApplication.translate(context, source_text)


def translate_option(option_text: str, context="ConfOpt") -> str:
    # We can't be sure of the case in capability descriptions retrieved from the monitors.
    # If there is no direct translation, we try a canonical version of the name (all lowercase with '-' replaced with ' ').
    if (translation := tr(option_text, context=context)) != option_text:  # Probably a command line option
        return translation
    canonical = option_text.lower().replace('-', ' ')
    return tr(canonical)

