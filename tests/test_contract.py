import ast
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest


SOURCE = (Path(__file__).parents[1] / "contracts" / "contract.py").read_text()
TREE = ast.parse(SOURCE)


def helpers():
    names = {"clean", "normalize_lot", "bounded_intervals", "https_source"}
    nodes = [node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name in names]
    scope = {"urlsplit": urlsplit, "unquote": unquote}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "<contract>", "exec"), scope)
    return scope


def test_lot_identifier_is_canonical_and_bounded():
    assert helpers()["normalize_lot"]("  lot-a7 ") == "LOT-A7"
    assert len(helpers()["normalize_lot"]("x" * 100)) == 64


def test_empty_lot_identifier_is_rejected():
    with pytest.raises(ValueError, match="lot id"):
        helpers()["normalize_lot"]("")


def test_https_source_normalizes_origin():
    raw, origin = helpers()["https_source"]("https://Sensor.Example.net/export/17")
    assert raw.endswith("/export/17")
    assert origin == "sensor.example.net"


@pytest.mark.parametrize(
    "url",
    [
        "ftp://sensor.example.net/export",
        "https://user:key@sensor.example.net/export",
        "https://sensor.example.net/a/%2e%2e/export",
        "https://sensor.example.net/export#latest",
    ],
)
def test_unsafe_sources_are_rejected(url):
    with pytest.raises(ValueError):
        helpers()["https_source"](url)


def test_breached_intervals_keep_only_attributed_bounded_rows():
    rows = [
        {"start": "10:00", "end": "10:15", "source_index": 2},
        {"start": "10:00", "end": "10:15", "source_index": 2},
        {"start": "", "end": "11:00", "source_index": 2},
        {"start": "12:00", "end": "12:30", "source_index": 9},
    ]
    assert helpers()["bounded_intervals"](rows, 4) == [{"start": "10:00", "end": "10:15", "source_index": 2}]


def test_consensus_and_attribution_requirements_are_explicit():
    assert "complete attributed custody disposition required" in SOURCE
    assert "all source digests must match exactly" in SOURCE
    assert "len(citations) < 3" in SOURCE


def test_lifecycle_methods_and_terminal_states_exist():
    for method in ("seal_lot", "inspect_receipt", "acknowledge", "cancel_before_receipt", "get_lot"):
        assert f"def {method}" in SOURCE
    for state in ("SEALED", "INSPECTED", "RECEIVED", "QUARANTINED", "CANCELLED"):
        assert f'"{state}"' in SOURCE


def test_counterparty_and_replay_guards_are_present():
    assert "key in self.lots" in SOURCE
    assert "gl.message.sender_address != lot.receiver" in SOURCE
    assert "gl.message.sender_address != lot.shipper" in SOURCE
    assert "four independent source origins required" in SOURCE

