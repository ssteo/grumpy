#!/usr/bin/env python
# coding=utf-8

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

"""A Python -> Go transcompiler."""

from __future__ import unicode_literals

import argparse
import os
import sys
from StringIO import StringIO
import textwrap

from .compiler import block
from .compiler import imputil
from .compiler import stmt
from .compiler import util
from .vendor import pythonparser
from .pep_support.pep3147pycache import make_transpiled_module_folders


def main(stream=None, modname=None, pep3147=False):
  script = os.path.abspath(stream.name)
  assert script and modname, 'Script "%s" or Modname "%s" is empty' % (script,modname)

  gopath = os.getenv('GOPATH', None)
  if not gopath:
    raise RuntimeError('GOPATH not set')

  stream.seek(0)
  py_contents = stream.read()
  mod = pythonparser.parse(py_contents)

  # Do a pass for compiler directives from `from __future__ import *` statements
  future_node, future_features = imputil.parse_future_features(mod)

  importer = imputil.Importer(gopath, modname, script,
                              future_features.absolute_import)
  full_package_name = modname.replace('.', '/')
  mod_block = block.ModuleBlock(importer, full_package_name, script,
                                py_contents, future_features)

  visitor = stmt.StatementVisitor(mod_block, future_node)
  # Indent so that the module body is aligned with the goto labels.
  with visitor.writer.indent_block():
    visitor.visit(mod)

  file_buffer = StringIO()
  writer = util.Writer(file_buffer)
  tmpl = textwrap.dedent("""\
      package $package
      import πg "grumpy"
      var Code *πg.Code
      func init() {
      \tCode = πg.NewCode("<module>", $script, nil, 0, func(πF *πg.Frame, _ []*πg.Object) (*πg.Object, *πg.BaseException) {
      \t\tvar πR *πg.Object; _ = πR
      \t\tvar πE *πg.BaseException; _ = πE""")
  writer.write_tmpl(tmpl, package=modname.split('.')[-1],
                    script=util.go_str(script))
  with writer.indent_block(2):
    for s in sorted(mod_block.strings):
      writer.write('ß{} := πg.InternStr({})'.format(s, util.go_str(s)))
    writer.write_temp_decls(mod_block)
    writer.write_block(mod_block, visitor.writer.getvalue())
  writer.write_tmpl(textwrap.dedent("""\
    \t\treturn nil, πE
    \t})
    \tπg.RegisterModule($modname, Code)
    }"""), modname=util.go_str(modname))

  if pep3147:
    file_buffer.seek(0)
    new_gopath = make_transpiled_module_folders(script)['gopath_folder']
    if new_gopath not in os.environ['GOPATH'].split(os.pathsep):
      os.environ['GOPATH'] += os.pathsep + new_gopath
  file_buffer.seek(0)
  return file_buffer.read()
