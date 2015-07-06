# -*- coding: utf8 -*-

from __future__ import absolute_import

from braspag.utils import to_bool
from braspag.utils import to_int
from braspag.utils import mask_credit_card_from_xml
from braspag.utils import is_valid_guid
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

    def test_is_valid_guid(self):
        self.assertTrue(is_valid_guid('555d97f7-92ab-4907-a8d0-f2ba51afe470'))
        self.assertTrue(is_valid_guid('937f36f1-8b8d-427e-83f1-02faadcdf6eb'))
        self.assertTrue(is_valid_guid('e3e8699c-7b4d-48f3-bd40-b75eddef0ab5'))
        self.assertTrue(is_valid_guid('a220b799-2734-4760-9a17-2d1f9f77328b'))
        self.assertTrue(is_valid_guid('514b9516-0aad-4fef-a1ad-9894cc9c925e'))
        self.assertTrue(is_valid_guid('92209184-7fd6-4272-b1dc-d60f5590972d'))
        self.assertTrue(is_valid_guid('a2f27876-c52e-4062-9a37-bc513239af60'))
