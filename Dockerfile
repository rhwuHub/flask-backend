# 使用 Python 3.9 作为基础镜像
FROM python:3.9

# 设置环境变量，避免 Python 生成 .pyc 文件
ENV PYTHONUNBUFFERED=1

# 安装必要的软件包
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 安装 CUDA 相关依赖（如果使用 GPU）
RUN pip install --upgrade pip
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 安装 vLLM
RUN pip install vllm

# 设置工作目录
WORKDIR /app

# 复制项目文件（如果有）
COPY . /app

# 暴露端口
EXPOSE 8000

# 运行 vLLM 服务
#CMD ["vllm", "serve", "/app/Fin-R1", "--host", "0.0.0.0", "--port", "8000", "--gpu-memory-utilization", "0.9", "--max-model-len", "16384", "--tensor-parallel-size", "2", "--served-model-name", "Fin-R1"]
