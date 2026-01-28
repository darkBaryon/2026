## AI 客服 Demo 项目结构

```text
.
├── app/
│   ├── __init__.py        # Flask 应用工厂（create_app）
│   ├── routes.py          # Web 路由 & 接口（/、/chat）
│   ├── ai/
│   │   ├── __init__.py    # 导出 generate_reply
│   │   └── client.py      # AI 交互模块（封装大模型 HTTP 调用）
│   └── templates/
│       └── index.html     # 前端聊天页面
├── run.py                 # 本地开发启动入口
├── requirements.txt       # Python 依赖
└── README.md              # 项目说明
```

### 快速开始

1. 安装依赖

```bash
pip install -r requirements.txt
```

2. 配置环境变量（以 OpenAI / 兼容接口为例）

```bash
export AI_API_KEY="你的真实API密钥"
export AI_BASE_URL="https://api.openai.com/v1/chat/completions"
export AI_MODEL="gpt-4.1-mini"
```

3. 启动服务

```bash
python run.py
```

4. 浏览器访问

在浏览器中打开：`http://127.0.0.1:5000`

