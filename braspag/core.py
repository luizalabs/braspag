# -*- encoding: utf-8 -*-

from __future__ import absolute_import

import uuid
import logging
import unicodedata
import urlparse

import jinja2

from .utils import spaceless
from .utils import is_valid_guid
from .utils import convert_amount
from .utils import method_must_be_redesigned
from .exceptions import BraspagHttpResponseException
from .response import CreditCardAuthorizationResponse
from .response import BilletResponse
from .response import BilletDataResponse
from .response import CreditCardCancelResponse
from .response import CreditCardRefundResponse
from .response import BraspagOrderIdResponse
from .response import CustomerDataResponse
from .response import CreditCardCaptureResponse
from .response import TransactionDataResponse
from decimal import Decimal
from decimal import InvalidOperation
from xml.dom import minidom

from tornado.httpclient import HTTPRequest
from tornado import ioloop
from tornado import httpclient


class TransactionType(object):
    PRE_AUTHORIZATION = '1'
    AUTOMATIC_CAPTURE = '2'
    PRE_AUTHORIZATION_WITH_AUTHENTICATION = '3'
    AUTOMATIC_CAPTURE_WITH_AUTHENTICATION = '4'
    RECURRENT_PRE_AUTHORIZATION = '5'
    RECURRENT_AUTOMATIC_CAPTURE = '6'


class BraspagRequest(object):
    """
    Implements Braspag Pagador API (manual version 1.9).
    """

    def __init__(self, merchant_id=None, homologation=False):
        if homologation:
            self.url = 'https://homologacao.pagador.com.br'
        else:
            self.url = 'https://www.pagador.com.br'

        self.merchant_id = merchant_id

        self.jinja_env = jinja2.Environment(
            autoescape=True,
            loader=jinja2.PackageLoader('braspag'),
        )

        self.log = logging.getLogger('braspag')
        self.http_client = httpclient.AsyncHTTPClient()

        # user callbacks
        self.user_authorize_callback = None
        self.user_capture_callback = None
        self.user_void_callback = None
        self.user_refund_callback = None
        self.get_order_id_by_transaction_id_callback = None
        self.get_customer_data_callback = None
        self.get_transaction_data_callback = None

        # services
        self.query_service = '/services/pagadorQuery.asmx'
        self.transaction_service = '/webservice/pagadorTransaction.asmx'

    @property
    def headers(self):
        """default heders to be sent on http requests"""
        return { "Content-Type": "text/xml; charset=UTF-8" }

    def _get_url(self, service):
        """Return the full URL for a given service
        """
        return urlparse.urljoin(self.url, service)

    def _get_request(self, url, body, headers=None):
        """Return an instance of HTTPRequest, with POST as the hardcoded
        HTTP method and optionally custom headers.
        The payload is in 'body' variable and HTTPRequest automatically
        encodes it to utf-8 is it's not already.
        """
        return HTTPRequest(url=url, method='POST',
                           body=body, headers=headers and headers or self.headers)

    def _request(self, callback, xml, query=False):
        """Actually send the HTTP request, note that we don't return anything here
        since it's an asynchronous request.
        """
        url = self._get_url(query and self.query_service or self.transaction_service)
        logging.debug(minidom.parseString(xml.encode('utf-8')).toprettyxml(indent='  '))
        self.http_client.fetch(self._get_request(url, xml), callback)

    def _authorize_callback(self, response):
        """Callback that's called when we get a response from braspag.
        Once called, we wrap the response in the needed response class,
        in our case CreditCardAuthorizationResponse() and call the
        user callback with it as an argument.
        """
        logging.debug(u'response: {0}'.format(response.body))
        self.user_authorize_callback(CreditCardAuthorizationResponse(response.body))

    @classmethod
    def authorize(klass, user_callback, merchant_id, homologation=False, **kwargs):
        """Pre-authorize a payment. This is a class method that instantiates a
        BraspagRequest class with whatever (merchant_id, homologation) are passed
        in.
        The user _must_ supply a valid callback as the user_callback argument that'll
        be called when we get a response from the Braspag API.

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
        assert callable(user_callback), 'You must pass in a method or function as first argument'

        instance = klass(merchant_id, homologation=homologation)
        instance.user_authorize_callback = user_callback

        kwargs['transactions'] = [BraspagTransaction(**t) for t in kwargs['transactions']]
        kwargs.update(transaction_type=TransactionType.PRE_AUTHORIZATION)

        instance._request(instance._authorize_callback,
                      instance._render_template('authorize.xml', kwargs))

    def _refund_callback(self, response):
        """Local callback that's called when we get a response from a refund
        Braspag API call.
        This callback just instantiate a CreditCardRefundResponse with the
        response it received from Braspag and call the user's callback with
        it as the only argument.
        """
        logging.debug(u'response: {0}'.format(response.body))
        self.user_refund_callback(CreditCardRefundResponse(response.body))

    @classmethod
    def refund(klass, user_callback, merchant_id, homologation=False, **kwargs):
        """Refund a payment. This is a class method that instantiates a
        BraspagRequest class with whatever (merchant_id, homologation) are passed
        in.
        The user _must_ supply a valid callback as the user_callback argument that'll
        be called when we get a response from the Braspag API.

        The arguments to the Braspag refund API call must be passed as keyword
        arguments and are:

        :arg transation_id: Braspag's transaction ID.
        :arg amount: The amount that should be refunded, must be <= the total
                     transaction amount.
        """
        assert is_valid_guid(kwargs.get('transaction_id')), 'Transaction ID invalido'
        assert isinstance(kwargs.get('amount', None), Decimal), 'Amount is required and must be Decimal'
        assert callable(user_callback), 'You must pass in a method or function as first argument'

        instance = klass(merchant_id, homologation=homologation)
        instance.user_refund_callback = user_callback
        kwargs['type'] = 'Refund'
        instance._request(instance._refund_callback, instance._render_template('base.xml', kwargs))

    def _capture_callback(self, response):
        """Local callback that's called when we get a response from a capture
        Braspag API call.
        This callback just instantiate a CreditCardCaptureResponse with the
        response it received from Braspag and call the user's callback with
        it as the only argument.
        """
        logging.debug(u'capture response: {0}'.format(response.body))
        self.user_capture_callback(CreditCardCaptureResponse(response.body))

    @classmethod
    def capture(klass, user_callback, merchant_id, homologation=False, **kwargs):
        """Capture a give amount from a previously-authorized transaction.

        As with all the currently implemented class-based methods, the user
        _must_ supply a valid callback as the user_callback argument that'll
        be called when we get a response from the Braspag API.

        The arguments to be sent to the Braspag capture API must be passed
        as keyword arguments and are:

        :arg transaction_id: Previously authorized transaction ID.
        :arg amount: Amount to be captured, in Decimal.
        """
        assert is_valid_guid(kwargs.get('transaction_id')), 'Transaction ID invalido'
        assert isinstance(kwargs.get('amount', None), Decimal), 'Amount is required and must be Decimal'
        assert callable(user_callback), 'You must pass in a method or function as first argument'

        instance = klass(merchant_id, homologation=homologation)
        instance.user_capture_callback = user_callback
        kwargs['type'] = 'Capture'
        instance._request(instance._capture_callback, instance._render_template('base.xml', kwargs))

    def _void_callback(self, response):
        """Local callback that's called when we get a response from a void
        Braspag API call.
        This callback instantiates a CreditCardCancelResponse with the
        response it received from Braspag and call the user's callback with
        it as the only argument.
        """
        logging.debug(u'response: {0}'.format(response.body))
        self.user_void_callback(CreditCardCancelResponse(response.body))

    @classmethod
    def void(klass, user_callback, merchant_id, homologation=False, **kwargs):
        """Void/cancel a transaction.

        As with all the currently implemented class-based methods, the user
        _must_ supply a valid callback as the user_callback argument that'll
        be called when we get a response from the Braspag API.

        The arguments to be sent to the Braspag capture API must be passed
        as keyword arguments and are:

        :arg transaction_id: ID of the transaction to be voided.
        :arg amount: Amount of the transaction, in Decimal.
        """
        assert is_valid_guid(kwargs.get('transaction_id')), 'Transaction ID invalido'
        assert isinstance(kwargs.get('amount', None), Decimal), 'Amount is required and must be Decimal'
        assert callable(user_callback), 'You must pass in a method or function as first argument'

        instance = klass(merchant_id, homologation=homologation)
        instance.user_void_callback = user_callback
        kwargs['type'] = 'Void'
        instance._request(instance._void_callback, instance._render_template('base.xml', kwargs))

    def _get_order_id_by_transaction_id_callback(self, response):
        """Local callback that's called when we get a response from a query
        Braspag API call.
        This callback instantiates a BraspagOrderIdResponse with the
        response it received from Braspag and call the user's callback with
        it as the only argument.
        """
        logging.debug(u'response: {0}'.format(response.body))
        self.get_order_id_by_transaction_id_callback(BraspagOrderIdResponse(response.body))

    @classmethod
    def get_order_id_by_transaction_id(klass, user_callback, merchant_id, homologation=False, **kwargs):
        """Get an order ID based on the received transaction ID.

        As with all the currently implemented class-based methods, the user
        _must_ supply a valid callback as the user_callback argument that'll
        be called when we get a response from the Braspag API.

        The arguments to be sent to the Braspag capture API must be passed
        as keyword arguments and are:

        :arg transaction_id: The id of the transaction.
        """
        assert is_valid_guid(kwargs.get('transaction_id')), 'Invalid Transaction ID'
        assert callable(user_callback), 'You must pass in a method or function as first argument'

        instance = klass(merchant_id, homologation=homologation)
        instance.get_order_id_by_transaction_id_callback = user_callback

        context = {
            'transaction_id': kwargs.get('transaction_id'),
            'request_id': kwargs.get('request_id')
        }

        instance._request(instance._get_order_id_by_transaction_id_callback,
                          instance._render_template('get_braspag_order_id.xml',
                                                    context), query=True)

    def _get_customer_data_callback(self, response):
        """Local callback that's called when we get a response from a query
        Braspag API call.
        This callback instantiates a CustomerDataResponse with the
        response it received from Braspag and call the user's callback with
        it as the only argument.
        """
        logging.debug('response: {0}'.format(response.body))
        self.get_customer_data_callback(CustomerDataResponse(response.body))

    @classmethod
    def get_customer_data(klass, user_callback, merchant_id, homologation=False, **kwargs):
        """Get the data from the customer that issued a transaction.

        As with all the currently implemented class-based methods, the user
        _must_ supply a valid callback as the user_callback argument that'll
        be called when we get a response from the Braspag API.

        The arguments to be sent to the Braspag capture API must be passed
        as keyword arguments and are:

        :arg order_id: The ID of the order the customer has placed.
        """
        assert is_valid_guid(kwargs.get('order_id')), 'Invalid Order ID'
        assert callable(user_callback), 'You must pass in a method or function as first argument'

        instance = klass(merchant_id, homologation=homologation)
        instance.get_customer_data_callback = user_callback

        context = {
            'order_id': kwargs.get('order_id'),
            'request_id': kwargs.get('request_id')
        }

        instance._request(instance._get_customer_data_callback,
                          instance._render_template('get_customer_data.xml',
                                                    context), query=True)

    def _get_transaction_data_callback(self, response):
        """Local callback that's called when we get a response from a query
        Braspag API call.
        This callback instantiates a TransactionDataResponse with the
        response it received from Braspag and call the user's callback with
        it as the only argument.
        """
        logging.debug('response: {0}'.format(response.body))
        self.get_transaction_data_callback(TransactionDataResponse(response.body))

    @classmethod
    def get_transaction_data(klass, user_callback, merchant_id, homologation=False, **kwargs):
        """Get the data from a transaction.

        As with all the currently implemented class-based methods, the user
        _must_ supply a valid callback as the user_callback argument that'll
        be called when we get a response from the Braspag API.

        The arguments to be sent to the Braspag capture API must be passed
        as keyword arguments and are:

        :arg transaction_id: The id of the transaction
        """
        assert is_valid_guid(kwargs.get('transaction_id')), 'Invalid Order ID'

        instance = klass(merchant_id, homologation=homologation)
        instance.get_transaction_data_callback = user_callback

        context = {
            'transaction_id': kwargs.get('transaction_id'),
            'request_id': kwargs.get('request_id')
        }

        instance._request(instance._get_transaction_data_callback,
                          instance._render_template('get_transaction_data.xml',
                                                    context), query=True)

    def _render_template(self, template_name, data_dict):
        """Helper to render a template.
        """
        data_dict['merchant_id'] = self.merchant_id

        if data_dict.has_key('amount'):
            data_dict.update(amount=convert_amount(data_dict['amount']))

        if not data_dict.get('request_id'):
            data_dict['request_id'] = unicode(uuid.uuid4())

        template = self.jinja_env.get_template(template_name)
        xml_request = template.render(data_dict)
        #self.log.debug(xml_request)
        return spaceless(xml_request)

    @method_must_be_redesigned
    def issue_billet(self, **kwargs):
        """DEPRECATED -- must be redesigned to work asynchronously.

        All arguments supplied to this method must be keyword arguments.

        :arg order_id: Order id. It will be used to indentify the
                       order later in Braspag.
        :arg customer_id: Must be user's CPF/CNPJ.
        :arg customer_name: User's full name.
        :arg customer_email: User's email address.
        :arg amount: Amount to charge.
        :arg currency: Currency of the given amount. *Default: BRL*.
        :arg country: User's country. *Default: BRA*.
        :arg payment_method: Payment method code
        :arg soft_descriptor: Order description to be shown on the customer
                              billet. Maximum of 13 characters.

        :returns: :class:`~braspag.BraspagResponse`

        """
        if not kwargs.get('currency'):
            kwargs['currency'] = 'BRL'

        if not kwargs.get('country'):
            kwargs['country'] = 'BRA'

        soft_desc = ''
        if kwargs.get('soft_descriptor'):
            # only keep first 13 chars
            soft_desc = kwargs.get('soft_descriptor')[:13]

            # Replace special chars by ascii
            soft_desc = unicodedata.normalize('NFKD', soft_desc)
            soft_desc = soft_desc.encode('ascii', 'ignore')

        kwargs['soft_descriptor'] = soft_desc

        kwargs['is_billet'] = True

        xml_request = self._render_template('authorize_billet.xml', kwargs)
        return BilletResponse(self._request(spaceless(xml_request)))

    @method_must_be_redesigned
    def get_billet_data(self, **kwargs):
        """DEPRECATED -- must be redesigned to work asynchronously.

        All arguments supplied to this method must be keyword arguments.

        :arg transaction_id: The id of the transaction generated previously by
        *issue_billet*

        :returns: :class:`~braspag.BilletResponse`

        """
        assert is_valid_guid(kwargs.get('transaction_id')), 'Invalid Transaction ID'

        context = {
            'transaction_id': kwargs.get('transaction_id'),
            'request_id': kwargs.get('request_id')
        }
        xml_request = self._render_template('get_billet_data.xml', context)
        xml_response = self._request(spaceless(xml_request), query=True)
        return BilletDataResponse(xml_response)

    def get_order_id_by_transaction_id(self, **kwargs):
        """All arguments supplied to this method must be keyword arguments.

        :arg transaction_id: The id of the transaction generated previously by
        *issue_billet*

        :returns: :class:`~braspag.BraspagOrderIdResponse`

        """
        assert is_valid_guid(kwargs.get('transaction_id')), 'Invalid Transaction ID'

        context = {
            'transaction_id': kwargs.get('transaction_id'),
            'request_id': kwargs.get('request_id')
        }

        xml_request = self._render_template('get_braspag_order_id.xml', context)
        xml_response = self._request(spaceless(xml_request), query=True)
        return BraspagOrderIdResponse(xml_response)

    def get_order_data(self, **kwargs):
        """All arguments supplied to this method must be keyword arguments.

        :arg order_id: The id of the order generated previously by
        *authorize*

        :returns: :class:`~braspag.BraspagOrderDataResponse`

        """
        assert is_valid_guid(kwargs.get('order_id')), 'Invalid Order ID'

        context = {
            'order_id': kwargs.get('order_id'),
            'request_id': kwargs.get('request_id')
        }

        xml_request = self._render_template('get_braspag_order_data.xml', context)
        xml_response = self._request(spaceless(xml_request), query=True)
        return BraspagOrderDataResponse(xml_response)

    def get_customer_data(self, **kwargs):
        """All arguments supplied to this method must be keyword arguments.

        :arg order_id: The id of the order generated previously by *get_order_id*
        passing trasaction_id as argument

        :returns: :class:`~braspag.CustomerDataResponse`

        """
        assert is_valid_guid(kwargs.get('order_id')), 'Invalid Order ID'

        context = {
            'order_id': kwargs.get('order_id'),
            'request_id': kwargs.get('request_id')
        }
        xml_request = self._render_template('get_customer_data.xml', context)
        xml_response = self._request(spaceless(xml_request), query=True)
        return CustomerDataResponse(xml_response)

    def get_transaction_data(self, **kwargs):
        """All arguments supplied to this method must be keyword arguments.

        :arg transaction_id: The id of the transaction

        :returns: :class:`~braspag.TransactionDataResponse`

        """
        assert is_valid_guid(kwargs.get('transaction_id')), 'Invalid Order ID'

        context = {
            'transaction_id': kwargs.get('transaction_id'),
            'request_id': kwargs.get('request_id')
        }
        xml_request = self._render_template('get_transaction_data.xml', context)
        xml_response = self._request(spaceless(xml_request), query=True)
        return TransactionDataResponse(xml_response)


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
                # 2 = parcelado pelo emissor do cartão
                kwargs['payment_plan'] = 2
            else:
                # 0 = a vista
                kwargs['payment_plan'] = 0

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
                assert isinstance(kwargs[attr], Decimal), 'amount must be Decimal'
                kwargs.update(amount=convert_amount(kwargs[attr]))
            setattr(self, attr, kwargs[attr])
