#!/usr/bin/python3
import sys

"""
Change context name: python3 set_context_translations from_name to_name filename.ts
"""


def main():
    from_context = sys.argv[1]
    to_context = sys.argv[2]
    import xml.etree.ElementTree as ET
    tree = ET.parse(sys.argv[3])
    ctx = tree.find('context')
    context_name = ctx.find('name')
    if context_name.text == from_context:
        context_name.text = to_context
        tree.write(sys.argv[3])
    else:
        print(f"No context with name {from_context} in {sys.argv[3]}")


if __name__ == '__main__':
    main()
