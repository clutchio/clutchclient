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

CLUTCH_CONF = '~/.clutchio'

PARSER = argparse.ArgumentParser(
    description='Command-line interface for clutch.io')
PARSER.add_argument('command')
PARSER.add_argument('-c', '--config', dest='config', action='store', nargs='?', default=CLUTCH_CONF)

APP_PARSER = argparse.ArgumentParser(
    description='Command-line interface for clutch.io')
APP_PARSER.add_argument('command')
APP_PARSER.add_argument('-a', '--app', dest='app', action='store', nargs='?')
APP_PARSER.add_argument('-c', '--config', dest='config', action='store', nargs='?', default=CLUTCH_CONF)
APP_PARSER.add_argument('-d', '--directory', dest='directory', action='store', nargs='?', default=os.getcwd())

from clutchclient.commands.dev import handle as dev
from clutchclient.commands.upload import handle as upload
from clutchclient.commands.startapp import handle as startapp
from clutchclient.commands.startscreen import handle as startscreen
from clutchclient.commands.version import handle as version


# Placate PyFlakes
def __exported_functionality__():
    return [dev, upload, startapp, startscreen, version]
