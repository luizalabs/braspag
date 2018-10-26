# encoding: utf-8
from __future__ import absolute_import

import re
import codecs
import os

from tornado.testing import AsyncTestCase
from braspag import BraspagRequest
from braspag import ProtectedCardRequest


MERCHANT_ID = u'F9B44052-4AE0-E311-9406-0026B939D54B'
PROTECTED_MERCHANT_ID = u'7E5B3E1F-AB80-4E4A-B00F-9297C99D211C'
HOMOLOGATION = True


class BraspagTestCase(AsyncTestCase):

    def setUp(self):
        super(BraspagTestCase, self).setUp()
        self.braspag = BraspagRequest(MERCHANT_ID, homologation=HOMOLOGATION)
        self.protected_card = ProtectedCardRequest(PROTECTED_MERCHANT_ID, homologation=HOMOLOGATION)
