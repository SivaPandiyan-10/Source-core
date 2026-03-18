FROM python:3.10-slim
WORKDIR /app
COPY ../../scheduler/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY ../../scheduler .
COPY ../../backend/app/utils ./backend/app/utils
COPY ../../ai-engine ./ai-engine
CMD ["python", "jobs.py"]
