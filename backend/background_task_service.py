"""
Background task service.

Handles creation, updates, queries, and lifecycle management for long-running tasks.
"""

import random
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from config import settings
from models.database import BackgroundTask, User


class BackgroundTaskService:
    """Background task service."""

    def __init__(self, db: Session):
        self.db = db

        # Error classification config
        self.TRANSIENT_ERRORS = [
            "timeout", "connection", "network", "rate limit", "quota",
            "service unavailable", "temporarily", "retry", "busy", "overload"
        ]

        self.PERMANENT_ERRORS = [
            "invalid", "unauthorized", "forbidden", "not found", "syntax",
            "validation", "malformed", "unsupported", "expired", "revoked"
        ]

        # Retry policy config
        self.MAX_RETRIES = 3
        self.RETRY_BASE_DELAY = 5  # 秒
        self.RETRY_MAX_DELAY = 300  # 秒
        self.RETRY_BACKOFF_FACTOR = 2

        # Task timeout config
        self.DEFAULT_TASK_TIMEOUT = 600  # 10分钟
        self.MAX_TASK_TIMEOUT = 1800  # 30分钟

    class ProgressTracker:
        """Progress tracker for background tasks."""

        def __init__(self, task_service: 'BackgroundTaskService', task_id: int):
            self.task_service = task_service
            self.task_id = task_id
            self.last_update_time = datetime.now()

        def update_progress(
            self,
            progress_percentage: int,
            current_step: Optional[int] = None,
            total_steps: Optional[int] = None,
            step_description: Optional[str] = None,
            step_details: Optional[dict[str, Any]] = None,
        ) -> bool:
            """
            Update task progress metadata.
            """
            try:
                task = self.task_service.db.query(BackgroundTask).filter(
                    BackgroundTask.id == self.task_id
                ).first()

                if not task:
                    logging.warning("Task not found; cannot update progress: id=%s", self.task_id)
                    return False

                # 更新进度百分比
                if 0 <= progress_percentage <= 100:
                    task.progress_percentage = progress_percentage

                # 更新步骤信息
                if current_step is not None:
                    task.current_step = current_step

                if total_steps is not None:
                    task.total_steps = total_steps

                if step_description is not None:
                    task.step_description = step_description

                if step_details is not None:
                    task.step_details = json.dumps(step_details, ensure_ascii=False)

                # 更新时间和提交
                task.updated_at = datetime.now()
                self.task_service.db.commit()
                self.last_update_time = datetime.now()

                logging.debug(
                    "Task progress updated: id=%s progress=%s%% current_step=%s/%s step=%r",
                    self.task_id,
                    progress_percentage,
                    current_step,
                    total_steps,
                    step_description,
                )
                return True

            except Exception as e:
                logging.error(
                    "Failed to update task progress: id=%s error=%s",
                    self.task_id,
                    str(e),
                    exc_info=True,
                )
                self.task_service.db.rollback()
                return False

        def increment_step(
            self,
            step_description: Optional[str] = None,
            step_details: Optional[dict[str, Any]] = None,
        ) -> bool:
            """
            Increment the current step and refresh progress.
            """
            try:
                task = self.task_service.db.query(BackgroundTask).filter(
                    BackgroundTask.id == self.task_id
                ).first()

                if not task:
                    return False

                # 递增当前步骤
                task.current_step += 1

                # 计算进度百分比
                if task.total_steps > 0:
                    progress_percentage = min(100, int((task.current_step / task.total_steps) * 100))
                else:
                    progress_percentage = min(100, task.progress_percentage + 10)

                task.progress_percentage = progress_percentage

                # 更新步骤描述
                if step_description is not None:
                    task.step_description = step_description

                # 更新步骤详情
                if step_details is not None:
                    task.step_details = json.dumps(step_details, ensure_ascii=False)

                # 更新时间和提交
                task.updated_at = datetime.now()
                self.task_service.db.commit()
                self.last_update_time = datetime.now()

                logging.info(
                    "Task step incremented: id=%s current_step=%s/%s progress=%s%%",
                    self.task_id,
                    task.current_step,
                    task.total_steps,
                    progress_percentage,
                )
                return True

            except Exception as e:
                logging.error(
                    "Failed to increment task step: id=%s error=%s",
                    self.task_id,
                    str(e),
                    exc_info=True,
                )
                self.task_service.db.rollback()
                return False

        def set_total_steps(self, total_steps: int) -> bool:
            """
            Set total step count.
            """
            return self.update_progress(
                progress_percentage=0,
                current_step=0,
                total_steps=total_steps,
                step_description="Task started",
                step_details={"action": "initialize", "total_steps": total_steps}
            )

    def create_progress_tracker(self, task_id: int) -> 'BackgroundTaskService.ProgressTracker':
        """
        Create a progress tracker for a task.
        """
        return self.ProgressTracker(self, task_id)

    def _classify_error(self, error_msg: str) -> str:
        """
        Classify an error message.
        """
        error_msg_lower = error_msg.lower()

        for transient_error in self.TRANSIENT_ERRORS:
            if transient_error in error_msg_lower:
                return "transient"

        for permanent_error in self.PERMANENT_ERRORS:
            if permanent_error in error_msg_lower:
                return "permanent"

        return "unknown"

    def _calculate_retry_delay(self, attempt: int) -> int:
        """
        Calculate exponential backoff retry delay.
        """
        if attempt <= 0:
            return self.RETRY_BASE_DELAY

        # Exponential backoff: base_delay * backoff_factor^(attempt-1)
        delay = self.RETRY_BASE_DELAY * (self.RETRY_BACKOFF_FACTOR ** (attempt - 1))

        # Add jitter (+/-20%)
        jitter = delay * 0.2
        delay_with_jitter = delay + random.uniform(-jitter, jitter)

        # Clamp delay into the allowed range
        return min(max(int(delay_with_jitter), self.RETRY_BASE_DELAY), self.RETRY_MAX_DELAY)

    def _should_retry(self, task: BackgroundTask, error_msg: str) -> tuple[bool, Optional[int]]:
        """
        Decide whether a task should be retried.
        """
        # Check max attempts
        if task.attempts >= task.max_attempts:
            return False, None

        # Classify error
        error_type = self._classify_error(error_msg)

        if error_type == "permanent":
            return False, None
        elif error_type == "transient":
            delay = self._calculate_retry_delay(task.attempts + 1)
            return True, delay
        else:
            if task.attempts < 2:
                delay = self._calculate_retry_delay(task.attempts + 1)
                return True, delay
            return False, None

    def _check_task_timeout(self, task: BackgroundTask) -> bool:
        """
        Check whether a task has timed out.
        """
        if not task.started_at:
            return False

        started_time = datetime.strptime(task.started_at, "%Y-%m-%d %H:%M:%S") if isinstance(task.started_at, str) else task.started_at
        elapsed_time = datetime.now() - started_time

        # 根据任务类型确定超时时间
        if task.task_type == "chat_literature_research":
            timeout_seconds = 1800
        else:
            timeout_seconds = 600

        return elapsed_time.total_seconds() > timeout_seconds

    def create_task(
        self,
        user_id: int,
        task_type: str,
        request_data: dict[str, Any],
        estimated_time: int = 600,  # 默认10分钟
    ) -> BackgroundTask:
        """
        Create a background task.
        """
        request_json = json.dumps(request_data, ensure_ascii=False)

        task = BackgroundTask(
            user_id=user_id,
            task_type=task_type,
            status="pending",
            request_data=request_json,
            attempts=0,
            max_attempts=3,
            created_at=datetime.now(),
        )

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        logging.info("Background task created: id=%s type=%s user_id=%s", task.id, task_type, user_id)
        return task

    def update_task_status(
        self,
        task_id: int,
        status: str,
        result_data: Optional[dict[str, Any]] = None,
        error_message: Optional[str] = None,
        increment_attempts: bool = False,
    ) -> Optional[BackgroundTask]:
        """
        Update task status.
        """
        task = self.db.query(BackgroundTask).filter(BackgroundTask.id == task_id).first()
        if not task:
            logging.error("Task not found: id=%s", task_id)
            return None

        # 更新状态
        task.status = status
        task.updated_at = datetime.now()

        if status == "processing" and not task.started_at:
            task.started_at = datetime.now()
        elif status in ["completed", "failed"] and not task.completed_at:
            task.completed_at = datetime.now()

        if result_data is not None:
            task.result_data = json.dumps(result_data, ensure_ascii=False)

        if error_message is not None:
            task.error_message = error_message

        if increment_attempts:
            task.attempts += 1

        self.db.commit()
        self.db.refresh(task)

        logging.info("Task status updated: id=%s status=%s", task_id, status)
        return task

    def get_task(self, task_id: int) -> Optional[BackgroundTask]:
        """
        Get task details.
        """
        return self.db.query(BackgroundTask).filter(BackgroundTask.id == task_id).first()

    def get_user_tasks(
        self,
        user_id: int,
        task_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10,
    ) -> list[BackgroundTask]:
        """
        Get the user's task list.
        """
        query = self.db.query(BackgroundTask).filter(BackgroundTask.user_id == user_id)

        if task_type:
            query = query.filter(BackgroundTask.task_type == task_type)

        if status:
            query = query.filter(BackgroundTask.status == status)

        query = query.order_by(BackgroundTask.created_at.desc()).limit(limit)

        return query.all()

    def cleanup_old_tasks(self, days: int = 7) -> int:
        """
        Remove old finished tasks.
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        result = self.db.query(BackgroundTask).filter(
            BackgroundTask.created_at < cutoff_date,
            BackgroundTask.status.in_(["completed", "failed"]),
        ).delete(synchronize_session=False)

        self.db.commit()
        logging.info("Old tasks cleaned up: %s records", result)
        return result

    def cleanup_stuck_tasks(self, timeout_minutes: int = 30) -> int:
        """
        Clean up stuck tasks that exceeded the timeout.
        """
        cutoff_time = datetime.now() - timedelta(minutes=timeout_minutes)

        stuck_tasks = (
            self.db.query(BackgroundTask)
            .filter(
                BackgroundTask.status == "processing",
                BackgroundTask.started_at < cutoff_time,
            )
            .all()
        )

        for task in stuck_tasks:
            logging.warning("Cleaning up stuck task: id=%s started_at=%s", task.id, task.started_at)
            self.update_task_status(
                task.id,
                "failed",
                error_message=f"Task processing timed out after {timeout_minutes} minutes",
            )

        return len(stuck_tasks)

    def get_pending_tasks(self, limit: int = 10) -> list[BackgroundTask]:
        """
        Get the list of pending tasks.
        """
        return (
            self.db.query(BackgroundTask)
            .filter(BackgroundTask.status == "pending")
            .order_by(BackgroundTask.created_at.asc())
            .limit(limit)
            .all()
        )

    def process_task(self, task: BackgroundTask) -> dict[str, Any]:
        """
        Process a task, typically invoked by the worker.
        """
        if task.status == "processing" and self._check_task_timeout(task):
            error_msg = "Task timed out; re-queueing"
            logging.warning("Task timeout detected: id=%s message=%s", task.id, error_msg)

            self.update_task_status(
                task.id,
                "pending",
                error_message=error_msg,
            )
            raise TimeoutError(error_msg)

        self.update_task_status(task.id, "processing")

        try:
            import json
            request_data = json.loads(task.request_data) if task.request_data else {}

            if task.task_type == "chat_literature_research":
                result = self._process_chat_literature_research(task, request_data)
            elif task.task_type == "chat_regular":
                result = self._process_chat_regular(task, request_data)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")

            self.update_task_status(
                task.id,
                "completed",
                result_data=result,
            )

            return result

        except Exception as e:
            error_msg = str(e)
            error_type = self._classify_error(error_msg)

            logging.error(
                "Task processing failed: id=%s error_type=%s error=%s attempts=%s/%s",
                task.id,
                error_type,
                error_msg,
                task.attempts + 1,
                task.max_attempts,
                exc_info=True
            )

            should_retry, retry_delay = self._should_retry(task, error_msg)

            if should_retry:
                retry_after = datetime.now() + timedelta(seconds=retry_delay)

                error_with_retry = (
                    f"{error_msg} (retry in {retry_delay} seconds, expected at {retry_after.strftime('%H:%M:%S')})"
                )

                self.update_task_status(
                    task.id,
                    "pending",
                    error_message=error_with_retry,
                    increment_attempts=True,
                )

                logging.info(
                    "Task scheduled for retry: id=%s delay=%ss next_retry=%s",
                    task.id,
                    retry_delay,
                    retry_after.strftime('%H:%M:%S'),
                )
            else:
                final_error_msg = "Task processing failed"
                if error_type == "permanent":
                    final_error_msg += f" (permanent error): {error_msg}"
                elif task.attempts + 1 >= task.max_attempts:
                    final_error_msg += f" (max attempts reached): {error_msg}"
                else:
                    final_error_msg += f": {error_msg}"

                self.update_task_status(
                    task.id,
                    "failed",
                    error_message=final_error_msg,
                    increment_attempts=True,
                )

                logging.error(
                    "Task marked as failed: id=%s error_type=%s error=%s",
                    task.id,
                    error_type,
                    final_error_msg,
                )

            raise

    def _process_chat_literature_research(
        self, task: BackgroundTask, request_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Process a literature research chat task.
        """
        from api_services import chat_with_manus

        # 提取必要参数
        prompt = request_data.get("prompt", "")
        generate_literature_review = request_data.get("generate_literature_review", False)
        manus_api_key = request_data.get("manus_api_key")

        if not manus_api_key:
            manus_api_key = settings.MANUS_API_KEY

        if not manus_api_key:
            raise ValueError("MANUS_API_KEY is not configured")

        progress_tracker = self.create_progress_tracker(task.id)

        total_steps = 8
        progress_tracker.set_total_steps(total_steps)

        def progress_callback(progress_percentage: int, step_description: str, step_details: Optional[Dict[str, Any]] = None):
            try:
                current_step = int((progress_percentage / 100) * total_steps) if total_steps > 0 else 0

                progress_tracker.update_progress(
                    progress_percentage=progress_percentage,
                    current_step=current_step,
                    total_steps=total_steps,
                    step_description=step_description,
                    step_details=step_details
                )

                logging.debug(
                    "Task progress callback: id=%s progress=%s%% step=%s/%s description=%r",
                    task.id,
                    progress_percentage,
                    current_step,
                    total_steps,
                    step_description,
                )
            except Exception as e:
                logging.warning("Progress callback update failed: id=%s error=%s", task.id, str(e))

        logging.info("Processing literature research task: id=%s prompt_length=%s", task.id, len(prompt))

        result = chat_with_manus(
            prompt=prompt,
            api_key=manus_api_key,
            generate_literature_review=generate_literature_review,
            prompt_already_built=False,  # 需要在后台任务中构建提示词
            progress_callback=progress_callback,
        )

        progress_tracker.update_progress(
            progress_percentage=100,
            current_step=total_steps,
            step_description="Literature research completed",
            step_details={"action": "complete", "result_length": len(result.get("text", ""))}
        )

        return {
            "success": result.get("success", False),
            "text": result.get("text", ""),
            "steps": result.get("steps", []),
            "documents": result.get("documents", []),
            "model_used": result.get("model_used", "manus-ai"),
            "error": result.get("error"),
        }

    def _process_chat_regular(
        self, task: BackgroundTask, request_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Process a regular chat task.
        """
        from api_services import chat_with_gemini

        # 提取必要参数
        messages = request_data.get("messages", [])
        api_key = request_data.get("api_key")

        if not api_key:
            api_key = settings.GEMINI_API_KEY

        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured")

        progress_tracker = self.create_progress_tracker(task.id)

        total_steps = 2
        progress_tracker.set_total_steps(total_steps)

        def progress_callback(progress_percentage: int, step_description: str, step_details: Optional[Dict[str, Any]] = None):
            try:
                current_step = int((progress_percentage / 100) * total_steps) if total_steps > 0 else 0

                progress_tracker.update_progress(
                    progress_percentage=progress_percentage,
                    current_step=current_step,
                    total_steps=total_steps,
                    step_description=step_description,
                    step_details=step_details
                )
            except Exception as e:
                logging.warning("Chat progress callback update failed: id=%s error=%s", task.id, str(e))

        logging.info("Processing regular chat task: id=%s messages_count=%s", task.id, len(messages))

        progress_tracker.update_progress(
            progress_percentage=30,
            current_step=0,
            step_description="Generating response"
        )

        result = chat_with_gemini(
            messages=messages,
            api_key=api_key,
        )

        progress_tracker.update_progress(
            progress_percentage=100,
            current_step=total_steps,
            step_description="Response generation completed",
            step_details={"action": "complete", "text_length": len(result.get("text", ""))}
        )

        return {
            "success": result.get("success", False),
            "text": result.get("text", ""),
            "model_used": result.get("model_used", "unknown"),
            "error": result.get("error"),
        }


_task_service_instance = None


def get_background_task_service(db: Session) -> BackgroundTaskService:
    """Get a background task service instance."""
    return BackgroundTaskService(db)
