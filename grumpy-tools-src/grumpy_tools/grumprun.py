#!/usr/bin/env python

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""grumprun compiles and runs a snippet of Python using Grumpy.

Usage: $ grumprun -m <module>             # Run the named module.
       $ echo 'print "hola!"' | grumprun  # Execute Python code from stdin.
"""

import argparse
import os
import random
import shutil
import string
import subprocess
import sys
import tempfile

from .compiler import imputil
from .pep_support.pep3147pycache import make_transpiled_module_folders
from . import grumpc


module_tmpl = string.Template("""\
package main
import (
\t"os"
\t"grumpy"
\tmod "$package"
$imports
)
func main() {
\tgrumpy.ImportModule(grumpy.NewRootFrame(), "traceback")
\tos.Exit(grumpy.RunMain(mod.Code))
}
""")


def main(stream=None, modname=None, pep3147=False):
  assert pep3147, 'It is no longer optional'
  assert stream is None or stream.name

  gopath = os.getenv('GOPATH', None)
  if not gopath:
    print >> sys.stderr, 'GOPATH not set'
    return 1

  # CPython does not cache the __main__. Should I?
  pep3147_folders = make_transpiled_module_folders(stream.name)
  workdir = pep3147_folders['transpiled_base_folder']

  try:
    if modname:
      # Find the script associated with the given module.
      for d in gopath.split(os.pathsep):
        script = imputil.find_script(
            os.path.join(d, 'src', '__python__'), modname)
        if script:
          break
      else:
        raise RuntimeError("can't find module '%s'", modname)
    else:
      # Generate a dummy python script on the 'cache_folder'
      modname = '__main__'
      script_name = os.path.join(pep3147_folders['cache_folder'], stream.name)
      with open(script_name, 'wb') as script_file:
        stream.seek(0)
        script_file.write(stream.read())

      py_dir = os.path.join(workdir, 'src', '__python__')
      script = os.path.abspath(stream.name)
      mod_dir = pep3147_folders['transpiled_module_folder']

      ## TODO: Manage the STDIN and `-c` scripts situation
      # script = os.path.join(py_dir, 'module.py')
      # with open(script, 'w') as f:
      #   f.write(stream.read())
      ##

      os.environ['GOPATH'] = gopath + os.pathsep + workdir

      # Compile the dummy script to Go using grumpc.
      with open(os.path.join(mod_dir, 'module.go'), 'w+') as dummy_file:
        transpiled = grumpc.main(stream, modname=modname, pep3147=True)
        dummy_file.write(transpiled)

    names = set() # TODO: Fix what this does -> imputil.calculate_transitive_deps(modname, script, gopath)
    # Make sure traceback is available in all Python binaries.
    names.add('traceback')
    go_main = os.path.join(workdir, 'main.go')
    package = _package_name(modname)
    imports = ''.join('\t_ "' + _package_name(name) + '"\n' for name in names)
    with open(go_main, 'w') as f:
      f.write(module_tmpl.substitute(package=package, imports=imports))
    return subprocess.Popen('go run ' + go_main, shell=True).wait()
  finally:
    pass


def _package_name(modname):
  if modname.startswith('__go__/'):
    return '__python__/' + modname
  return '__python__/' + modname.replace('.', '/')
