"""Provides a small application for the container deployment demo.
The /health endpoint reports application status and the deployed Git SHA.
The /chat endpoint returns a fixed reply to verify a real request.
"""

"""Small deployment demo; /chat returns a fixed response without an LLM."""
import logging
import os

from flask import Flask, jsonify, request
from waitress import serve

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


@app.get("/health")
def health():
    return jsonify(status="ok", version=os.getenv("APP_VERSION", "local"))


@app.post("/chat")
def chat():
    body = request.get_json(silent=True)
    message = body.get("message") if isinstance(body, dict) else None
    if not isinstance(message, str) or not message.strip():
        return jsonify(error="Provide a non-empty message string."), 400
    if len(message) > 1000:
        return jsonify(error="Message must be at most 1000 characters."), 400
    app.logger.info("Chat request handled")
    return jsonify(reply=f"Application received: {message.strip()}")


if __name__ == "__main__":
    app.logger.info("Application starting on port 8080")
    serve(app, host="0.0.0.0", port=8080)
