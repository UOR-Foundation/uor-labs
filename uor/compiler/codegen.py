"""AST to assembly code generation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from .parser import (
    NodeVisitor,
    ProgramNode,
    FunctionNode,
    VarDeclNode,
    VariableNode,
    AssignmentNode,
    BinaryOpNode,
    UnaryOpNode,
    IfNode,
    WhileNode,
    ForNode,
    ReturnNode,
    CallNode,
    ExpressionStatement,
    BlockNode,
    LiteralNode,
    Node,
)


@dataclass
class GeneratedProgram:
    """Simple container for generated assembly code."""

    instructions: List[str]

    def as_text(self) -> str:
        return "\n".join(self.instructions)


class CodeGenerator(NodeVisitor):
    """Generate assembly instructions from an AST."""

    def __init__(self) -> None:
        self.instructions: List[str] = []
        self._label_counter = 0
        self._var_stack: List[Dict[str, int]] = []
        self._addr_counter = 0
        self._functions: Dict[str, FunctionNode] = {}
        self._expr_cache: Dict[str, int] = {}
        self._discard_addr = self._new_address()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _new_label(self, prefix: str = "L") -> str:
        label = f"{prefix}{self._label_counter}"
        self._label_counter += 1
        return label

    def _emit(self, text: str) -> None:
        self.instructions.append(text)

    def _push_env(self) -> None:
        self._var_stack.append({})

    def _pop_env(self) -> None:
        self._var_stack.pop()

    def _new_address(self) -> int:
        addr = self._addr_counter
        self._addr_counter += 1
        return addr

    def _alloc_var(self, name: str) -> int:
        addr = self._new_address()
        self._var_stack[-1][name] = addr
        return addr

    def _lookup_var(self, name: str) -> int:
        for scope in reversed(self._var_stack):
            if name in scope:
                return scope[name]
        raise NameError(f"Undefined variable {name}")

    def _expr_key(self, node: Node) -> str:
        return repr(node)

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------
    def generate(self, program: ProgramNode) -> GeneratedProgram:
        """Generate assembly from ``program``."""

        self._push_env()

        # Collect function declarations
        body: List[Node] = []
        for stmt in program.body:
            if isinstance(stmt, FunctionNode):
                self._functions[stmt.name] = stmt
            else:
                body.append(stmt)

        for stmt in body:
            for _ in stmt.accept(self):
                pass

        self._pop_env()

        return GeneratedProgram(self.instructions)

    # ------------------------------------------------------------------
    # Visitors
    # ------------------------------------------------------------------
    def visit_BlockNode(self, node: BlockNode):
        self._push_env()
        for stmt in node.statements:
            yield from stmt.accept(self)
        self._pop_env()

    def visit_VarDeclNode(self, node: VarDeclNode):
        addr = self._alloc_var(node.name)
        if node.initializer is not None:
            yield from self._eval_expr(node.initializer)
            self._emit(f"STORE {addr}")
        return iter(())

    def visit_AssignmentNode(self, node: AssignmentNode):
        yield from self._eval_expr(node.value)
        addr = self._lookup_var(node.target.name)
        self._emit(f"STORE {addr}")
        self._emit(f"LOAD {addr}")
        return iter(())

    def visit_VariableNode(self, node: VariableNode):
        addr = self._lookup_var(node.name)
        self._emit(f"LOAD {addr}")
        return iter(())

    def visit_LiteralNode(self, node: LiteralNode):
        self._emit(f"PUSH {node.value}")
        return iter(())

    def visit_BinaryOpNode(self, node: BinaryOpNode):
        # Constant folding
        if isinstance(node.left, LiteralNode) and isinstance(node.right, LiteralNode):
            op_map = {
                "+": lambda a, b: a + b,
                "-": lambda a, b: a - b,
                "*": lambda a, b: a * b,
            }
            func = op_map.get(node.operator)
            if func is None:
                raise NotImplementedError(f"Operator {node.operator} not supported")
            value = func(int(node.left.value), int(node.right.value))
            self._emit(f"PUSH {value}")
            return iter(())

        key = self._expr_key(node)
        if key in self._expr_cache:
            addr = self._expr_cache[key]
            self._emit(f"LOAD {addr}")
            return iter(())

        yield from self._eval_expr(node.left)
        yield from self._eval_expr(node.right)

        op_map = {
            "+": "ADD",
            "-": "SUB",
            "*": "MUL",
        }
        op = op_map.get(node.operator)
        if op is None:
            raise NotImplementedError(f"Operator {node.operator} not supported")
        self._emit(op)

        addr = self._new_address()
        self._expr_cache[key] = addr
        self._emit(f"STORE {addr}")
        self._emit(f"LOAD {addr}")
        return iter(())

    def visit_UnaryOpNode(self, node: UnaryOpNode):
        if node.operator == "-" and isinstance(node.operand, LiteralNode):
            self._emit(f"PUSH {-int(node.operand.value)}")
            return iter(())
        elif node.operator == "-":
            yield from self._eval_expr(node.operand)
            self._emit("PUSH -1")
            self._emit("MUL")
            return iter(())
        elif node.operator == "!":
            yield from self._eval_expr(node.operand)
            false_label = self._new_label("false")
            end_label = self._new_label("end")
            self._emit(f"JNZ {false_label}")
            self._emit("PUSH 1")
            self._emit(f"JMP {end_label}")
            self._emit(f"{false_label}:")
            self._emit("PUSH 0")
            self._emit(f"{end_label}:")
            return iter(())
        else:
            raise NotImplementedError(f"Unary op {node.operator} not supported")

    def visit_ExpressionStatement(self, node: ExpressionStatement):
        yield from self._eval_expr(node.expression, discard=True)
        return iter(())

    def visit_IfNode(self, node: IfNode):
        if isinstance(node.condition, LiteralNode):
            cond = int(node.condition.value)
            branch = node.then_branch if cond else node.else_branch
            if branch:
                yield from branch.accept(self)
            return iter(())

        yield from self._eval_expr(node.condition)
        else_label = self._new_label("else")
        end_label = self._new_label("ifend")
        self._emit(f"JZ {else_label}")
        yield from node.then_branch.accept(self)
        self._emit(f"JMP {end_label}")
        self._emit(f"{else_label}:")
        if node.else_branch:
            yield from node.else_branch.accept(self)
        self._emit(f"{end_label}:")
        return iter(())

    def visit_WhileNode(self, node: WhileNode):
        if isinstance(node.condition, LiteralNode) and not int(node.condition.value):
            return iter(())

        start = self._new_label("while_start")
        end = self._new_label("while_end")
        self._emit(f"{start}:")
        yield from self._eval_expr(node.condition)
        self._emit(f"JZ {end}")
        yield from node.body.accept(self)
        self._emit(f"JMP {start}")
        self._emit(f"{end}:")
        return iter(())

    def visit_ForNode(self, node: ForNode):
        if node.init:
            yield from node.init.accept(self)
        if node.condition and isinstance(node.condition, LiteralNode) and not int(node.condition.value):
            return iter(())
        start = self._new_label("for_start")
        end = self._new_label("for_end")
        self._emit(f"{start}:")
        if node.condition:
            yield from self._eval_expr(node.condition)
            self._emit(f"JZ {end}")
        yield from node.body.accept(self)
        if node.increment:
            yield from self._eval_expr(node.increment, discard=True)
        self._emit(f"JMP {start}")
        self._emit(f"{end}:")
        return iter(())

    def visit_CallNode(self, node: CallNode):
        if isinstance(node.callee, VariableNode) and node.callee.name == "print":
            for arg in node.args:
                yield from self._eval_expr(arg)
                self._emit("PRINT")
            return iter(())
        if isinstance(node.callee, VariableNode) and node.callee.name in self._functions:
            func = self._functions[node.callee.name]
            yield from self._inline_function(func, node.args)
            return iter(())
        raise NotImplementedError("Only builtin print or defined functions supported")

    def visit_ReturnNode(self, node: ReturnNode):
        if node.value is not None:
            yield from self._eval_expr(node.value)
            self._emit(f"STORE {self._return_addr}")
        self._emit(f"JMP {self._current_end}")
        return iter(())

    def visit_FunctionNode(self, node: FunctionNode):
        # Handled during call via inline expansion
        return iter(())

    def visit_ProgramNode(self, node: ProgramNode):
        yield from self.generate(node)
        return iter(())

    # ------------------------------------------------------------------
    # Internal expression evaluation
    # ------------------------------------------------------------------
    def _eval_expr(self, node: Node, discard: bool = False):
        if isinstance(node, LiteralNode) and discard:
            return iter(())
        for _ in node.accept(self):
            pass
        if discard:
            self._emit(f"STORE {self._discard_addr}")
        return iter(())

    # ------------------------------------------------------------------
    # Function inlining helpers
    # ------------------------------------------------------------------
    def _inline_function(self, fn: FunctionNode, args: List[Node]):
        self._push_env()
        old_return = getattr(self, "_return_addr", None)
        old_end = getattr(self, "_current_end", None)

        # Bind parameters
        for name, arg in zip(fn.params, args):
            addr = self._alloc_var(name)
            yield from self._eval_expr(arg)
            self._emit(f"STORE {addr}")

        ret_addr = self._new_address()
        end_label = self._new_label(f"func_{fn.name}_end")
        self._return_addr = ret_addr
        self._current_end = end_label

        yield from fn.body.accept(self)

        # Default return value
        self._emit(f"PUSH 0")
        self._emit(f"STORE {ret_addr}")
        self._emit(f"{end_label}:")
        self._emit(f"LOAD {ret_addr}")

        if old_return is not None:
            self._return_addr = old_return
        if old_end is not None:
            self._current_end = old_end
        self._pop_env()
        return iter(())

