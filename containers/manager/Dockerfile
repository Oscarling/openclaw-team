FROM python:3.11-slim
WORKDIR /app
COPY ./skills /app/skills
COPY ./dispatcher /app/dispatcher
COPY ./agents /app/agents

# 屏蔽可能导致冲突的代理环境变量，并使用清华源加速下载
RUN HTTP_PROXY="" HTTPS_PROXY="" http_proxy="" https_proxy="" pip install --no-cache-dir docker -i https://pypi.tuna.tsinghua.edu.cn/simple

CMD ["bash"]
