# Pikpak2TelDrive

aria2 下载 + TelDrive 上传中转服务 —— 通过 Web 面板管理下载任务，自动上传到 TelDrive，支持实时进度监控。

## 功能特性

- 📥 **aria2 下载**：通过 aria2 RPC 接口下载文件，支持暂停/恢复/重试
- 📤 **自动上传**：下载完成后自动分片上传到 TelDrive
- 🌐 **Web 管理面板**：可视化任务管理，实时进度显示
- 📊 **WebSocket 推送**：实时同步下载/上传进度到前端
- 🗑️ **自动清理**：上传完成后可自动删除本地文件
- 🧩 **Random Chunking 支持**：兼容 TelDrive Random Chunking 模式
- 🔄 **断点续传**：分片上传失败自动重试

## 部署步骤

### 1. 下载项目

```bash
git clone https://github.com/MengStar-L/Pikpak2TelDrive.git /opt/Pikpak2TelDrive
```

### 2. 创建虚拟环境并安装依赖

```bash
cd /opt/Pikpak2TelDrive
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. 创建配置文件

```bash
cp config.example.toml config.toml
```

编辑配置文件：

```bash
nano config.toml
```

填入你的信息：

```toml
[server]
port = 8010                         # Web 管理面板端口

[aria2]
rpc_url = "http://localhost"        # aria2 RPC 地址
rpc_port = 6800                     # aria2 RPC 端口
rpc_secret = ""                     # aria2 RPC 密钥
max_concurrent = 3                  # 最大同时下载数
download_dir = "./downloads"        # 下载目录

[teldrive]
api_host = "http://localhost:7888"  # TelDrive API 地址
access_token = ""                   # TelDrive JWT Token
channel_id = 0                      # Telegram 频道 ID
chunk_size = "500M"                 # 分片大小 (支持 M/G 后缀)
upload_concurrency = 4              # 上传并发数
upload_dir = ""                     # 上传文件路径 (留空使用下载目录)
target_path = "/"                   # TelDrive 目标路径

[general]
max_retries = 3                     # 失败重试次数
auto_delete = true                  # 上传后自动删除本地文件
max_tasks = 3                       # 最大同时任务数
```

### 4. 确保 aria2 已运行

本程序通过 RPC 连接外部 aria2 实例，请确保 aria2 已启动并开启 RPC：

```bash
aria2c --enable-rpc --rpc-listen-all=true --rpc-listen-port=6800
```

### 5. 运行

```bash
source /opt/Pikpak2TelDrive/venv/bin/activate
cd /opt/Pikpak2TelDrive
python app/main.py
```

访问 `http://localhost:8010` 即可打开管理面板。

### 6. 注册为系统服务（可选）

创建服务文件：

```bash
cat > /etc/systemd/system/pikpak2teldrive.service << 'EOF'
[Unit]
Description=Pikpak2TelDrive
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/Pikpak2TelDrive
ExecStart=/opt/Pikpak2TelDrive/venv/bin/python app/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

启用并启动服务：

```bash
systemctl daemon-reload
systemctl enable --now pikpak2teldrive
```

### 7. 确认运行状态

```bash
systemctl status pikpak2teldrive
```

看到 `active (running)` 即表示部署成功 ✅

## 常用命令

```bash
# 查看实时日志
journalctl -u pikpak2teldrive -f

# 重启服务
systemctl restart pikpak2teldrive

# 停止服务
systemctl stop pikpak2teldrive
```

## License

MIT
