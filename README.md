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

#### 方式一：使用预构建镜像（最快）

```bash
# 创建数据目录和配置文件
mkdir -p mcp-gateway && cd mcp-gateway
mkdir -p data

# 下载示例配置
curl -o config.yaml https://raw.githubusercontent.com/thsrite/mcp-gateway/main/config.yaml.example

# 启动（amd64 / arm64 均可）
docker run -d \
  --name mcp-gateway \
  --restart unless-stopped \
  -p 9000:9000 \
  -p 9001:9001 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -e TZ=Asia/Shanghai \
  thsrite/mcp-gateway:latest
```

#### 方式二：Docker Compose（预构建镜像）

```yaml
# docker-compose.yml
services:
  mcp-gateway:
    image: thsrite/mcp-gateway:latest
    container_name: mcp-gateway
    restart: unless-stopped
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - ./data:/app/data
      - ./config.yaml:/app/config.yaml
    environment:
      - TZ=Asia/Shanghai
```

```bash
docker compose up -d
```

#### 方式三：从源码构建

```bash
git clone https://github.com/thsrite/mcp-gateway.git
cd mcp-gateway
docker compose up -d
```

### 手动部署

```bash
# 复制配置文件
cp config.yaml.example config.yaml

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

复制 `config.yaml.example` 为 `config.yaml` 后按需修改：

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

## 添加 MCP 服务

### 从 GitHub 导入

在 Web UI 中填入 GitHub URL，Gateway 会自动克隆、检测项目类型、安装依赖并启动。

**Python 项目**要求：
- 包含 `pyproject.toml`（或 `setup.py`）
- Gateway 自动创建 `.venv` 并 `pip install -e .`
- 启动命令自动检测优先级：
  1. `[project.scripts]` 定义的入口 → `.venv/bin/<script>`
  2. `project.name` → `python -m <module>`
  3. 常见入口文件：`server.py`、`main.py`

**Node.js 项目**要求：
- 包含 `package.json`
- Gateway 自动 `npm install`，有 `tsconfig.json` 时自动 `npm run build`
- 启动命令自动检测优先级：
  1. `package.json` 的 `bin` 字段
  2. `scripts.start`
  3. 常见入口：`dist/index.js`、`index.js`

> 绝大多数 GitHub 上的标准 MCP Server 仓库可直接导入。如果自动检测不准确，可在「配置管理」中手动修改启动命令。

### 手动配置

填写服务名称、启动命令（如 `python`、`node`、`npx`）、启动参数、本地路径和环境变量即可。

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
