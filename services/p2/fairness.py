from typing import Any, Dict


class FairnessAuditor:
    PROHIBITED = {"race", "gender", "age", "ethnicity", "religion"}

    def check_prohibited_attributes(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        found = [key for key in inputs if key.lower() in self.PROHIBITED]
        return {
            "criterion": "prohibited-input-presence",
            "passed": not found,
            "prohibited_found": found,
            "limitation": "This is not approval-rate or error-rate parity analysis.",
        }
