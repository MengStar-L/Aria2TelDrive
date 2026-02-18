# Pikpak2TelDrive 需求文档

## 1. 项目概述

本项目是一个基于 Python 的 aria2 下载监控与自动中转服务。程序**主动监控本地 aria2 中的所有下载任务**（无论通过何种方式添加到 aria2），下载完成后自动通过 TelDrive API 上传到 Telegram，文件上传完成后自动删除本地文件。同时提供一个 Web 前端界面，用于配置管理、进度监控，也支持通过面板手动添加下载任务。

## 2. 核心功能

### 2.1 aria2 下载监控
- 通过 aria2 JSON-RPC 接口与本地 aria2c 进程通信
- **主动轮询** aria2 中的所有下载任务（active、waiting、stopped），自动发现并同步
- 用户可通过任何方式向 aria2 添加下载（如 Pikpak、RPC 客户端、命令行等），本程序自动监控
- 实时监控下载进度（下载速度、进度百分比、文件大小）
- 支持通过 Web 面板手动添加下载任务、暂停、恢复、取消
- 支持配置：aria2 RPC 地址、端口、密钥
- 下载完成后自动触发上传流程

### 2.3 TelDrive 上传
- 通过 TelDrive REST API 将文件上传到 Telegram
- 支持大文件分块上传
- 实时监控上传进度
- 支持配置：TelDrive API 地址、访问令牌（access_token）、目标频道 ID、上传分块大小
- 上传完成后自动删除本地文件

### 2.4 任务管理
- 统一任务生命周期：等待 → 下载中 → 上传中 → 完成/失败
- 任务队列管理，支持并发控制
- 失败任务自动重试（可配置重试次数）
- 任务历史记录

## 3. Web 前端

### 3.1 仪表盘（Dashboard）
- 当前活跃任务数量概览
- 下载/上传速度实时显示
- 磁盘使用情况

### 3.2 任务列表
- 显示所有任务（下载中、上传中、已完成、失败）
- 每个任务显示：文件名、状态、进度条、速度、预计剩余时间
- 支持操作：暂停、恢复、取消、重试、删除记录

### 3.3 设置页面
- **aria2 设置**：RPC 地址、端口、密钥（secret）、最大并发下载数、下载目录
- **TelDrive 设置**：API 地址、访问令牌、目标频道 ID、上传分块大小、上传并发数
- **通用设置**：最大重试次数、文件上传后是否自动删除、任务并发数
- 设置测试连接按钮（验证 aria2 和 TelDrive 连通性）
- 设置保存/加载

## 4. 技术架构

### 4.1 后端
- **Web 框架**：FastAPI（异步支持好，自带 OpenAPI 文档）
- **aria2 通信**：通过 HTTP JSON-RPC 直接调用 aria2 接口
- **TelDrive 通信**：HTTP 请求调用 TelDrive REST API
- **任务管理**：asyncio + 内部任务队列
- **配置存储**：TOML 文件（config.toml）
- **数据库**：SQLite（存储任务记录）
- **实时通信**：WebSocket（推送进度更新到前端）

### 4.2 前端
- 单页应用（SPA），使用原生 HTML/CSS/JavaScript
- 通过 WebSocket 接收实时进度更新
- 响应式设计，支持桌面和移动端
- 现代 UI 风格（暗色主题、卡片式布局、动画效果）

### 4.3 目录结构
```
Pikpak2TelDrive/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py             # 配置管理
│   ├── database.py           # SQLite 数据库操作
│   ├── models.py             # 数据模型
│   ├── aria2_client.py       # aria2 RPC 客户端
│   ├── teldrive_client.py    # TelDrive API 客户端
│   ├── task_manager.py       # 任务管理器
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── api.py            # RPC / REST API 路由
│   │   ├── settings.py       # 设置相关路由
│   │   └── ws.py             # WebSocket 路由
│   └── static/
│       ├── index.html         # 主页面
│       ├── css/
│       │   └── style.css      # 样式文件
│       └── js/
│           └── app.js         # 前端逻辑
├── config.toml                # 配置文件
├── requirements.txt           # Python 依赖
├── REQUIREMENTS.md            # 本需求文档
└── README.md                  # 项目说明
```

## 5. API 接口设计

### 5.1 RPC 接口

#### 添加下载任务
```
POST /api/task/add
{
    "url": "https://example.com/file.zip",
    "filename": "file.zip",           // 可选
    "teldrive_path": "/downloads/"    // 可选，TelDrive 目标路径
}

Response:
{
    "task_id": "uuid",
    "status": "pending"
}
```

#### 查询任务状态
```
GET /api/task/{task_id}

Response:
{
    "task_id": "uuid",
    "filename": "file.zip",
    "status": "downloading",
    "progress": 45.2,
    "speed": "5.2 MB/s",
    "eta": "00:02:30"
}
```

#### 获取所有任务
```
GET /api/tasks

Response:
{
    "tasks": [...]
}
```

#### 任务操作
```
POST /api/task/{task_id}/pause
POST /api/task/{task_id}/resume
POST /api/task/{task_id}/cancel
POST /api/task/{task_id}/retry
DELETE /api/task/{task_id}
```

### 5.2 设置接口

#### 获取设置
```
GET /api/settings

Response:
{
    "aria2": {
        "rpc_url": "http://localhost",
        "rpc_port": 6800,
        "rpc_secret": "",
        "max_concurrent": 3,
        "download_dir": "./downloads"
    },
    "teldrive": {
        "api_host": "http://localhost:8080",
        "access_token": "",
        "channel_id": 0,
        "chunk_size": "500M",
        "upload_concurrency": 4
    },
    "general": {
        "max_retries": 3,
        "auto_delete": true,
        "max_tasks": 3
    }
}
```

#### 保存设置
```
PUT /api/settings
Body: (同上结构)
```

#### 测试连接
```
POST /api/settings/test/aria2
POST /api/settings/test/teldrive
```

### 5.3 WebSocket

```
WS /ws

推送消息格式:
{
    "type": "task_update",
    "data": {
        "task_id": "uuid",
        "status": "downloading",
        "progress": 45.2,
        "speed": "5.2 MB/s",
        "download_progress": 45.2,
        "upload_progress": 0
    }
}
```

## 6. 依赖

- **fastapi**: Web 框架
- **uvicorn**: ASGI 服务器
- **aiohttp**: 异步 HTTP 客户端（用于 aria2 RPC 和 TelDrive API 通信）
- **aiosqlite**: 异步 SQLite
- **websockets**: WebSocket 支持（FastAPI 内置）

## 7. 运行方式

```bash
# 安装依赖
pip install -r requirements.txt

# 确保 aria2c 已启动且开启 RPC
aria2c --enable-rpc --rpc-listen-port=6800

# 启动应用
python -m app.main
```

应用默认在 `http://localhost:8000` 启动，Web 界面可在浏览器中直接访问。
