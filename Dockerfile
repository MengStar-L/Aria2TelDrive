FROM python:3.11-slim

LABEL maintainer="MengStar-L"
LABEL description="Aria2TelDrive - TelDrive 上传中转服务（需外部 aria2）"

WORKDIR /opt/Aria2TelDrive

# 先复制依赖文件，利用 Docker 缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app/ app/
COPY config.example.toml .

# 创建数据和下载目录
RUN mkdir -p /data /downloads

# 环境变量
ENV CONFIG_PATH=/data/config.toml
ENV DOCKER=1

EXPOSE 8010

VOLUME ["/data", "/downloads"]

CMD ["python", "app/main.py"]
