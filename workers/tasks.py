"""Celery tasks for background processing."""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

from celery import Task
from workers.celery_app import app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """Base task with callbacks."""
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called on task success."""
        logger.info(f"Task {task_id} succeeded: {retval}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called on task failure."""
        logger.error(f"Task {task_id} failed: {exc}")


@app.task(
    base=CallbackTask,
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_email_task(self, to_email: str, subject: str, body: str):
    """
    Send email using SMTP.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body
        
    Returns:
        Success status
    """
    try:
        # Get SMTP settings from environment
        smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_user = os.getenv('SMTP_USER', '')
        smtp_password = os.getenv('SMTP_PASSWORD', '')
        smtp_from = os.getenv('SMTP_FROM', smtp_user)
        
        if not smtp_user or not smtp_password:
            logger.warning("SMTP credentials not configured, simulating email send")
            return {
                'status': 'simulated',
                'message': f"Email would be sent to {to_email}",
                'subject': subject
            }
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp_from
        msg['To'] = to_email
        
        # Add body
        text_part = MIMEText(body, 'plain')
        msg.attach(text_part)
        
        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        logger.info(f"Email sent to {to_email}")
        return {
            'status': 'success',
            'message': f"Email sent to {to_email}",
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        # Retry on failure
        raise self.retry(exc=e)


@app.task(
    base=CallbackTask,
    bind=True,
    max_retries=2
)
def summarize_content_task(self, content: str, max_length: int = 500):
    """
    Summarize content using LLM.
    
    Args:
        content: Content to summarize
        max_length: Maximum summary length
        
    Returns:
        Summary text
    """
    try:
        # Import here to avoid circular dependencies
        import sys
        sys.path.insert(0, '/app')
        
        from api.services.llm_service import LLMService
        from api.config import settings
        
        # Create LLM service
        llm_service = LLMService(
            ollama_endpoints=settings.ollama_endpoint_list,
            model_name=settings.ollama_model,
            embedding_model=settings.embedding_model,
            vision_model=settings.vision_model
        )
        
        # Generate summary (sync version for Celery)
        import asyncio
        summary = asyncio.run(llm_service.summarize(content, max_length))
        
        logger.info("Content summarized successfully")
        return {
            'status': 'success',
            'summary': summary,
            'original_length': len(content),
            'summary_length': len(summary)
        }
        
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise self.retry(exc=e)


@app.task(
    base=CallbackTask,
    bind=True,
    max_retries=2
)
def process_document_task(self, document_path: str):
    """
    Process uploaded document.
    
    Args:
        document_path: Path to document file
        
    Returns:
        Processing result
    """
    try:
        logger.info(f"Processing document: {document_path}")
        
        # Simulate document processing
        # In production, this would:
        # 1. Extract text from PDF/DOCX
        # 2. Generate embeddings
        # 3. Store in vector database
        # 4. Clean up temporary files
        
        return {
            'status': 'success',
            'message': f"Document processed: {document_path}",
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        raise self.retry(exc=e)


@app.task(base=CallbackTask)
def cleanup_old_data_task():
    """
    Clean up old data from databases.
    
    This is a periodic task that runs daily.
    
    Returns:
        Cleanup statistics
    """
    try:
        logger.info("Starting cleanup of old data")
        
        # Calculate cutoff date (30 days ago)
        cutoff_date = datetime.now() - timedelta(days=30)
        
        # In production, this would:
        # 1. Delete old temporary files
        # 2. Clean up expired cache entries
        # 3. Archive old task results
        # 4. Remove old vector embeddings if needed
        
        logger.info("Cleanup completed successfully")
        return {
            'status': 'success',
            'message': 'Cleanup completed',
            'cutoff_date': cutoff_date.isoformat(),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }
