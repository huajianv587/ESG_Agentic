import logging
import sys
from pathlib import Path

# 日志目录：项目根目录/logs，自动创建
LOG_DIR = Path(__file__).resolve().parents[3] / "logs"
LOG_DIR.mkdir(exist_ok=True)


def get_logger(name: str) -> logging.Logger:
    """
    返回统一格式的 logger，带三个输出目标。
    
    输出策略：
    - DEBUG+  → logs/app.log（全量日志存档）
    - INFO+   → 终端（开发时实时查看）
    - WARNING+ → logs/error.log（错误日志单独存储，便于排查）
    
    日志级别：DEBUG < INFO < WARNING < ERROR < CRITICAL
    
    用法:
        from gateway.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("something happened")
    """
    logger = logging.getLogger(name)

    # 单例检查：避免重复添加 handler（多次调用 get_logger 时）
    if logger.handlers:
        return logger

    # logger 本身设为 DEBUG，由各 handler 控制实际输出级别
    logger.setLevel(logging.DEBUG)
    
    # 统一日志格式：时间 | 级别 | 模块名 | 消息
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler 1: 终端输出（INFO 及以上）
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)

    # Handler 2: 全量日志文件（DEBUG 及以上，用于完整追溯）
    app_file = logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8")
    app_file.setLevel(logging.DEBUG)
    app_file.setFormatter(fmt)

    # Handler 3: 错误日志文件（WARNING 及以上，便于快速定位问题）
    err_file = logging.FileHandler(LOG_DIR / "error.log", encoding="utf-8")
    err_file.setLevel(logging.WARNING)
    err_file.setFormatter(fmt)

    logger.addHandler(console)
    logger.addHandler(app_file)
    logger.addHandler(err_file)

    return logger
