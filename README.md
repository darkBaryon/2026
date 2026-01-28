## AI 客服 Demo 项目结构（Controller - Service - Adapter）

```text
.
├── app/
│   ├── __init__.py              # Flask 应用工厂（create_app）
│   ├── routes.py                # Controller：Web 路由 & 接口（/、/chat）
│   ├── core/
│   │   └── llm/                 # Adapter：对接不同大模型提供商
│   │       ├── __init__.py
│   │       ├── base.py          # 抽象基类 BaseLLMClient
│   │       ├── openai_client.py # OpenAI / 兼容接口适配器
│   │       └── factory.py       # 工厂：根据 AI_PROVIDER 选择具体 Client
│   ├── services/
│   │   ├── __init__.py
│   │   └── chat_service.py      # Service：业务逻辑，构建 messages、调用 LLM
│   └── templates/
│       └── index.html           # 前端聊天页面（简单 UI）
├── run.py                       # 本地开发启动入口
├── requirements.txt             # Python 依赖
└── README.md                    # 项目说明
```

### 快速开始（本地运行）

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

### 环境变量说明

- `AI_API_KEY`：大模型服务的 API Key（必填）
- `AI_BASE_URL`：Chat Completions 接口地址，默认为 `https://api.openai.com/v1/chat/completions`
- `AI_MODEL`：模型名称，例如 `gpt-4.1-mini`、`deepseek-chat` 等
- `AI_TIMEOUT`：请求超时时间（秒，可选，默认 20）
- `AI_PROVIDER`：当前仅支持 `openai`（默认），未来可扩展 `deepseek`、`claude` 等

