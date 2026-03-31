# MCP Gateway

统一管理所有 MCP 服务的 HTTP 网关。将多个 MCP Server 聚合为一个 Streamable HTTP 端点，提供 Web 管理界面。

## 功能特性

- **服务聚合** — 将多个 STDIO MCP Server 聚合为单一 HTTP 端点（Streamable HTTP）
- **GitHub 导入** — 输入 GitHub URL 自动克隆、检测项目类型、启动服务，支持指定分支
- **手动配置** — 支持手动配置本地 MCP Server（command + args + env）
- **Web 管理界面** — 现代化前端，服务管理、工具浏览、配置编辑、日志查看
- **身份认证** — JWT 登录 + API Key 认证，Web UI 和 MCP 端点统一保护
- **自动运维** — 定时 Git 拉取更新、健康检查、异常自动重启
- **工具调用日志** — 记录每次 MCP 工具调用的参数和返回结果
- **多语言** — 中文 / English 切换
- **Docker 部署** — 多阶段构建，支持 amd64 / arm64

## 快速开始

### Docker 部署（推荐）

```bash
# 克隆项目
git clone https://github.com/thsrite/mcp-gateway.git
cd mcp-gateway

# 启动
docker compose up -d
```

### 手动部署

```bash
# 后端
pip install .
python run.py

# 前端（开发模式）
cd frontend
npm install
npm run dev
```

### 访问

- **Web UI**: http://localhost:9000
- **MCP 端点**: http://localhost:9001/mcp

## MCP 客户端配置

### Claude Desktop

```json
{
  "mcpServers": {
    "gateway": {
      "url": "http://localhost:9001/mcp"
    }
  }
}
```

### 带认证的配置

开启认证后，在设置页面获取 API Key，MCP 客户端配置 Bearer Token 即可：

```
Authorization: Bearer <your-api-key>
```

## 配置文件

`config.yaml`:

```yaml
server:
  host: "0.0.0.0"
  port: 9000

database:
  url: "sqlite+aiosqlite:///data/gateway.db"

repos:
  base_dir: "data/repos"

scheduler:
  update_interval_minutes: 30
  health_check_interval_seconds: 60

log:
  max_lines_per_server: 1000

auth:
  enabled: false
  secret_key: "your-secret-key"
  token_expire_minutes: 1440
```

## 架构

```
┌─────────────────────────────────────────────┐
│  Web UI (:9000)          MCP Endpoint (:9001)│
│  ┌──────────┐            ┌──────────────┐   │
│  │ FastAPI  │            │ Starlette    │   │
│  │ REST API │            │ Streamable   │   │
│  └────┬─────┘            │ HTTP         │   │
│       │                  └──────┬───────┘   │
│       └────────┬───────────────┘            │
│           ┌────▼────┐                       │
│           │Aggregator│ ← 工具/资源/提示词聚合│
│           └────┬────┘                       │
│       ┌────────┼────────┐                   │
│  ┌────▼──┐ ┌───▼───┐ ┌──▼───┐              │
│  │Server1│ │Server2│ │ServerN│  ← STDIO    │
│  └───────┘ └───────┘ └──────┘              │
└─────────────────────────────────────────────┘
```

## 技术栈

**后端**: Python 3.11+ / FastAPI / SQLAlchemy / MCP SDK

**前端**: Vue 3 / TypeScript / Element Plus / Pinia / vue-i18n

## License

MIT
