# -*- encoding: utf-8 -*-

import sys
import uuid
import logging
from tornado import ioloop
from datetime import timedelta

from pprint import pformat
from braspag.core import BraspagRequest
from braspag.consts import PAYMENT_METHODS

# log setup
logger = logging.getLogger('01-authorize-capture-void')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s;%(levelname)s;%(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

if len(sys.argv) > 1:
    MERCHANT_ID = sys.argv[1]
else:
    MERCHANT_ID = u'F9B44052-4AE0-E311-9406-0026B939D54B'

def authorize_callback(response):
    logger.info(pformat(response.__dict__))
    logger.info('transaction_id: %s' % response.braspag_order_id)

    # fire a capture request

#ioloop.IOLoop.instance().stop()

# Create request object
request = BraspagRequest(merchant_id=MERCHANT_ID, homologation=True)

# Authorize
logger.info('firing request')
request.authorize(
    authorize_callback,
    request_id=u'782a56e2-2dae-11e2-b3ee-080027d29772',
    order_id=uuid.uuid4(),
    customer_id=u'12345678900',
    customer_name=u'José da Silva',
    customer_email='jose123@dasilva.com.br',
    transactions=[{
        'amount': 10000,
        'card_holder': 'Jose da Silva',
        'card_number': '0000000000000001',
        'card_security_code': '123',
        'card_exp_date': '05/2018',
        'save_card': True,
        'payment_method': PAYMENT_METHODS['Simulated']['BRL'],
    }],
)
logger.info('fired')

# Capture
#response2 = request.capture(transaction_id=response.transaction_id)
#logger.info(pformat(response2.__dict__))

# Void
#response3 = request.void(transaction_id=response.transaction_id)
#logger.info(pformat(response3.__dict__))

def dot():
    print '.'
    ioloop.IOLoop.instance().add_timeout(timedelta(seconds=1), dot)

ioloop.IOLoop.instance().add_timeout(timedelta(seconds=1), dot)
ioloop.IOLoop.instance().start()
