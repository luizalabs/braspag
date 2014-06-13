# -*- coding: utf8 -*-

from __future__ import absolute_import

import codecs

from mock import MagicMock

from decimal import Decimal
from datetime import datetime

from braspag.utils import spaceless
from braspag.consts import PAYMENT_METHODS

from base import BraspagTestCase


ORDER_DATA = 'tests/data/get_order_data_request.xml'


class OrderDataTest(BraspagTestCase):

    def setUp(self):
        super(OrderDataTest, self).setUp()
        self.data_dict = {
            'request_id': '782a56e2-2dae-11e2-b3ee-080027d29772',
            'order_id':   '5876143c-7a54-404d-ba5a-51a299e51cf7',
        }

        with open('tests/data/get_order_data_response.xml') as response:
            self.braspag._request.return_value = response.read()
        self.response = self.braspag.get_order_data(**self.data_dict)

    def test_render_order_data_template(self):
        self.braspag._render_template = MagicMock(name='_render_template')
        self.data_dict = {
            'request_id': '782a56e2-2dae-11e2-b3ee-080027d29772',
            'order_id':   '5876143c-7a54-404d-ba5a-51a299e51cf7',
        }
        
        response = self.braspag.get_order_data(**self.data_dict)

    def test_webservice_request(self):
        self.data_dict = {
            'request_id': '782a56e2-2dae-11e2-b3ee-080027d29772',
            'order_id':   '5876143c-7a54-404d-ba5a-51a299e51cf7',
        }
        response = self.braspag.get_order_data(**self.data_dict)
        with codecs.open(ORDER_DATA, encoding='utf-8') as xml:
            self.braspag._request.assert_called_with(spaceless(xml.read()), query=True)

    def test_amount(self):
        assert self.response.transactions[0]['amount'] == Decimal('2599.99')

    def test_auth_code(self):
        assert self.response.transactions[0]['authorization_code'] == u'20140605102307824'

    def test_acquirer_transaction(self):
        assert self.response.transactions[0]['acquirer_transaction_id'] == u'0605102307824'

    def test_correlation_id(self):
        assert self.response.correlation_id == u'782a56e2-2dae-11e2-b3ee-080027d29772'

    def test_payment_method(self):
        assert self.response.transactions[0]['payment_method'] == 997

    def test_transaction_type(self):
        assert self.response.transactions[0]['transaction_type'] == 2

    def test_received_date(self):
        assert self.response.transactions[0]['received_date'] == datetime(2014, 6, 5, 10, 23, 7)

    def test_captured_date(self):
        assert self.response.transactions[0]['captured_date'] == datetime(2014, 6, 5, 10, 23, 7)

    def test_status(self):
        assert self.response.transactions[0]['status'] == 2

    def test_status_message(self):
        assert self.response.transactions[0]['status_message'] == 'Authorized'

    def test_success(self):
        assert self.response.success == True

    def test_transaction_id(self):
        assert self.response.transactions[0]['braspag_transaction_id'] == u'c4d3c969-dc95-4310-9a98-a4e80327afb8'

    def test_card_token(self):
        assert self.response.transactions[0]['card_token'] == u'eb57948c-018c-4713-ba89-c10a566906fb'

    def test_card_token(self):
        assert self.response.transactions[0]['proof_of_sale'] == u'2307824'
        