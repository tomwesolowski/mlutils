import argparse
import fnmatch
import glob
import json
import os
import pprint as pp
import time
import wave
from pathlib import Path

import numpy as np
import pyaudio

p = pyaudio.PyAudio()


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def cprint(msg, color):
    print(color + msg + bcolors.ENDC)


def save(labeled_data, path):
    """Saves dictionary with labels."""
    with open(path, 'w') as f:
        json.dump(labeled_data, f)


def load(dirname):
    """Loads ALL labels and join them into one dictionary."""
    labeled_data = dict()
    for filename in glob.glob(os.path.join(dirname, '*.json')):
        with open('%s' % filename, 'r') as f:
            labeled_data.update(json.load(f))
    return labeled_data


def find_files(directory, pattern):
    """Finds all files in directory matching pattern."""
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename


def play(filename):
    """Plays wave."""
    chunk = 1024
    with wave.open(filename, "rb") as file:
        stream = p.open(
            format=p.get_format_from_width(file.getsampwidth()),
            channels=file.getnchannels(),
            rate=file.getframerate(),
            output=True)
        data = file.readframes(chunk)
        while data:
            stream.write(data)
            data = file.readframes(chunk)

        stream.stop_stream()
        stream.close()


def ask(filename):
    """Plays wave and asks for label."""
    cprint("Playing: %s" % filename, bcolors.HEADER)
    play(filename)

    labels = ["yes", "no", "up", "down", "left", "right",
              "on", "off", "stop", "go", "silence", "unknown"]
    commands = dict([(label[:2], label) for label in labels])

    for id, (command, label) in enumerate(sorted(commands.items())):
        print("(%s)%s, " % (command, label), end='')
    print()
    print("(omit)omit, (rep)repeat, (end)end")

    command = input()
    if command in ['end', 'omit']:
        return '__' + command
    if command in commands:
        label = commands[command]
        cprint("You chose: %s" % label, bcolors.OKGREEN)
        return label
    else:
        return ask(filename)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("datadir", help="directory with wav files")
    parser.add_argument("labelsdir", help="directory where to store labels")

    args = parser.parse_args()

    # Check directories paths
    if not Path(args.datadir).is_dir():
        cprint("%s does not exist!" % args.datadir, bcolors.FAIL)
        exit(1)

    if not Path(args.labelsdir).is_dir():
        cprint("%s does not exist!" % args.labelsdir, bcolors.FAIL)
        exit(1)

    # Read all wav files and select subset of them.
    all_files = np.array(list(find_files(args.datadir, '*.wav')))
    labels = dict()

    while True:
        filename = np.random.choice(all_files)
        label = ask(filename)
        if label == '__end':
            break
        elif label == '__omit':
            continue
        else:
            filename_without_dir = filename[len(args.datadir):]
            labels[filename_without_dir] = label
        print('labeled so far: %d' % len(labels.keys()))

    print("%d labeled files:" % len(labels.keys()))
    pp.pprint(labels)

    labelspath = '%s/%d.json' % (args.labelsdir, int(time.time()))
    save(labels, labelspath)
    print("Saved into: %s" % labelspath)

    cprint("Labeled samples in total: %d" % len(load(args.labelsdir).keys()), bcolors.UNDERLINE)