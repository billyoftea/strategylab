"""Offline unit tests (no Qlib data needed)."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from strategylab.spec import FactorSpec
from strategylab.sources.manual import from_expression


def test_factorspec_infers_fields():
    s = FactorSpec(name="mom", description="x", expression="Mean($close, 20)")
    assert "close" in s.fields


def test_factorspec_requires_expr_or_code():
    try:
        FactorSpec(name="x", description="x")
        assert False, "should have raised"
    except ValueError:
        pass


def test_manual_source_builds_spec():
    s = from_expression("($close - $open) / $open")
    assert s.expression.startswith("($close")
    assert s.source == "manual"
    assert "close" in s.fields and "open" in s.fields


def test_factorspec_roundtrip_json():
    s = FactorSpec(name="mom", description="x", expression="Mean($close,20)")
    s2 = FactorSpec.from_dict(__import__("json").loads(s.to_json()))
    assert s2.expression == s.expression
