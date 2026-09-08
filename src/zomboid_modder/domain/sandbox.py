from __future__ import annotations

import re
from typing import Any

try:
    import lupa
except ImportError:
    lupa = None


class SandboxParseError(Exception):
    pass


class SandboxVars:
    """Parses SandboxVars.lua into a mutable tree; serializes back preserving
    PZ formatting conventions (2-space indent, trailing commas, key ordering).

    PZ format looks like:

        SandboxVars = {
            VERSION = 5,
            Zombies = 3,
            ZombieLore = {
                Speed = 2,
                ...
            },
        }
    """

    ROOT = "SandboxVars"
    INDENT = "\t"

    def __init__(self, tree: dict[str, Any], key_order: list[list[str]]) -> None:
        self._tree = tree
        self._key_order = key_order

    @classmethod
    def parse(cls, text: str) -> SandboxVars:
        if lupa is None:
            raise SandboxParseError("lupa is required to parse SandboxVars.lua")
        try:
            lua = lupa.LuaRuntime(unpack_returned_tuples=True)
            lua.execute(text)
            root = lua.globals()[cls.ROOT]
            if root is None:
                raise SandboxParseError(f"{cls.ROOT} not found in file")
            tree = cls._lua_to_python(root)
        except Exception as e:
            raise SandboxParseError(f"failed to parse: {e}") from e
        key_order = cls._extract_key_order(text)
        return cls(tree, key_order)

    @staticmethod
    def _lua_to_python(obj: Any) -> Any:
        if lupa is not None and lupa.lua_type(obj) == "table":
            return {str(k): SandboxVars._lua_to_python(v) for k, v in obj.items()}
        return obj

    @staticmethod
    def _extract_key_order(text: str) -> list[list[str]]:
        """Best-effort: capture the order keys appear in the source so
        serialization stays stable. Returns a flat list of paths in appearance
        order (nested paths use dotted form)."""
        order: list[list[str]] = []
        stack: list[str] = []
        for raw in text.splitlines():
            line = raw.strip().rstrip(",")
            if not line or line.startswith("--"):
                continue
            m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{", line)
            if m:
                key = m.group(1)
                if key != SandboxVars.ROOT:
                    stack.append(key)
                    order.append(list(stack))
                continue
            m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*", line)
            if m:
                key = m.group(1)
                order.append([*stack, key])
                continue
            if line.startswith("}"):
                if stack:
                    stack.pop()
        return order

    def get(self, dotted_key: str) -> Any:
        node: Any = self._tree
        for part in dotted_key.split("."):
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        return node

    def set(self, dotted_key: str, value: Any) -> None:
        parts = dotted_key.split(".")
        node = self._tree
        for part in parts[:-1]:
            if part not in node or not isinstance(node[part], dict):
                node[part] = {}
            node = node[part]
        node[parts[-1]] = value

    def flat_keys(self) -> list[str]:
        keys: list[str] = []

        def walk(prefix: str, node: dict[str, Any]) -> None:
            for k, v in node.items():
                path = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    walk(path, v)
                else:
                    keys.append(path)

        walk("", self._tree)
        return keys

    def serialize(self) -> str:
        lines = [f"{self.ROOT} =", "{"]
        self._render_dict(self._tree, 1, lines)
        lines.append("}")
        return "\n".join(lines) + "\n"

    def _render_dict(self, node: dict[str, Any], depth: int, out: list[str]) -> None:
        indent = self.INDENT * depth
        for key, value in node.items():
            if isinstance(value, dict):
                out.append(f"{indent}{key} =")
                out.append(f"{indent}{{")
                self._render_dict(value, depth + 1, out)
                out.append(f"{indent}}},")
            else:
                out.append(f"{indent}{key} = {self._format_scalar(value)},")

    @staticmethod
    def _format_scalar(value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            s = repr(value)
            return s if "." in s or "e" in s else s + ".0"
        if isinstance(value, str):
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        if value is None:
            return "nil"
        return str(value)
