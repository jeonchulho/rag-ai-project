"""Action scheduling endpoints."""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from celery.result import AsyncResult

from api.models import ActionRequest, ActionResponse, ActionType, TaskStatus
from api.config import Settings
from api.dependencies import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/action/email", response_model=ActionResponse)
async def schedule_email(
    request: ActionRequest,
    settings: Settings = Depends(get_settings)
):
    """
    Schedule email action.
    
    Args:
        request: Action request with email parameters
        
    Returns:
        Task ID and scheduling status
    """
    try:
        if request.action_type != ActionType.EMAIL:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action type must be 'email'"
            )
        
        # Import Celery tasks
        from workers.tasks import send_email_task
        
        # Extract email parameters
        email_params = request.parameters
        
        # Schedule task
        if request.scheduled_time:
            # Schedule for specific time
            task = send_email_task.apply_async(
                args=[
                    email_params.get('to'),
                    email_params.get('subject'),
                    email_params.get('body')
                ],
                eta=request.scheduled_time
            )
        else:
            # Execute immediately
            task = send_email_task.delay(
                email_params.get('to'),
                email_params.get('subject'),
                email_params.get('body')
            )
        
        logger.info(f"Email task scheduled: {task.id}")
        
        return ActionResponse(
            task_id=task.id,
            action_type="email",
            status="scheduled" if request.scheduled_time else "pending",
            scheduled_time=request.scheduled_time,
            message="Email task scheduled successfully"
        )
        
    except ImportError:
        # Celery workers not available - return mock response
        logger.warning("Celery workers not available, returning mock response")
        return ActionResponse(
            task_id="mock-task-id",
            action_type="email",
            status="scheduled",
            scheduled_time=request.scheduled_time,
            message="Email task scheduled (mock mode)"
        )
    except Exception as e:
        logger.error(f"Email scheduling failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule email: {str(e)}"
        )


@router.post("/action/summarize", response_model=ActionResponse)
async def schedule_summarize(
    request: ActionRequest,
    settings: Settings = Depends(get_settings)
):
    """
    Schedule content summarization action.
    
    Args:
        request: Action request with summarization parameters
        
    Returns:
        Task ID and scheduling status
    """
    try:
        if request.action_type != ActionType.SUMMARIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action type must be 'summarize'"
            )
        
        # Import Celery tasks
        from workers.tasks import summarize_content_task
        
        # Extract parameters
        content = request.parameters.get('content', '')
        max_length = request.parameters.get('max_length', 500)
        
        # Schedule task
        task = summarize_content_task.delay(content, max_length)
        
        logger.info(f"Summarization task scheduled: {task.id}")
        
        return ActionResponse(
            task_id=task.id,
            action_type="summarize",
            status="pending",
            scheduled_time=None,
            message="Summarization task scheduled successfully"
        )
        
    except ImportError:
        # Celery workers not available - return mock response
        logger.warning("Celery workers not available, returning mock response")
        return ActionResponse(
            task_id="mock-task-id",
            action_type="summarize",
            status="pending",
            scheduled_time=None,
            message="Summarization task scheduled (mock mode)"
        )
    except Exception as e:
        logger.error(f"Summarization scheduling failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule summarization: {str(e)}"
        )


@router.get("/action/status/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """
    Get status of a background task.
    
    Args:
        task_id: Task ID
        
    Returns:
        Task status and result
    """
    try:
        # Get task result
        result = AsyncResult(task_id)
        
        status_map = {
            'PENDING': 'pending',
            'STARTED': 'running',
            'SUCCESS': 'completed',
            'FAILURE': 'failed',
            'RETRY': 'retrying',
            'REVOKED': 'cancelled'
        }
        
        task_status = status_map.get(result.state, 'unknown')
        
        response = TaskStatus(
            task_id=task_id,
            status=task_status,
            result=result.result if result.successful() else None,
            error=str(result.result) if result.failed() else None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to get task status: {e}", exc_info=True)
        # Return unknown status instead of error
        return TaskStatus(
            task_id=task_id,
            status="unknown",
            result=None,
            error=f"Failed to retrieve status: {str(e)}",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
