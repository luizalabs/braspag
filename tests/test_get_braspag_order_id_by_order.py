# -*- coding: utf8 -*-

from __future__ import absolute_import

from braspag.consts import PAYMENT_METHODS
from .base import BraspagTestCase
from tornado.testing import gen_test


class GetTransactionDataTest(BraspagTestCase):

    @gen_test
    def test_get_braspag_order_id_by_order(self):
        response = yield self.braspag.authorize(**{
            'request_id': '782a56e2-2dae-11e2-b3ee-080027d29772',
            'order_id': '2cf84e51-c45b-45d9-9f64-554a6e088668',
            'customer_id': '12345678900',
            'customer_name': u'José da Silva',
            'customer_email': 'jose123@dasilva.com.br',
            'transactions': [{
                'amount': 100000,
                'card_holder': 'Jose da Silva',
                'card_number': '0000000000000001',
                'card_security_code': '123',
                'card_exp_date': '05/2018',
                'save_card': True,
                'payment_method': PAYMENT_METHODS['Simulated']['BRL'],
                'soft_descriptor': u'Sax Alto Chinês',
                }],
            })
        assert response.success == True
        order_id = response.orders[0]['order_id']

        response = yield self.braspag.get_braspag_order_id_by_order(**{
            'request_id': '782a56e2-2dae-11e2-b3ee-080027d29772',
            'order_id': '7345623457234823234',
        })

        assert response.success == True
        assert response.orders[0]['braspag_transaction_id'] == braspag_transaction_id
        #assert response.orders[0]['braspag_transaction_id'] == u'cb3321af-627f-46ce-aa0d-05f413304c72'
        #assert response.orders[0]['braspag_order_id'] == u'b1aede44-e3a7-4672-b041-069fef97aa67'
        #assert response.orders[1]['braspag_transaction_id'] == u'3e766fbb-3d36-4049-9018-893b97dc5643'
        #assert response.orders[1]['braspag_order_id'] == u'b5aa9eff-55d4-4cc0-9fbc-6b237920ded0'
