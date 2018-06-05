# coding: utf-8
from __future__ import unicode_literals

import os
import sys

import importlib2
import grumpy_tools


GOPATH_FOLDER = 'gopath'
TRANSPILED_MODULES_FOLDER = 'src/__python__/'
GRUMPY_MAGIC_TAG = 'grumpy-' + grumpy_tools.__version__.replace('.', '')  # alike cpython-27
ORIGINAL_MAGIC_TAG = sys.implementation.cache_tag  # On Py27, only because importlib2


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


def get_gopath_folder(script_path):
    cache_folder = get_pycache_folder(script_path)
    return os.path.join(cache_folder, GOPATH_FOLDER)


def get_transpiled_base_folder(script_path):
    gopath_folder = get_gopath_folder(script_path)
    return os.path.join(gopath_folder, TRANSPILED_MODULES_FOLDER)


def get_transpiled_module_folder(script_path):
    # TODO: Handle __init__.py scripts. Should create a folder-named path
    script_paths = script_path.rpartition('.')[0].split('/')
    if script_path.endswith('__init__.py'):
        script_basename = script_paths[-2]
    else:
        script_basename = script_paths[-1]

    transpiled_base_folder = get_transpiled_base_folder(script_path)
    return os.path.join(transpiled_base_folder, script_basename)


def make_transpiled_module_folders(script_path):
    """
    Make the folder to store all the tree needed by the 'script_path' script

    Recursively "stomp" the files found in places that a folder is needed.
    """
    needed_folders = {
        'cache_folder': get_pycache_folder(script_path),
        'gopath_folder': get_gopath_folder(script_path),
        'transpiled_base_folder': get_transpiled_base_folder(script_path),
        'transpiled_module_folder': get_transpiled_module_folder(script_path),
    }
    for role, folder in needed_folders.items():
        if os.path.isfile(folder):  # 1. Need a folder. Remove the file
            os.unlink(folder)
        if not os.path.exists(folder):  # 2. Create the needed folder
            os.makedirs(folder)
    return needed_folders
