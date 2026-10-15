"""Minimal S-expression reader/writer for KiCad files (no dependencies)."""

from __future__ import annotations


class Sym(str):
    """An unquoted atom."""


def parse(text: str):
    toks = _tokens(text)
    pos = 0

    def rd():
        nonlocal pos
        t = toks[pos]
        pos += 1
        if t == "(":
            out = []
            while toks[pos] != ")":
                out.append(rd())
            pos += 1
            return out
        return t

    return rd()


def _tokens(s: str):
    out, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c in " \t\r\n":
            i += 1
        elif c in "()":
            out.append(c)
            i += 1
        elif c == '"':
            j, buf = i + 1, []
            while s[j] != '"':
                if s[j] == "\\":
                    buf.append(s[j : j + 2])
                    j += 2
                else:
                    buf.append(s[j])
                    j += 1
            out.append("".join(buf))  # plain str = quoted string (escapes kept raw)
            i = j + 1
        else:
            j = i
            while j < n and s[j] not in ' \t\r\n()"':
                j += 1
            out.append(Sym(s[i:j]))
            i = j
    return out


def dump(x, ind: int = 0) -> str:
    if isinstance(x, list):
        if all(not isinstance(e, list) for e in x):
            return "(" + " ".join(dump(e) for e in x) + ")"
        pad = "\t" * (ind + 1)
        parts = [dump(x[0])] if x else []
        for e in x[1:]:
            parts.append("\n" + pad + dump(e, ind + 1))
        return "(" + " ".join(parts[:1]) + "".join(parts[1:]) + "\n" + "\t" * ind + ")"
    if isinstance(x, Sym):
        return str(x)
    if isinstance(x, (int, float)):
        return fmt(x)
    return '"' + str(x) + '"'  # strings are kept in raw escaped form


def fmt(v) -> str:
    if isinstance(v, int):
        return str(v)
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def find(lst, key):
    return [e for e in lst if isinstance(e, list) and e and e[0] == key]
