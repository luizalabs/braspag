# -*- encoding: utf-8 -*-

from __future__ import absolute_import

import uuid
import httplib
import logging
import unicodedata

import jinja2

from .utils import spaceless, is_valid_guid
from .exceptions import BraspagHttpResponseException
from .response import (CreditCardAuthorizationResponse, BilletResponse,
    BilletDataResponse, CreditCardCancelResponse, CreditCardRefundResponse,
    BraspagOrderIdResponse, CustomerDataResponse, CreditCardCaptureResponse,
    TransactionDataResponse, BraspagOrderDataResponse)
from xml.dom import minidom
from xml.etree import ElementTree
from decimal import Decimal, InvalidOperation


class BraspagRequest(object):
    """
    Implements Braspag Pagador API (manual version 1.9).
    """

    def __init__(self, merchant_id=None, homologation=False):
        if homologation:
            self.url = 'homologacao.pagador.com.br'
        else:
            self.url = 'www.pagador.com.br'

        self.merchant_id = merchant_id

        self.jinja_env = jinja2.Environment(
            autoescape=True,
            loader=jinja2.PackageLoader('braspag'),
        )

        self.log = logging.getLogger('braspag')

    def _request(self, xml, query=False):
        if query:
            uri = '/services/pagadorQuery.asmx'
        else:
            uri = '/webservice/pagadorTransaction.asmx'

        if isinstance(xml, unicode):
            xml = xml.encode('utf-8')

        http = httplib.HTTPSConnection(self.url)
        http.request("POST", uri, body=xml, headers={
            "Host": "localhost",
            "Content-Type": "text/xml; charset=UTF-8",
        })
        response = http.getresponse()
        xmlresponse = response.read()
        self.log.debug(minidom.parseString(xmlresponse).toprettyxml(indent='  '))
        return xmlresponse

    def authorize(self, **kwargs):
        """All arguments supplied to this method must be keyword arguments.

        :arg order_id: Order id. It will be used to indentify the
                       order later in Braspag.
        :arg customer_id: Must be user's CPF/CNPJ.
        :arg customer_name: User's full name.
        :arg customer_email: User's email address.

        :returns: :class:`~braspag.BraspagResponse`
        """
        transactions = []
        for transaction in kwargs['transactions']:
            transactions.append(BraspagTransaction(**transaction))

        xml_request = self._render_template('authorize.xml', {
            'request_id': kwargs['request_id'],
            'order_id': kwargs['order_id'],
            'customer_id': kwargs['customer_id'],
            'customer_name': kwargs['customer_name'],
            'customer_email': kwargs['customer_email'],
            'transactions': transactions,
        })
        response = self._request(spaceless(xml_request))
        return CreditCardAuthorizationResponse(response)

    def _base_transaction(self, **kwargs):
        assert kwargs.get('type') in ('Refund', 'Void', 'Capture')
        assert is_valid_guid(kwargs.get('transaction_id')), 'Transaction ID invalido'

        data_dict = {
            'amount': kwargs.get('amount'),
            'type': kwargs.get('type'),
            'transaction_id': kwargs.get('transaction_id'),
            'request_id': kwargs.get('request_id'),
        }
        xml_request = self._render_template('base.xml', data_dict)
        xml_response = self._request(xml_request)

        if kwargs.get('type') == 'Void':
            return CreditCardCancelResponse(xml_response)
        elif kwargs.get('type') == 'Refund':
            return CreditCardRefundResponse(xml_response)
        else:
            return CreditCardCaptureResponse(xml_response)


    def void(self, **kwargs):
        """Void the given amount for the given transaction_id.

        This method should be used to return funds to customers
        for transactions that happened within less than 23h and
        59 minutes ago. For other transactions use
        :meth:`~braspag.BraspagRequest.refund`.

        If the amount is 0 (zero) the full transaction will be
        voided.

        :returns: :class:`~braspag.BraspagResponse`

        """
        kwargs['type'] = 'Void'
        kwargs['amount'] = kwargs.get('amount', 0)
        return self._base_transaction(**kwargs)

    def refund(self, **kwargs):
        """Refund the given amount for the given transaction_id.

        This method should be used to return funds to customers
        for transactions that happened at least 24 hours ago.
        For transactions that happended within 24 hours use
        :meth:`~braspag.BraspagRequest.void`.

        If the amount is 0 (zero) the full transaction will be
        refunded.

        :returns: :class:`~braspag.BraspagResponse`

        """
        kwargs['type'] = 'Refund'
        kwargs['amount'] = kwargs.get('amount', 0)
        return self._base_transaction(**kwargs)

    def capture(self, **kwargs):
        """Capture the given `amount` from the given transaction_id.

        This method should only be called after pre-authorizing the
        transaction by calling :meth:`~braspag.BraspagRequest.authorize`
        with `transaction_types` 1 or 3.

        :returns: :class:`~braspag.BraspagResponse`

        """
        kwargs['type'] = 'Capture'
        return self._base_transaction(**kwargs)

    def _render_template(self, template_name, data_dict):
        if self.merchant_id:
            data_dict['merchant_id'] = self.merchant_id

        if not data_dict.get('request_id'):
            data_dict['request_id'] = unicode(uuid.uuid4())

        template = self.jinja_env.get_template(template_name)
        xml_request = template.render(data_dict)
        self.log.debug(xml_request)
        return xml_request

    def issue_billet(self, **kwargs):
        """All arguments supplied to this method must be keyword arguments.

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

    def get_billet_data(self, **kwargs):
        """All arguments supplied to this method must be keyword arguments.

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
            # 2 = captura automatica
            kwargs['transaction_type'] = 2

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

        for attr in ('amount', 'card_holder', 'card_number', 'card_security_code',
                     'card_exp_date', 'number_of_payments', 'currency', 'country', 'payment_plan',
                     'payment_method', 'soft_descriptor', 'save_card', 'transaction_type'):
            setattr(self, attr, kwargs[attr])