"""Accessibility-hierarchy parsing and LLM-friendly compaction.

``uiautomator2`` gives you a raw UiAutomator XML dump. On a typical screen that
is 20-100 KB of XML -- far too much to feed an LLM on every step, and most of it
is invisible layout scaffolding.

This module turns that dump into a small, *indexed* text tree. Every interesting
node gets a numeric id, so an agent can say ``tap_element(17)`` instead of
hallucinating coordinates, and a caller can resolve id 17 back to a precise
centre point.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple

__all__ = ["UiNode", "UiTree", "parse_hierarchy", "compact_hierarchy"]

_BOUNDS_RE = re.compile(r"\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]")

# Attributes that decide whether a node is worth showing to a model.
_INTERACTIVE = ("clickable", "scrollable", "long-clickable", "checkable", "editable")


@dataclass
class UiNode:
    """A single accessibility node, normalised."""
    node_id: int
    depth: int
    cls: str = ""
    text: str = ""
    resource_id: str = ""
    content_desc: str = ""
    package: str = ""
    bounds: Tuple[int, int, int, int] = (0, 0, 0, 0)
    clickable: bool = False
    scrollable: bool = False
    checkable: bool = False
    checked: bool = False
    enabled: bool = True
    selected: bool = False
    focused: bool = False
    password: bool = False
    children: List[int] = field(default_factory=list)

    # -- derived ---------------------------------------------------------
    @property
    def center(self) -> Tuple[int, int]:
        x1, y1, x2, y2 = self.bounds
        return ((x1 + x2) // 2, (y1 + y2) // 2)

    @property
    def width(self) -> int:
        return self.bounds[2] - self.bounds[0]

    @property
    def height(self) -> int:
        return self.bounds[3] - self.bounds[1]

    @property
    def label(self) -> str:
        """Best human/LLM-readable name for this node."""
        return self.text or self.content_desc or self.short_id or ""

    @property
    def short_id(self) -> str:
        """``com.foo:id/bar`` -> ``bar`` (keeps output small)."""
        if not self.resource_id:
            return ""
        return self.resource_id.rsplit("/", 1)[-1]

    @property
    def short_class(self) -> str:
        """``android.widget.TextView`` -> ``TextView``."""
        return self.cls.rsplit(".", 1)[-1] if self.cls else ""

    @property
    def is_visible(self) -> bool:
        return self.width > 0 and self.height > 0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["center"] = self.center
        d["label"] = self.label
        return d


@dataclass
class UiTree:
    """Parsed hierarchy + fast lookup indexes."""
    nodes: Dict[int, UiNode]
    root_id: Optional[int] = None
    package: str = ""
    activity: str = ""

    def get(self, node_id: int) -> UiNode:
        try:
            return self.nodes[node_id]
        except KeyError:
            raise KeyError(f"No UI element with id {node_id}. "
                           f"Known ids: {sorted(self.nodes)[:20]}...") from None

    def center_of(self, node_id: int) -> Tuple[int, int]:
        return self.get(node_id).center

    def find(self, *, text: Optional[str] = None, resource_id: Optional[str] = None,
             content_desc: Optional[str] = None, cls: Optional[str] = None,
             clickable: Optional[bool] = None) -> List[UiNode]:
        """Substring / equality search across nodes."""
        out: List[UiNode] = []
        for n in self.nodes.values():
            if text is not None and text.lower() not in n.text.lower():
                continue
            if resource_id is not None and resource_id not in n.resource_id:
                continue
            if content_desc is not None and content_desc.lower() not in n.content_desc.lower():
                continue
            if cls is not None and cls.lower() not in n.cls.lower():
                continue
            if clickable is not None and n.clickable != clickable:
                continue
            out.append(n)
        return out

    def find_one(self, **kwargs) -> Optional[UiNode]:
        hits = self.find(**kwargs)
        return hits[0] if hits else None

    def to_text(self, include_all: bool = False, max_nodes: int = 400) -> str:
        """Compact indented tree, one line per interesting node."""
        return compact_hierarchy(self, include_all=include_all, max_nodes=max_nodes)

    def interactive(self) -> List[UiNode]:
        return [n for n in self.nodes.values()
                if (n.clickable or n.scrollable or n.checkable) and n.is_visible]


def _to_bool(value: Optional[str]) -> bool:
    return str(value).lower() == "true"


def parse_hierarchy(xml_text: str, *, package: str = "", activity: str = "") -> UiTree:
    """Parse a ``dump_hierarchy()`` XML string into a :class:`UiTree`.

    Node ids are assigned in document order starting at 0, which is stable for a
    given dump and cheap to reason about.
    """
    if not xml_text or not xml_text.strip():
        raise ValueError("Empty hierarchy XML -- is the screen off or the app still loading?")

    root = ET.fromstring(xml_text)
    nodes: Dict[int, UiNode] = {}
    counter = 0
    root_id: Optional[int] = None

    def walk(element: ET.Element, depth: int, parent_id: Optional[int]) -> Optional[int]:
        nonlocal counter, root_id
        attrib = element.attrib
        # `<hierarchy>` is the wrapper element; `<node>` are the real entries.
        if element.tag != "node":
            for child in element:
                walk(child, depth, parent_id)
            return None

        bounds = (0, 0, 0, 0)
        m = _BOUNDS_RE.match(attrib.get("bounds", ""))
        if m:
            bounds = tuple(int(g) for g in m.groups())  # type: ignore[assignment]

        node = UiNode(
            node_id=counter,
            depth=depth,
            cls=attrib.get("class", ""),
            text=attrib.get("text", ""),
            resource_id=attrib.get("resource-id", ""),
            content_desc=attrib.get("content-desc", ""),
            package=attrib.get("package", ""),
            bounds=bounds,
            clickable=_to_bool(attrib.get("clickable")),
            scrollable=_to_bool(attrib.get("scrollable")),
            checkable=_to_bool(attrib.get("checkable")),
            checked=_to_bool(attrib.get("checked")),
            enabled=_to_bool(attrib.get("enabled", "true")),
            selected=_to_bool(attrib.get("selected")),
            focused=_to_bool(attrib.get("focused")),
            password=_to_bool(attrib.get("password")),
        )
        nodes[counter] = node
        if parent_id is not None:
            nodes[parent_id].children.append(counter)
        if root_id is None:
            root_id = counter

        my_id = counter
        counter += 1
        for child in element:
            walk(child, depth + 1, my_id)
        return my_id

    walk(root, 0, None)
    pkg = package or (nodes[0].package if nodes else "")
    return UiTree(nodes=nodes, root_id=root_id, package=pkg, activity=activity)


def _is_interesting(n: UiNode) -> bool:
    if not n.is_visible or not n.enabled:
        return False
    if n.text or n.content_desc or n.resource_id:
        return True
    return any(getattr(n, key.replace("-", "_"), False) for key in _INTERACTIVE)


def compact_hierarchy(tree: UiTree, *, include_all: bool = False,
                      max_nodes: int = 400) -> str:
    """Render a small text tree an LLM can actually reason over.

    Example output::

        screen: com.android.settings  1080x2340  nodes=42 (showing 18)
        [0] TextView "Wi-Fi" rid=header clickable center=(120,180)
        [3] Switch rid=wifi_toggle checked=true clickable center=(980,300)
    """
    shown = [n for n in tree.nodes.values() if include_all or _is_interesting(n)]
    if len(shown) > max_nodes:
        shown = shown[:max_nodes]

    header = f"screen: {tree.package or '?'}"
    if tree.activity:
        header += f"/{tree.activity}"
    header += f"  nodes={len(tree.nodes)} (showing {len(shown)})"

    lines = [header]
    for n in shown:
        parts = [f"[{n.node_id}]", n.short_class or "View"]
        if n.label:
            parts.append(f'"{n.label}"')
        if n.short_id:
            parts.append(f"rid={n.short_id}")
        flags = []
        if n.clickable:
            flags.append("clickable")
        if n.scrollable:
            flags.append("scrollable")
        if n.checkable:
            flags.append("checked" if n.checked else "unchecked")
        if n.password:
            flags.append("password")
        if n.selected:
            flags.append("selected")
        if not n.enabled:
            flags.append("disabled")
        if flags:
            parts.append(" ".join(flags))
        cx, cy = n.center
        parts.append(f"center=({cx},{cy})")
        lines.append("  " * min(n.depth, 6) + " ".join(parts))
    return "\n".join(lines)
