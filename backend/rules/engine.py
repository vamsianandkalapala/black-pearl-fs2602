"""Load and evaluate versioned rules stored as JSON data."""

import json
import re
from pathlib import Path
from datetime import date
from typing import Any, Dict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RULES_DIRECTORY = PROJECT_ROOT / "rules"


def load_rulebook(version: str, rules_directory: Path = RULES_DIRECTORY) -> Dict[str, Any]:
    """Load a rulebook by version without requiring source-code changes."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", version):
        raise ValueError("Invalid rulebook version.")
    directory = Path(rules_directory).resolve()
    path = (directory / f"{version}.json").resolve()
    if path.parent != directory:
        raise ValueError("Invalid rulebook path.")
    if not path.exists():
        raise FileNotFoundError(f"Unknown rulebook version: {version}")
    rulebook = json.loads(path.read_text(encoding="utf-8"))
    if (
        rulebook.get("version") != version
        or not isinstance(rulebook.get("effective_date"), str)
        or not isinstance(rulebook.get("rules"), list)
    ):
        raise ValueError("Rulebook must contain matching version and rules list.")
    date.fromisoformat(rulebook["effective_date"])
    rule_ids = set()
    for rule in rulebook["rules"]:
        required = {
            "rule_id",
            "rulebook_version",
            "effective_from",
            "priority",
            "condition",
            "action",
            "active",
        }
        if not isinstance(rule, dict) or not required.issubset(rule):
            raise ValueError("Rule is missing required fields.")
        if rule["rule_id"] in rule_ids:
            raise ValueError(f"Duplicate rule ID: {rule['rule_id']}")
        rule_ids.add(rule["rule_id"])
        if rule["rulebook_version"] != version:
            raise ValueError("Rule version does not match rulebook version.")
        date.fromisoformat(rule["effective_from"])
        if rule.get("effective_to"):
            date.fromisoformat(rule["effective_to"])
            if rule["effective_to"] < rule["effective_from"]:
                raise ValueError(f"Rule has invalid effective range: {rule['rule_id']}")
        if rule["action"] not in {"APPROVED", "DECLINED"}:
            raise ValueError(f"Unsupported rule action: {rule['action']}")
        if not isinstance(rule["priority"], int):
            raise ValueError("Rule priority must be an integer.")
        condition = rule["condition"]
        if (
            not isinstance(condition, dict)
            or condition.get("operator") not in {"gte", "gt", "lte", "lt", "eq", "exists"}
            or not isinstance(condition.get("field"), str)
        ):
            raise ValueError(f"Invalid condition in rule: {rule['rule_id']}")
    return rulebook


def _condition_matches(condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
    """Evaluate the small, generic condition vocabulary used by rule JSON."""
    actual = context.get(condition["field"])
    expected = condition.get("value")
    operator = condition["operator"]
    if operator == "gte":
        return actual is not None and actual >= expected
    if operator == "gt":
        return actual is not None and actual > expected
    if operator == "lte":
        return actual is not None and actual <= expected
    if operator == "lt":
        return actual is not None and actual < expected
    if operator == "eq":
        return actual == expected
    if operator == "exists":
        return actual is not None
    raise ValueError(f"Unsupported rule operator: {operator}")


def evaluate_rulebook(
    rulebook: Dict[str, Any],
    context: Dict[str, Any],
    decision_date: str,
) -> Dict[str, Any]:
    """Return the first active, matching rule in deterministic priority order."""
    matches = []
    for rule in rulebook["rules"]:
        if not rule.get("active", False):
            continue
        if rule["rulebook_version"] != rulebook["version"]:
            continue
        if decision_date < rule["effective_from"]:
            continue
        if rule.get("effective_to") and decision_date > rule["effective_to"]:
            continue
        if _condition_matches(rule["condition"], context):
            matches.append(rule)
    if not matches:
        raise ValueError("No active rule matched the decision context.")
    selected = sorted(matches, key=lambda item: (item["priority"], item["rule_id"]))[0]
    return {
        "rule_id": selected["rule_id"],
        "rulebook_version": rulebook["version"],
        "action": selected["action"],
        "reason": selected["reason"],
        "description": selected["description"],
    }


def load_rules(rule_file_path: str) -> dict:
    """Backward-compatible loader for callers that provide a JSON path."""
    path = Path(rule_file_path)
    return json.loads(path.read_text(encoding="utf-8"))
