import json
from typing import Callable

from hadloc.grammar import Terminal, Sequential, Optional, AnyOf, ZeroOrMore, Repeated
from hadloc.grammar.abstract_syntax_tree import ASTNode
from hadloc.translator.tokenizer import TokenType
from hadloc.utils import local_open

with local_open('./translator/parser_errors.json') as f:
    ERRORS = json.load(f)


def keyword(word: str, name: str = None):
    return Terminal(lambda x: x.value == word, name=name)


def identifier(name: str, error: str | Callable[[ASTNode], str] | None = None):
    return Terminal(lambda x: x.token_type == TokenType.IDENTIFIER, name=name, error=error)


def integer(name: str, error: str | Callable[[ASTNode], str] | None = None):
    return Terminal(lambda x: x.token_type == TokenType.INTEGER, name=name, error=error)


def symbol(char: str, error: str | Callable[[ASTNode], str] | None = None):
    return Terminal(lambda x: x.value == char, error=error)


def memory_segment(error: str | None = None):
    return Sequential(
        Terminal(lambda x: x.token_type == TokenType.SEGMENT),
        symbol('[', error=lambda x: ERRORS['segment opening bracket'].format(x[-1].node_type)),
        integer('index', error=lambda x: ERRORS['segment index'].format(x[-1].node_type)),
        symbol(']', error=lambda x: ERRORS['segment closing bracket'].format(x[-1].node_type)),
        error=error,
        auto_name=True
    )


def function_definition():
    return Sequential(
        keyword('function'),
        identifier('name', ERRORS['function name']),
        Optional(integer('locals', ERRORS['function locals'])),
        auto_name=True
    )


def function_call():
    return Sequential(
        keyword('call'),
        identifier('name', ERRORS['call name']),
        Optional(integer('arguments', ERRORS['call arguments'])),
        auto_name=True
    )


def push():
    return Sequential(
        keyword('push'),
        AnyOf(
            integer('constant'),
            memory_segment(),
            error=ERRORS['push argument']
        ),
        auto_name=True
    )


def pop():
    return Sequential(
        keyword('pop'),
        Optional(memory_segment(ERRORS['pop argument'])),
        auto_name=True
    )


def label():
    return Sequential(
        keyword('label'),
        identifier('label', ERRORS['label argument'])
    )


def binary_operation():
    return Sequential(
        AnyOf(*[keyword(kw) for kw in ['add', 'sub', 'and', 'or', 'eq', 'ne', 'le', 'lt', 'ge', 'gt']]),
        Repeated(AnyOf(
            integer('constant'),
            memory_segment(),
            error=lambda x: ERRORS['binary operator argument'].format(x[-2].node_type)
        ), 0, 2),
        auto_name=True
    )


def unary_operation():
    return Sequential(
        AnyOf(keyword('neg'), keyword('not'), keyword('inc'), keyword('dec')),
        Optional(AnyOf(
            integer('constant'),
            memory_segment(),
            error=lambda x: ERRORS['unary operator argument'].format(x[-2].node_type)
        )),
        auto_name=True
    )


def goto(error: str | None = None):
    return Sequential(
        keyword('goto'),
        identifier('label', ERRORS['goto argument']),
        auto_name=True,
        error=error
    )


def if_goto():
    return Sequential(
        keyword('if'),
        Optional(AnyOf(
            memory_segment(),
            AnyOf(*[keyword(kw, name='condition') for kw in ['eq', 'ne', 'le', 'lt', 'ge', 'gt']]),
            error=ERRORS['if argument']
        )),
        goto(error=ERRORS['if goto']),
        auto_name=True
    )


def return_statement():
    return Sequential(
        keyword('return'),
        Optional(AnyOf(
            integer('constant'),
            memory_segment(),
            error=lambda x: ERRORS['return argument'].format(x[-2].node_type)
        )),
        auto_name=True
    )


def instruction():
    return Sequential(
        AnyOf(function_definition(), function_call(), push(), pop(), label(),
              binary_operation(), unary_operation(), goto(), if_goto(), return_statement()),
        Terminal(lambda x: x.token_type == TokenType.INSTRUCTION_END)
    )


def vm_program():
    return Sequential(
        ZeroOrMore(instruction()),
        Terminal(lambda x: x.token_type == TokenType.PROGRAM_END),
        name='program'
    )
