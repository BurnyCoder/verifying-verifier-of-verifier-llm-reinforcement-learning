"""Generate numbered arithmetic problems and keep related records in one split."""

import ast
import hashlib
import operator
import random
from dataclasses import dataclass
from functools import lru_cache

OPS = {ast.Add: ("+", operator.add), ast.Sub: ("-", operator.sub), ast.Mult: ("*", operator.mul)}


@dataclass(frozen=True)
class Problem:
    expression: str
    steps: tuple[str, ...]
    values: tuple[int, ...]
    key: str
    balanced_root: bool

    @classmethod
    def from_expression(cls, expression):
        """Walk the restricted input AST in postorder. Model text never enters this parser."""
        root = ast.parse(expression, mode="eval").body
        steps, values = [], []

        def visit(node):
            if isinstance(node, ast.Constant) and type(node.value) is int:
                return str(node.value), node.value, str(node.value)
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub) and isinstance(node.operand, ast.Constant):
                literal = -node.operand.value
                return str(literal), literal, str(literal)
            if not isinstance(node, ast.BinOp) or type(node.op) not in OPS:
                raise ValueError("Unsupported arithmetic expression")
            lref, left, lkey = visit(node.left)
            rref, right, rkey = visit(node.right)
            symbol, operation = OPS[type(node.op)]
            value = operation(left, right)
            steps.append(f"s{len(steps)+1} = {lref} {symbol} {rref}")
            values.append(value)
            if symbol in ("+", "*"):
                lkey, rkey = sorted((lkey, rkey))
            return f"s{len(steps)}", value, f"({lkey}{symbol}{rkey})"

        _, _, canonical = visit(root)
        if not isinstance(root, ast.BinOp):
            raise ValueError("A problem requires an operation")
        key = hashlib.sha256(canonical.encode()).hexdigest()
        return cls(expression, tuple(steps), tuple(values), key,
                   isinstance(root.left, ast.BinOp) and isinstance(root.right, ast.BinOp))

    @property
    def question(self):
        """The public problem contains instructions and operations, with no oracle values."""
        return "\n".join(self.steps)


def _expression(rng, terms):
    """Adapt Reasoning Gym's signed integer sampler to +, -, * and one-digit operands.

    Source and Apache license are in third_party/reasoning-gym. Retain the upstream
    recursive split and optional parenthesis rule; grade the resulting AST separately.
    """
    left = rng.randint(1, terms)
    if left > 1 and rng.random() > 0.5:
        parts = ["(" + _expression(rng, left) + ")"]
    else:
        parts = [str(rng.randint(-9, 9))]
        for _ in range(left - 1):
            parts.extend((rng.choice(("+", "-", "*")), str(rng.randint(-9, 9))))
    if left < terms:
        parts.extend((rng.choice(("+", "-", "*")), _expression(rng, terms - left)))
    return " ".join(parts)


def shape(problem):
    """Apply the registered transfer exclusions before assigning random partitions."""
    if len(problem.steps) >= 5:
        return "long"
    return "layout" if problem.balanced_root else "id"


def partition(problem):
    category = shape(problem)
    if category != "id":
        return category
    bucket = int(problem.key[:12], 16) % 100
    if bucket < 70:
        return "train"
    if bucket < 80:
        return "dev"
    return "test" if bucket < 95 else "mechanism"


@lru_cache(maxsize=32)
def problems(split, count):
    """Return a reproducible prefix of distinct canonical problems from this split."""
    streams = dict(train=1061, dev=2081, test=3023, mechanism=4021, layout=5011, long=6029)
    rng = random.Random(streams[split])
    found = {}
    while len(found) < count:
        n = rng.randint(6, 8) if split == "long" else rng.randint(3, 5)
        problem = Problem.from_expression(_expression(rng, n))
        if partition(problem) == split:
            found.setdefault(problem.key, problem)
    return tuple(found.values())
