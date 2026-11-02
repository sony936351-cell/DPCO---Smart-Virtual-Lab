import os
import tempfile
import pytest

from app import app, init_db


@pytest.fixture
def client():

    fd, path = tempfile.mkstemp()
    os.close(fd)

    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"

    import app as app_module

    old_database = app_module.DATABASE
    app_module.DATABASE = path

    init_db()

    with app.test_client() as client:
        yield client

    app_module.DATABASE = old_database
    os.unlink(path)


def test_register_login_and_dashboard(client):

    response = client.post(
        "/register",
        data={
            "username": "student1",
            "email": "student1@example.com",
            "password": "strongpass123",
            "confirm_password": "strongpass123"
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b"Laboratory Overview" in response.data

    client.get("/logout")

    response = client.post(
        "/login",
        data={
            "identity": "student1",
            "password": "strongpass123"
        }
    )

    assert response.status_code == 302


def test_progress_is_saved_for_logged_in_student(client):

    client.post(
        "/register",
        data={
            "username": "student2",
            "email": "student2@example.com",
            "password": "strongpass123",
            "confirm_password": "strongpass123"
        }
    )

    response = client.post(
        "/api/progress",
        json={
            "module": "Binary Playground",
            "score": 90,
            "completed": True
        }
    )

    assert response.status_code == 200

    data = client.get("/api/progress").get_json()

    assert data[0]["module"] == "Binary Playground"
    assert data[0]["score"] == 90