from typing import List

EMPTY = "∅"
EPS = "ε"


def is_empty(r: str) -> bool:
    return r == EMPTY or r == ""


def is_eps(r: str) -> bool:
    return r == EPS


def as_group(r: str) -> str:
    if r in (EMPTY, EPS):
        return r
    # Avoid double-wrapping when already parenthesized
    if r.startswith('(') and r.endswith(')'):
        return r
    # Wrap unions to preserve precedence in concatenation/closure
    if '|' in r:
        return f"({r})"
    return r


def re_union(parts: List[str]) -> str:
    # Remove empties
    clean = [p for p in parts if not is_empty(p)]
    if not clean:
        return EMPTY
    # Deduplicate while preserving order, then sort for determinism
    seen = []
    for p in clean:
        if p not in seen:
            seen.append(p)
    if len(seen) == 1:
        return seen[0]
    return '|'.join(seen)


def re_concat(a: str, b: str) -> str:
    if is_empty(a) or is_empty(b):
        return EMPTY
    if is_eps(a):
        return b
    if is_eps(b):
        return a
    return f"{as_group(a)}{as_group(b)}"


def re_star(r: str) -> str:
    if is_empty(r) or is_eps(r):
        return EPS
    return f"{as_group(r)}*"
