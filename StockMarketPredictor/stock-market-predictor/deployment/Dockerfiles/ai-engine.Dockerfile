FROM python:3.10-slim
WORKDIR /app
COPY ../../ai-engine/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY ../../ai-engine .
CMD ["sleep", "infinity"]
