import os
from celery import Celery, Task
from celery.schedules import crontab
from app import app

_redis_base = os.environ.get("REDIS_URL", "redis://localhost:6379")
# Strip trailing /N if present so we can append our own db numbers
_redis_host = _redis_base.rsplit("/", 1)[0] if _redis_base.count("/") > 2 else _redis_base

celery_app = Celery(
    'tasks',
    broker=f"{_redis_host}/1",
    backend=f"{_redis_host}/2",
    include=['tasks']
)


class FlaskTask(Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)


celery_app.Task = FlaskTask
celery_app.conf.timezone = 'Asia/Kolkata'

celery_app.conf.beat_schedule = {
    'daily-exam-reminder': {
        'task': 'tasks.send_daily_reminder',
        'schedule': crontab(hour=8, minute=0),
    },
    'monthly-exam-report': {
        'task': 'tasks.send_monthly_report',
        'schedule': crontab(hour=0, minute=1, day_of_month=1),
    },
}
