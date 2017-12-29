# -*- coding: utf-8 -*-
from contextlib import contextmanager

from newrelic.agent import current_transaction, ExternalTrace


@contextmanager
def newrelic_external_trace(url, method):
    """
    This context manager map an external transaction to newrelic
    :param url: Url to be mapped in newrelic
    :param method: Method to be mapped in newrelic
    """
    transaction = current_transaction()
    with ExternalTrace(
        transaction,
        'tornado.httpclient',
        url,
        method
    ):
        yield
