# coding: utf-8
from __future__ import unicode_literals

import importlib2

def get_pycache_folder(script_path):
    assert script_path.endswith('.py')

    ### TODO: Fix race conditions
    sys.implementation.cache_tag = GRUMPY_MAGIC_TAG
    cache_folder = os.path.abspath(os.path.normpath(
        importlib2._bootstrap.cache_from_source(script_path)
    ))
    sys.implementation.cache_tag = ORIGINAL_MAGIC_TAG
    ###
    return cache_folder
