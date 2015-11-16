# -*- coding: utf8 -*-

from __future__ import absolute_import

from datetime import datetime
from braspag.utils import to_bool
from braspag.utils import to_int
from braspag.utils import to_date
from braspag.utils import mask_card_data_from_xml
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

        assert to_date('11/15/2015 12:19:44 AM') == datetime(2015, 11, 15, 0, 19, 44)
        assert to_date('11/14/2015 01:57:23 PM') == datetime(2015, 11, 14, 13, 57, 23)
        with self.assertRaises(TypeError):
            to_date(None)

    def test_mask_card_data_from_xml_with_existing_card_number(self):
        xml = '<CardNumber>1234567890123456</CardNumber>'

        assert (mask_card_data_from_xml(xml) ==
                '<CardNumber>123456******3456</CardNumber>')

    def test_mask_card_data_from_xml_with_non_existing_card_number(self):
        xml = '<html><head></head><body></body></html>'

        assert mask_card_data_from_xml(xml) == xml

    def test_mask_card_data_from_xml_with_mixed_xml(self):
        xml = '<html><head></head><CardNumber>1234567890123456</CardNumber><body></body></html>'

        assert (mask_card_data_from_xml(xml) ==
                '<html><head></head><CardNumber>123456******3456</CardNumber><body></body></html>')

    def test_mask_card_data_from_xml_with_existing_cvv(self):
        xml = '<CardSecurityCode>123</CardSecurityCode>'

        assert (mask_card_data_from_xml(xml) ==
                '<CardSecurityCode>***</CardSecurityCode>')

    def test_mask_card_data_from_xml_with_non_existing_cvv(self):
        xml = '<html><head></head><body></body></html>'

        assert mask_card_data_from_xml(xml) == xml

    def test_mask_card_data_from_xml_with_mixed_xml_with_cvv(self):
        xml = '<html><head></head><CardSecurityCode>1234</CardSecurityCode><body></body></html>'

        assert (mask_card_data_from_xml(xml) ==
                '<html><head></head><CardSecurityCode>****</CardSecurityCode><body></body></html>')

    def test_mask_card_data_from_xml_with_existing_card_number_and_cvv(self):
        xml = '<CardNumber>1234567890123456</CardNumber><CardSecurityCode>123</CardSecurityCode>'

        assert (mask_card_data_from_xml(xml) ==
                '<CardNumber>123456******3456</CardNumber><CardSecurityCode>***</CardSecurityCode>')

    def test_is_valid_guid(self):
        self.assertTrue(is_valid_guid('555d97f7-92ab-4907-a8d0-f2ba51afe470'))
        self.assertTrue(is_valid_guid('937f36f1-8b8d-427e-83f1-02faadcdf6eb'))
        self.assertTrue(is_valid_guid('e3e8699c-7b4d-48f3-bd40-b75eddef0ab5'))
        self.assertTrue(is_valid_guid('a220b799-2734-4760-9a17-2d1f9f77328b'))
        self.assertTrue(is_valid_guid('514b9516-0aad-4fef-a1ad-9894cc9c925e'))
        self.assertTrue(is_valid_guid('92209184-7fd6-4272-b1dc-d60f5590972d'))
        self.assertTrue(is_valid_guid('a2f27876-c52e-4062-9a37-bc513239af60'))
