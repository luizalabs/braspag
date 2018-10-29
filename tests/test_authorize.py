# -*- coding: utf8 -*-
from __future__ import absolute_import

from tornado.testing import gen_test

from braspag.consts import PAYMENT_METHODS
from braspag.exceptions import BraspagException, HTTPTimeoutError

from .base import BraspagTestCase
from .vcrutils import replay


class AuthorizeTest(BraspagTestCase):

    @gen_test
    @replay
    def test_authorize(self):
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
             },{
                 'amount': 190099,
                 'card_holder': u'João Silveira',
                 'card_number': '9000000000000001',
                 'card_security_code': '432',
                 'card_exp_date': '05/2020',
                 'save_card': False,
                 'payment_method': PAYMENT_METHODS['Simulated']['BRL'],
                 'soft_descriptor': u'Sax Alto Thailandês',
             }]
            })

        assert response.success == True
        assert response.order_id == u'2cf84e51-c45b-45d9-9f64-554a6e088668'
        assert response.correlation_id == u'782a56e2-2dae-11e2-b3ee-080027d29772'
        assert response.transactions[0]['amount'] == 100000
        assert response.transactions[0]['payment_method'] == 997
        assert response.transactions[0]['return_code'] == '4'
        assert response.transactions[0]['return_message'] == u'Operation Successful'
        assert response.transactions[0]['status'] == 1  # TODO: transformar em constante, tabela 13.10.1 do manual do pagador
        assert response.transactions[0]['status_message'] == 'Authorized'
        assert response.transactions[0]['masked_credit_card_number'] == u'000000******0001'

        assert response.transactions[1]['amount'] == 190099
        assert response.transactions[1]['payment_method'] == 997
        assert response.transactions[1]['return_code'] == '4'
        assert response.transactions[1]['return_message'] == u'Operation Successful'
        assert response.transactions[1]['status'] == 1  # TODO: transformar em constante, tabela 13.10.1 do manual do pagador
        assert response.transactions[1]['status_message'] == 'Authorized'
        assert response.transactions[1]['masked_credit_card_number'] == u'900000******0001'

    @gen_test
    @replay
    def test_authorize_with_card_token(self):
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
             },{
                 'amount': 190099,
                 'card_holder': u'João Silveira',
                 'card_number': '9000000000000001',
                 'card_security_code': '432',
                 'card_exp_date': '05/2020',
                 'save_card': True,
                 'payment_method': PAYMENT_METHODS['Simulated']['BRL'],
                 'soft_descriptor': u'Sax Alto Thailandês',
             }],
         })

        assert response.success == True
        assert response.transactions[0]['return_code'] == '4'
        assert response.transactions[0]['return_message'] == u'Operation Successful'
        assert response.transactions[0]['status'] == 1
        assert response.transactions[0]['status_message'] == 'Authorized'

        card_token = response.transactions[0]['card_token']
        response = yield self.braspag.authorize(**{
             'request_id': '782a56e2-2dae-11e2-b3ee-080027d29772',
             'order_id': '2cf84e51-c45b-45d9-9f64-554a6e088668',
             'customer_id': '12345678900',
             'customer_name': u'José da Silva',
             'customer_email': 'jose123@dasilva.com.br',
             'transactions': [{
                 'amount': 100000,
                 'card_token': card_token,
                 'soft_descriptor': u'Sax Alto Chinês',
                 'card_holder': '',
                 'card_number': '',
                 'card_security_code': '',
                 'card_exp_date': '',
                 'payment_method': PAYMENT_METHODS['Simulated']['BRL'],
             }],
         })

        assert response.success == True
        assert response.transactions[0]['return_code'] == '4'
        assert response.transactions[0]['return_message'] == u'Operation Successful'
        assert response.transactions[0]['status'] == 1
        assert response.transactions[0]['status_message'] == 'Authorized'

    @gen_test
    @replay
    def test_wrong_number_of_payments(self):
        with self.assertRaises(BraspagException):
            response = yield self.braspag.authorize(**{
                'request_id': '782a56e2-2dae-11e2-b3ee-080027d29772',
                'order_id': '2cf84e51-c45b-45d9-9f64-554a6e088668',
                'customer_id': '12345678900',
                'customer_name': u'José da Silva',
                'customer_email': 'jose123@dasilva.com.br',
                'transactions': [{
                    'amount': 1000,
                    'card_holder': 'Jose da Silva',
                    'card_number': '0000000000000001',
                    'card_security_code': '123',
                    'card_exp_date': '05/2018',
                    'save_card': True,
                    'payment_method': PAYMENT_METHODS['Simulated']['BRL'],
                    'soft_descriptor': u'Sax Alto Chinês',
                    'number_of_payments': u'foobar',
                }],
            })

    @gen_test
    @replay
    def test_authorize_timeout(self):
        self.braspag.request_timeout = 0.000001
        with self.assertRaises(HTTPTimeoutError):
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
                 },{
                     'amount': 190099,
                     'card_holder': u'João Silveira',
                     'card_number': '9000000000000001',
                     'card_security_code': '432',
                     'card_exp_date': '05/2020',
                     'save_card': False,
                     'payment_method': PAYMENT_METHODS['Simulated']['BRL'],
                     'soft_descriptor': u'Sax Alto Thailandês',
                 }],
             })
