from datetime import datetime

from flask import Blueprint, jsonify, render_template, request

from .ai.client import generate_reply

bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    return render_template("index.html")


@bp.post("/chat")
def chat():
    data = request.get_json(force=True, silent=True) or {}
    user_message = data.get("message", "")

    ai_message = generate_reply(user_message)

    return jsonify(
        {
            "user": {
                "text": user_message,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            },
            "ai": {
                "text": ai_message,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            },
        }
    )

