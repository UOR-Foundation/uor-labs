"""Recursive-descent parser and AST node definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Dict, Iterator

from .lexer import Lexer, Token


# ---------------------------------------------------------------------------
# AST Nodes
# ---------------------------------------------------------------------------

class Node:
    """Base class for all AST nodes."""

    def accept(self, visitor: "NodeVisitor") -> Iterator:
        method = getattr(visitor, f"visit_{self.__class__.__name__}", None)
        if method is None:
            yield from visitor.generic_visit(self)
        else:
            yield from method(self)


@dataclass
class ProgramNode(Node):
    body: List[Node]


@dataclass
class FunctionNode(Node):
    name: str
    params: List[str]
    body: 'BlockNode'


@dataclass
class VariableNode(Node):
    name: str


@dataclass
class LiteralNode(Node):
    value: object


@dataclass
class BinaryOpNode(Node):
    left: Node
    operator: str
    right: Node


@dataclass
class UnaryOpNode(Node):
    operator: str
    operand: Node


@dataclass
class IfNode(Node):
    condition: Node
    then_branch: Node
    else_branch: Optional[Node] = None


@dataclass
class WhileNode(Node):
    condition: Node
    body: Node


@dataclass
class ForNode(Node):
    init: Optional[Node]
    condition: Optional[Node]
    increment: Optional[Node]
    body: Node


@dataclass
class ReturnNode(Node):
    value: Optional[Node]


@dataclass
class CallNode(Node):
    callee: Node
    args: List[Node]


@dataclass
class AssignmentNode(Node):
    target: VariableNode
    value: Node


@dataclass
class VarDeclNode(Node):
    name: str
    initializer: Optional[Node]


@dataclass
class ExpressionStatement(Node):
    expression: Node


@dataclass
class BlockNode(Node):
    statements: List[Node]


# ---------------------------------------------------------------------------
# Visitor helper
# ---------------------------------------------------------------------------

class NodeVisitor:
    def generic_visit(self, node: Node) -> Iterator:
        for field in getattr(node, '__dataclass_fields__', {}):
            value = getattr(node, field)
            if isinstance(value, Node):
                yield from value.accept(self)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, Node):
                        yield from item.accept(self)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class Parser:
    """Recursive descent parser producing an AST."""

    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.pos = 0
        self.scopes: List[Dict[str, object]] = [{}]

    @classmethod
    def from_text(cls, text: str) -> 'Parser':
        lexer = Lexer(text)
        tokens = list(lexer.tokenize())
        return cls(tokens)

    # ---- basic helpers -------------------------------------------------
    def _peek(self) -> Token:
        if self.pos >= len(self.tokens):
            return Token("EOF", "", -1, -1)
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        tok = self._peek()
        self.pos += 1
        return tok

    def _check(self, type_: str, value: Optional[str] = None) -> bool:
        tok = self._peek()
        if tok.type != type_:
            return False
        if value is not None and tok.value != value:
            return False
        return True

    def _match(self, type_: str, value: Optional[str] = None) -> bool:
        if self._check(type_, value):
            self._advance()
            return True
        return False

    def _match_keyword(self, kw: str) -> bool:
        return self._match("KEYWORD", kw)

    def _expect(self, type_: str, value: Optional[str] = None) -> Token:
        if not self._check(type_, value):
            tok = self._peek()
            raise SyntaxError(
                f"Expected {type_}{' ' + value if value else ''} at line {tok.line}"
            )
        return self._advance()

    def _at_end(self) -> bool:
        return self.pos >= len(self.tokens)

    def push_scope(self) -> None:
        self.scopes.append({})

    def pop_scope(self) -> None:
        self.scopes.pop()

    # ---- parsing entry points -----------------------------------------
    def parse(self) -> ProgramNode:
        return self.parse_program()

    def parse_program(self) -> ProgramNode:
        body: List[Node] = []
        while not self._at_end():
            body.append(self.parse_declaration())
        return ProgramNode(body)

    def parse_declaration(self) -> Node:
        if self._match_keyword("function"):
            return self.parse_function()
        if self._match_keyword("var") or self._match_keyword("let") or self._match_keyword("const"):
            return self.parse_var_decl(self.tokens[self.pos - 1].value)
        return self.parse_statement()

    def parse_function(self) -> FunctionNode:
        name = self._expect("IDENTIFIER").value
        self._expect("(")
        params: List[str] = []
        if not self._check(")"):
            while True:
                param = self._expect("IDENTIFIER").value
                params.append(param)
                if not self._match(","):
                    break
        self._expect(")")
        self.scopes[-1][name] = True
        self.push_scope()
        for p in params:
            self.scopes[-1][p] = True
        body = self.parse_block()
        self.pop_scope()
        return FunctionNode(name, params, body)

    def parse_var_decl(self, keyword: str) -> VarDeclNode:
        name = self._expect("IDENTIFIER").value
        init: Optional[Node] = None
        if self._match("="):
            init = self.parse_expression()
        self._expect(";")
        self.scopes[-1][name] = True
        return VarDeclNode(name, init)

    # ---- statements ----------------------------------------------------
    def parse_statement(self) -> Node:
        if self._match_keyword("if"):
            return self.parse_if()
        if self._match_keyword("while"):
            return self.parse_while()
        if self._match_keyword("for"):
            return self.parse_for()
        if self._match_keyword("return"):
            return self.parse_return()
        if self._match("{"):
            return self.parse_block()
        return self.parse_expression_statement()

    def parse_block(self) -> BlockNode:
        statements: List[Node] = []
        while not self._check("}"):
            statements.append(self.parse_declaration())
        self._expect("}")
        return BlockNode(statements)

    def parse_if(self) -> IfNode:
        self._expect("(")
        cond = self.parse_expression()
        self._expect(")")
        then_branch = self.parse_statement()
        else_branch = None
        if self._match_keyword("else"):
            else_branch = self.parse_statement()
        return IfNode(cond, then_branch, else_branch)

    def parse_while(self) -> WhileNode:
        self._expect("(")
        cond = self.parse_expression()
        self._expect(")")
        body = self.parse_statement()
        return WhileNode(cond, body)

    def parse_for(self) -> ForNode:
        self._expect("(")
        init: Optional[Node] = None
        if not self._check(";"):
            if self._check("KEYWORD", "var") or self._check("KEYWORD", "let") or self._check("KEYWORD", "const"):
                init = self.parse_declaration()
            else:
                init = self.parse_expression_statement()
        else:
            self._expect(";")
        cond: Optional[Node] = None
        if not self._check(";"):
            cond = self.parse_expression()
        self._expect(";")
        inc: Optional[Node] = None
        if not self._check(")"):
            inc = self.parse_expression()
        self._expect(")")
        body = self.parse_statement()
        return ForNode(init, cond, inc, body)

    def parse_return(self) -> ReturnNode:
        value: Optional[Node] = None
        if not self._check(";"):
            value = self.parse_expression()
        self._expect(";")
        return ReturnNode(value)

    def parse_expression_statement(self) -> ExpressionStatement:
        expr = self.parse_expression()
        self._expect(";")
        return ExpressionStatement(expr)

    # ---- expressions ---------------------------------------------------
    def parse_expression(self) -> Node:
        return self.parse_assignment()

    def parse_assignment(self) -> Node:
        expr = self.parse_logic_or()
        if self._match("="):
            if not isinstance(expr, VariableNode):
                raise SyntaxError("Invalid assignment target")
            value = self.parse_assignment()
            return AssignmentNode(expr, value)
        return expr

    def parse_logic_or(self) -> Node:
        expr = self.parse_logic_and()
        while self._match("OPERATOR", "||"):
            op = self.tokens[self.pos - 1].value
            right = self.parse_logic_and()
            expr = BinaryOpNode(expr, op, right)
        return expr

    def parse_logic_and(self) -> Node:
        expr = self.parse_equality()
        while self._match("OPERATOR", "&&"):
            op = self.tokens[self.pos - 1].value
            right = self.parse_equality()
            expr = BinaryOpNode(expr, op, right)
        return expr

    def parse_equality(self) -> Node:
        expr = self.parse_comparison()
        while self._match("OPERATOR", "==") or self._match("OPERATOR", "!="):
            op = self.tokens[self.pos - 1].value
            right = self.parse_comparison()
            expr = BinaryOpNode(expr, op, right)
        return expr

    def parse_comparison(self) -> Node:
        expr = self.parse_term()
        while self._match("OPERATOR", "<") or self._match("OPERATOR", "<=") or self._match("OPERATOR", ">") or self._match("OPERATOR", ">="):
            op = self.tokens[self.pos - 1].value
            right = self.parse_term()
            expr = BinaryOpNode(expr, op, right)
        return expr

    def parse_term(self) -> Node:
        expr = self.parse_factor()
        while self._match("OPERATOR", "+") or self._match("OPERATOR", "-"):
            op = self.tokens[self.pos - 1].value
            right = self.parse_factor()
            expr = BinaryOpNode(expr, op, right)
        return expr

    def parse_factor(self) -> Node:
        expr = self.parse_unary()
        while self._match("OPERATOR", "*") or self._match("OPERATOR", "/") or self._match("OPERATOR", "%"):
            op = self.tokens[self.pos - 1].value
            right = self.parse_unary()
            expr = BinaryOpNode(expr, op, right)
        return expr

    def parse_unary(self) -> Node:
        if self._match("OPERATOR", "!") or self._match("OPERATOR", "-"):
            op = self.tokens[self.pos - 1].value
            operand = self.parse_unary()
            return UnaryOpNode(op, operand)
        return self.parse_call()

    def parse_call(self) -> Node:
        expr = self.parse_primary()
        while self._match("("):
            args: List[Node] = []
            if not self._check(")"):
                while True:
                    args.append(self.parse_expression())
                    if not self._match(","):
                        break
            self._expect(")")
            expr = CallNode(expr, args)
        return expr

    def parse_primary(self) -> Node:
        tok = self._peek()
        if tok.type == "NUMBER":
            self._advance()
            return LiteralNode(int(tok.value))
        if tok.type == "STRING":
            self._advance()
            return LiteralNode(tok.value)
        if tok.type == "IDENTIFIER":
            self._advance()
            return VariableNode(tok.value)
        if self._match("("):
            expr = self.parse_expression()
            self._expect(")")
            return expr
        raise SyntaxError(
            f"Unexpected token {tok.type} {tok.value!r} at line {tok.line}"
        )

