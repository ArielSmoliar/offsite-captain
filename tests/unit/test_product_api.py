from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.product_api import router
from app.product_app import app as product_app


def client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_review_exposes_decision_ready_plan() -> None:
    response = client().get("/product/api/review")

    assert response.status_code == 200
    body = response.json()
    assert body["finding_count"] == 0
    assert body["plan"]["offsite_id"] == "offsite-seed-001"
    assert body["reservation_status"].endswith("human_authorization_required")


def test_coordinate_exposes_three_defect_classes_without_reserving() -> None:
    response = client().post(
        "/product/api/coordinate",
        json={"session_hash": "coordinate-test-session"},
    )

    assert response.status_code == 200
    body = response.json()
    assert {finding["code"] for finding in body["findings"]} == {
        "ARRIVAL_BUFFER",
        "DOUBLE_BOOKED",
        "PREP_MISSING",
    }
    assert body["reservation_status"] == "not_created"


def test_http_boundary_requires_authorization_before_reservation() -> None:
    test_client = client()
    review = test_client.get("/product/api/review").json()

    response = test_client.post(
        "/product/api/reserve",
        json={
            "session_hash": "unapproved-http-session",
            "plan_hash": review["plan_hash"],
            "request_key": "http-reserve-before-approval",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "AUTHORIZATION_REQUIRED"


def test_http_boundary_names_stale_plan_recovery() -> None:
    test_client = client()

    response = test_client.post(
        "/product/api/authorize",
        json={
            "session_hash": "stale-plan-session",
            "plan_hash": "0" * 64,
            "idempotency_key": "stale-plan-approval",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "PLAN_CHANGED"


def test_http_boundary_rejects_short_session_identifiers() -> None:
    response = client().post(
        "/product/api/coordinate",
        json={"session_hash": "short"},
    )

    assert response.status_code == 422


def test_standalone_product_routes_page_and_assets_under_same_base() -> None:
    test_client = TestClient(product_app)

    home = test_client.get("/", follow_redirects=False)
    page = test_client.get("/product/")
    script = test_client.get("/product/app.js")
    health = test_client.get("/healthz")
    ready = test_client.get("/readyz")

    assert home.status_code == 307
    assert home.headers["location"] == "/product/"
    assert page.status_code == 200
    assert script.status_code == 200
    assert health.json() == {"status": "ok"}
    assert ready.json() == {"status": "ready"}
