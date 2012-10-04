# Copyright 2012 Twitter
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import os
import plistlib
import re
import shutil
import sys
import tempfile


PARSER = argparse.ArgumentParser(
    description='Command-line interface for clutch.io')
PARSER.add_argument('command')
PARSER.add_argument('dirname')

SLUG_RE = re.compile(r'^[\w-]+$')


def handle(namespace, extra):
    namespace = PARSER.parse_args()

    if SLUG_RE.search(namespace.dirname) is None:
        print >> sys.stderr, 'Sorry, you specified an invalid directory name'
        sys.exit(1)

    if namespace.dirname.lower() in ('global', 'clutch-core'):
        print >> sys.stderr, 'Sorry, both "global" and "clutch-core" are reserved names'
        sys.exit(1)

    dirname = os.path.abspath(os.path.expanduser(namespace.dirname))
    if os.path.exists(dirname):
        print >> sys.stderr, 'Sorry, a directory by that name already exists'
        sys.exit(1)

    # Find the path to the app skeleton
    pth_commands = os.path.dirname(os.path.abspath(__file__))
    pth_clutchclient = os.path.dirname(pth_commands)
    pth_skeletons = os.path.join(pth_clutchclient, 'skeletons')
    pth_app = os.path.join(pth_skeletons, 'app')

    # First we copy the skeleton file into a temporary directory
    tmp_dir = os.path.join(tempfile.mkdtemp(), 'tmp')
    shutil.copytree(pth_app, tmp_dir)

    # Delete any DELETEME.txt files
    for root, dirs, files in os.walk(tmp_dir):
        for fn in files:
            if fn.endswith('DELETEME.txt'):
                os.unlink(os.path.join(root, fn))

    plist_path = os.path.join(tmp_dir, 'clutch.plist')
    plist = plistlib.readPlist(plist_path)
    plist['ClutchAppShortName'] = namespace.dirname
    plistlib.writePlist(plist, plist_path)

    # Now we rename it to the user's desired directory
    os.rename(tmp_dir, dirname)
