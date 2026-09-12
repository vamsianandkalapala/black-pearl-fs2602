"""Explicit version availability used by replay diagnostics."""


class VersionRegistry:
    def __init__(self):
        self.models = {"v1": {"source": "P1 model manifest"}}
        self.rules = {"v1": {"source": "P1 rules/v1.json"}, "v2": {"source": "P1 rules/v2.json"}}

    def get_model_spec(self, version: str):
        return self.models.get(version)

    def get_rule_spec(self, version: str):
        return self.rules.get(version)
