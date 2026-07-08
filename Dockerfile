# 羽智选后端镜像
FROM python:3.13-slim

WORKDIR /app

# 系统依赖（chroma/langchain 编译需要 gcc）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && rm -rf /var/lib/apt/lists/*

# Python 依赖（利用 Docker 层缓存）
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端源码
COPY server/ .

# 上传目录与向量库目录
RUN mkdir -p /app/uploads14 /app/chroma_db

EXPOSE 8000

# 生产关闭 reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
