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

import httplib
import os
import posixpath
import threading
import time
import urllib
import urlparse

from clutchclient.utils import json, get_config, remote_call, get_app_slug

from clutchclient.commands import APP_PARSER


def _translate_path(initial_path, path):
    # abandon query parameters
    path = path.split('?', 1)[0]
    path = path.split('#', 1)[0]
    path = posixpath.normpath(urllib.unquote(path))
    words = path.split('/')
    words = filter(None, words)
    path = initial_path
    for word in words:
        drive, word = os.path.splitdrive(word)
        head, word = os.path.split(word)
        if word in (os.curdir, os.pardir):
            continue
        path = os.path.join(path, word)
    return path


def poll(config, app_slug, **kwargs):
    headers = kwargs.get('headers', {})
    headers.update({
        'Accept': 'application/json',
        'X-Clutch-Username': config['username'],
        'X-Clutch-Password': config['password'],
        'X-Clutch-App-Slug': app_slug,
    })
    parsed_url = urlparse.urlparse(config['tunnel_url'])
    if parsed_url.scheme == 'http':
        conn_class = httplib.HTTPConnection
    else:
        conn_class = httplib.HTTPSConnection
    conn = conn_class(parsed_url.netloc)
    conn.request('GET', '/poll/', '', headers)
    try:
        response = conn.getresponse()
    except (IOError, httplib.HTTPException):
        # Something busted on the server side, sleep 1 second and try again.
        time.sleep(1)
        return {}
    raw_data = response.read()
    conn.close()
    try:
        return json.loads(raw_data)
    except ValueError:
        # Something busted on the server side, sleep 2 seconds and try again.
        time.sleep(2)
        return {}


def post(config, path, uuid):
    headers = {'Accept': 'application/json'}
    parsed_url = urlparse.urlparse(config['tunnel_url'])
    if parsed_url.scheme == 'http':
        conn_class = httplib.HTTPConnection
    else:
        conn_class = httplib.HTTPSConnection
    conn = conn_class(parsed_url.netloc)

    if isinstance(path, basestring):
        try:
            with open(path, 'r') as f:
                conn.request('POST', '/post/' + uuid, f, headers)
        except IOError:
            conn.request('POST', '/post/' + uuid, 'CLUTCH404DOESNOTEXIST',
                headers)
    else:
        conn.request('POST', '/post/' + uuid, json.dumps(path), headers)

    response = conn.getresponse()
    raw_data = response.read()
    conn.close()
    return json.loads(raw_data)


def serve(config, initial_path, app_slug):
    print 'Serving at %s%sview/%s/%s/' % (
        config['tunnel_url'],
        '' if config['tunnel_url'].endswith('/') else '/',
        config['username'],
        app_slug,
    )
    while 1:
        data = poll(config, app_slug)
        for item in data.get('files', []):
            if 'dir' in item:
                print 'GET', '/'
                listing = []
                for d in os.listdir(initial_path):
                    idx = os.path.join(initial_path, d, 'index.html')
                    if os.path.exists(idx):
                        listing.append(d)
                t = threading.Thread(target=post,
                    args=[config, listing, item['uuid']])
                t.start()
            else:
                print 'GET', item['path']
                path = _translate_path(initial_path, item['path'])
                t = threading.Thread(target=post,
                    args=[config, path, item['uuid']])
                t.start()


def send_reload_message(config, filename, app_slug, **kwargs):
    headers = kwargs.get('headers', {})
    headers.update({
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    })
    parsed_url = urlparse.urlparse(config['tunnel_url'])
    if parsed_url.scheme == 'http':
        conn_class = httplib.HTTPConnection
    else:
        conn_class = httplib.HTTPSConnection
    conn = conn_class(parsed_url.netloc)
    print filename
    data = json.dumps({
        'password': config['password'],
        'message': {'changed_file': filename},
    })
    path = '/event/%s/%s/' % (config['username'], app_slug)
    conn.request('POST', path, data, headers)
    response = conn.getresponse()
    raw_data = response.read()
    conn.close()
    return raw_data


def create_monitor_thread(config, path, app_slug=None):
    sleep_time = 1  # check every second

    mtimes = {}

    # Pre-fill the mtimes dictionary
    paths = [path]
    while len(paths):
        hidden = '%s.' % (os.sep,)
        for root, dirs, files in os.walk(paths.pop()):
            if hidden in root:
                continue
            for d in dirs:
                if d.startswith('.'):
                    continue
                normdir = os.path.join(root, d)
                if os.path.islink(normdir):
                    paths.append(normdir)
            for fn in files:
                if fn.startswith('.'):
                    continue
                filename = os.path.join(root, fn)
                mtimes[filename] = os.path.getmtime(filename)

    def _monitor():
        while 1:
            paths = [path]
            while len(paths):
                hidden = '%s.' % (os.sep,)
                for root, dirs, files in os.walk(paths.pop()):
                    if hidden in root:
                        continue
                    for d in dirs:
                        if d.startswith('.'):
                            continue
                        normdir = os.path.join(root, d)
                        if os.path.islink(normdir):
                            paths.append(normdir)
                    for fn in files:
                        if fn.startswith('.'):
                            continue
                        filename = os.path.join(root, fn)
                        mt = os.path.getmtime(filename)
                        old_mt = mtimes.get(filename)
                        mtimes[filename] = mt
                        if old_mt != mt:
                            trimmed = filename[len(path) + len(os.sep):]
                            print 'Detected change in %s, sending reload message' % (trimmed,)
                            send_reload_message(config, trimmed, app_slug)
            time.sleep(sleep_time)

    return _monitor


def handle(namespace, extra):
    APP_PARSER.add_argument('-t', '--no-toolbar', dest='toolbar', action='store_false', default=True)
    namespace = APP_PARSER.parse_args()

    dirname = os.path.abspath(os.path.expanduser(namespace.directory))

    app_slug = get_app_slug(namespace)

    config = get_config(namespace)

    def _ping_dev():
        url = '%sview/%s/%s/' % (
            config['tunnel_url'],
            config['username'],
            app_slug,
        )
        while 1:
            remote_call(config, 'start_dev',
                app_slug=app_slug,
                url=url,
                toolbar=namespace.toolbar,
            )
            time.sleep(240)  # Wait 4 Minutes

    ping_dev_thread = threading.Thread(target=_ping_dev)
    ping_dev_thread.daemon = True
    ping_dev_thread.start()

    func = create_monitor_thread(config, dirname, app_slug=app_slug)
    watch_change_thread = threading.Thread(target=func)
    watch_change_thread.daemon = True
    watch_change_thread.start()

    try:
        print 'Starting up development server'
        serve(config, dirname, app_slug)
    except KeyboardInterrupt:
        print '\nTearing down development server'
        remote_call(config, 'stop_dev', app_slug=app_slug)
