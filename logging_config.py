# -*- coding: utf-8 -*-
"""
日志配置模块
配置标准的logging模块，用于整个应用程序的日志记录
"""

import logging
import os
from datetime import datetime

# 全局标志，用于跟踪日志系统是否已初始化
_logging_initialized = False

def setup_logging(log_level=logging.INFO, log_file=None):
    """设置日志配置
    
    Args:
        log_level: 日志级别，默认为INFO
        log_file: 日志文件路径，如果为None则不写入文件
    """
    global _logging_initialized
    
    # 如果日志系统已经初始化，直接返回
    if _logging_initialized:
        return logging.getLogger()
    
    # 创建日志记录器
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # 清除现有的处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 创建格式化器 - 包含文件名和行号
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 如果指定了日志文件，创建文件处理器
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 创建文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('plotly').setLevel(logging.WARNING)
    logging.getLogger('streamlit').setLevel(logging.WARNING)
    
    # 标记日志系统已初始化
    _logging_initialized = True
    
    return logger

def get_logger(name):
    """获取指定名称的日志记录器
    
    Args:
        name: 日志记录器名称，通常是__name__
    
    Returns:
        配置好的日志记录器
    """
    return logging.getLogger(name)

def setup_default_logging():
    """设置默认的日志配置"""
    # 检查是否已经初始化
    if _logging_initialized:
        logger = get_logger(__name__)
        logger.debug("日志系统已经初始化，跳过重复配置")
        return
    
    log_dir = "logs"
    log_file = os.path.join(log_dir, f"web_app_{datetime.now().strftime('%Y%m%d')}.log")
    setup_logging(log_level=logging.INFO, log_file=log_file)
    
    # 输出初始日志信息
    logger = get_logger(__name__)
    logger.info("日志系统初始化完成")
    logger.info(f"日志文件路径: {os.path.abspath(log_file)}")

def setup_debug_logging():
    """设置调试级别的日志配置"""
    # 检查是否已经初始化
    if _logging_initialized:
        logger = get_logger(__name__)
        logger.debug("日志系统已经初始化，跳过重复配置")
        return
    
    log_dir = "logs"
    log_file = os.path.join(log_dir, f"web_app_debug_{datetime.now().strftime('%Y%m%d')}.log")
    setup_logging(log_level=logging.DEBUG, log_file=log_file)
    
    # 输出初始日志信息
    logger = get_logger(__name__)
    logger.debug("调试日志系统初始化完成")
    logger.debug(f"调试日志文件路径: {os.path.abspath(log_file)}")

def setup_minimal_logging():
    """设置最小化的日志配置（仅控制台输出）"""
    # 检查是否已经初始化
    if _logging_initialized:
        logger = get_logger(__name__)
        logger.debug("日志系统已经初始化，跳过重复配置")
        return
    
    setup_logging(log_level=logging.INFO, log_file=None)
    
    # 输出初始日志信息
    logger = get_logger(__name__)
    logger.info("最小化日志系统初始化完成（仅控制台输出）")

def reset_logging():
    """重置日志系统（用于测试或特殊情况）"""
    global _logging_initialized
    _logging_initialized = False
    
    # 清除所有处理器
    logger = logging.getLogger()
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    logger.info("日志系统已重置")

def is_logging_initialized():
    """检查日志系统是否已初始化"""
    return _logging_initialized

def get_log_file_path():
    """获取当前日志文件路径"""
    log_dir = "logs"
    return os.path.join(log_dir, f"web_app_{datetime.now().strftime('%Y%m%d')}.log")

def clear_old_logs(days_to_keep=30):
    """清理旧的日志文件
    
    Args:
        days_to_keep: 保留最近几天的日志文件，默认30天
    """
    try:
        log_dir = "logs"
        if not os.path.exists(log_dir):
            return
        
        current_time = datetime.now()
        for filename in os.listdir(log_dir):
            if filename.startswith("web_app_") and filename.endswith(".log"):
                file_path = os.path.join(log_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                
                if (current_time - file_time).days > days_to_keep:
                    os.remove(file_path)
                    logger = get_logger(__name__)
                    logger.info(f"已删除旧日志文件: {filename}")
                    
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"清理旧日志文件时出错: {e}")
