from apscheduler.schedulers.blocking import BlockingScheduler
import subprocess
import datetime

scheduler = BlockingScheduler(timezone="UTC")

@scheduler.scheduled_job('cron', hour=12, minute=0)
def fetch_stock_data():
    subprocess.run(["python", "backend/app/utils/fetch_data.py"])

@scheduler.scheduled_job('cron', hour=12, minute=5)
def generate_indicators():
    subprocess.run(["python", "ai-engine/feature_engineering.py"])

@scheduler.scheduled_job('cron', hour=12, minute=10)
def prepare_dataset():
    # Placeholder: dataset preparation logic
    pass

@scheduler.scheduled_job('cron', hour=12, minute=15)
def train_model():
    subprocess.run(["python", "ai-engine/train_model.py"])

@scheduler.scheduled_job('cron', hour=12, minute=20)
def generate_predictions():
    subprocess.run(["python", "ai-engine/predict.py"])

@scheduler.scheduled_job('cron', hour=12, minute=25)
def update_redis():
    subprocess.run(["python", "backend/app/utils/update_redis.py"])

if __name__ == "__main__":
    scheduler.start()
