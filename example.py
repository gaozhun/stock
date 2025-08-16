# -*- coding: utf-8 -*-
"""
使用示例
展示如何使用股票基金回测系统
"""

from datetime import datetime, timedelta
from data_handler import DataHandler
from strategies import StrategyFactory
from backtest_engine import BacktestEngine
from performance import PerformanceAnalyzer
from visualization import Visualizer


def simple_backtest_example():
    """简单回测示例"""
    print("🚀 运行简单回测示例")
    print("=" * 50)
    
    # 设置参数
    symbols = ['000001']
    # 使用固定的历史日期范围
    end_date = '2024-12-31'   # 2024年底
    start_date = '2024-01-01' # 2024年初，完整一年数据
    initial_capital = 100000
    
    print(f"股票: {symbols}")
    print(f"期间: {start_date} 至 {end_date}")
    print(f"初始资金: ${initial_capital:,}")
    print("-" * 30)
    
    # 创建策略
    strategy = StrategyFactory.create_strategy('buy_hold')
    
    # 运行回测（添加基准对比）
    engine = BacktestEngine(initial_capital=initial_capital)
    results = engine.run_backtest(
        symbols=symbols,
        strategy=strategy,
        start_date=start_date,
        end_date=end_date,
        benchmark='sh000300'  # 使用沪深300作为基准
    )
    
    # 生成报告
    analyzer = PerformanceAnalyzer()
    report = analyzer.generate_performance_report(results)
    print(report)


def strategy_comparison_example():
    """策略对比示例"""
    print("\n🔄 运行策略对比示例")
    print("=" * 50)
    
    # 设置参数
    symbols = ['000001']
    # 使用固定的历史日期范围（2年数据）
    end_date = '2024-12-31'   # 2024年底
    start_date = '2023-01-01' # 2023年初，2年数据
    initial_capital = 100000
    
    # 创建多个策略
    strategies = [
        StrategyFactory.create_strategy('buy_hold'),
        StrategyFactory.create_strategy('moving_average', {'short_window': 20, 'long_window': 60}),
        StrategyFactory.create_strategy('rsi', {'rsi_period': 14, 'oversold': 30, 'overbought': 70})
    ]
    
    # 运行回测
    engine = BacktestEngine(initial_capital=initial_capital)
    results_dict = engine.run_multiple_strategies(
        symbols=symbols,
        strategies=strategies,
        start_date=start_date,
        end_date=end_date
    )
    
    # 生成对比报告
    analyzer = PerformanceAnalyzer()
    comparison_df = analyzer.compare_strategies(results_dict)
    
    print("📊 策略对比结果:")
    print(comparison_df)


def parameter_optimization_example():
    """参数优化示例"""
    print("\n🎯 运行参数优化示例")
    print("=" * 50)
    
    # 设置参数
    symbols = ['AAPL']
    # 使用固定的历史日期范围
    end_date = '2024-12-31'   # 2024年底
    start_date = '2024-01-01' # 2024年初
    
    # 定义参数网格（简化版本用于演示）
    param_grid = {
        'short_window': [10, 20],
        'long_window': [50, 60]
    }
    
    # 运行优化
    engine = BacktestEngine()
    try:
        optimization_result = engine.optimize_strategy(
            symbols=symbols,
            strategy_name='moving_average',
            param_grid=param_grid,
            start_date=start_date,
            end_date=end_date,
            metric='sharpe_ratio'
        )
        
        if optimization_result['best_params']:
            print(f"🎯 最优参数: {optimization_result['best_params']}")
            print(f"📈 最优夏普比率: {optimization_result['best_score']:.4f}")
        else:
            print("❌ 优化失败")
            
    except Exception as e:
        print(f"优化过程出错: {str(e)}")


def data_exploration_example():
    """数据探索示例"""
    print("\n📊 数据探索示例")
    print("=" * 50)
    
    # 创建数据处理器
    data_handler = DataHandler()
    
    # 获取股票数据
    try:
        symbol = 'AAPL'
        # 使用固定的历史日期范围
        end_date = '2024-12-31'   # 2024年底
        start_date = '2024-07-01' # 2024年7月，约6个月数据
        
        print(f"获取 {symbol} 数据...")
        data = data_handler.get_stock_data(symbol, start_date, end_date)
        
        print(f"数据形状: {data.shape}")
        print(f"日期范围: {data.index[0].date()} 至 {data.index[-1].date()}")
        print(f"价格范围: ${data['Close'].min():.2f} - ${data['Close'].max():.2f}")
        
        # 计算技术指标
        data_with_indicators = data_handler.calculate_technical_indicators(data)
        print(f"技术指标数量: {len(data_with_indicators.columns)}")
        
        # 获取股票信息
        stock_info = data_handler.get_stock_info(symbol)
        print(f"股票名称: {stock_info.get('name', 'Unknown')}")
        print(f"行业: {stock_info.get('sector', 'Unknown')}")
        
    except Exception as e:
        print(f"数据获取失败: {str(e)}")


if __name__ == "__main__":
    try:
        # 运行各种示例
        simple_backtest_example()
        strategy_comparison_example()
        data_exploration_example()
        # parameter_optimization_example()  # 注释掉避免过长运行时间
        
        print("\n✅ 所有示例运行完成！")
        print("\n🌐 要使用Web界面，请运行: streamlit run web_app.py")
        print("🚀 或者使用快速启动: python run.py web")
        
    except Exception as e:
        print(f"\n❌ 示例运行失败: {str(e)}")
        print("请确保已安装所有依赖: pip install -r requirements.txt")
