"""Celery application configuration."""

import os
from celery import Celery
from celery.schedules import crontab

# Get Redis URL from environment
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

# Create Celery app
app = Celery(
    'rag_workers',
    broker=REDIS_URL + '/0',
    backend=REDIS_URL + '/0',
    include=['workers.tasks']
)

# Celery configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    
    # Task routes
    task_routes={
        'workers.tasks.send_email_task': {'queue': 'email'},
        'workers.tasks.summarize_content_task': {'queue': 'processing'},
        'workers.tasks.process_document_task': {'queue': 'processing'},
        'workers.tasks.cleanup_old_data_task': {'queue': 'maintenance'},
    },
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'cleanup-old-data': {
            'task': 'workers.tasks.cleanup_old_data_task',
            'schedule': crontab(hour=2, minute=0),  # Run daily at 2 AM
        },
    }
)

if __name__ == '__main__':
    app.start()
