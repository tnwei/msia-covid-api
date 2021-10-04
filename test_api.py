from main import app, MsianState
from fastapi.testclient import TestClient

client = TestClient(app)


def test_read_summary_national():
    response = client.get("/")
    assert response.status_code == 200
    # assert response.json() == {"msg": "Hello World"}


def test_read_summary_state():
    for i in MsianState:
        print(i)
        response = client.get(f"/?state={i.value}")
        assert response.status_code == 200


def test_read_summary_allstates():
    response = client.get("/?state=allstates")
    assert response.status_code == 200


def test_read_detailed_national():
    response = client.get("/detailed")
    assert response.status_code == 200


def test_read_detailed_state():
    for i in MsianState:
        print(i)
        response = client.get(f"/detailed?state={i.value}")
        assert response.status_code == 200


def test_read_detailed_allstates():
    response = client.get("/detailed?state=allstates")
    assert response.status_code == 200
