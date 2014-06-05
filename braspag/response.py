
import xml.parsers.expat
import xml.etree.ElementTree as ET

from decimal import Decimal
from datetime import datetime
from xml.etree.ElementTree import Element
import xmltodict


def unescape(s):
    """Copied from http://wiki.python.org/moin/EscapingXml"""

    want_unicode = False
    if isinstance(s, unicode):
        s = s.encode("utf-8")
        want_unicode = True

    # the rest of this assumes that `s` is UTF-8
    list = []

    # create and initialize a parser object
    p = xml.parsers.expat.ParserCreate("utf-8")
    p.buffer_text = True
    p.returns_unicode = want_unicode
    p.CharacterDataHandler = list.append

    # parse the data wrapped in a dummy element
    # (needed so the "document" is well-formed)
    p.Parse("<e>", 0)
    p.Parse(s, 0)
    p.Parse("</e>", 1)

    # join the extracted strings and return
    es = ""
    if want_unicode:
        es = u""
    return es.join(list)


def to_bool(value):
    value = value.lower()
    if value == 'true':
        return True
    elif value == 'false':
        return False


def to_decimal(value):
    return Decimal(int(value)/100.0).quantize(Decimal('1.00'))


def to_unicode(value):
    if isinstance(value, str):
        value = value.decode('utf-8')

    return unescape(value)


def to_date(value):
    return datetime.strptime(value, '%m/%d/%Y %H:%M:%S %p')


def to_int(value):
    if value.isdigit():
        return int(value)
    else:
        #some BoletoNumber came with - e.g: 10027-1
        return int(value.replace('-',''))
 

class PagadorResponse(object):

    def __init__(self, xml):
        self._fields = getattr(self, '_fields', {})

        self._fields['transaction_id'] = 'BraspagTransactionId'
        self._fields['correlation_id'] = 'CorrelationId'
        self._fields['amount'] = ('Amount', to_decimal)
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
                        value = convert(str(elem.text).strip())
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
                'amount': to_decimal(transaction_items.get('Amount')),
                'return_code': transaction_items.get('ReturnCode'),
                'return_message': transaction_items.get('ReturnMessage') ,
                'status': status,
                'status_message': self.STATUS[status],
            }

            if transaction_items.has_key('PaymentMethod'):
                data['payment_method'] = to_int(transaction_items.get('PaymentMethod'))
            if transaction_items.has_key('CreditCardToken'):
                data['card_token'] = transaction_items.get('CreditCardToken')
            
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
        0: 'Void/Refund Confirmed',
        1: 'Void/Refund Denied',
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
        0: 'Void/Refund Confirmed',
        1: 'Void/Refund Denied',
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


class BilletResponse(PagadorResponse):

    def __init__(self, xml):
        self._fields = getattr(self, '_fields', {})

        # auth fields
        self._fields['order_id'] = 'OrderId'
        self._fields['braspag_order_id'] = 'BraspagOrderId'
        self._fields['payment_method'] = ('PaymentMethod', int)

        self._fields['number'] = ('BoletoNumber', to_int)
        self._fields['expiration_date'] = ('BoletoExpirationDate', to_date)
        self._fields['url'] = 'BoletoUrl'
        self._fields['assignor'] = 'Assignor'
        self._fields['barcode'] = 'BarCodeNumber'
        self._fields['message'] = 'Message'

        super(BilletResponse, self).__init__(xml)


class BilletDataResponse(BilletResponse):

    def __init__(self, xml):
        self._fields = getattr(self, '_fields', {})

        self._fields['document_number'] = 'DocumentNumber'
        self._fields['document_date'] = ('DocumentDate', to_date)
        self._fields['payment_date'] = ('PaymentDate', to_date)
        self._fields['type'] = 'BoletoType'
        self._fields['paid_amount'] = ('PaidAmount', to_decimal)
        self._fields['bank_number'] = 'BankNumber'
        self._fields['agency'] = 'Agency'
        self._fields['account'] = 'Account'

        super(BilletDataResponse, self).__init__(xml)


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