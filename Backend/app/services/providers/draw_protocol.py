"""Whiteboard draw protocol v1.1 — backend half.

The typed drawing language the Claude provider emits and the frontend renders as
native Excalidraw elements. Single source of truth for the wire format:
``docs/specs/whiteboard-draw-protocol-v1.md``. This module is pure (no SDK imports)
so every rule is unit-testable without network or Anthropic dependencies.

Contents:
    - DrawAction                one validated drawing primitive (grid coordinates)
    - DRAW_ACTIONS_TOOL         the strict tool schema handed to the Anthropic API
                                (op mechanics documented HERE, not in the system
                                prompt: per-field descriptions + input_examples)
    - tool_without_examples     fallback copy if the API rejects input_examples
    - parse_actions             untrusted tool output -> List[DrawAction] (never raises)
    - summarize_actions         short summary for TutoringState.already_drawn
    - format_board_elements     boardElements listing -> BOARD CONTENTS prompt block
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

GRID_WIDTH = 60
GRID_HEIGHT = 40
MAX_ACTIONS = 24
MAX_TEXT_CHARS = 80
MAX_MATH_CHARS = 120
MAX_ARC_RADIUS = 30.0

DRAW_OPS = (
    "stroke", "line", "arrow", "text", "math", "point", "arc", "ellipse", "rect", "erase",
)
COLORS = {"blue": "#2563eb", "green": "#16a34a", "red": "#dc2626"}
SIZES = ("small", "medium", "large")
STYLES = ("solid", "dashed", "dotted")
TEXT_SIZE_PX = {"small": 16, "medium": 24, "large": 32}
STROKE_WIDTH = {"small": 1, "medium": 2, "large": 4}

# Point-count bounds per op: (min_points, max_points). erase has no points.
_POINT_BOUNDS = {
    "stroke": (2, 64),
    "line": (2, 16),
    "arrow": (2, 16),
    "text": (1, 1),
    "math": (1, 1),
    "point": (1, 1),
    "arc": (1, 1),
    "ellipse": (2, 2),
    "rect": (2, 2),
}

# Ops that honor the line-style field; on all others style is silently nulled.
_STYLED_OPS = ("stroke", "line", "arrow", "arc", "ellipse", "rect")

# Erase targets may only reference tutor-owned aliases (spec §3).
_TUTOR_ALIAS = re.compile(r"^t\d+$")


@dataclass
class DrawAction:
    """One validated drawing primitive in grid coordinates (spec §3)."""

    op: str
    points: List[Tuple[float, float]]
    content: Optional[str] = None
    color: str = "blue"
    size: Optional[str] = None
    style: Optional[str] = None
    radius: Optional[float] = None
    angles: Optional[Tuple[float, float]] = None
    target: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Wire shape for the SSE ``draw`` event."""
        return {
            "op": self.op,
            "points": [[x, y] for x, y in self.points],
            "content": self.content,
            "color": self.color,
            "size": self.size,
            "style": self.style,
            "radius": self.radius,
            "angles": list(self.angles) if self.angles else None,
            "target": self.target,
        }


# Strict tool schema for the drawing call. Op mechanics are documented here — in
# per-field descriptions and input_examples — NOT in the system prompt (spec §3).
# Loose bounds in the schema; hard invariants enforced by parse_actions (LLM output
# is untrusted either way).
DRAW_ACTIONS_TOOL: Dict[str, Any] = {
    "name": "draw_actions",
    "description": (
        "Draw on the shared whiteboard. Emit an ordered list of drawing actions in "
        "grid coordinates (60 wide x 40 tall, origin top-left, y increases downward). "
        "Actions render one by one in order, like a tutor drawing by hand: structure "
        "first (lines, shapes, arcs), then labels (text/math), then emphasis "
        "(circles, arrows, points)."
    ),
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "actions": {
                "type": "array",
                "description": "Drawing actions, in the order a human tutor would draw them. Usually 3-12; max 24.",
                "items": {
                    "type": "object",
                    "properties": {
                        "op": {
                            "type": "string",
                            "enum": list(DRAW_OPS),
                            "description": (
                                "stroke: freehand polyline, 2-64 points (curves, checkmarks, underlines). "
                                "line/arrow: straight segments, 2-16 points; arrowhead at the LAST point. "
                                "text: one anchor point (top-left) + plain-text content (max 80 chars). "
                                "math: one anchor point + LaTeX content (max 120 chars) rendered as real "
                                "notation - use for fractions, roots, exponents, integrals (e.g. \\frac{a}{b}, \\sqrt{x}). "
                                "point: one point, a small filled dot (plotted coordinates). "
                                "arc: one CENTER point + radius + angles - angle marks, semicircles, circles. "
                                "ellipse/rect: exactly [topLeft, bottomRight]; outline only. "
                                "erase: remove ONE of YOUR OWN earlier marks by target id."
                            ),
                        },
                        "points": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {"type": "number"},
                            },
                            "description": (
                                "Grid coordinates; each point is exactly [gx, gy] with "
                                "gx in [0,60], gy in [0,40]. For arc: the single CENTER point. "
                                "For erase: empty list."
                            ),
                        },
                        "content": {
                            "type": ["string", "null"],
                            "description": (
                                "text op: plain text to write. math op: LaTeX source (no $ delimiters). "
                                "Null for every other op."
                            ),
                        },
                        "color": {
                            "type": "string",
                            "enum": list(COLORS),
                            "description": "blue = new/neutral, green = correct, red = error/attention.",
                        },
                        "size": {
                            "type": ["string", "null"],
                            "description": 'One of "small", "medium", "large", or null (= medium). Sets stroke width, font size, or dot size.',
                        },
                        "style": {
                            "type": ["string", "null"],
                            "description": (
                                'Line style: "solid" (default), "dashed" (construction/auxiliary lines), '
                                '"dotted". Null = solid. Only meaningful on stroke/line/arrow/arc/ellipse/rect.'
                            ),
                        },
                        "radius": {
                            "type": ["number", "null"],
                            "description": "arc only: radius in grid units (0 < r <= 30). Null otherwise.",
                        },
                        "angles": {
                            "type": ["array", "null"],
                            "items": {"type": "number"},
                            "description": (
                                "arc only: [startDeg, endDeg]. 0 deg points along +x; angles run CLOCKWISE "
                                "because y grows downward. Full circle = [0, 360]. Null otherwise."
                            ),
                        },
                        "target": {
                            "type": ["string", "null"],
                            "description": "erase only: the tutor mark's id from BOARD CONTENTS (e.g. 't3'). Null otherwise.",
                        },
                    },
                    "required": [
                        "op", "points", "content", "color", "size", "style",
                        "radius", "angles", "target",
                    ],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["actions"],
        "additionalProperties": False,
    },
    # Canonical worked drawings — behavioral documentation the schema can't express.
    # (Anthropic input_examples; stripped via tool_without_examples on API rejection.)
    "input_examples": [
        {
            # 1) Marking up a student's work: check the right line, circle the error.
            "actions": [
                {"op": "ellipse", "points": [[23, 11], [37, 15]], "content": None,
                 "color": "green", "size": None, "style": None, "radius": None,
                 "angles": None, "target": None},
                {"op": "text", "points": [[38, 12]], "content": "correct", "color": "green",
                 "size": "small", "style": None, "radius": None, "angles": None, "target": None},
                {"op": "ellipse", "points": [[23, 17], [37, 22]], "content": None,
                 "color": "red", "size": None, "style": None, "radius": None,
                 "angles": None, "target": None},
                {"op": "arrow", "points": [[42, 19], [38, 19]], "content": None,
                 "color": "red", "size": None, "style": None, "radius": None,
                 "angles": None, "target": None},
                {"op": "text", "points": [[43, 18]], "content": "sign flips here",
                 "color": "red", "size": "medium", "style": None, "radius": None,
                 "angles": None, "target": None},
            ],
        },
        {
            # 2) Right triangle with real notation and an angle mark.
            "actions": [
                {"op": "line", "points": [[10, 30], [10, 10], [40, 30], [10, 30]],
                 "content": None, "color": "blue", "size": None, "style": None,
                 "radius": None, "angles": None, "target": None},
                {"op": "rect", "points": [[10, 27], [13, 30]], "content": None,
                 "color": "blue", "size": "small", "style": None, "radius": None,
                 "angles": None, "target": None},
                {"op": "arc", "points": [[40, 30]], "content": None, "color": "blue",
                 "size": None, "style": None, "radius": 4, "angles": [180, 215], "target": None},
                {"op": "text", "points": [[4, 19]], "content": "a = 3", "color": "blue",
                 "size": "medium", "style": None, "radius": None, "angles": None, "target": None},
                {"op": "text", "points": [[22, 31]], "content": "b = 4", "color": "blue",
                 "size": "medium", "style": None, "radius": None, "angles": None, "target": None},
                {"op": "math", "points": [[42, 8]], "content": "c = \\sqrt{a^2 + b^2}",
                 "color": "blue", "size": "large", "style": None, "radius": None,
                 "angles": None, "target": None},
            ],
        },
        {
            # 3) Plotting points with dashed axes.
            "actions": [
                {"op": "line", "points": [[8, 35], [52, 35]], "content": None,
                 "color": "blue", "size": None, "style": None, "radius": None,
                 "angles": None, "target": None},
                {"op": "line", "points": [[10, 37], [10, 6]], "content": None,
                 "color": "blue", "size": None, "style": None, "radius": None,
                 "angles": None, "target": None},
                {"op": "point", "points": [[16, 29]], "content": None, "color": "blue",
                 "size": None, "style": None, "radius": None, "angles": None, "target": None},
                {"op": "point", "points": [[22, 23]], "content": None, "color": "blue",
                 "size": None, "style": None, "radius": None, "angles": None, "target": None},
                {"op": "point", "points": [[28, 17]], "content": None, "color": "blue",
                 "size": None, "style": None, "radius": None, "angles": None, "target": None},
                {"op": "line", "points": [[13, 32], [31, 14]], "content": None,
                 "color": "green", "size": None, "style": "dashed", "radius": None,
                 "angles": None, "target": None},
                {"op": "math", "points": [[33, 12]], "content": "y = -x + 45",
                 "color": "green", "size": "medium", "style": None, "radius": None,
                 "angles": None, "target": None},
            ],
        },
        {
            # 4) Correcting your own earlier mark: erase it, redraw it right.
            "actions": [
                {"op": "erase", "points": [], "content": None, "color": "blue",
                 "size": None, "style": None, "radius": None, "angles": None, "target": "t2"},
                {"op": "math", "points": [[24, 18]], "content": "x = \\frac{11 - 3}{2}",
                 "color": "blue", "size": "large", "style": None, "radius": None,
                 "angles": None, "target": None},
            ],
        },
    ],
}


def tool_without_examples(tool: Dict[str, Any]) -> Dict[str, Any]:
    """Copy of a tool definition with input_examples stripped (API-rejection fallback)."""
    return {k: v for k, v in tool.items() if k != "input_examples"}


def parse_actions(raw: Any) -> List[DrawAction]:
    """Validate untrusted tool output into DrawActions (spec §3). Never raises."""
    actions, _ = parse_actions_with_reasons(raw)
    return actions


def parse_actions_with_reasons(raw: Any) -> Tuple[List[DrawAction], List[str]]:
    """Like parse_actions, but also returns the per-action drop reasons.

    The reasons feed the PTC tool_result JSON (spec §9) so Claude's running code can
    self-correct. At most MAX_ACTIONS actions survive.
    """
    reasons: List[str] = []
    if not isinstance(raw, dict):
        reasons.append(f"tool output is not an object: {type(raw).__name__}")
        _log(reasons[-1])
        return [], reasons

    items = raw.get("actions")
    if not isinstance(items, list):
        reasons.append("tool output has no 'actions' list")
        _log(reasons[-1])
        return [], reasons

    actions: List[DrawAction] = []
    for i, item in enumerate(items):
        if len(actions) >= MAX_ACTIONS:
            reasons.append(f"action cap {MAX_ACTIONS} reached; dropped actions {i}..{len(items) - 1}")
            _log(reasons[-1])
            break
        action = _parse_one(item, i, reasons)
        if action is not None:
            actions.append(action)
    return actions, reasons


def _parse_one(item: Any, index: int, reasons: List[str]) -> Optional[DrawAction]:
    """Validate a single raw action; return None (recording the reason) if invalid."""
    if not isinstance(item, dict):
        return _drop(index, "not an object", reasons)

    op = item.get("op")
    if op not in DRAW_OPS:
        return _drop(index, f"unknown op {op!r}", reasons)

    color = item.get("color")
    if color not in COLORS:
        return _drop(index, f"unknown color {color!r}", reasons)

    size = item.get("size")
    if size is not None and size not in SIZES:
        return _drop(index, f"unknown size {size!r}", reasons)

    style = item.get("style")
    if style is not None and style not in STYLES:
        return _drop(index, f"unknown style {style!r}", reasons)
    if op not in _STYLED_OPS:
        style = None

    if op == "erase":
        target = item.get("target")
        if not isinstance(target, str) or not _TUTOR_ALIAS.match(target):
            return _drop(index, f"erase needs a tutor target id, got {target!r}", reasons)
        return DrawAction(op="erase", points=[], color=color, size=size, target=target)

    points = _parse_points(item.get("points"))
    if points is None:
        return _drop(index, "points is not a list of [x, y] numbers", reasons)

    min_pts, max_pts = _POINT_BOUNDS[op]
    if not (min_pts <= len(points) <= max_pts):
        return _drop(index, f"{op} needs {min_pts}-{max_pts} points, got {len(points)}", reasons)

    content: Optional[str] = None
    if op in ("text", "math"):
        content = item.get("content")
        max_chars = MAX_TEXT_CHARS if op == "text" else MAX_MATH_CHARS
        if not isinstance(content, str) or not content.strip():
            return _drop(index, f"{op} needs non-empty content", reasons)
        content = content.strip()[:max_chars]

    radius: Optional[float] = None
    angles: Optional[Tuple[float, float]] = None
    if op == "arc":
        radius = _parse_arc_radius(item.get("radius"))
        if radius is None:
            return _drop(
                index, f"arc needs radius in (0, {MAX_ARC_RADIUS}], got {item.get('radius')!r}", reasons
            )
        angles = _parse_arc_angles(item.get("angles"))
        if angles is None:
            return _drop(
                index, f"arc needs angles [startDeg, endDeg], got {item.get('angles')!r}", reasons
            )

    if op in ("ellipse", "rect"):
        (x1, y1), (x2, y2) = points
        if x2 <= x1 or y2 <= y1:
            return _drop(index, f"{op} needs bottomRight > topLeft, got {points}", reasons)

    return DrawAction(
        op=op, points=points, content=content, color=color, size=size,
        style=style, radius=radius, angles=angles, target=None,
    )


def _parse_arc_radius(raw: Any) -> Optional[float]:
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return None
    if raw <= 0:
        return None
    return min(float(raw), MAX_ARC_RADIUS)


def _parse_arc_angles(raw: Any) -> Optional[Tuple[float, float]]:
    if not isinstance(raw, (list, tuple)) or len(raw) != 2:
        return None
    start, end = raw
    for value in (start, end):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
    if float(start) == float(end):
        return None
    # Cap the sweep at one full turn so a confused model can't emit a 7200-degree arc.
    start_f, end_f = float(start), float(end)
    sweep = end_f - start_f
    if abs(sweep) > 360.0:
        end_f = start_f + (360.0 if sweep > 0 else -360.0)
    return (start_f, end_f)


def _parse_points(raw: Any) -> Optional[List[Tuple[float, float]]]:
    """Coerce raw points to clamped (gx, gy) tuples, or None if malformed."""
    if not isinstance(raw, list):
        return None
    points: List[Tuple[float, float]] = []
    for pair in raw:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            return None
        x, y = pair
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            return None
        if isinstance(x, bool) or isinstance(y, bool):
            return None
        points.append((_clamp(float(x), GRID_WIDTH), _clamp(float(y), GRID_HEIGHT)))
    return points


def _clamp(value: float, upper: float) -> float:
    return max(0.0, min(value, float(upper)))


def _drop(index: int, reason: str, reasons: List[str]) -> None:
    reasons.append(f"action #{index}: {reason}")
    _log(reasons[-1])
    return None


def _log(message: str) -> None:
    print(f"[draw_protocol] {message}")


def summarize_actions(actions: List[DrawAction], plan_hint: Optional[str] = None) -> str:
    """One-line summary of a turn's drawing for TutoringState.already_drawn."""
    counts: Dict[str, int] = {}
    for action in actions:
        counts[action.op] = counts.get(action.op, 0) + 1
    parts = [f"{n} {op}" for op, n in counts.items()]
    summary = f"{len(actions)} marks ({', '.join(parts)})"
    first_text = next(
        (a.content for a in actions if a.op in ("text", "math") and a.content), None
    )
    if first_text:
        summary += f'; text: "{first_text[:40]}"'
    if plan_hint:
        summary = f"{plan_hint}: {summary}"
    return summary


def format_board_elements(board_elements: Optional[List[Dict[str, Any]]]) -> str:
    """Render the frontend's boardElements listing as a prompt block (spec §2).

    Malformed entries are skipped — the listing is advisory context, not critical path.
    """
    if not board_elements:
        return "BOARD CONTENTS: (empty board)"

    lines = ["BOARD CONTENTS (grid coords, 60x40; s* = student ink, t* = your earlier marks):"]
    for entry in board_elements:
        if not isinstance(entry, dict):
            continue
        elem_id = entry.get("id")
        source = entry.get("source")
        elem_type = entry.get("type")
        grid_box = entry.get("gridBox")
        if not (isinstance(elem_id, str) and isinstance(elem_type, str)):
            continue
        if not (isinstance(grid_box, list) and len(grid_box) == 4):
            continue
        x1, y1, x2, y2 = grid_box
        label = "student" if source == "student" else "tutor"
        line = f"  {elem_id} [{label}, {elem_type}] ({x1},{y1})->({x2},{y2})"
        content = entry.get("content")
        if isinstance(content, str) and content:
            line += f': "{content[:MAX_MATH_CHARS]}"'
        lines.append(line)

    if len(lines) == 1:
        return "BOARD CONTENTS: (empty board)"
    return "\n".join(lines)
