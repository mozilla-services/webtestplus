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
import json
from webtest import TestApp
from webtestplus.override import DISABLED, RECORD, REPLAY

__all__ = ['TestAppPlus']


class TestAppPlus(TestApp):
    def __init__(self, app, extra_environ=None, relative_to=None,
                 use_unicode=True, mock_path='/__testing__',
                 filter_path='/__filter__',
                 rec_path='/__record__', secret=None):
        super(TestAppPlus, self).__init__(app, extra_environ, relative_to,
                                          use_unicode)
        self._mock_path = mock_path
        self._filter_path = filter_path
        self._rec_path = rec_path
        if secret is not None:
            self.extra_environ['HTTP_X_SECRET'] = secret

    def rec_status(self):
        return json.loads(self.get(self._rec_path).body)

    def _send_status(self, status):
        res = self.post(self._rec_path, params=json.dumps(status))
        return res.status_int == 200

    def start_recording(self):
        return self._send_status(RECORD)

    def start_replaying(self):
        return self._send_status(REPLAY)

    def disable_recording(self):
        return self._send_status(DISABLED)

    def del_filters(self):
        return self.delete(self._filter_path).status_int == 200

    def filter(self, filters):
        filters = json.dumps(filters)
        res = self.post(self._filter_path, params=filters)
        return res.status_int == 200

    def del_mocks(self):
        return self.delete(self._mock_path).status_int == 200

    def mock(self, status=200, body='', headers=None, repeat=1, delay=0.):
        if headers is None:
            headers = {}

        resp = {'status': status, 'body': body, 'headers': headers,
                'repeat': repeat, 'delay': delay}

        res = self.post(self._mock_path, params=json.dumps(resp))
        return res.status_int == 200
