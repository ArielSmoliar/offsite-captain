from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.product_api import router


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
    response = client().post("/product/api/coordinate")

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
