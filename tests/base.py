
from __future__ import absolute_import

import re
import codecs

from tornado.testing import AsyncTestCase
from braspag import BraspagRequest
from braspag import ProtectedCardRequest


MERCHANT_ID = u'F9B44052-4AE0-E311-9406-0026B939D54B'
PROTECTED_MERCHANT_ID = u'7E5B3E1F-AB80-4E4A-B00F-9297C99D211C'
HOMOLOGATION = True
ASYNC_TIMEOUT = 20  # timeout for async operations, in seconds


class BraspagTestCase(AsyncTestCase):

    def setUp(self):
        super(BraspagTestCase, self).setUp()
        self.braspag = BraspagRequest(MERCHANT_ID, homologation=HOMOLOGATION)
        self.protected_card = ProtectedCardRequest(PROTECTED_MERCHANT_ID, homologation=HOMOLOGATION)


class RegexpMatcher(object):
    def __init__(self, data_filepath):
        with codecs.open(data_filepath, 'rb', encoding='utf-8') as data_file:
            self.data = data_file.read().strip()

    def __eq__(self, other):
        if not isinstance(other, basestring):
            return False

        if not re.match(self.data, other):
            return False

        return True

    def __unicode__(self):
        return self.data

    def __repr__(self):
        return repr(unicode(self))
