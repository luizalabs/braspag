# -*- coding: utf8 -*-

from __future__ import absolute_import

from braspag.consts import PAYMENT_METHODS
from braspag.exceptions import BraspagException
from braspag.exceptions import HTTPTimeoutError
from .base import BraspagTestCase
from .base import ASYNC_TIMEOUT
from tornado.testing import gen_test


class ProtectedCardTest(BraspagTestCase):

    @gen_test(timeout=ASYNC_TIMEOUT)
    def test_add_card(self):
        response = yield self.protected_card.add_card(**{
            'customer_name': u'José da Silva',
            'card_holder': 'Jose da Silva',
            'card_number': '0000000000000001',
            'card_expiration': '05/2018',
            'customer_identification': 1,
        })
        assert response.success == True

    @gen_test(timeout=ASYNC_TIMEOUT)
    def test_add_card_without_required_field(self):
        response = yield self.protected_card.add_card(**{
            'customer_name': u'José da Silva',
            'card_holder': 'Jose da Silva',
            'card_number': '0000000000000001',
            'just_click_alias': 'XPTO',
            'card_expiration': '05/2018',
            'customer_identification': 1,
        })
        assert response.success == False
        assert response.errors[0]['error_code'] == u'749'
        assert response.errors[0]['error_message'] == u'JustClick alias already exists'

    @gen_test(timeout=ASYNC_TIMEOUT)
    def test_invalidate_card(self):
        response = yield self.protected_card.add_card(**{
            'customer_name': u'José da Silva',
            'card_holder': 'Jose da Silva',
            'card_number': '0000000000000001',
            'card_expiration': '05/2018',
            'customer_identification': 1,
        })
        assert response.success == True

        response = yield self.protected_card.invalidate_card(**{
            'just_click_key': response.just_click_key
        })
        assert response.success == True
        