"""Unit tests for the draw protocol validator (spec §3 invariants)."""
from typing import Any, Dict, List, Optional

from app.services.providers.draw_protocol import (
    DRAW_ACTIONS_TOOL,
    GRID_HEIGHT,
    GRID_WIDTH,
    MAX_ACTIONS,
    MAX_ARC_RADIUS,
    MAX_MATH_CHARS,
    DrawAction,
    format_board_elements,
    parse_actions,
    summarize_actions,
    tool_without_examples,
)


def make_action(**overrides: Any) -> Dict[str, Any]:
    """A valid wire-shape stroke action, overridable per test."""
    action: Dict[str, Any] = {
        "op": "stroke",
        "points": [[10, 10], [20, 15], [30, 12]],
        "content": None,
        "color": "blue",
        "size": None,
        "style": None,
        "radius": None,
        "angles": None,
        "target": None,
    }
    action.update(overrides)
    return action


def parse_one(**overrides: Any) -> List[DrawAction]:
    return parse_actions({"actions": [make_action(**overrides)]})


# ─────────────────────────── valid actions per op ───────────────────────────

def test_valid_stroke() -> None:
    actions = parse_one()
    assert len(actions) == 1
    assert actions[0].op == "stroke"
    assert actions[0].points == [(10.0, 10.0), (20.0, 15.0), (30.0, 12.0)]
    assert actions[0].color == "blue"


def test_valid_line_and_arrow() -> None:
    for op in ("line", "arrow"):
        actions = parse_one(op=op, points=[[0, 0], [60, 40]])
        assert len(actions) == 1
        assert actions[0].op == op


def test_valid_text() -> None:
    actions = parse_one(op="text", points=[[5, 5]], content="x^2 + 3x", size="large")
    assert len(actions) == 1
    assert actions[0].content == "x^2 + 3x"
    assert actions[0].size == "large"


def test_valid_ellipse_and_rect() -> None:
    for op in ("ellipse", "rect"):
        actions = parse_one(op=op, points=[[10, 10], [20, 18]], color="red")
        assert len(actions) == 1
        assert actions[0].points == [(10.0, 10.0), (20.0, 18.0)]


def test_valid_erase() -> None:
    actions = parse_one(op="erase", points=[], target="t3")
    assert len(actions) == 1
    assert actions[0].target == "t3"
    assert actions[0].points == []


def test_valid_math() -> None:
    actions = parse_one(op="math", points=[[5, 5]], content="\\frac{a}{b}", size="large")
    assert len(actions) == 1
    assert actions[0].op == "math"
    assert actions[0].content == "\\frac{a}{b}"


def test_valid_point() -> None:
    actions = parse_one(op="point", points=[[16, 29]])
    assert len(actions) == 1
    assert actions[0].points == [(16.0, 29.0)]


def test_valid_arc() -> None:
    actions = parse_one(op="arc", points=[[30, 20]], radius=5, angles=[0, 90])
    assert len(actions) == 1
    assert actions[0].radius == 5.0
    assert actions[0].angles == (0.0, 90.0)


def test_valid_styles() -> None:
    for style in ("solid", "dashed", "dotted"):
        actions = parse_one(op="line", points=[[0, 0], [10, 10]], style=style)
        assert actions[0].style == style


# ─────────────────────────── invariant violations ───────────────────────────

def test_unknown_op_dropped() -> None:
    assert parse_one(op="scribble") == []


def test_unknown_color_dropped() -> None:
    assert parse_one(color="black") == []


def test_unknown_size_dropped() -> None:
    assert parse_one(size="huge") == []


def test_stroke_needs_two_points() -> None:
    assert parse_one(points=[[10, 10]]) == []


def test_stroke_caps_at_64_points() -> None:
    assert parse_one(points=[[i % 60, i % 40] for i in range(65)]) == []


def test_line_caps_at_16_points() -> None:
    assert parse_one(op="line", points=[[i, i % 40] for i in range(17)]) == []


def test_text_requires_content() -> None:
    assert parse_one(op="text", points=[[5, 5]], content=None) == []
    assert parse_one(op="text", points=[[5, 5]], content="   ") == []


def test_text_requires_exactly_one_point() -> None:
    assert parse_one(op="text", points=[[5, 5], [6, 6]], content="hi") == []


def test_text_content_truncated_to_80_chars() -> None:
    actions = parse_one(op="text", points=[[5, 5]], content="a" * 200)
    assert len(actions[0].content) == 80


def test_ellipse_needs_ordered_corners() -> None:
    assert parse_one(op="ellipse", points=[[20, 20], [10, 10]]) == []
    assert parse_one(op="rect", points=[[10, 10], [10, 18]]) == []


def test_erase_rejects_student_target() -> None:
    assert parse_one(op="erase", points=[], target="s3") == []
    assert parse_one(op="erase", points=[], target=None) == []
    assert parse_one(op="erase", points=[], target="t3x") == []


def test_malformed_points_dropped() -> None:
    assert parse_one(points="not a list") == []
    assert parse_one(points=[[1, 2], [3]]) == []
    assert parse_one(points=[[1, "a"], [3, 4]]) == []
    assert parse_one(points=[[True, 2], [3, 4]]) == []


def test_unknown_style_dropped() -> None:
    assert parse_one(op="line", points=[[0, 0], [1, 1]], style="wavy") == []


def test_style_nulled_on_unstyled_ops() -> None:
    actions = parse_one(op="text", points=[[5, 5]], content="hi", style="dashed")
    assert actions[0].style is None
    actions = parse_one(op="point", points=[[5, 5]], style="dotted")
    assert actions[0].style is None


def test_math_requires_content_and_caps_length() -> None:
    assert parse_one(op="math", points=[[5, 5]], content=None) == []
    assert parse_one(op="math", points=[[5, 5]], content="  ") == []
    actions = parse_one(op="math", points=[[5, 5]], content="x" * 500)
    assert len(actions[0].content) == MAX_MATH_CHARS


def test_math_requires_exactly_one_point() -> None:
    assert parse_one(op="math", points=[[5, 5], [6, 6]], content="x") == []


def test_point_requires_exactly_one_point() -> None:
    assert parse_one(op="point", points=[[5, 5], [6, 6]]) == []


def test_arc_invariants() -> None:
    assert parse_one(op="arc", points=[[30, 20]], radius=None, angles=[0, 90]) == []
    assert parse_one(op="arc", points=[[30, 20]], radius=0, angles=[0, 90]) == []
    assert parse_one(op="arc", points=[[30, 20]], radius=-3, angles=[0, 90]) == []
    assert parse_one(op="arc", points=[[30, 20]], radius=True, angles=[0, 90]) == []
    assert parse_one(op="arc", points=[[30, 20]], radius=5, angles=None) == []
    assert parse_one(op="arc", points=[[30, 20]], radius=5, angles=[90]) == []
    assert parse_one(op="arc", points=[[30, 20]], radius=5, angles=[90, 90]) == []
    assert parse_one(op="arc", points=[[30, 20]], radius=5, angles=["a", 90]) == []
    assert parse_one(op="arc", points=[[30, 20], [1, 1]], radius=5, angles=[0, 90]) == []


def test_arc_radius_clamped() -> None:
    actions = parse_one(op="arc", points=[[30, 20]], radius=999, angles=[0, 90])
    assert actions[0].radius == MAX_ARC_RADIUS


def test_arc_sweep_capped_at_full_turn() -> None:
    actions = parse_one(op="arc", points=[[30, 20]], radius=5, angles=[0, 7200])
    assert actions[0].angles == (0.0, 360.0)
    actions = parse_one(op="arc", points=[[30, 20]], radius=5, angles=[0, -7200])
    assert actions[0].angles == (0.0, -360.0)


# ────────────────────────── clamping, caps, raw shapes ──────────────────────

def test_out_of_bounds_coordinates_clamped() -> None:
    actions = parse_one(points=[[-5, -5], [999, 999]])
    assert actions[0].points == [(0.0, 0.0), (float(GRID_WIDTH), float(GRID_HEIGHT))]


def test_action_cap() -> None:
    raw = {"actions": [make_action() for _ in range(MAX_ACTIONS + 10)]}
    assert len(parse_actions(raw)) == MAX_ACTIONS


def test_invalid_action_dropped_others_survive() -> None:
    raw = {"actions": [make_action(), make_action(op="nope"), make_action(color="red")]}
    actions = parse_actions(raw)
    assert [a.color for a in actions] == ["blue", "red"]


def test_malformed_raw_shapes() -> None:
    assert parse_actions(None) == []
    assert parse_actions("[]") == []
    assert parse_actions({}) == []
    assert parse_actions({"actions": "nope"}) == []
    assert parse_actions({"actions": [None, 42, "x"]}) == []


def test_to_dict_round_trip() -> None:
    [action] = parse_one()
    wire = action.to_dict()
    assert wire["op"] == "stroke"
    assert wire["points"] == [[10.0, 10.0], [20.0, 15.0], [30.0, 12.0]]
    assert set(wire) == {
        "op", "points", "content", "color", "size", "style", "radius", "angles", "target",
    }


def test_arc_to_dict_serializes_angles_as_list() -> None:
    [action] = parse_one(op="arc", points=[[30, 20]], radius=5, angles=[0, 90])
    wire = action.to_dict()
    assert wire["angles"] == [0.0, 90.0]
    assert wire["radius"] == 5.0


# ───────────────────────── tool schema / input_examples ─────────────────────

def test_input_examples_all_parse_cleanly() -> None:
    """Every example shipped to the API must survive our own validator intact."""
    for example in DRAW_ACTIONS_TOOL["input_examples"]:
        actions = parse_actions(example)
        assert len(actions) == len(example["actions"])


def test_tool_without_examples() -> None:
    stripped = tool_without_examples(DRAW_ACTIONS_TOOL)
    assert "input_examples" not in stripped
    assert stripped["name"] == "draw_actions"
    assert "input_examples" in DRAW_ACTIONS_TOOL  # original untouched


# ────────────────────────────── summaries ───────────────────────────────────

def test_summarize_actions() -> None:
    actions = parse_actions({"actions": [
        make_action(),
        make_action(op="text", points=[[5, 5]], content="area = l x w"),
        make_action(op="arrow", points=[[0, 0], [10, 10]]),
    ]})
    summary = summarize_actions(actions, plan_hint="worked_example")
    assert summary.startswith("worked_example: 3 marks")
    assert "1 stroke" in summary
    assert 'text: "area = l x w"' in summary


def test_summarize_without_hint() -> None:
    actions = parse_one()
    assert summarize_actions(actions) == "1 marks (1 stroke)"


# ─────────────────────────── board listing block ─────────────────────────────

def test_format_board_elements_empty() -> None:
    assert format_board_elements(None) == "BOARD CONTENTS: (empty board)"
    assert format_board_elements([]) == "BOARD CONTENTS: (empty board)"


def test_format_board_elements_listing() -> None:
    block = format_board_elements([
        {"id": "s1", "source": "student", "type": "freedraw",
         "gridBox": [10, 4, 22, 9], "content": None},
        {"id": "t2", "source": "tutor", "type": "text",
         "gridBox": [30, 4, 43, 6], "content": "2x + 3 = 11"},
    ])
    assert "s1 [student, freedraw] (10,4)->(22,9)" in block
    assert 't2 [tutor, text] (30,4)->(43,6): "2x + 3 = 11"' in block


def test_format_board_elements_skips_malformed() -> None:
    block = format_board_elements([
        "garbage",
        {"id": "s1"},
        {"id": "s2", "source": "student", "type": "freedraw", "gridBox": [1, 2, 3]},
    ])
    assert block == "BOARD CONTENTS: (empty board)"
