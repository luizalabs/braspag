# -*- encoding: utf-8 -*-


class TransactionType(object):
    """Transaction types within Braspag API"""
    PRE_AUTHORIZATION = '1'
    AUTOMATIC_CAPTURE = '2'
    PRE_AUTHORIZATION_WITH_AUTHENTICATION = '3'
    AUTOMATIC_CAPTURE_WITH_AUTHENTICATION = '4'
    RECURRENT_PRE_AUTHORIZATION = '5'
    RECURRENT_AUTOMATIC_CAPTURE = '6'


class PaymentPlanType(object):
    """Playment plan types' constants"""
    NO_INSTALLMENTS = 0
    INSTALLMENTS_BY_ESTABLISHMENT = 1
    INSTALLMENTS_BY_ISSUING_BANK = 2


#Payment Methods
PAYMENT_METHODS = {
    'Cielo': {
        'Visa Electron': 123,
        'Visa': 500,
        'MasterCard': 501,
        'Amex': 502,
        'Diners': 503,
        'Elo': 504,
    },
    'Banorte': {
        'Visa': 505,
        'MasterCard': 506,
        'Diners': 507,
        'Amex': 508,
    },
    'Redecard': {
        'Visa': 509,
        'MasterCard': 510,
        'Diners':511,
    },
    'PagosOnLine': {
        'Visa': 512,
        'MasterCard': 513,
        'Amex': 514,
        'Diners': 515,
    },
    'Payvision': {
        'Visa': 516,
        'MasterCard': 517,
        'Diners': 518,
        'Amex': 519,
    },
    'Banorte Cargos Automaticos': {
        'Visa': 520,
        'MasterCard': 521,
        'Diners': 522,
    },
    'Amex': {
        '2P': 523,
    },
    'SITEF': {
        'Visa': 524,
        'MasterCard': 525,
        'Amex': 526,
        'Diners': 527,
        'HiperCard': 528,
        'Leader': 529,
        'Aura': 530,
        'Santander Visa': 531,
        'Santander MasterCard': 532,
    },
    'Simulated': {
        'USD': 995,
        'EUR': 996,
        'BRL': 997,
    }
}
