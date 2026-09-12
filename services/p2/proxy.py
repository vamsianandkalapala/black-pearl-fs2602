from typing import Any, Dict, List


class ProxyAnalyzer:
    def analyze_feature_proxies(self, features: List[str]) -> Dict[str, Any]:
        prohibited = {"race", "gender", "age", "ethnicity", "religion"}
        direct = sorted(set(features).intersection(prohibited))
        return {
            "status": "LIMITED",
            "direct_prohibited_features": direct,
            "proxy_analysis_performed": False,
            "limitation": "Feature names alone cannot support reconstruction or R-squared proxy analysis.",
        }
