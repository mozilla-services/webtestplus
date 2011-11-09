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
""" Tests for mozsvc.tests.support
"""
import unittest
import time

from webob.dec import wsgify
from webtestplus import ClientTesterMiddleware, TestAppPlus


class SomeApp(object):

    @wsgify
    def __call__(self, request):
        resp = request.response
        resp.body = 'ok'
        resp.content_type = 'text/plain'
        resp.status = 200
        return resp


class TestSupport(unittest.TestCase):

    def test_clienttester(self):

        app = TestAppPlus(ClientTesterMiddleware(SomeApp()))

        # that calls the app
        app.get('/bleh', status=200)

        # let's ask for a 503 and then a 400
        app.record(503)
        app.record(400)

        app.get('/buh', status=503)
        app.get('/buh', status=400)

        # back to normal
        app.get('/buh', status=200)

        # let's ask for two 503s
        app.record(503, repeat=2)

        app.get('/buh', status=503)
        app.get('/buh', status=503)
        app.get('/buh', status=200)

        # some headers and body now
        app.record(503, 'oy', headers={'foo': '1'})

        res = app.get('/buh', status=503)
        self.assertEqual(res.body, 'oy')
        self.assertEqual(res.headers['foo'], '1')

        # repeat stuff indefinitely
        app.record(503, repeat=-1)

        for i in range(20):
            app.get('/buh', status=503)

        # let's wipe out the pile
        app.del_records()
        app.get('/buh', status=200)

        # a bit of timing now
        app.record(503, delay=.5)
        now = time.time()
        app.get('/buh', status=503)
        then = time.time()
        self.assertTrue(then - now >= .5)

    def test_filtering(self):
        # we want to add .5 delays for *all* requests
        app = TestAppPlus(ClientTesterMiddleware(SomeApp()))
        app.filter({'*': .5})

        # let see if it worked
        now = time.time()
        app.get('/buh', status=200)
        then = time.time()
        self.assertTrue(then - now >= .5)

        # we want to add .5 delays for *503* requests only
        app.filter({503: .5})

        # let see if it worked
        now = time.time()
        app.get('/buh', status=200)
        then = time.time()
        self.assertTrue(then - now < .5)

        app.record(503)
        now = time.time()
        app.get('/buh', status=503)
        then = time.time()
        self.assertTrue(then - now >= .5)

        # let's remove the filters
        app.del_filters()

        app.record(503)
        now = time.time()
        app.get('/buh', status=503)
        then = time.time()
        self.assertTrue(then - now < .5)
