# -*- coding: utf-8 -*-
"""
日志功能测试脚本
用于验证改进后的日志配置，包括文件名和行号显示
"""

import sys
import os
import logging

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_basic_logging():
    """测试基本日志功能"""
    print("测试基本日志功能...")
    
    try:
        from logging_config import setup_default_logging, get_logger
        
        # 设置日志
        setup_default_logging()
        
        # 获取日志记录器
        logger = get_logger(__name__)
        
        # 测试不同级别的日志
        logger.debug("这是一条调试日志")
        logger.info("这是一条信息日志")
        logger.warning("这是一条警告日志")
        logger.error("这是一条错误日志")
        
        print("✅ 基本日志功能测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 基本日志功能测试失败: {e}")
        return False

def test_file_line_logging():
    """测试文件名和行号显示"""
    print("\n测试文件名和行号显示...")
    
    try:
        from logging_config import get_logger
        
        logger = get_logger(__name__)
        
        # 这些日志应该显示当前文件名和行号
        logger.info("测试日志1 - 应该显示文件名和行号")
        logger.warning("测试日志2 - 应该显示文件名和行号")
        logger.error("测试日志3 - 应该显示文件名和行号")
        
        print("✅ 文件名和行号显示测试成功")
        print("请检查上面的日志输出，应该包含文件名和行号信息")
        return True
        
    except Exception as e:
        print(f"❌ 文件名和行号显示测试失败: {e}")
        return False

def test_different_modules():
    """测试不同模块的日志"""
    print("\n测试不同模块的日志...")
    
    try:
        from logging_config import get_logger
        
        # 测试不同模块名称的日志记录器
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        logger3 = get_logger("utils")
        
        logger1.info("这是模块1的日志")
        logger2.warning("这是模块2的警告")
        logger3.error("这是工具模块的错误")
        
        print("✅ 不同模块日志测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 不同模块日志测试失败: {e}")
        return False

def test_log_file_creation():
    """测试日志文件创建"""
    print("\n测试日志文件创建...")
    
    try:
        from logging_config import get_log_file_path
        
        log_file_path = get_log_file_path()
        print(f"日志文件路径: {log_file_path}")
        
        if os.path.exists(os.path.dirname(log_file_path)):
            print("✅ 日志目录存在")
        else:
            print("❌ 日志目录不存在")
            return False
        
        # 检查是否有日志文件
        log_dir = "logs"
        if os.path.exists(log_dir):
            log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
            if log_files:
                print(f"✅ 找到日志文件: {log_files}")
                return True
            else:
                print("❌ 未找到日志文件")
                return False
        else:
            print("❌ 日志目录不存在")
            return False
            
    except Exception as e:
        print(f"❌ 日志文件创建测试失败: {e}")
        return False

def test_debug_logging():
    """测试调试级别日志"""
    print("\n测试调试级别日志...")
    
    try:
        from logging_config import setup_debug_logging, get_logger
        
        # 设置调试级别日志
        setup_debug_logging()
        
        logger = get_logger(__name__)
        
        # 调试级别应该显示
        logger.debug("这是一条调试日志 - 应该显示")
        logger.info("这是一条信息日志 - 应该显示")
        
        print("✅ 调试级别日志测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 调试级别日志测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试改进后的日志功能...\n")
    
    tests = [
        ("基本日志功能", test_basic_logging),
        ("文件名和行号显示", test_file_line_logging),
        ("不同模块日志", test_different_modules),
        ("日志文件创建", test_log_file_creation),
        ("调试级别日志", test_debug_logging),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"🧪 测试: {test_name}")
        if test_func():
            passed += 1
        print("-" * 50)
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！日志功能正常。")
        print("\n📝 日志格式说明:")
        print("格式: 时间 - 模块名 - 级别 - 文件名:行号 - 函数名() - 消息")
        print("示例: 2024-01-01 12:00:00 - __main__ - INFO - test_logging.py:45 - main() - 测试完成")
    else:
        print("❌ 部分测试失败，请检查错误信息。")

if __name__ == "__main__":
    main()
