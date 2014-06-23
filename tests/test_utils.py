# -*- coding: utf8 -*-

from __future__ import absolute_import

from braspag.utils import to_bool
from braspag.utils import to_int
from .base import BraspagTestCase


class UtilsTest(BraspagTestCase):

    def test_utils(self):

        assert to_bool('false') == False
        assert to_bool('False') == False
        assert to_bool('FALSE') == False
        assert to_bool('true') == True
        assert to_bool('True') == True
        assert to_bool('TRUE') == True

        assert to_int('1') == 1
        assert to_int('1432-2') == 14322
