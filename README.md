## AI 客服 Demo 项目结构（Controller - Service - Adapter + RAG）

```text
.
├── app/
│   ├── __init__.py              # Flask 应用工厂（create_app + 日志初始化）
│   ├── routes.py                # Controller：Web 路由 & 接口（/、/chat）
│   ├── core/
│   │   ├── llm/                 # Adapter：对接不同大模型提供商
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # 抽象基类 BaseLLMClient
│   │   │   ├── openai_client.py # OpenAI / 兼容接口适配器（使用官方 SDK）
│   │   │   ├── factory.py       # 工厂：根据 AI_PROVIDER 选择具体 Client
│   │   │   └── llm_config.json  # LLM 配置（模型、温度、base_url 等）
│   │   ├── logger.py            # 全局日志配置（彩色控制台 + 文件轮转）
│   │   └── prompt_manager.py    # Prompt 模板管理器（Jinja2，支持热更新）
│   ├── prompts/                 # Prompt 模板目录（与代码解耦）
│   │   ├── __init__.py
│   │   └── system_chat.j2       # 主系统提示词模板（Jinja2 语法）
│   ├── services/
│   │   ├── __init__.py
│   │   └── chat_service.py     # Service：NLU → Query → NLG 标准 RAG 流程
│   └── templates/
│       └── index.html           # 前端聊天页面（简单 UI）
├── data/                        # 数据层（独立于 app/）
│   ├── __init__.py
│   ├── house_data.py            # Mock 房源数据源（MOCK_HOUSES）
│   └── house_repository.py      # Repository：房源查询接口（按区域/预算）
├── logs/                        # 日志目录（自动创建，已加入 .gitignore）
│   └── app.log                  # 应用日志（轮转，单文件 10MB，保留 10 个备份）
├── run.py                       # 本地开发启动入口
├── requirements.txt             # Python 依赖
└── README.md                    # 项目说明
```

### 架构说明

- **Controller 层** (`routes.py`): 解析 HTTP 请求，调用 Service，返回 JSON
- **Service 层** (`chat_service.py`): 实现 **NLU（参数提取）→ Query（查库）→ NLG（生成回复）** 的 RAG 流程
- **Adapter 层** (`core/llm/`): 抽象大模型接口，支持多 Provider（OpenAI / DeepSeek 等）
- **Repository 层** (`data/house_repository.py`): 封装数据查询逻辑，与业务层解耦
- **Prompt 管理** (`prompts/` + `prompt_manager.py`): 使用 Jinja2 模板，支持热更新

### 快速开始（本地运行）

1. **安装依赖**

```bash
pip install -r requirements.txt
```

2. **配置环境变量（以 OpenAI / 兼容接口为例）**

```bash
export AI_API_KEY="你的真实API密钥"
export AI_BASE_URL="https://api.openai.com/v1/chat/completions"
export AI_MODEL="gpt-4.1-mini"
```

或者使用配置文件 `app/core/llm/llm_config.json`：

```json
{
  "active_provider": "openai",
  "providers": {
    "openai": {
      "model": "gpt-4-turbo",
      "temperature": 0.7,
      "base_url": "https://api.openai.com/v1"
    },
    "deepseek": {
      "model": "deepseek-chat",
      "temperature": 0.3,
      "base_url": "https://api.deepseek.com"
    }
  }
}
```

3. **启动服务**

```bash
python run.py
```

4. **浏览器访问**

在浏览器中打开：`http://127.0.0.1:5000`

### 环境变量说明

- `AI_API_KEY` / `OPENAI_API_KEY`：大模型服务的 API Key（必填，优先使用 `OPENAI_API_KEY`）
- `AI_BASE_URL`：Chat Completions 接口地址，默认为 `https://api.openai.com/v1/chat/completions`
- `AI_MODEL`：模型名称，例如 `gpt-4.1-mini`、`deepseek-chat` 等
- `AI_TIMEOUT`：请求超时时间（秒，可选，默认 20）
- `AI_PROVIDER`：当前仅支持 `openai`（默认），未来可扩展 `deepseek`、`claude` 等

### 功能特性

- ✅ **标准 RAG 流程**：NLU（参数提取）→ Query（Repository 查库）→ NLG（模板 + LLM 生成）
- ✅ **多 Provider 支持**：通过 Factory 模式轻松切换 OpenAI / DeepSeek 等
- ✅ **Prompt 模板化**：使用 Jinja2 管理提示词，支持热更新，与代码完全解耦
- ✅ **日志系统**：彩色控制台输出 + 文件轮转，便于开发调试和生产排查
- ✅ **分层架构**：Controller - Service - Adapter - Repository，职责清晰

### 开发提示

- **修改 Prompt**：直接编辑 `app/prompts/system_chat.j2`，修改后立即生效（热更新）
- **查看日志**：控制台输出彩色日志，文件日志保存在 `logs/app.log`
- **添加新 Provider**：在 `app/core/llm/` 下实现新的 Client 类，继承 `BaseLLMClient`，在 `factory.py` 中注册
