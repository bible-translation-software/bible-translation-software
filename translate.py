#!/usr/bin/env python3

# This script updates the .po files with any newly found translatable strings,
# and then compiles the .mo files

import os
import subprocess
import glob


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print("Running makemessages")
    subprocess.check_call([
        "python", "manage.py", "makemessages",
        "-a",
        "-l", "fr",
        "--no-wrap",
        "--no-location",
        "--no-obsolete",
        "--ignore", "env/*",
        "--ignore", "src/*",
        "--ignore", "manage.py",
        "--ignore", "requirements.txt",
        "--ignore", "setup.py",
        "--ignore", "node_modules",
        "--ignore", "admin.py",
    ])

    for po_file in glob.glob("locale/*/LC_MESSAGES/*.po"):
        output = []
        for line in open(po_file, "r", encoding="UTF-8").readlines():
            # Remove the annoying POT-Creation-Date timestamp:
            if line.startswith('"POT-Creation-Date') or line.startswith('"PO-Revision-Date'):
                line = ""
            # Remove all U+202B RIGHT-TO-LEFT EMBEDDING characters
            # sed -i bak "s/$(perl -CS -e 'print "\x{202b}"')//" "$po_file"
            line = line.replace("\u202b", "").replace("\u200f", "").replace("\u202c", "")
            output.append(line)
        with open(po_file, "w", encoding="UTF-8") as ff:
            for line in output:
                ff.write(line)


    os.chdir("locale")
    print("Running compilemessages")
    subprocess.check_call(["python", "../manage.py", "compilemessages",])
    print("Done")

if __name__ == "__main__":
    main()
