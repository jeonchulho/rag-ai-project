"""Task schedulers for periodic jobs."""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Scheduler for managing periodic tasks."""
    
    def __init__(self):
        """Initialize task scheduler."""
        self.scheduled_tasks = {}
        logger.info("Task scheduler initialized")
    
    def schedule_task(self, task_id: str, task_func, schedule_time: datetime):
        """
        Schedule a task for future execution.
        
        Args:
            task_id: Unique task identifier
            task_func: Function to execute
            schedule_time: When to execute the task
        """
        self.scheduled_tasks[task_id] = {
            'func': task_func,
            'schedule_time': schedule_time,
            'status': 'scheduled'
        }
        logger.info(f"Task {task_id} scheduled for {schedule_time}")
    
    def cancel_task(self, task_id: str):
        """Cancel a scheduled task."""
        if task_id in self.scheduled_tasks:
            del self.scheduled_tasks[task_id]
            logger.info(f"Task {task_id} cancelled")
    
    def get_task_status(self, task_id: str) -> dict:
        """Get status of a scheduled task."""
        return self.scheduled_tasks.get(task_id, {'status': 'not_found'})
