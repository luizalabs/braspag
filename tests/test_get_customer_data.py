# -*- coding: utf8 -*-

from __future__ import absolute_import

from decimal import Decimal
from braspag.consts import PAYMENT_METHODS
from braspag import BraspagRequest
from .base import BraspagTestCase


class GetCustomerDataTest(BraspagTestCase):

    def test_get_customer_data(self):
        BraspagRequest.authorize(self._authorize_callback,
                                 self.merchant_id,
                                 homologation=True,
                                 **{
                                     'request_id': '782a56e2-2dae-11e2-b3ee-080027d29772',
                                     'order_id': '2cf84e51-c45b-45d9-9f64-554a6e088668',
                                     'customer_id': '12345678900',
                                     'customer_name': u'José da Silva',
                                     'customer_email': 'jose123@dasilva.com.br',
                                     'transactions': [{
                                         'amount': Decimal(1000),
                                         'card_holder': 'Jose da Silva',
                                         'card_number': '0000000000000001',
                                         'card_security_code': '123',
                                         'card_exp_date': '05/2018',
                                         'save_card': True,
                                         'payment_method': PAYMENT_METHODS['Simulated']['BRL'],
                                     }],
                                 })
        self.wait(timeout=30)

    def _authorize_callback(self, response):
        assert response.success == True
        assert response.transactions[0]['amount'] == Decimal('1000.00')
        assert response.order_id == u'2cf84e51-c45b-45d9-9f64-554a6e088668'
        assert response.correlation_id == u'782a56e2-2dae-11e2-b3ee-080027d29772'
        assert response.transactions[0]['payment_method'] == 997
        assert response.transactions[0]['return_code'] == '4'
        assert response.transactions[0]['return_message'] == u'Operation Successful'
        assert response.transactions[0]['status'] == 1  # TODO: transformar em constante, tabela 13.10.1 do manual do pagador
        assert response.transactions[0]['status_message'] == 'Authorized'

        BraspagRequest.get_order_id_by_transaction_id(self._get_order_id_by_transaction_id_callback,
                                                      self.merchant_id,
                                                      homologation=True,
                                                      **{
                                                          'transaction_id': response.transactions[0]['braspag_transaction_id'],
                                                      })

    def _get_order_id_by_transaction_id_callback(self, response):
        assert response.success == True

        BraspagRequest.get_customer_data(self._get_customer_data_callback,
                                                      self.merchant_id,
                                                      homologation=True,
                                                      **{
                                                          'order_id': response.braspag_order_id,
                                                      })

    def _get_customer_data_callback(self, response):
        assert response.success == True
        assert response.customer_name == u'José da Silva'
        assert response.customer_email == 'jose123@dasilva.com.br'
        assert response.customer_identity == u'12345678900'

        self.stop()
