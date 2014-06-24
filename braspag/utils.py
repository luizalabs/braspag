# -*- encoding: utf-8 -*-

import string
import functools
import warnings
import xml.parsers.expat
from datetime import datetime

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

def to_float(value):
    return float(int(value)/100.00)

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

def method_must_be_redesigned(func):
    """Decorator to mark functions that must be redesigned to work
    asynchronously before being used.
    """

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.warn_explicit(  # pragma: no cover
            u"If you plan to use {}(), please redesign it to work asynchronously.".format(func.__name__),
            category=Exception,
            filename=func.func_code.co_filename,
            lineno=func.func_code.co_firstlineno + 1
        )
        return func(*args, **kwargs)  # pragma: no cover
    return new_func
