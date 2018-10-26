# -*- coding: utf8 -*-
from __future__ import absolute_import

from tornado.testing import gen_test

from braspag.consts import PAYMENT_METHODS
from braspag.exceptions import BraspagException, HTTPTimeoutError

from .base import BraspagTestCase
from .vcrutils import replay


class ProtectedCardTest(BraspagTestCase):

    @gen_test
    @replay
    def test_add_card(self):
        response = yield self.protected_card.add_card(**{
            'customer_name': u'José da Silva',
            'card_holder': 'Jose da Silva',
            'card_number': '0000000000000001',
            'card_expiration': '05/2018',
            'customer_identification': 1,
        })
        assert response.success == True

    @gen_test
    @replay
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
        assert (
            response.errors[0]['error_message'] ==
            u'JustClick alias already exists'
        )

    @gen_test
    @replay
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

    @gen_test
    @replay
    def test_add_card_and_get_card(self):
        response = yield self.protected_card.add_card(**{
            'customer_name': u'José da Silva',
            'card_holder': 'Jose da Silva',
            'card_number': '1000000000000001',
            'card_expiration': '05/2018',
            'customer_identification': 1,
        })
        assert response.success == True

        response = yield self.protected_card.get_card(**{
            'just_click_key': response.just_click_key
        })
        assert response.success == True
        assert response.card_expiration == '05/2018'
        assert response.card_number == '1000000000000001'
