from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator


@dataclass
class Token:
    """Represents a single lexical token."""

    type: str
    value: str
    line: int
    column: int


class Lexer:
    """Simple lexer for the toy language defined in ``grammar.ebnf``."""

    KEYWORDS = {
        "function",
        "object",
        "if",
        "else",
        "while",
        "for",
        "return",
        "let",
        "const",
        "print",
        "int",
        "float",
        "bool",
        "string",
        "void",
        "true",
        "false",
        "coherent",
    }

    OPERATORS = {
        "+",
        "-",
        "*",
        "/",
        "%",
        "==",
        "!=",
        "<",
        ">",
        "<=",
        ">=",
        "&&",
        "||",
        "!",
        "->",
    }

    SINGLE_CHARS = {
        "(", ")",
        "{", "}",
        ";", ",",
        "=",
        ":",
    }

    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1

    def _peek(self, offset: int = 1) -> str:
        if self.pos + offset >= len(self.text):
            return ""
        return self.text[self.pos + offset]

    def _advance(self, count: int = 1) -> None:
        for _ in range(count):
            if self.pos >= len(self.text):
                return
            ch = self.text[self.pos]
            self.pos += 1
            if ch == "\n":
                self.line += 1
                self.col = 1
            else:
                self.col += 1

    def tokenize(self) -> Iterator[Token]:
        """Yield :class:`Token` objects from the input text."""

        text = self.text
        while self.pos < len(text):
            ch = text[self.pos]

            # Skip whitespace
            if ch.isspace():
                self._advance()
                continue

            # Single-line comment
            if ch == "/" and self._peek() == "/":
                self._advance(2)
                while self.pos < len(text) and text[self.pos] != "\n":
                    self._advance()
                continue

            # Multi-line comment
            if ch == "/" and self._peek() == "*":
                self._advance(2)
                while self.pos < len(text):
                    if text[self.pos] == "*" and self._peek() == "/":
                        self._advance(2)
                        break
                    if text[self.pos] == "\n":
                        self._advance()
                    else:
                        self._advance()
                else:
                    raise SyntaxError(
                        f"Unterminated comment at line {self.line}, column {self.col}"
                    )
                continue

            start_line, start_col = self.line, self.col

            # Annotation
            if ch == "@":
                if text.startswith("@coherent", self.pos):
                    self._advance(len("@coherent"))
                    yield Token("COHERENT", "@coherent", start_line, start_col)
                    continue
                raise SyntaxError(
                    f"Unknown annotation at line {start_line}, column {start_col}"
                )

            # String literal
            if ch == '"':
                self._advance()
                value = ""
                while self.pos < len(text) and text[self.pos] != '"':
                    if text[self.pos] == "\n":
                        raise SyntaxError(
                            f"Unterminated string at line {start_line}, column {start_col}"
                        )
                    value += text[self.pos]
                    self._advance()
                if self.pos >= len(text):
                    raise SyntaxError(
                        f"Unterminated string at line {start_line}, column {start_col}"
                    )
                self._advance()  # closing quote
                yield Token("STRING", value, start_line, start_col)
                continue

            # Number literal (integer or float)
            if ch.isdigit():
                num = ch
                self._advance()
                while self.pos < len(text) and text[self.pos].isdigit():
                    num += text[self.pos]
                    self._advance()
                if self.pos < len(text) and text[self.pos] == ".":
                    num += "."
                    self._advance()
                    while self.pos < len(text) and text[self.pos].isdigit():
                        num += text[self.pos]
                        self._advance()
                yield Token("NUMBER", num, start_line, start_col)
                continue

            # Identifier or keyword
            if ch.isalpha() or ch == "_":
                ident = ch
                self._advance()
                while self.pos < len(text) and (
                    text[self.pos].isalnum() or text[self.pos] == "_"
                ):
                    ident += text[self.pos]
                    self._advance()
                token_type = "KEYWORD" if ident in self.KEYWORDS else "IDENTIFIER"
                yield Token(token_type, ident, start_line, start_col)
                continue

            # Two-character operators
            two = ch + self._peek()
            if two in self.OPERATORS:
                self._advance(2)
                yield Token("OPERATOR", two, start_line, start_col)
                continue

            # Single-character operators
            if ch in self.OPERATORS:
                self._advance()
                yield Token("OPERATOR", ch, start_line, start_col)
                continue

            # Punctuation
            if ch in self.SINGLE_CHARS:
                self._advance()
                yield Token(ch, ch, start_line, start_col)
                continue

            raise SyntaxError(
                f"Invalid character '{ch}' at line {self.line}, column {self.col}"
            )
