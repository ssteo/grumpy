# coding: utf-8
"""
Grumpy uses `pythonparser` as its AST parser. This module contains an augmented
(extended) parser from it, letting us to accept special Grumpy-only syntax, like
the `import '__go__/...'` syntax for importing Go code.
"""
import logging

import pythonparser.parser
from pythonparser.parser import Parser, Seq, Loc, List, Alt, Rule, action
from pythonparser import ast

logger = logging.getLogger(__name__)

PYTHNOPARSER_PATCHED = False


def patch_pythonparser():
    global PYTHNOPARSER_PATCHED
    if PYTHNOPARSER_PATCHED:
        return False

    logger.info('Monkeypatching pythonparser.parser.Parser with Grumpy extensions')
    pythonparser.parser.Parser = GrumpyParser
    PYTHNOPARSER_PATCHED = True
    return True


class GrumpyParser(Parser):
    @action(Seq(Loc("from"), Alt(Parser.import_from_3, Parser.import_from_4),
                Loc("import"), Alt(Parser.import_from_5,
                                   Seq(Loc("("), Rule("import_as_names"), Loc(")")),
                                   Parser.import_from_6)))
    def import_from(self, *args, **kwargs):
        return super(GrumpyParser, self).import_from(*args, **kwargs)

    dotted_as_names = List(Rule("dotted_as_name"), ",", trailing=False)
