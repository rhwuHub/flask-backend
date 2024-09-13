# Dockerfile
# 使用 Python 3.11 作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制当前目录内容到容器中
COPY ./code .

# 复制 requirements.txt 文件到容器中
COPY ./requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露 Flask 应用的端口
EXPOSE 5000

# 运行 Flask 应用
CMD ["python", "app.py"]
