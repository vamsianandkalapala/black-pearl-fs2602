from backend.data.normalization import normalize_applicant
from backend.features.engineering import build_features
from backend.features.registry import ALLOWED_FEATURE_NAMES, FEATURE_REGISTRY


def valid_values() -> dict:
    return {
        "applicant_id": "applicant-001",
        "monthly_income": 30000,
        "monthly_rent": 10000,
        "bank_income": 28000,
        "bank_cashflow": 25000,
        "gig_income": 5000,
        "repayment_history": 8,
        "utility_payment_history": 12,
        "telecom_payment_history": 10,
    }


def test_valid_applicant_generates_expected_features() -> None:
    features = build_features(normalize_applicant(valid_values()))

    assert features["income_to_rent_ratio"] == 3.0
    assert features["bank_income"] == 28000.0
    assert features["gig_income"] == 5000.0


def test_zero_rent_produces_none_ratio() -> None:
    values = {**valid_values(), "monthly_rent": 0}

    features = build_features(normalize_applicant(values))

    assert features["income_to_rent_ratio"] is None


def test_missing_optional_data_stays_missing() -> None:
    values = valid_values()
    values["utility_payment_history"] = None

    features = build_features(normalize_applicant(values))

    assert features["utility_payment_history"] is None


def test_feature_generation_is_deterministic() -> None:
    normalized = normalize_applicant(valid_values())

    assert build_features(normalized) == build_features(normalized)


def test_feature_order_is_deterministic() -> None:
    features = build_features(normalize_applicant(valid_values()))
    expected_order = [
        feature["name"]
        for feature in FEATURE_REGISTRY
        if feature["allowed_model_input"]
    ]

    assert list(features) == expected_order


def test_only_registered_allowed_features_are_produced() -> None:
    values = {**valid_values(), "unregistered_secret": "do not use"}

    features = build_features(normalize_applicant(values))

    assert tuple(features) == ALLOWED_FEATURE_NAMES
    assert "unregistered_secret" not in features


def test_prohibited_attribute_is_not_a_registered_feature() -> None:
    prohibited_names = {"age", "gender", "race", "religion", "disability"}
    registered_names = {feature["name"] for feature in FEATURE_REGISTRY}

    assert prohibited_names.isdisjoint(registered_names)


def test_bank_and_gig_income_can_both_be_features() -> None:
    features = build_features(normalize_applicant(valid_values()))

    assert features["bank_income"] == 28000.0
    assert features["gig_income"] == 5000.0
