# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is Sync Server
#
# The Initial Developer of the Original Code is the Mozilla Foundation.
# Portions created by the Initial Developer are Copyright (C) 2010
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#   Tarek Ziade (tarek@mozilla.com)
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****
""" Test helpers
"""
from collections import defaultdict
import json
import time


__all__ = ['ClientTesterMiddleware']


DISABLED = 'disabled'
RECORD = 'recording'
REPLAY = 'playing'



def _int2status(status):
    if status == 200:
        return '200 OK'
    if status == 400:
        return '400 Bad Request'
    if status == '401':
        return '400 Unauthorized'

    return '%d Explanation' % status


class ClientTesterMiddleware(object):
    """Middleware that let a client drive failures for testing purposes.
    """
    def __init__(self, app, mock_path='/__testing__',
                 filter_path='/__filter__',
                 rec_path='/__record__'):
        self.app = app
        self.mock_path = mock_path
        self.filter_path = filter_path
        self.rec_path = rec_path
        self.replays = defaultdict(list)
        self.filters = defaultdict(dict)
        self.is_recording = defaultdict(lambda: DISABLED)

    def _get_client_ip(self, environ):
        if 'HTTP_X_FORWARDED_FOR' in environ:
            return environ['HTTP_X_FORWARDED_FOR'].split(',')[0].strip()

        if 'REMOTE_ADDR' in environ:
            return environ['REMOTE_ADDR']

        return None

    def _resp(self, sr, status='200 OK', body='', headers=None):
        if headers is None:
            headers = {}
        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'text/plain'
        sr(status, [(key, value.encode('utf8'))
                    for key, value in headers.items()])
        return [body]

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO']
        environ['_ip'] = ip = self._get_client_ip(environ)
        environ['_replays'] = replays = self.replays[ip]
        environ['_filters'] = filters = self.filters[ip]
        environ['_is_recording'] = rec = self.is_recording[ip]

        # routing
        if path.startswith(self.mock_path):
            return self._mock(environ, start_response)
        elif path.startswith(self.filter_path):
            return self._filter(environ, start_response)
        elif path.startswith(self.rec_path):
            return self._record(environ, start_response)

        def sr(_filters):
            def _sr(status, headers):
                res = start_response(status, headers)
                intst = int(status.split()[0])
                if intst in _filters:
                    time.sleep(_filters[intst])
                elif '*' in _filters:
                    time.sleep(_filters['*'])
                return res
            return _sr

        # classical call, do we have something to replay ?
        if len(replays) > 0:
            # yes
            replay = replays.pop()
            status = _int2status(replay['status'])
            body = replay.get('body', u'').encode('utf8')
            headers = replay.get('headers')
            delay = replay.get('delay', 0)

            # repeat it, always
            if replay.get('repeat') == -1:
                replays.insert(0, replay)

            res = self._resp(sr(filters), status, body, headers)
            time.sleep(delay)
            return res
        else:
            # no, regular app
            # do we record. replay or just call the app ?
            return self.app(environ, sr(filters))

    def _badmethod(self, method, start_response, allowed=None):
        if allowed is None:
            allowed = ('POST', 'DELETE')

        if method not in allowed:
            return self._resp(start_response,
                              '405 Method not ALlowed',
                              {'Allow': ','.join(allowed)})
        return None

    def _record(self, environ, start_response):
        ip = environ['_ip']
        # what's the method ?
        method = environ['REQUEST_METHOD']
        allowed = ('POST', 'GET')
        bad = self._badmethod(method, start_response, allowed)
        if bad is not None:
            return bad

        if method == 'POST':
            # define the toggle
            try:
                st = json.loads(environ['wsgi.input'].read())
            except ValueError:
                return self._resp(start_response, '400 Bad Request')
            self.is_recording[ip] = st
            return self._resp(start_response)

        status = json.dumps(self.is_recording[ip])
        return self._resp(start_response, body=status)

    def _mock(self, environ, start_response):
        # what's the method ?
        method = environ['REQUEST_METHOD']
        bad = self._badmethod(method, start_response)
        if bad is not None:
            return bad

        replays = environ['_replays']
        if method == 'DELETE':
            # wipe out
            replays[:] = []
            return self._resp(start_response)

        # that's something to add to the pile
        try:
            resp = json.loads(environ['wsgi.input'].read())
        except ValueError:
            return self._resp(start_response, '400 Bad Request')

        repeat = resp.get('repeat', 1)
        if repeat == -1:
            # will repeat indefinitely
            replays.insert(0, resp)
        else:
            for i in range(repeat):
                replays.insert(0, resp)

        return self._resp(start_response)

    def _filter(self, environ, start_response):
        # what's the method ?
        method = environ['REQUEST_METHOD']
        bad = self._badmethod(method, start_response)
        if bad is not None:
            return bad

        filters = environ['_filters']
        if method == 'DELETE':
            # wipe out
            filters.clear()
            return self._resp(start_response)

        # that's something to set
        try:
            new = json.loads(environ['wsgi.input'].read())
        except ValueError:
            return self._resp(start_response, '400 Bad Request')
        filters.clear()

        for status, delay in new.items():
            if status != '*':
                status = int(status)
            filters[status] = delay

        return self._resp(start_response)
