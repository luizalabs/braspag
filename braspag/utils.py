# -*- encoding: utf-8 -*-

import string
import functools
import warnings

def spaceless(xml_str):
    return ''.join(line.strip() for line in xml_str.split('\n') if line.strip())

def is_valid_guid(guid):
    VALID_CHARS = string.hexdigits + '-'
    VALID_PARTS_LEN = [8, 4, 4, 4, 12]

    if not isinstance(guid, basestring):
        guid = unicode(guid)

    if not all(c in VALID_CHARS for c in guid):
        return False

    guid_parts_len = [len(part) for part in guid.split('-')]
    if guid_parts_len != VALID_PARTS_LEN:
        return False

    return True

def convert_amount(decimal_value):
    """Helper to ensure we convert the amount in a single method.
    _Always_ use this method to convert the amount value from the
    decimal type to integer.
    """
    return int(decimal_value) * 100

def method_must_be_redesigned(func):
    """Decorator to mark functions that must be redesigned to work
    asynchronously before being used.
    """

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.warn_explicit(
            u"If you plan to use {}(), please redesign it to work asynchronously.".format(func.__name__),
            category=Exception,
            filename=func.func_code.co_filename,
            lineno=func.func_code.co_firstlineno + 1
        )
        return func(*args, **kwargs)
    return new_func
