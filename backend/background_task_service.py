"""
后台任务服务模块

处理长时间运行任务的创建、更新、查询和状态管理。
支持两种模式：同步处理（直接返回结果）和异步处理（通过后台工作器）。
"""

import json
import logging
import time
import random
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List, Union

from sqlalchemy.orm import Session

from config import settings
from models.database import BackgroundTask, User


class BackgroundTaskService:
    """后台任务服务类"""

    def __init__(self, db: Session):
        self.db = db

        # 错误分类配置
        self.TRANSIENT_ERRORS = [
            "timeout", "connection", "network", "rate limit", "quota",
            "service unavailable", "temporarily", "retry", "busy", "overload"
        ]

        self.PERMANENT_ERRORS = [
            "invalid", "unauthorized", "forbidden", "not found", "syntax",
            "validation", "malformed", "unsupported", "expired", "revoked"
        ]

        # 重试策略配置
        self.MAX_RETRIES = 3
        self.RETRY_BASE_DELAY = 5  # 秒
        self.RETRY_MAX_DELAY = 300  # 秒
        self.RETRY_BACKOFF_FACTOR = 2

        # 任务超时配置
        self.DEFAULT_TASK_TIMEOUT = 600  # 10分钟
        self.MAX_TASK_TIMEOUT = 1800  # 30分钟

    class ProgressTracker:
        """任务进度跟踪器

        用于更新和跟踪后台任务的进度信息，提供实时进度更新。
        """

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
            更新任务进度信息

            Args:
                progress_percentage: 进度百分比 (0-100)
                current_step: 当前步骤索引，如果为None则保持原值
                total_steps: 总步骤数，如果为None则保持原值
                step_description: 当前步骤描述，如果为None则保持原值
                step_details: 详细进度信息（字典），如果为None则保持原值

            Returns:
                bool: 更新是否成功
            """
            try:
                task = self.task_service.db.query(BackgroundTask).filter(
                    BackgroundTask.id == self.task_id
                ).first()

                if not task:
                    logging.warning(f"任务不存在，无法更新进度: id={self.task_id}")
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
                    f"更新任务进度: id={self.task_id}, "
                    f"progress={progress_percentage}%, "
                    f"current_step={current_step}/{total_steps}, "
                    f"step='{step_description}'"
                )
                return True

            except Exception as e:
                logging.error(f"更新任务进度失败: id={self.task_id}, error={str(e)}", exc_info=True)
                self.task_service.db.rollback()
                return False

        def increment_step(
            self,
            step_description: Optional[str] = None,
            step_details: Optional[dict[str, Any]] = None,
        ) -> bool:
            """
            递增当前步骤并更新进度

            Args:
                step_description: 新的步骤描述
                step_details: 新的步骤详细信息

            Returns:
                bool: 更新是否成功
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
                    progress_percentage = min(100, task.progress_percentage + 10)  # 默认递增10%

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
                    f"递增任务步骤: id={self.task_id}, "
                    f"current_step={task.current_step}/{task.total_steps}, "
                    f"progress={progress_percentage}%"
                )
                return True

            except Exception as e:
                logging.error(f"递增任务步骤失败: id={self.task_id}, error={str(e)}", exc_info=True)
                self.task_service.db.rollback()
                return False

        def set_total_steps(self, total_steps: int) -> bool:
            """
            设置总步骤数

            Args:
                total_steps: 总步骤数

            Returns:
                bool: 更新是否成功
            """
            return self.update_progress(
                progress_percentage=0,
                current_step=0,
                total_steps=total_steps,
                step_description="任务开始",
                step_details={"action": "initialize", "total_steps": total_steps}
            )

    def create_progress_tracker(self, task_id: int) -> 'BackgroundTaskService.ProgressTracker':
        """
        为指定任务创建进度跟踪器

        Args:
            task_id: 任务ID

        Returns:
            ProgressTracker: 进度跟踪器实例
        """
        return self.ProgressTracker(self, task_id)

    def _classify_error(self, error_msg: str) -> str:
        """
        分类错误类型

        Args:
            error_msg: 错误消息

        Returns:
            str: "transient"（临时错误）、"permanent"（永久错误）或 "unknown"
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
        计算指数退避重试延迟

        Args:
            attempt: 当前尝试次数（从1开始）

        Returns:
            int: 延迟时间（秒）
        """
        if attempt <= 0:
            return self.RETRY_BASE_DELAY

        # 指数退避：base_delay * backoff_factor^(attempt-1)
        delay = self.RETRY_BASE_DELAY * (self.RETRY_BACKOFF_FACTOR ** (attempt - 1))

        # 添加抖动（±20%）
        jitter = delay * 0.2
        delay_with_jitter = delay + random.uniform(-jitter, jitter)

        # 确保延迟在合理范围内
        return min(max(int(delay_with_jitter), self.RETRY_BASE_DELAY), self.RETRY_MAX_DELAY)

    def _should_retry(self, task: BackgroundTask, error_msg: str) -> tuple[bool, Optional[int]]:
        """
        判断任务是否应该重试

        Args:
            task: 任务对象
            error_msg: 错误消息

        Returns:
            tuple[bool, Optional[int]]: (是否重试, 重试延迟秒数)
        """
        # 检查是否超过最大尝试次数
        if task.attempts >= task.max_attempts:
            return False, None

        # 分类错误类型
        error_type = self._classify_error(error_msg)

        if error_type == "permanent":
            # 永久错误不重试
            return False, None
        elif error_type == "transient":
            # 临时错误应该重试
            delay = self._calculate_retry_delay(task.attempts + 1)
            return True, delay
        else:
            # 未知错误，默认重试但限制尝试次数
            if task.attempts < 2:  # 最多重试2次
                delay = self._calculate_retry_delay(task.attempts + 1)
                return True, delay
            else:
                return False, None

    def _check_task_timeout(self, task: BackgroundTask) -> bool:
        """
        检查任务是否超时

        Args:
            task: 任务对象

        Returns:
            bool: 是否超时
        """
        if not task.started_at:
            return False

        started_time = datetime.strptime(task.started_at, "%Y-%m-%d %H:%M:%S") if isinstance(task.started_at, str) else task.started_at
        elapsed_time = datetime.now() - started_time

        # 根据任务类型确定超时时间
        if task.task_type == "chat_deep_research":
            timeout_seconds = 1800  # 文献调研任务最长30分钟
        else:
            timeout_seconds = 600  # 其他任务10分钟

        return elapsed_time.total_seconds() > timeout_seconds

    def create_task(
        self,
        user_id: int,
        task_type: str,
        request_data: dict[str, Any],
        estimated_time: int = 600,  # 默认10分钟
    ) -> BackgroundTask:
        """
        创建后台任务

        Args:
            user_id: 用户ID
            task_type: 任务类型
            request_data: 原始请求数据
            estimated_time: 预估处理时间（秒）

        Returns:
            BackgroundTask: 创建的任务对象
        """
        # 序列化请求数据为JSON字符串
        request_json = json.dumps(request_data, ensure_ascii=False)

        # 创建任务
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

        logging.info(f"创建后台任务: id={task.id}, type={task_type}, user_id={user_id}")
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
        更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态
            result_data: 处理结果数据
            error_message: 错误信息
            increment_attempts: 是否增加尝试次数

        Returns:
            Optional[BackgroundTask]: 更新后的任务对象，如果任务不存在则返回None
        """
        task = self.db.query(BackgroundTask).filter(BackgroundTask.id == task_id).first()
        if not task:
            logging.error(f"任务不存在: id={task_id}")
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

        logging.info(f"更新任务状态: id={task_id}, status={status}")
        return task

    def get_task(self, task_id: int) -> Optional[BackgroundTask]:
        """
        获取任务详情

        Args:
            task_id: 任务ID

        Returns:
            Optional[BackgroundTask]: 任务对象，如果不存在则返回None
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
        获取用户的任务列表

        Args:
            user_id: 用户ID
            task_type: 任务类型筛选
            status: 状态筛选
            limit: 返回数量限制

        Returns:
            list[BackgroundTask]: 任务列表
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
        清理旧任务

        Args:
            days: 保留天数

        Returns:
            int: 清理的任务数量
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        result = self.db.query(BackgroundTask).filter(
            BackgroundTask.created_at < cutoff_date,
            BackgroundTask.status.in_(["completed", "failed"]),
        ).delete(synchronize_session=False)

        self.db.commit()
        logging.info(f"清理旧任务: {result} 条记录")
        return result

    def cleanup_stuck_tasks(self, timeout_minutes: int = 30) -> int:
        """
        清理卡住的任务（处理中但超过超时时间的任务）

        Args:
            timeout_minutes: 超时时间（分钟）

        Returns:
            int: 清理的任务数量
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
            logging.warning(f"清理卡住的任务: id={task.id}, started_at={task.started_at}")
            self.update_task_status(
                task.id,
                "failed",
                error_message=f"任务处理超时（超过{timeout_minutes}分钟）",
            )

        return len(stuck_tasks)

    def get_pending_tasks(self, limit: int = 10) -> list[BackgroundTask]:
        """
        获取待处理的任务列表

        Args:
            limit: 返回数量限制

        Returns:
            list[BackgroundTask]: 待处理任务列表
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
        处理任务（由工作器调用）

        Args:
            task: 任务对象

        Returns:
            dict[str, Any]: 处理结果

        Raises:
            TimeoutError: 如果任务超时
        """
        # 检查任务是否超时（如果已经在处理中）
        if task.status == "processing" and self._check_task_timeout(task):
            error_msg = f"任务已超时，重新排队处理"
            logging.warning(f"任务超时检测: id={task.id}, {error_msg}")

            # 重置任务状态为pending以便重试
            self.update_task_status(
                task.id,
                "pending",
                error_message=error_msg,
            )
            raise TimeoutError(error_msg)

        # 更新任务状态为处理中
        self.update_task_status(task.id, "processing")

        try:
            # 解析请求数据
            import json
            request_data = json.loads(task.request_data) if task.request_data else {}

            # 根据任务类型调用不同的处理函数
            if task.task_type == "chat_deep_research":
                result = self._process_chat_deep_research(task, request_data)
            elif task.task_type == "chat_regular":
                result = self._process_chat_regular(task, request_data)
            else:
                raise ValueError(f"未知的任务类型: {task.task_type}")

            # 更新任务状态为完成
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
                f"处理任务失败: id={task.id}, error_type={error_type}, "
                f"error={error_msg}, attempts={task.attempts+1}/{task.max_attempts}",
                exc_info=True
            )

            # 判断是否应该重试
            should_retry, retry_delay = self._should_retry(task, error_msg)

            if should_retry:
                # 计算下次重试时间
                retry_after = datetime.now() + timedelta(seconds=retry_delay)

                # 更新任务状态为pending，设置错误信息和下次重试时间
                error_with_retry = f"{error_msg} (将 {retry_delay} 秒后重试，预计 {retry_after.strftime('%H:%M:%S')})"

                self.update_task_status(
                    task.id,
                    "pending",
                    error_message=error_with_retry,
                    increment_attempts=True,
                )

                logging.info(
                    f"任务标记为重试: id={task.id}, delay={retry_delay}s, "
                    f"next_retry={retry_after.strftime('%H:%M:%S')}"
                )
            else:
                # 不再重试，标记为失败
                final_error_msg = f"任务处理失败"
                if error_type == "permanent":
                    final_error_msg += f"（永久错误）: {error_msg}"
                elif task.attempts + 1 >= task.max_attempts:
                    final_error_msg += f"（已达到最大尝试次数）: {error_msg}"
                else:
                    final_error_msg += f": {error_msg}"

                self.update_task_status(
                    task.id,
                    "failed",
                    error_message=final_error_msg,
                    increment_attempts=True,
                )

                logging.error(
                    f"任务标记为失败: id={task.id}, error_type={error_type}, "
                    f"error={final_error_msg}"
                )

            raise

    def _process_chat_deep_research(
        self, task: BackgroundTask, request_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        处理文献调研聊天任务

        Args:
            task: 任务对象
            request_data: 请求数据

        Returns:
            dict[str, Any]: 处理结果
        """
        from api_services import chat_with_manus

        # 提取必要参数
        prompt = request_data.get("prompt", "")
        generate_literature_review = request_data.get("generate_literature_review", False)
        manus_api_key = request_data.get("manus_api_key")

        if not manus_api_key:
            manus_api_key = settings.MANUS_API_KEY

        if not manus_api_key:
            raise ValueError("MANUS_API_KEY未配置")

        # 创建进度跟踪器
        progress_tracker = self.create_progress_tracker(task.id)

        # 设置任务总步骤数（根据文献调研特点分为多个阶段）
        total_steps = 8  # 文献调研通常有8个主要阶段
        progress_tracker.set_total_steps(total_steps)

        # 定义进度回调函数
        def progress_callback(progress_percentage: int, step_description: str, step_details: Optional[Dict[str, Any]] = None):
            """
            进度回调函数，将进度更新传递给ProgressTracker

            Args:
                progress_percentage: 进度百分比 (0-100)
                step_description: 步骤描述
                step_details: 详细进度信息
            """
            try:
                # 根据进度百分比计算当前步骤
                current_step = int((progress_percentage / 100) * total_steps) if total_steps > 0 else 0

                progress_tracker.update_progress(
                    progress_percentage=progress_percentage,
                    current_step=current_step,
                    total_steps=total_steps,
                    step_description=step_description,
                    step_details=step_details
                )

                logging.debug(
                    f"任务进度更新: id={task.id}, progress={progress_percentage}%, "
                    f"step={current_step}/{total_steps}, description='{step_description}'"
                )
            except Exception as e:
                logging.warning(f"进度回调更新失败: id={task.id}, error={str(e)}")

        # 调用Manus API
        logging.info(f"处理文献调研任务: id={task.id}, prompt_length={len(prompt)}")

        result = chat_with_manus(
            prompt=prompt,
            api_key=manus_api_key,
            generate_literature_review=generate_literature_review,
            prompt_already_built=True,  # 已经在AIChatPanel中构建了提示词
            progress_callback=progress_callback,
        )

        # 任务完成，更新进度为100%
        progress_tracker.update_progress(
            progress_percentage=100,
            current_step=total_steps,
            step_description="文献调研完成",
            step_details={"action": "complete", "result_length": len(result.get("text", ""))}
        )

        return {
            "success": result.get("success", False),
            "text": result.get("text", ""),
            "steps": result.get("steps", []),
            "model_used": result.get("model_used", "manus-ai"),
            "error": result.get("error"),
        }

    def _process_chat_regular(
        self, task: BackgroundTask, request_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        处理普通聊天任务

        Args:
            task: 任务对象
            request_data: 请求数据

        Returns:
            dict[str, Any]: 处理结果
        """
        from api_services import chat_with_gemini

        # 提取必要参数
        messages = request_data.get("messages", [])
        api_key = request_data.get("api_key")

        if not api_key:
            api_key = settings.GEMINI_API_KEY

        if not api_key:
            raise ValueError("GEMINI_API_KEY未配置")

        # 创建进度跟踪器（普通聊天任务，进度相对简单）
        progress_tracker = self.create_progress_tracker(task.id)

        # 设置简单进度（普通聊天通常只有2个阶段）
        total_steps = 2
        progress_tracker.set_total_steps(total_steps)

        # 定义简单进度回调
        def progress_callback(progress_percentage: int, step_description: str, step_details: Optional[Dict[str, Any]] = None):
            """
            普通聊天进度回调函数

            Args:
                progress_percentage: 进度百分比 (0-100)
                step_description: 步骤描述
                step_details: 详细进度信息
            """
            try:
                # 根据进度百分比计算当前步骤
                current_step = int((progress_percentage / 100) * total_steps) if total_steps > 0 else 0

                progress_tracker.update_progress(
                    progress_percentage=progress_percentage,
                    current_step=current_step,
                    total_steps=total_steps,
                    step_description=step_description,
                    step_details=step_details
                )
            except Exception as e:
                logging.warning(f"聊天进度回调更新失败: id={task.id}, error={str(e)}")

        # 调用Gemini API
        logging.info(f"处理普通聊天任务: id={task.id}, messages_count={len(messages)}")

        # 更新进度：开始处理
        progress_tracker.update_progress(
            progress_percentage=30,
            current_step=0,
            step_description="正在生成回复"
        )

        result = chat_with_gemini(
            messages=messages,
            api_key=api_key,
        )

        # 任务完成，更新进度为100%
        progress_tracker.update_progress(
            progress_percentage=100,
            current_step=total_steps,
            step_description="回复生成完成",
            step_details={"action": "complete", "text_length": len(result.get("text", ""))}
        )

        return {
            "success": result.get("success", False),
            "text": result.get("text", ""),
            "model_used": result.get("model_used", "unknown"),
            "error": result.get("error"),
        }


# 全局任务服务实例
_task_service_instance = None


def get_background_task_service(db: Session) -> BackgroundTaskService:
    """获取后台任务服务实例（工厂函数）"""
    return BackgroundTaskService(db)