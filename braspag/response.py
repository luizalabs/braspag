
import xml.etree.ElementTree as ET

from xml.etree.ElementTree import Element
from utils import to_float
from utils import to_bool
from utils import to_int
from utils import to_date
from utils import to_unicode
import xmltodict


class PagadorResponse(object):

    def __init__(self, xml):
        self._fields = getattr(self, '_fields', {})

        self._fields['transaction_id'] = 'BraspagTransactionId'
        self._fields['correlation_id'] = 'CorrelationId'
        self._fields['amount'] = ('Amount', to_int)
        self._fields['success'] = ('Success', to_bool)
        self.errors = []

        self.parse_xml(xml)

    def parse_xml(self, xml):

        # Set None as defaults
        for field in self._fields:
            setattr(self, field, None)

        xml = ET.fromstring(xml)
        for elem in xml.iter():
            # if elem.text:
                for field, tag_info in self._fields.items():
                    if isinstance(tag_info, (list, tuple)):
                        tag, convert = tag_info
                    else:
                        tag = tag_info
                        convert = to_unicode

                    if elem.tag.endswith('}' + tag):
                        value = convert(unicode(elem.text).strip())
                        setattr(self, field, value)
                    elif elem.tag.endswith('}ErrorReportDataResponse'):
                        error = self._get_error(elem)
                        self.errors = self._put_error(error, self.errors)
                    elif elem.tag == 'faultstring':
                        error = [0, elem.text]
                        self.errors = self._put_error(error, self.errors)

    def _put_error(self, error, errors):
        if not error in errors:
            errors.append(error)
        return errors

    def _get_error(self, error_node):
        for node in error_node.iter():
            if node.tag.endswith('}ErrorCode'):
                code = node.text.strip()
            elif node.tag.endswith('}ErrorMessage'):
                msg = node.text.strip()
        return int(code), msg


class PagadorDictResponse(object):

    def __init__(self, xml):
        dictxml = xmltodict.parse(xml)
        self.body = dict
        self.transactions = []
        self.errors = []

        if dictxml['soap:Envelope']['soap:Body']:
            self.body = dictxml['soap:Envelope']['soap:Body']

    def get_body_data(self, body):
        self.correlation_id = body.get('CorrelationId')
        self.success = to_bool(body.get('Success'))

    def format_transactions(self, transaction_items):
        if isinstance(transaction_items, list):
            [self.format_transactions(t) for t in transaction_items]
        else:
            status = to_int(transaction_items.get('Status'))
            data = {
                'braspag_transaction_id': transaction_items.get('BraspagTransactionId'),
                'acquirer_transaction_id': transaction_items.get('AcquirerTransactionId'),
                'authorization_code': transaction_items.get('AuthorizationCode'),
                'amount': to_int(transaction_items.get('Amount')),
                'status': status,
                'status_message': self.STATUS[status],
                'proof_of_sale': transaction_items.get('ProofOfSale'),
            }

            if transaction_items.has_key('MaskedCreditCardNumber'):
                data['masked_credit_card_number'] = transaction_items.get('MaskedCreditCardNumber')

            if transaction_items.has_key('ReturnCode'):
                data['return_code'] = transaction_items.get('ReturnCode')

            if transaction_items.has_key('ReturnMessage'):
                data['return_message'] = transaction_items.get('ReturnMessage')

            if transaction_items.has_key('PaymentMethod'):
                data['payment_method'] = to_int(transaction_items.get('PaymentMethod'))

            if transaction_items.has_key('CreditCardToken'):
                data['card_token'] = transaction_items.get('CreditCardToken')

            if transaction_items.has_key('PaymentMethodName'):
                data['payment_method_name'] = transaction_items.get('PaymentMethodName')

            if transaction_items.has_key('TransactionType'):
                data['transaction_type'] = to_int(transaction_items.get('TransactionType'))

            if transaction_items.has_key('ReceivedDate'):
                data['received_date'] = to_date(transaction_items.get('ReceivedDate'))

            if transaction_items.has_key('CapturedDate'):
                data['captured_date'] = to_date(transaction_items.get('CapturedDate'))

            if transaction_items.has_key('OrderId'):
                data['order_id'] = transaction_items.get('OrderId')

            self.transactions.append(data)

    def format_errors(self, error_items):
        if isinstance(error_items, list):
            [self.format_errors(e) for e in error_items]
        else:
            self.errors.append({
                'error_code': error_items.get('ErrorCode'),
                'error_message': error_items.get('ErrorMessage')
            })


class CreditCardAuthorizationResponse(PagadorDictResponse):

    STATUS = {
        0: 'Captured',
        1: 'Authorized',
        2: 'Not Authorized',
        3: 'Disqualifying Error',
        4: 'Waiting for Answer',
    }

    def __init__(self, xml):
        super(CreditCardAuthorizationResponse, self).__init__(xml)
        body = self.body.get('AuthorizeTransactionResponse').get('AuthorizeTransactionResult')
        self.get_body_data(body)

        if self.success:
            self.braspag_order_id = body.get('OrderData').get('BraspagOrderId')
            self.order_id = body.get('OrderData').get('OrderId')

            transactions = body.get('PaymentDataCollection').get('PaymentDataResponse')
            self.format_transactions(transactions)
        else:
            error_items = body.get('ErrorReportDataCollection').get('ErrorReportDataResponse')
            self.format_errors(error_items)


class CreditCardCaptureResponse(PagadorDictResponse):

    STATUS = {
        0: 'Captured',
        1: 'Authorized',
        2: 'Not Authorized',
        3: 'Disqualifying Error',
        4: 'Waiting for Answer',
    }

    def __init__(self, xml):
        super(CreditCardCaptureResponse, self).__init__(xml)
        body = self.body.get('CaptureCreditCardTransactionResponse').get('CaptureCreditCardTransactionResult')
        self.get_body_data(body)

        if self.success:
            transactions = body.get('TransactionDataCollection').get('TransactionDataResponse')
            self.format_transactions(transactions)
        else:
            error_items = body.get('ErrorReportDataCollection').get('ErrorReportDataResponse')
            self.format_errors(error_items)


class CreditCardCancelResponse(PagadorDictResponse):

    STATUS = {
        0: 'Void Confirmed',
        1: 'Void Denied',
        2: 'Invalid Transaction',
    }

    def __init__(self, xml):
        super(CreditCardCancelResponse, self).__init__(xml)
        body = self.body.get('VoidCreditCardTransactionResponse').get('VoidCreditCardTransactionResult')
        self.get_body_data(body)

        if self.success:
            transactions = body.get('TransactionDataCollection').get('TransactionDataResponse')
            self.format_transactions(transactions)
        else:
            error_items = body.get('ErrorReportDataCollection').get('ErrorReportDataResponse')
            self.format_errors(error_items)


class CreditCardRefundResponse(PagadorDictResponse):

    STATUS = {
        0: 'Refund Confirmed',
        1: 'Refund Denied',
        2: 'Invalid Transaction',
    }

    def __init__(self, xml):
        super(CreditCardRefundResponse, self).__init__(xml)
        body = self.body.get('RefundCreditCardTransactionResponse').get('RefundCreditCardTransactionResult')
        self.get_body_data(body)
        if self.success:
            transactions = body.get('TransactionDataCollection').get('TransactionDataResponse')
            self.format_transactions(transactions)
        else:
            error_items = body.get('ErrorReportDataCollection').get('ErrorReportDataResponse')
            self.format_errors(error_items)


class BraspagOrderDataResponse(PagadorDictResponse):

    STATUS = {
        0: 'Unknown',
        1: 'Captured',
        2: 'Authorized',
        3: 'Not Authorized',
        4: 'Voided',
        5: 'Refunded',
        6: 'Waiting',
        7: 'Unqualified',
    }

    def __init__(self, xml):
        super(BraspagOrderDataResponse, self).__init__(xml)
        body = self.body.get('GetOrderDataResponse').get('GetOrderDataResult')
        self.get_body_data(body)
        if self.success:
            transactions = body.get('TransactionDataCollection').get('OrderTransactionDataResponse')
            self.format_transactions(transactions)
        else:
            error_items = body.get('ErrorReportDataCollection').get('ErrorReportDataResponse')
            self.format_errors(error_items)


class BraspagOrderIdDataResponse(PagadorDictResponse):

    def __init__(self, xml):
        super(BraspagOrderIdDataResponse, self).__init__(xml)
        body = self.body.get('GetOrderIdDataResponse').get('GetOrderIdDataResult')
        self.get_body_data(body)
        self.orders = []

        if self.success:
            if isinstance(body.get('OrderIdDataCollection').get('OrderIdTransactionResponse'), list):
                self.orders = [self.format_order(order) for order in body.get('OrderIdDataCollection').get('OrderIdTransactionResponse')]
            else:
                self.orders = [self.format_order(body.get('OrderIdDataCollection').get('OrderIdTransactionResponse'))]
        else:
            error_items = body.get('ErrorReportDataCollection').get('ErrorReportDataResponse')
            self.format_errors(error_items)

    def format_order(self, order):
        return {
            'braspag_order_id': order.get('BraspagOrderId'),
            'braspag_transaction_id': order.get('BraspagTransactionId').get('guid')
        }


class BraspagOrderIdResponse(PagadorResponse):

    def __init__(self, xml):
        self._fields = getattr(self, '_fields', {})

        self._fields['braspag_order_id'] = 'BraspagOrderId'

        super(BraspagOrderIdResponse, self).__init__(xml)


class CustomerDataResponse(PagadorResponse):

    def __init__(self, xml):
        self._fields = getattr(self, '_fields', {})

        self._fields['customer_identity'] = 'CustomerIdentity'
        self._fields['customer_name'] = 'CustomerName'
        self._fields['customer_email'] = 'CustomerEmail'
        self._fields['street'] = 'Street'
        self._fields['number'] = 'Number'
        self._fields['complement'] = 'Complement'
        self._fields['district'] = 'District'
        self._fields['zipcode'] = 'ZipCode'
        self._fields['city'] = 'City'
        self._fields['state'] = 'State'
        self._fields['country'] = 'Country'

        super(CustomerDataResponse, self).__init__(xml)


class TransactionDataResponse(PagadorResponse):

    def __init__(self, xml):
        self._fields = getattr(self, '_fields', {})

        self._fields['order_id'] = 'OrderId'
        self._fields['acquirer_transaction_id'] = 'AcquirerTransactionId'
        self._fields['payment_method'] = ('PaymentMethod', int)
        self._fields['payment_method_name'] = 'PaymentMethodName'
        self._fields['error_code'] = 'ErrorCode'
        self._fields['error_message'] = 'ErrorMessage'
        self._fields['authorization_code'] = 'AuthorizationCode'
        self._fields['number_of_payments'] = ('NumberOfPayments', int)
        self._fields['currency'] = 'Currency'
        self._fields['country'] = 'Country'
        self._fields['transaction_type'] = 'TransactionType'
        self._fields['status'] = ('Status', int)
        self._fields['received_date'] = ('ReceivedDate', to_date)
        self._fields['captured_date'] = ('CapturedDate', to_date)
        self._fields['voided_date'] = ('VoidedDate', to_date)
        self._fields['credit_card_token'] = 'CreditCardToken'

        super(TransactionDataResponse, self).__init__(xml)


class ProtectedCardResponse(object):
    def __init__(self, xml):
        dictxml = xmltodict.parse(xml)
        self.body = dict
        self.errors = []

        if dictxml['soap:Envelope']['soap:Body']:
            self.body = dictxml['soap:Envelope']['soap:Body']

    def get_body_data(self, body):
        self.correlation_id = body.get('CorrelationId')
        self.success = to_bool(body.get('Success'))

    def format_errors(self, error_items):
        if isinstance(error_items, list):
            [self.format_errors(e) for e in error_items]
        else:
            self.errors.append({
                'error_code': error_items.get('ErrorCode'),
                'error_message': error_items.get('ErrorMessage')
            })


class AddCardResponse(ProtectedCardResponse):
    def __init__(self, xml):
        super(AddCardResponse, self).__init__(xml)
        body = self.body.get('SaveCreditCardResponse').get('SaveCreditCardResult')
        self.get_body_data(body)

        if self.success:
            self.just_click_key = body.get('JustClickKey')
        else:
            error_items = body.get('ErrorReportCollection').get('ErrorReport')
            self.format_errors(error_items)


class InvalidateCardResponse(ProtectedCardResponse):
    def __init__(self, xml):
        super(InvalidateCardResponse, self).__init__(xml)
        body = self.body.get('InvalidateCreditCardResponse').get('InvalidateCreditCardResult')
        self.get_body_data(body)

        if not self.success:
            error_items = body.get('ErrorReportCollection').get('ErrorReport')
            self.format_errors(error_items)
