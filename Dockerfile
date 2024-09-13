# 使用最新的 Ubuntu 作为基础镜像
FROM ubuntu:latest

# 设置环境变量，避免交互式安装
ENV DEBIAN_FRONTEND=noninteractive

# 设置工作目录
WORKDIR /app

# 更新并安装系统依赖，包括 Python 3.11 和必要的 OpenGL 库
# 更新并安装系统依赖，包括 Python 3.11 和必要的 OpenGL 库
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    libglu1-mesa \
    libgl1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 创建 Python 3.11 的软链接
RUN ln -s /usr/bin/python3.11 /usr/bin/python && ln -s /usr/bin/pip3 /usr/bin/pip

# 复制 requirements.txt 文件到容器中
COPY requirements.txt .

# 使用 Python 3.11 的 pip 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码文件到容器中
COPY ./code .

# 暴露 Flask 应用的端口
EXPOSE 5000

# 运行 Flask 应用
CMD ["python", "app.py"]
