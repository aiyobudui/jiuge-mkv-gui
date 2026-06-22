# -*- coding: utf-8 -*-
"""
通用后台任务执行器 — 封装 threading.Thread + ThreadPoolExecutor + 信号发射模式

所有界面（混流、轨道提取、视频轨道加载等）统一调用此类，避免每个界面重复写线程代码。

使用方式（从主线程调用）：
    runner = BackgroundRunner()
    runner.task_finished.connect(on_finished)      # Qt 信号 -> 主线程 UI 更新
    runner.task_error.connect(on_error)
    runner.all_done.connect(on_all_done)
    runner.run(tasks, worker_func, max_workers=8,
               on_task_done=my_callback,            # 后台线程回调 -> 后处理
               on_all_done=my_final_callback)

已经在后台线程中的调用者（如 ExtractTracksDialog），请勿使用 run()
（会嵌套线程）；直接用 calc_workers() 获取线程数后自行管理 ThreadPoolExecutor。
"""

import os
import threading
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from PySide6.QtCore import QObject, Signal


class BackgroundRunner(QObject):
    """在后台线程中并发执行任务，通过 Qt 信号通知主线程更新 UI。

    Signal:
        task_progress(int task_id, str message)  -- 单任务进度（文本消息）
        task_finished(int task_id, dict result)   -- 单任务完成
        task_error(int task_id, str error)        -- 单任务失败
        all_done(int completed, int failed, int total) -- 全部完成
    """

    task_progress = Signal(int, str)
    task_finished = Signal(int, object)   # dict
    task_error = Signal(int, str)
    all_done = Signal(int, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._generation = 0
        self._stop_requested = False

    @property
    def stop_requested(self):
        return self._stop_requested

    def request_stop(self):
        """请求停止正在运行的任务"""
        self._stop_requested = True

    def run(self, tasks, worker_func, max_workers=None,
            on_task_done=None, on_all_done=None):
        """启动后台任务（从主线程调用，自动创建后台线程）。

        Args:
            tasks: 任务数据列表 (list)，每个元素作为 task_data 传递给 worker_func
            worker_func: 单个任务的处理函数，签名 func(task_data, task_id) -> dict
                         返回 dict 可通过 {"error": "..."} 标记失败
            max_workers: 并发线程数。默认 cpu_count * 2，上限 16，至少为 1
            on_task_done: 可选，每个任务完成时的回调（在后台线程中调用）
                          签名 callback(task_id, result_dict)
            on_all_done: 可选，全部任务完成时的回调（在后台线程中调用）
                         签名 callback(completed, failed, total)
        """
        if not tasks:
            self.all_done.emit(0, 0, 0)
            if on_all_done:
                on_all_done(0, 0, 0)
            return

        if max_workers is None:
            max_workers = max(1, min((os.cpu_count() or 4) * 2, 16, len(tasks)))

        self._generation += 1
        gen = self._generation
        self._stop_requested = False

        def _worker():
            completed = 0
            failed = 0
            total = len(tasks)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_map = {}
                for i, task_data in enumerate(tasks):
                    if self._stop_requested:
                        break
                    future = executor.submit(worker_func, task_data, i)
                    future_map[future] = i

                for future in as_completed(future_map):
                    if self._generation != gen:
                        return  # 过期任务，丢弃

                    if self._stop_requested:
                        break

                    task_id = future_map[future]
                    try:
                        result = future.result()
                        if isinstance(result, dict) and result.get("error"):
                            failed += 1
                            self.task_error.emit(task_id, str(result["error"]))
                        else:
                            completed += 1
                            self.task_finished.emit(task_id, result or {})
                            if on_task_done:
                                on_task_done(task_id, result or {})
                    except Exception as e:
                        failed += 1
                        logging.warning(f"任务 {task_id} 异常: {e}")
                        self.task_error.emit(task_id, str(e))

            if self._generation == gen:
                if on_all_done:
                    on_all_done(completed, failed, total)
                self.all_done.emit(completed, failed, total)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    @staticmethod
    def calc_workers(task_count=None):
        """计算合理的并发线程数（IO 密集型任务）。

        Returns:
            int: max_workers 值
        """
        cpu = os.cpu_count() or 4
        workers = min(cpu * 2, 16)
        if task_count:
            workers = min(workers, task_count)
        return max(1, workers)
