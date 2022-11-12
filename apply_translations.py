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
        line_num = location.attrib['line']
        while line_num in lines_done:
            line_num = '0' + line_num
        lines_done[line_num] = True
        # print(s.text)
        if line_num in translation_map:
            # print(s.text, subs[s.text])
            translation = message_node.find('translation')
            new_text = translation_map[line_num]
            if new_text != source_map[line_num] and new_text.strip() != '':
                print("Found", line_num)
                translation.text = new_text
                translation.set('type', None)
                del (translation.attrib['type'])
            else:
                missing += f"[[{line_num}]]\n{source_map[line_num]} .\n"

    output_filename = sys.argv[3]
    print(f"Updating {output_filename}")

    tree.write(output_filename)
    if missing != '':
        print("Missing translation for:")
        print(missing)


if __name__ == '__main__':
    main()
