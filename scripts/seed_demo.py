"""Run deterministic synthetic demo cases through the local P1 engine."""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.decision import make_decision
from backend.schemas.decision import DecisionRequest


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    cases = json.loads(
        (ROOT / "data" / "raw" / "demo_cases.json").read_text(encoding="utf-8")
    )
    outputs = []
    for case in cases:
        request = DecisionRequest(
            applicant=case["applicant"],
            rulebook_version="v1",
            decision_date="2026-09-12",
            language="en",
        )
        result = make_decision(request)
        outputs.append(
            {
                "case_id": case["case_id"],
                "applicant_id": result["applicant_id"],
                "decision": result["decision"],
                "score": result["score"],
                "decision_id": result["decision_id"],
            }
        )
    print(json.dumps(outputs, indent=2, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
