from datetime import datetime

from flask import Blueprint, jsonify, render_template, request

from app.services import ChatService

bp = Blueprint("main", __name__)

# 简单场景下直接在模块级维护一个 Service 实例即可。
chat_service = ChatService()


@bp.get("/")
def index():
    return render_template("index.html", history=chat_service.history)


@bp.post("/chat")
def chat():
    """
    Controller 层：
    - 解析请求参数
    - 调用 Service 层处理业务
    - 组装响应返回给前端
    """
    data = request.get_json(force=True, silent=True) or {}
    user_message = data.get("message", "")

    ai_message = chat_service.handle_chat(user_message)

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

