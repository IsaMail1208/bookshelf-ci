import pytest

from app import create_app


@pytest.fixture
def client():
    # A fresh app per test, so books added in one test do not leak into another.
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_healthz_returns_ok(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_index_describes_service(client):
    body = client.get("/").get_json()

    assert body["service"] == "bookshelf"
    assert "/healthz" in body["endpoints"]


def test_list_books_returns_seed_data(client):
    response = client.get("/api/books")

    assert response.status_code == 200
    titles = [book["title"] for book in response.get_json()]
    assert titles == ["The Phoenix Project", "Accelerate"]


def test_add_book_assigns_next_id(client):
    response = client.post("/api/books", json={"title": "Release It!", "author": "Michael Nygard"})

    assert response.status_code == 201
    assert response.get_json() == {"id": 3, "title": "Release It!", "author": "Michael Nygard"}
    assert len(client.get("/api/books").get_json()) == 3


@pytest.mark.parametrize(
    "payload",
    [{}, {"title": "No author"}, {"author": "No title"}, {"title": "  ", "author": "Blank title"}],
)
def test_add_book_rejects_incomplete_payload(client, payload):
    response = client.post("/api/books", json=payload)

    assert response.status_code == 400
    assert "required" in response.get_json()["error"]


def test_add_book_rejects_non_json_body(client):
    response = client.post("/api/books", data="title=x", content_type="text/plain")

    assert response.status_code == 400
