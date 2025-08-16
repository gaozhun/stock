# -*- coding: utf-8 -*-
"""
快速启动脚本
提供便捷的启动选项
"""

import sys
import os
import subprocess
from pathlib import Path


def check_dependencies():
    """检查依赖是否安装"""
    required_packages = [
        'pandas', 'numpy', 'matplotlib', 'akshare',
        'seaborn', 'plotly', 'streamlit', 'scipy'
    ]
    
    missing_packages = []
    
    print("📦 检查系统依赖...")
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    # 检查akshare版本
    try:
        import akshare as ak
        print(f"🎯 akshare版本: {ak.__version__}")
    except:
        pass
    
    # 检查Python版本
    import sys
    python_version = sys.version_info
    print(f"🐍 Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 10):
        print("💡 建议使用Python 3.10+以获得最佳性能")
    
    if missing_packages:
        print(f"\n❌ 缺少依赖: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    print("\n✅ 系统环境检查通过")
    return True


def run_web_app():
    """启动Web应用"""
    print("🌐 启动Web界面...")
    try:
        subprocess.run(['streamlit', 'run', 'web_app.py'], check=True)
    except subprocess.CalledProcessError:
        print("❌ Web应用启动失败")
    except FileNotFoundError:
        print("❌ 未找到streamlit命令，请确保已安装streamlit")


def run_example():
    """运行示例"""
    print("📚 运行示例程序...")
    try:
        subprocess.run([sys.executable, 'example.py'], check=True)
    except subprocess.CalledProcessError:
        print("❌ 示例程序运行失败")





def run_etf_example():
    """运行ETF回测示例"""
    print("📊 运行ETF回测示例...")
    try:
        subprocess.run([sys.executable, 'etf_example.py'], check=True)
    except subprocess.CalledProcessError:
        print("❌ ETF示例运行失败")
    except FileNotFoundError:
        print("❌ 未找到示例脚本 etf_example.py")

def run_akshare_test():
    """运行AKShare数据源测试"""
    print("📊 运行AKShare数据源测试...")
    try:
        subprocess.run([sys.executable, 'test_akshare.py'], check=True)
    except subprocess.CalledProcessError:
        print("❌ AKShare测试运行失败")
    except FileNotFoundError:
        print("❌ 未找到测试脚本 test_akshare.py")


def show_help():
    """显示帮助信息"""
    help_text = """
📈 股票基金回测系统 - 快速启动

使用方法:
  python run.py [选项]

选项:
  web       启动Web界面 (推荐)
  example   运行示例程序
  etf       运行ETF回测示例
  akshare   测试AKShare数据源
  check     检查依赖
  help      显示此帮助信息

示例:
  python run.py web      # 启动Web界面
  python run.py example  # 运行示例
  python run.py etf      # ETF回测示例
  python run.py akshare  # 测试AKShare
  python run.py check    # 检查依赖

功能特点:
✨ 多种投资策略 (买入持有、移动平均、RSI等)
📊 完整的性能分析指标
📈 交互式图表展示
🔧 参数优化功能
🌐 友好的Web界面

首次使用建议:
1. 运行 'python run.py check' 检查依赖
2. 运行 'python run.py akshare' 测试数据源
3. 运行 'python run.py example' 查看股票示例
4. 运行 'python run.py etf' 查看ETF示例
5. 运行 'python run.py web' 启动Web界面
"""
    print(help_text)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("📈 股票基金回测系统")
        print("运行 'python run.py help' 查看使用方法")
        print("运行 'python run.py web' 快速启动Web界面")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'help':
        show_help()
    elif command == 'check':
        check_dependencies()
    elif command == 'akshare':
        if check_dependencies():
            run_akshare_test()
    elif command == 'web':
        if check_dependencies():
            run_web_app()
    elif command == 'example':
        if check_dependencies():
            run_example()
    elif command == 'etf':
        if check_dependencies():
            run_etf_example()
    else:
        print(f"❌ 未知命令: {command}")
        print("运行 'python run.py help' 查看可用命令")


if __name__ == "__main__":
    main()
