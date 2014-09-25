# -*- coding: utf8 -*-

from __future__ import absolute_import

from braspag.consts import PAYMENT_METHODS
from .base import BraspagTestCase
from .base import ASYNC_TIMEOUT
from tornado.testing import gen_test


class GetTransactionDataTest(BraspagTestCase):

    @gen_test(timeout=ASYNC_TIMEOUT)
    def test_get_braspag_order_id_by_order(self):
        response = yield self.braspag.get_braspag_order_id_by_order(**{
            'request_id': '782a56e2-2dae-11e2-b3ee-080027d29772',
            'order_id': '7345623457234823234',
        })

        assert response.success == True
        assert response.orders[0]['braspag_transaction_id'] == u'cb3321af-627f-46ce-aa0d-05f413304c72'
        assert response.orders[0]['braspag_order_id'] == u'b1aede44-e3a7-4672-b041-069fef97aa67'
        assert response.orders[1]['braspag_transaction_id'] == u'05bc5eab-c5fc-4dce-8782-f587ebba1882'
        assert response.orders[1]['braspag_order_id'] == u'5675c820-29f5-4dd9-bc90-9ff970d0aed5'
