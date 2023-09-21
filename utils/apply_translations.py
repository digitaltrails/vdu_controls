#!/usr/bin/python3
import re
import sys
from pathlib import Path

"""
See extract_translations.py
"""


def main():
    with open(sys.argv[1]) as source_file:
        source_text = source_file.read()

    source_map = {}
    for item in source_text.split('[['):
        if item:

            source_match = re.match(r'^([0-9]+)\]\]\n(.*)', item, flags=re.DOTALL)
            key = source_match.group(1)
            source_map[source_match.group(1)] = source_match.group(2)[:-2]

    with open(sys.argv[2]) as translation_file:
        translation_text = translation_file.read()

    translation_map = {}
    for item in translation_text.split('[['):
        if item:
            translation_match = re.match(r'^([0-9]+)\]\]\n(.*)', item, flags=re.DOTALL)
            if translation_match:
                translation_map[translation_match.group(1)] = translation_match.group(2)[:-2]

    print(translation_map)

    import xml.etree.ElementTree as ET
    tree = ET.parse(sys.argv[3])
    # print(tree)
    ctx = tree.find('context')
    message_list = ctx.findall('message')
    # print(len(msg))
    missing = ''
    lines_done = {}
    for message_node in message_list:
        s = message_node.find('source')
        location = message_node.find('location')
        line_key = location.attrib['line']
        if line_key in translation_map:
            # print(s.text, subs[s.text])
            translation = message_node.find('translation')
            if 'type' in translation.attrib and translation.attrib['type'] == 'unfinished':
                new_text = translation_map[line_key]
                if new_text != source_map[line_key] and new_text.strip() != '':
                    print("Found", line_key, translation.text, translation.attrib, new_text)
                    translation.text = new_text
                    translation.set('type', None)
                    del (translation.attrib['type'])
                else:
                    missing += f"[[{line_key}]]\n{source_map[line_key]} .\n"

    output_filename = sys.argv[3]
    print(f"Updating {output_filename }")
    with open(output_filename, 'w') as of:
        of.write(ET.tostring(tree.getroot(), encoding="unicode"))
    #tree.write(output_filename)
    if missing != '':
        print("Missing translation for:")
        print(missing)


if __name__ == '__main__':
    main()
