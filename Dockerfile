FROM nvcr.io/nvidia/pytorch:24.08-py3

ENV DEBIAN_FRONTEND=noninteractive

# ✅ 正确的 LABEL 格式（使用 key=value 而不是 key value）
LABEL org.opencontainers.image.source="https://github.com/FunAudioLLM/InspireMusic"
LABEL org.opencontainers.image.licenses="Apache-2.0"

# 克隆项目
WORKDIR /workspace
RUN apt-get update && apt-get install -y git && git clone https://github.com/FunAudioLLM/InspireMusic.git

WORKDIR /workspace/InspireMusic

# ✅ 安装系统依赖，加入 tzdata 避免阻塞，以及 locales 以防某些 Python 库出错
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg sox libsox-dev git tzdata ca-certificates locales && \
    rm -rf /var/lib/apt/lists/*

# 设置 locale（有些 Python 包可能需要）
RUN locale-gen en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

# 安装 Python 依赖
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 安装 flash-attn（可以改为指定版本）
RUN pip install "flash-attn>=2.0.0" --no-build-isolation

# 设置默认启动命令
CMD ["/bin/bash"]
