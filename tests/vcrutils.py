# encoding: utf-8
import inspect
import os

import vcr


def path_generator(function):
    func_dir = os.path.dirname(inspect.getfile(function))
    file_name = '{}.yml'.format(function.__name__)
    return os.path.join(func_dir, 'cassettes', file_name)


replay = vcr.VCR(func_path_generator=path_generator).use_cassette
