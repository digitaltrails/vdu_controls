#!/usr/bin/python3
import sys
import xml.etree.ElementTree as ElementTree

"""
Bulk translation utility.

Extract message text from Qt internationalisation .ts files into a simpler format
that can be pasted into a site such as https://www.deepl.com/translator
or Google Translate.  The resulting translation can then be inserted back
into the .ts file by apply_translations.py

Example:
   # Lets try for a Danish translation:

   # Use the qt utility to extract the messages from vdu_controls.py:
   pylupdate5 vdu_controls.py -ts translations/da_DK.ts
   
   # Use extract_translations.py to extract the messages to a simpler format:
   python3 utils/extract_translations.py translations/da_DK.ts > temp.txt
   
   # Now cut and paste the contents of temp.txt into https://www.deepl.com/translator
   # And cut and past the resulting translation into deepl.txt
   
   # Then apply deepl.txt back into the .ts file to create translations/proto.ts.output
   python3 utils/apply_translations.py temp.txt deepl.txt translations/da_DK.ts
   
   # The above script may report some phrases that were not translated, you could
   # paste those phrases to a different site, for example Google Translate. Then run
   # apply on the previous output file to update it with any new translations:
   python3 apply_translations.py temp.txt google.txt translations/da_DK.ts
   
   # Create the binary .qm file:
   mv translations/da_DK.ts.output translations/da_DK.ts
   lrelease-qt5 translations/da_DK.ts
   
   # Copy the .qm file to somewhere the app can find it and then test:
   cp translations/da_DK.qm $HOME/.config/vdu_controls/translations/da_DK.qm
   LC_ALL.UTF-8=da_DK LANG=da_DK.UTF-8 LANGUAGE=da_DK.UTF-8 python3  vdu_controls.py

"""


def main():
    tree = ElementTree.parse(sys.argv[1])
    context = tree.find('context')
    message_list = context.findall('message')
    line_index = {}
    for count, message in enumerate(message_list):
        translation = message.find('translation')
        if 'type' in translation.attrib and translation.attrib['type'] == 'unfinished':
            source = message.find('source')
            location = message.find('location')

            line_key = location.attrib['line']
            while line_key in line_index:
                # More than one translate() allocated this line, make each uniquely keyed by repeatedly prefixing 0
                line_key = '0' + line_key
            line_index[line_key] = True
            print(f"[[{line_key}]]")
            print(source.text, '.')
    #tree.write('translations/test-edited.ts')


if __name__ == '__main__':
    main()
