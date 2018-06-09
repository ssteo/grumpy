# coding: utf-8
from __future__ import unicode_literals

import os
import sys
import logging

import importlib2
import grumpy_tools

from ..compiler import imputil

logger = logging.getLogger(__name__)

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


def get_transpiled_module_folder(script_path, module_name):
    transpiled_base_folder = get_transpiled_base_folder(script_path)
    parts = module_name.split('.')
    return os.path.join(transpiled_base_folder, *parts)


def link_parent_modules(script_path, module_name):
    package_parts = module_name.split('.')[:-1]
    if not package_parts:
        return  # No parent packages to be linked

    script_parts = script_path.split(os.sep)
    if script_parts[-1] == '__init__.py':
        script_parts = script_parts[:-1]
    if script_parts[0] == '':
        script_parts[0] = '/'
    script_parts = script_parts[:-1]

    for i, part in enumerate(reversed(package_parts)):
        parent_script = os.path.join(*script_parts[:(-i or None)])
        parent_package = '.'.join(package_parts[:(-i or None)])
        parent_package_script = imputil.find_script(parent_package, parent_script)
        if not parent_package_script:
            continue
        parent_module_folder = get_transpiled_module_folder(parent_package_script, parent_package)
        local_parent_module_folder = get_transpiled_module_folder(script_path, parent_package)

        logger.debug("Checking link of package '%s' on %s",
                     parent_package, local_parent_module_folder)
        _maybe_link_paths(os.path.join(parent_module_folder, 'module.go'),
                          os.path.join(local_parent_module_folder, 'module.go'))


def make_transpiled_module_folders(script_path, module_name):
    """
    Make the folder to store all the tree needed by the 'script_path' script

    Recursively "stomp" the files found in places that a folder is needed.
    """
    needed_folders = {
        'cache_folder': get_pycache_folder(script_path),
        'gopath_folder': get_gopath_folder(script_path),
        'transpiled_base_folder': get_transpiled_base_folder(script_path),
        'transpiled_module_folder': get_transpiled_module_folder(script_path, module_name),
    }
    for role, folder in needed_folders.items():
        if os.path.isfile(folder):  # 1. Need a folder. Remove the file
            os.unlink(folder)
        if not os.path.exists(folder):  # 2. Create the needed folder
            os.makedirs(folder)

    link_parent_modules(script_path, module_name)
    return needed_folders


def _maybe_link_paths(orig, dest):
    relpath = os.path.relpath(orig, os.path.dirname(dest))
    if os.path.exists(dest) and not os.path.islink(dest):
        os.unlink(dest)

    if not os.path.exists(dest):
        os.symlink(relpath, dest)
        logger.debug('Linked %s to %s', orig, dest)
        return True
    return False
