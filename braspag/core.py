# -*- encoding: utf-8 -*-

from __future__ import absolute_import

import uuid
import logging
import unicodedata
import urlparse

import jinja2

from .utils import spaceless
from .utils import is_valid_guid
from .utils import mask_credit_card_from_xml
from .exceptions import BraspagException
from .exceptions import HTTPTimeoutError
from .response import CreditCardAuthorizationResponse
from .response import CreditCardCancelResponse
from .response import CreditCardRefundResponse
from .response import BraspagOrderIdResponse
from .response import CustomerDataResponse
from .response import CreditCardCaptureResponse
from .response import TransactionDataResponse
from .response import BraspagOrderDataResponse
from .response import AddCardResponse
from .response import InvalidateCardResponse
from .response import BraspagOrderIdDataResponse
from .consts import TransactionType
from .consts import PaymentPlanType
from xml.dom import minidom

from tornado.httpclient import HTTPRequest
from tornado.httpclient import HTTPError
from tornado import httpclient
from tornado import gen
import re


class BaseRequest(object):
    def __init__(self, merchant_id=None, homologation=False, request_timeout=10):
        self.merchant_id = merchant_id

        self.jinja_env = jinja2.Environment(
            autoescape=True,
            loader=jinja2.PackageLoader('braspag'),
        )

        self.log = logging.getLogger('braspag')
        self.http_client = httpclient.AsyncHTTPClient()

        # services
        self.query_service = '/services/pagadorQuery.asmx'
        self.transaction_service = '/webservice/pagadorTransaction.asmx'

        # timeout
        self.request_timeout = request_timeout

    @property
    def headers(self):
        """default headers to be sent on http requests"""
        return {"Content-Type": "text/xml; charset=UTF-8"}

    def _get_url(self, service):
        """Return the full URL for a given service
        """
        return urlparse.urljoin(self.url, service)

    def _get_request(self, url, body, headers=None):
        """Return an instance of HTTPRequest, with POST as the hardcoded
        HTTP method and optionally custom headers.
        The body is automatically encoded to utf-8 by HTTPRequest if it's not already.
        """
        return HTTPRequest(
            url=url,
            method='POST',
            body=body,
            request_timeout=self.request_timeout,
            headers=headers or self.headers
        )

    def _render_template(self, template_name, data_dict):
        """Render a template.
        """
        data_dict['merchant_id'] = self.merchant_id

        if not data_dict.get('request_id'):
            data_dict['request_id'] = unicode(uuid.uuid4())

        template = self.jinja_env.get_template(template_name)
        xml_request = template.render(data_dict)
        return spaceless(xml_request)

    def pretty_xml(self, payload):
        """Try and return the payload as parsed and indented XML. If we fail to parse it,
        print it as is.
        """
        try:
            body = minidom.parseString(payload.encode('utf-8')).toprettyxml(indent='  ')
        except Exception as e:
            body = payload
        return body


    @gen.coroutine
    def fetch(self, xml, url):
        masked_xml = utils.mask_credit_card(xml)
        self.log.debug('Request: %s' % self.pretty_xml(masked_xml))
        try:
            response = yield self.http_client.fetch(self._get_request(url, xml))
        except HTTPError as e:
            self.log.error('No response received.')
            raise e.code == 599 and HTTPTimeoutError(e.code, e.message) or HTTPError(e.code, e.message)

        self.log.debug('Response code: %s body: %s' % (response.code, self.pretty_xml(response.body)))
        raise gen.Return(response)


class BraspagRequest(BaseRequest):
    """
    Implements Braspag Pagador API (manual version 1.9).
    """

    def __init__(self, merchant_id=None, homologation=False, request_timeout=10):
        super(BraspagRequest, self).__init__(merchant_id, homologation, request_timeout)
        if homologation:
            self.url = 'https://homologacao.pagador.com.br'
        else:
            self.url = 'https://www.pagador.com.br'  # pragma: no cover

        # services
        self.query_service = '/services/pagadorQuery.asmx'
        self.transaction_service = '/webservice/pagadorTransaction.asmx'

    @gen.coroutine
    def _request(self, xml, query=False):
        """Make the http request to Braspag.
        """
        url = self._get_url(query and self.query_service or self.transaction_service)
        response = yield gen.Task(self.fetch, xml, url)
        raise gen.Return(response)

    @gen.coroutine
    def authorize(self, **kwargs):
        """Pre-authorize a payment.

        The arguments to the Braspag authorize API call must be passed as keyword
        arguments and are:

        :arg order_id: Order id. It will be used to indentify the
                       order later in Braspag.
        :arg customer_id: Must be user's CPF/CNPJ.
        :arg customer_name: User's full name.
        :arg customer_email: User's email address.
        :arg transactions: List of transactions to pre-authorize.
        """
        required_keys = ['order_id', 'customer_id', 'customer_name', 'customer_email', 'transactions']
        assert all([kwargs.has_key(k) for k in required_keys]), 'authorize requires all the variables: {0}'.format(required_keys)

        kwargs['transactions'] = [BraspagTransaction(**t) for t in kwargs['transactions']]
        kwargs.update(transaction_type=TransactionType.PRE_AUTHORIZATION)

        response = yield self._request(self._render_template('authorize.xml', kwargs))
        raise gen.Return(CreditCardAuthorizationResponse(response.body))

    @gen.coroutine
    def refund(self, **kwargs):
        """Refund a payment.

        The arguments to the Braspag refund API call must be passed as keyword
        arguments and are:

        :arg transation_id: Braspag's transaction ID.
        :arg amount: The amount that should be refunded, must be <= the total
                     transaction amount.
        """
        assert is_valid_guid(kwargs.get('transaction_id')), 'Transaction ID invalido'
        assert isinstance(kwargs.get('amount', None), int), 'Amount is required and must be int'

        kwargs['type'] = 'Refund'
        response = yield self._request(self._render_template('base.xml', kwargs))
        raise gen.Return(CreditCardRefundResponse(response.body))

    @gen.coroutine
    def capture(self, **kwargs):
        """Capture a give amount from a previously-authorized transaction.

        The arguments to be sent to the Braspag capture API must be passed
        as keyword arguments and are:

        :arg transaction_id: Previously authorized transaction ID.
        :arg amount: Amount to be captured, in int.
        """
        assert is_valid_guid(kwargs.get('transaction_id')), 'Transaction ID invalido'
        assert isinstance(kwargs.get('amount', None), int), 'Amount is required and must be int'

        kwargs['type'] = 'Capture'
        response = yield self._request(self._render_template('base.xml', kwargs))
        raise gen.Return(CreditCardCaptureResponse(response.body))

    @gen.coroutine
    def void(self, **kwargs):
        """Void/cancel a transaction.

        The arguments to be sent to the Braspag capture API must be passed
        as keyword arguments and are:

        :arg transaction_id: ID of the transaction to be voided.
        :arg amount: Amount of the transaction, in int.
        """
        assert is_valid_guid(kwargs.get('transaction_id')), 'Transaction ID invalido'
        assert isinstance(kwargs.get('amount', None), int), 'Amount is required and must be int'

        kwargs['type'] = 'Void'
        response = yield self._request(self._render_template('base.xml', kwargs))
        raise gen.Return(CreditCardCancelResponse(response.body))

    @gen.coroutine
    def get_order_id_by_transaction_id(self, **kwargs):
        """Get an order ID based on the received transaction ID.

        The arguments to be sent to the Braspag capture API must be passed
        as keyword arguments and are:

        :arg transaction_id: The id of the transaction.
        """
        assert is_valid_guid(kwargs.get('transaction_id')), 'Invalid Transaction ID'

        context = {
            'transaction_id': kwargs.get('transaction_id'),
            'request_id': kwargs.get('request_id')
        }

        response = yield self._request(self._render_template('get_braspag_order_id.xml',
                                                    context), query=True)
        raise gen.Return(BraspagOrderIdResponse(response.body))

    @gen.coroutine
    def get_customer_data(self, **kwargs):
        """Get the data from the customer that issued a transaction.

        The arguments to be sent to the Braspag capture API must be passed
        as keyword arguments and are:

        :arg order_id: The ID of the order the customer has placed.
        """
        assert is_valid_guid(kwargs.get('order_id')), 'Invalid Order ID'

        context = {
            'order_id': kwargs.get('order_id'),
            'request_id': kwargs.get('request_id')
        }

        response = yield self._request(self._render_template('get_customer_data.xml',
                                                    context), query=True)
        raise gen.Return(CustomerDataResponse(response.body))

    @gen.coroutine
    def get_transaction_data(self, **kwargs):
        """Get the data from a transaction.

        The arguments to be sent to the Braspag capture API must be passed
        as keyword arguments and are:

        :arg transaction_id: The id of the transaction
        """
        assert is_valid_guid(kwargs.get('transaction_id')), 'Invalid Order ID'

        context = {
            'transaction_id': kwargs.get('transaction_id'),
            'request_id': kwargs.get('request_id')
        }

        response = yield self._request(self._render_template('get_transaction_data.xml',
                                                    context), query=True)
        raise gen.Return(TransactionDataResponse(response.body))

    @gen.coroutine
    def get_order_data(self, **kwargs):
        """Get the data from an order.

        The arguments to be sent to the Braspag capture API must be passed
        as keyword arguments and are:

        :arg order_id: The id of the order
        :arg request_id: The request_id used to generate the order, optional.
        """
        assert is_valid_guid(kwargs.get('order_id')), 'Invalid Order ID'

        context = {
            'order_id': kwargs.get('order_id'),
            'request_id': kwargs.get('request_id')
        }

        response = yield self._request(self._render_template('get_braspag_order_data.xml',
                                                    context), query=True)
        raise gen.Return(BraspagOrderDataResponse(response.body))

    @gen.coroutine
    def get_braspag_order_id_by_order(self, **kwargs):
        """Get the data from an order.

        The arguments to be sent to the Braspag capture API must be passed
        as keyword arguments and are:

        :arg order_id: The id of the order
        :arg request_id: The request_id used to generate the order, optional.
        """
        assert kwargs.has_key('order_id'), 'Invalid Order ID'

        context = {
            'order_id': kwargs.get('order_id'),
            'request_id': kwargs.get('request_id')
        }

        response = yield self._request(self._render_template('get_braspag_order_id_by_order.xml',
                                                    context), query=True)
        raise gen.Return(BraspagOrderIdDataResponse(response.body))


class BraspagTransaction(object):
    """
    :arg amount: Amount to charge.
    :arg card_holder: Name printed on card.
    :arg card_number: Card number.
    :arg card_security_code: Card security code.
    :arg card_exp_date: Card expiration date.
    :arg save_card: Flag that tell to Braspag to store card number.
                    If set to True Response will return a card token.
                    *Default: False*.
    :arg card_token: Card token returned by Braspag. When used it
                     should replace *card_holder*, *card_exp_date*,
                     *card_number* and *card_security_code*.
    :arg number_of_payments: Number of payments that the amount will
                             be devided (number of months). *Default: 1*.
    :arg currency: Currency of the given amount. *Default: BRL*.
    :arg country: User's country. *Default: BRA*.
    :arg transaction_type: An integer representing one of the
                           :ref:`transaction_types`. *Default: 2*.
    :arg payment_plan: An integer representing how multiple payments should
                       be handled. *Default: 0*. See :ref:`payment_plans`.
    :arg payment_method: Integer representing one of the
                         available :ref:`payment_methods`.
    :arg soft_descriptor: Order description to be shown on the customer
                          card statement. Maximum of 13 characters.
    """

    def __init__(self, **kwargs):
        assert any((kwargs.get('card_number'),
                    kwargs.get('card_token'))),\
            'card_number ou card_token devem ser fornecidos'

        if kwargs.get('card_number'):
            kwargs['card_token'] = None
            card_keys = (
                'card_holder',
                'card_security_code',
                'card_exp_date',
                'card_number',
            )
            assert all(kwargs.has_key(key) for key in card_keys), \
                (u'Transações com Cartão de Crédito exigem os '
                 u'parametros: {0}'.format(', '.join(card_keys)))

        if not kwargs.get('number_of_payments'):
            kwargs['number_of_payments'] = 1

        try:
            number_of_payments = int(kwargs.get('number_of_payments'))
        except ValueError:
            raise BraspagException('Number of payments must be int.')

        if not kwargs.get('payment_plan'):
            if number_of_payments > 1:
                kwargs['payment_plan'] = PaymentPlanType.INSTALLMENTS_BY_ESTABLISHMENT
            else:
                kwargs['payment_plan'] = PaymentPlanType.NO_INSTALLMENTS

        if not kwargs.get('currency'):
            kwargs['currency'] = 'BRL'

        if not kwargs.get('country'):
            kwargs['country'] = 'BRA'

        if not kwargs.get('transaction_type'):
            kwargs['transaction_type'] = TransactionType.PRE_AUTHORIZATION

        if kwargs.get('save_card', False):
            kwargs['save_card'] = 'true'
        else:
            kwargs['save_card'] = 'false'

        soft_desc = ''
        if kwargs.get('soft_descriptor'):
            # only keep first 13 chars
            soft_desc = kwargs.get('soft_descriptor')[:13]

            # Replace special chars by ascii
            soft_desc = unicodedata.normalize('NFKD', soft_desc)
            soft_desc = soft_desc.encode('ascii', 'ignore')

        kwargs['soft_descriptor'] = soft_desc

        for attr in ('amount', 'card_holder', 'card_number', 'card_security_code', 'card_token',
                     'card_exp_date', 'number_of_payments', 'currency', 'country', 'payment_plan',
                     'payment_method', 'soft_descriptor', 'save_card', 'transaction_type'):
            if attr == 'amount':
                assert isinstance(kwargs[attr], int), 'amount must be int'
            setattr(self, attr, kwargs[attr])


class ProtectedCardRequest(BaseRequest):
    """
    Implements Braspag Cartão Protegido API (manual version 2.1).
    """

    def __init__(self, merchant_id=None, homologation=False, request_timeout=10):
        super(ProtectedCardRequest, self).__init__(merchant_id, homologation, request_timeout)
        if homologation:
            self.url = 'https://homologacao.braspag.com.br'
            self.protected_card_service = '/services/v2/testenvironment/cartaoprotegido.asmx'
        else:
            self.url = 'https://cartaoprotegido.braspag.com.br'
            self.protected_card_service = '/services/v2/cartaoprotegido.asmx'

    @gen.coroutine
    def _request(self, xml):
        """Make the http request to Braspag.
        """
        url = self._get_url(self.protected_card_service)
        response = yield gen.Task(self.fetch, xml, url)
        raise gen.Return(response)

    @gen.coroutine
    def add_card(self, **kwargs):
        """Add a card to JustClick

        The arguments to the Cartão Protegido API call must be passed as keyword
        arguments and are:

        :arg customer_identification
        :arg customer_name
        :arg card_holder
        :arg card_number
        :arg card_expiration
        :arg just_click_alias
        """
        required_keys = ['customer_identification', 'customer_name', 'card_holder', 'card_number', 'card_expiration']
        assert all([kwargs.has_key(k) for k in required_keys]), 'add_card requires all the variables: {0}'.format(required_keys)

        response = yield self._request(self._render_template('add_card.xml', kwargs))
        raise gen.Return(AddCardResponse(response.body))

    @gen.coroutine
    def invalidate_card(self, **kwargs):
        """Invalidate a card to JustClick

        The arguments to the Cartão Protegido API call must be passed as keyword
        arguments and are:

        :arg just_click_key
        :arg just_click_alias
        """
        assert kwargs.has_key('just_click_key'), 'invalidate_card requires just_click_key variable'

        response = yield self._request(self._render_template('invalidate_card.xml', kwargs))
        raise gen.Return(InvalidateCardResponse(response.body))
