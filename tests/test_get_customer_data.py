# -*- coding: utf8 -*-

from __future__ import absolute_import

from braspag.consts import PAYMENT_METHODS
from .base import BraspagTestCase
from .base import ASYNC_TIMEOUT
from tornado.testing import gen_test


class GetCustomerDataTest(BraspagTestCase):

    @gen_test(timeout=ASYNC_TIMEOUT)
    def test_get_customer_data(self):
        response = yield self.braspag.authorize(**{
                                     'request_id': '782a56e2-2dae-11e2-b3ee-080027d29772',
                                     'order_id': '2cf84e51-c45b-45d9-9f64-554a6e088668',
                                     'customer_id': '12345678900',
                                     'customer_name': u'José da Silva',
                                     'customer_email': 'jose123@dasilva.com.br',
                                     'transactions': [{
                                         'amount': float(1000),
                                         'card_holder': 'Jose da Silva',
                                         'card_number': '0000000000000001',
                                         'card_security_code': '123',
                                         'card_exp_date': '05/2018',
                                         'save_card': True,
                                         'payment_method': PAYMENT_METHODS['Simulated']['BRL'],
                                     }],
                                 })

        assert response.success == True
        assert response.transactions[0]['amount'] == float('1000.00')
        assert response.order_id == u'2cf84e51-c45b-45d9-9f64-554a6e088668'
        assert response.correlation_id == u'782a56e2-2dae-11e2-b3ee-080027d29772'
        assert response.transactions[0]['payment_method'] == 997
        assert response.transactions[0]['return_code'] == '4'
        assert response.transactions[0]['return_message'] == u'Operation Successful'
        assert response.transactions[0]['status'] == 1  # TODO: transformar em constante, tabela 13.10.1 do manual do pagador
        assert response.transactions[0]['status_message'] == 'Authorized'

        response = yield self.braspag.get_order_id_by_transaction_id(**{
                                                          'transaction_id': response.transactions[0]['braspag_transaction_id'],
                                                      })

        assert response.success == True

        response = yield self.braspag.get_customer_data(**{
                                                          'order_id': response.braspag_order_id,
                                                      })

        assert response.success == True
        assert response.customer_name == u'José da Silva'
        assert response.customer_email == 'jose123@dasilva.com.br'
        assert response.customer_identity == u'12345678900'
