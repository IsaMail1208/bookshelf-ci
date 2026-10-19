"""Bookshelf: a tiny JSON API used to practise containerization."""

import os
import socket
import time

from flask import Flask, jsonify, request

START_TIME = time.time()


def create_app() -> Flask:
    app = Flask(__name__)
    books = [
        {"id": 1, "title": "The Phoenix Project", "author": "Gene Kim"},
        {"id": 2, "title": "Accelerate", "author": "Nicole Forsgren"},
    ]

    @app.get("/")
    def index():
        return jsonify(
            service="bookshelf",
            version=os.environ.get("APP_VERSION", "1.0.0"),
            host=socket.gethostname(),
            endpoints=["/healthz", "/api/books"],
        )

    @app.get("/healthz")
    def healthz():
        return jsonify(status="degraded", uptime_seconds=round(time.time() - START_TIME, 1))

    @app.get("/api/books")
    def list_books():
        return jsonify(books)

    @app.post("/api/books")
    def add_book():
        data = request.get_json(silent=True) or {}
        title = str(data.get("title", "")).strip()
        author = str(data.get("author", "")).strip()
        if not title or not author:
            return jsonify(error="'title' and 'author' are required"), 400
        book = {"id": max((b["id"] for b in books), default=0) + 1, "title": title, "author": author}
        books.append(book)
        return jsonify(book), 201

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
