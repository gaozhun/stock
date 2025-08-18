# -*- coding: utf-8 -*-
"""
模块测试文件
用于验证重构后的各个模块是否正常工作
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试模块导入"""
    try:
        print("测试模块导入...")
        
        # 测试日志配置模块
        from logging_config import setup_default_logging, get_logger
        print("✅ logging_config 模块导入成功")
        
        # 测试工具函数模块
        from utils import format_currency, format_percentage, validate_symbols
        print("✅ utils 模块导入成功")
        
        # 测试UI组件模块
        from ui_components import get_custom_css, render_stock_card
        print("✅ ui_components 模块导入成功")
        
        # 测试回测运行器模块
        from backtest_runner import validate_backtest_inputs
        print("✅ backtest_runner 模块导入成功")
        
        # 测试策略UI模块
        from strategy_ui import open_strategy_modal
        print("✅ strategy_ui 模块导入成功")
        
        # 测试结果显示模块
        from results_display import display_results
        print("✅ results_display 模块导入成功")
        
        print("\n🎉 所有模块导入成功！")
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        return False

def test_logging():
    """测试日志功能"""
    try:
        print("\n测试日志功能...")
        
        from logging_config import setup_default_logging, get_logger
        
        # 设置日志
        setup_default_logging()
        
        # 获取日志记录器
        logger = get_logger("test")
        
        # 测试不同级别的日志
        logger.debug("这是一条调试日志")
        logger.info("这是一条信息日志")
        logger.warning("这是一条警告日志")
        logger.error("这是一条错误日志")
        
        print("✅ 日志功能测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 日志功能测试失败: {e}")
        return False

def test_utility_functions():
    """测试工具函数"""
    try:
        print("\n测试工具函数...")
        
        from utils import format_currency, format_percentage, validate_symbols
        
        # 测试货币格式化
        assert format_currency(1234567) == "¥123.46万"
        assert format_currency(123456789) == "¥1.23亿"
        
        # 测试百分比格式化
        assert format_percentage(0.1234) == "12.34%"
        
        # 测试股票代码验证
        assert validate_symbols(['000001', '000002']) == True
        assert validate_symbols([]) == False
        
        print("✅ 工具函数测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 工具函数测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试重构后的模块...\n")
    
    # 测试模块导入
    if not test_imports():
        return
    
    # 测试日志功能
    if not test_logging():
        return
    
    # 测试工具函数
    if not test_utility_functions():
        return
    
    print("\n🎉 所有测试通过！重构后的模块工作正常。")

if __name__ == "__main__":
    main()
