import math
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.data.validation import validate_applicant
from backend.data.normalization import normalize_applicant
from backend.features.engineering import build_features
from backend.model.predict import predict_score
from backend.schemas.applicant import Applicant
from backend.decision import make_decision
from backend.schemas.decision import DecisionRequest


app = FastAPI(
    title="BLACK PEARL Decision Engine",
    description="Foundation API for reproducible FS-2602 credit decisioning.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8080", "http://localhost:8080"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def _safe_validation_value(value):
    """Remove non-JSON numeric values from validation error details."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, BaseException):
        return str(value)
    if isinstance(value, dict):
        sanitized = {
            key: _safe_validation_value(item)
            for key, item in value.items()
            if key not in {"input", "ctx"}
        }
        if value.get("type") == "extra_forbidden":
            sanitized["loc"] = list(value.get("loc", []))[:-1]
            sanitized["msg"] = "Unexpected applicant field."
        return sanitized
    if isinstance(value, list):
        return [_safe_validation_value(item) for item in value]
    return value


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_, error: RequestValidationError):
    """Return deterministic validation errors without leaking invalid JSON."""
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "invalid_request",
                "message": "Request validation failed.",
                "details": _safe_validation_value(error.errors()),
            }
        },
    )

METRICS = {
    "validation_requests_total": 0,
    "feature_generation_requests_total": 0,
    "score_requests_total": 0,
    "decision_requests_total": 0,
    "approved_decisions_total": 0,
    "declined_decisions_total": 0,
    "data_quality_flags_total": 0,
}


@app.get("/healthz")
def health_check() -> dict[str, str]:
    """Report whether the API process is running."""
    return {"status": "ok"}


@app.get("/rules/{version}")
def rules_endpoint(version: str) -> dict:
    """Expose the selected data-driven rulebook for display by an adapter."""
    from backend.rules.engine import load_rulebook
    from backend.integrity import sha256_file

    rulebook = load_rulebook(version)
    rules_path = Path(__file__).resolve().parents[2] / "rules" / f"{version}.json"
    return {
        "version": rulebook["version"],
        "effective_date": rulebook["effective_date"],
        "rules": rulebook["rules"],
        "sha256": sha256_file(rules_path),
    }


@app.post("/validate")
def validate_endpoint(applicant: Applicant) -> dict:
    """Validate applicant data without making a credit decision."""
    METRICS["validation_requests_total"] += 1
    return validate_applicant(applicant)


@app.post("/features")
def features_endpoint(applicant: Applicant) -> dict:
    """Return deterministic features without making a credit decision."""
    METRICS["feature_generation_requests_total"] += 1
    normalized_applicant = normalize_applicant(applicant)
    return build_features(normalized_applicant)


@app.post("/score")
def score_endpoint(applicant: Applicant) -> dict:
    """Return a model score without applying approval or decline rules."""
    METRICS["score_requests_total"] += 1
    normalized_applicant = normalize_applicant(applicant)
    features = build_features(normalized_applicant)
    try:
        return predict_score(features)
    except (OSError, EOFError, KeyError, ValueError, ImportError) as error:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "model_unavailable",
                "message": "Scoring model is unavailable or incompatible.",
            },
        ) from error


@app.post("/decision")
def decision_endpoint(request: DecisionRequest) -> dict:
    """Return a versioned, policy-based decision package."""
    METRICS["decision_requests_total"] += 1
    try:
        result = make_decision(request)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (OSError, EOFError, ImportError) as error:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "model_unavailable",
                "message": "Decision engine model is unavailable or incompatible.",
            },
        ) from error
    except (ValueError, KeyError) as error:
        raise HTTPException(
            status_code=400,
            detail={"code": "invalid_decision_request", "message": str(error)},
        ) from error

    if result["decision"] == "APPROVED":
        METRICS["approved_decisions_total"] += 1
    else:
        METRICS["declined_decisions_total"] += 1
    if result["data_quality"]["signals"]:
        METRICS["data_quality_flags_total"] += 1
    return result


@app.get("/metrics", response_class=PlainTextResponse)
def metrics_endpoint() -> str:
    """Expose simple domain-specific counters in Prometheus text format."""
    lines = [
        "# HELP decision_validation_requests_total Applicant validation requests.",
        "# TYPE decision_validation_requests_total counter",
        f"decision_validation_requests_total {METRICS['validation_requests_total']}",
        "# HELP decision_feature_generation_requests_total Feature generation requests.",
        "# TYPE decision_feature_generation_requests_total counter",
        f"decision_feature_generation_requests_total {METRICS['feature_generation_requests_total']}",
        "# HELP decision_score_requests_total Model score requests.",
        "# TYPE decision_score_requests_total counter",
        f"decision_score_requests_total {METRICS['score_requests_total']}",
        "# HELP credit_decisions_total Final policy decisions.",
        "# TYPE credit_decisions_total counter",
        f"credit_decisions_total {METRICS['decision_requests_total']}",
        "# HELP credit_approvals_total Approved decisions.",
        "# TYPE credit_approvals_total counter",
        f"credit_approvals_total {METRICS['approved_decisions_total']}",
        "# HELP credit_declines_total Declined decisions.",
        "# TYPE credit_declines_total counter",
        f"credit_declines_total {METRICS['declined_decisions_total']}",
        "# HELP credit_data_quality_flags_total Decisions with quality flags.",
        "# TYPE credit_data_quality_flags_total counter",
        f"credit_data_quality_flags_total {METRICS['data_quality_flags_total']}",
    ]
    return "\n".join(lines) + "\n"
