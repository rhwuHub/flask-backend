# 使用最新的 Ubuntu 作为基础镜像
FROM ubuntu:latest

# 设置环境变量，避免交互式安装
ENV DEBIAN_FRONTEND=noninteractive

# 设置工作目录
WORKDIR /app

# 复制 . 文件到容器中
COPY . .

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
    libxrender1 \
    libxcursor1 \
    libx11-dev \
    libxext-dev \
    libxt-dev \
    libxi-dev \
    libxft2 \
    libxft-dev \
    libxinerama1 \
    libgomp1 \
    git \
    gcc \
    g++ \
    gfortran \
    openmpi-bin \
    libopenmpi-dev \
    make \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 配置安装specfem2D
# 克隆 Specfem2D 的最新 devel 分支代码
RUN git clone --recursive --branch devel https://github.com/geodynamics/specfem2d.git

# 配置安装 Specfem2D
WORKDIR /app/specfem2d
RUN ./configure FC=gfortran CC=gcc MPIFC=mpif90 --with-mpi

# 安装 Specfem2D
RUN make

# 返回到 /app 目录
WORKDIR /app

# 创建虚拟环境
RUN python3.11 -m venv /env

# 激活虚拟环境并安装依赖
RUN /env/bin/pip install --upgrade pip setuptools \
    && /env/bin/pip install --no-cache-dir -r requirements.txt

# 设置环境变量，确保使用虚拟环境中的 Python 和 pip
ENV PATH="/env/bin:$PATH"


# 暴露 Flask 应用的端口
EXPOSE 5000

# 运行 Flask 应用
CMD ["python", "./code/app.py"]
