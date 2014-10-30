# -*- coding: utf8 -*-

from __future__ import absolute_import

from braspag.utils import to_bool
from braspag.utils import to_int
from braspag.utils import mask_credit_card_from_xml
from .base import BraspagTestCase


class UtilsTest(BraspagTestCase):

    def test_utils(self):

        assert to_bool('false') == False
        assert to_bool('False') == False
        assert to_bool('FALSE') == False
        assert to_bool('true') == True
        assert to_bool('True') == True
        assert to_bool('TRUE') == True

        assert to_int('1') == 1
        assert to_int('1432-2') == 14322

    def test_mask_credit_card_from_xml_with_exiting_card_number(self):
        xml = '<CardNumber>1234567890123456</CardNumber>'

        assert (mask_credit_card_from_xml(xml) ==
                '<CardNumber>123456******3456</CardNumber>')

    def test_mask_credit_card_from_xml_with_non_existing_card_number(self):
        xml = '<html><head></head><body></body></html>'

        assert mask_credit_card_from_xml(xml) == xml

    def test_mask_credit_card_from_xml_with_mixed_xml(self):
        xml = '<html><head></head><CardNumber>1234567890123456</CardNumber><body></body></html>'

        assert (mask_credit_card_from_xml(xml) ==
                '<html><head></head><CardNumber>123456******3456</CardNumber><body></body></html>')
