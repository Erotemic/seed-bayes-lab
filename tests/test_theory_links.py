"""Check MAGNET static theory links without requiring the full MAGNET runtime.

The full ``magnet.theory`` static extractor is also exercised by the optional
``scripts/report_theory.py`` command. This small test keeps index/declaration
links from silently drifting when Lean or Python names are refactored.
"""

from __future__ import annotations

import ast
from pathlib import Path
import re

import magnet_theory as theory
import yaml

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "theory" / "index.yaml"
SPEC = ROOT / "theory" / "link-spec.yaml"


def _links():
    spec = yaml.safe_load(SPEC.read_text())["theory"]
    for relative in spec["empirical_sources"]:
        source = (SPEC.parent / relative).resolve()
        tree = ast.parse(source.read_text(), filename=str(source))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not (isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "theory"):
                continue
            if node.func.attr not in theory.RELATIONS:
                continue
            assert len(node.args) == 1, (source, node.lineno)
            assert isinstance(node.args[0], ast.Constant), (source, node.lineno)
            assert isinstance(node.args[0].value, str), (source, node.lineno)
            for keyword in node.keywords:
                assert keyword.arg == "note"
                assert isinstance(keyword.value, ast.Constant)
                assert isinstance(keyword.value.value, str)
            yield (str(source.relative_to(ROOT)), node.lineno,
                   node.func.attr, node.args[0].value)


def test_index_declarations_exist_and_premise_names_match_lean():
    data = yaml.safe_load(INDEX.read_text())
    assert data["schema_version"] == 1
    assert data["formalization"]["system"] == "lean4"
    entries = data["entries"]
    assert len(entries) >= 10
    assert len({entry["id"] for entry in entries}) == len(entries)
    for entry in entries:
        declaration = entry["declaration"]
        assert declaration.startswith("SeedBayes.")
        short = declaration.split(".")[-1]
        path = ROOT / entry["source_path"]
        source = path.read_text()
        pattern = re.compile(
            r"(?m)^\s*(?:(?:noncomputable|private)\s+)?"
            r"(?:def|theorem|structure)\s+" + re.escape(short) + r"\b"
        )
        match = pattern.search(source)
        assert match is not None, (entry["id"], declaration, str(path))
        # Compare against the signature, not arbitrary mentions inside the body.
        signature = source[match.end():].split(":=", 1)[0].split(" where\n", 1)[0]
        premise_ids = [p["id"] for p in entry.get("premises", [])]
        assert len(set(premise_ids)) == len(premise_ids)
        for binder in premise_ids:
            assert re.search(r"\b" + re.escape(binder) + r"\b", signature), (
                entry["id"], binder, path
            )


def test_theory_links_resolve_and_use_the_right_relation_kind():
    index = yaml.safe_load(INDEX.read_text())
    entries = {entry["id"]: entry for entry in index["entries"]}
    links = list(_links())
    assert len(links) >= 20
    assert any(relation == "tests" for _, _, relation, _ in links)
    assert any(relation == "approximates" for _, _, relation, _ in links)
    assert any(relation == "checks" for _, _, relation, _ in links)
    for source, line, relation, ref in links:
        target, separator, premise = ref.partition("::")
        assert target in entries, (source, line, ref)
        if separator:
            assert relation in theory.PREMISE_RELATIONS, (source, line, ref)
            assert premise in {p["id"] for p in entries[target].get("premises", [])}, (
                source, line, ref
            )
        else:
            assert relation in theory.STATEMENT_RELATIONS, (source, line, ref)


def test_theory_decorators_do_not_replace_functions():
    def dummy(x: int) -> int:
        return x + 1

    assert theory.approximates("SeedBayes.Bayes.Posterior")(dummy) is dummy
    assert theory.tests("SeedBayes.Bayes.Posterior")(dummy) is dummy
    assert theory.checks("SeedBayes.Bayes.UpdateDelta::hE")(dummy) is dummy


def test_readme_uses_github_display_math_delimiters():
    content = (ROOT / "README.md").read_text()
    assert "\\[" not in content
    assert "\\]" not in content
    assert content.count("$$") == 4
