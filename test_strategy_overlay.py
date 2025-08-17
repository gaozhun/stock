# -*- coding: utf-8 -*-
"""
测试策略叠加机制
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import sys
import os

# 导入自定义模块
from stock_strategy import Strategy, SignalType, Stock, Portfolio
from data_handler import DataHandler
from backtest_engine import BacktestEngine

def create_test_data(start_date='2022-01-01', end_date='2022-12-31', freq='D'):
    """创建测试数据"""
    date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
    
    # 创建价格数据
    data = pd.DataFrame(index=date_range)
    
    # 生成模拟价格
    np.random.seed(42)  # 设置随机种子，保证结果可重现
    
    # 基础价格从100开始
    base_price = 100
    
    # 生成随机价格变化
    price_changes = np.random.normal(0, 1, len(date_range))
    price_changes[0] = 0  # 第一天不变
    
    # 累积价格变化
    cumulative_changes = np.cumsum(price_changes)
    
    # 生成价格
    prices = base_price + cumulative_changes * 2
    
    # 确保价格为正
    prices = np.maximum(prices, 10)
    
    # 设置价格数据
    data['Open'] = prices * 0.99
    data['High'] = prices * 1.02
    data['Low'] = prices * 0.98
    data['Close'] = prices
    data['Volume'] = np.random.randint(1000, 10000, len(date_range))
    
    return data

def test_strategy_overlay():
    """测试策略叠加机制"""
    print("开始测试策略叠加机制...")
    
    # 创建测试数据
    data = create_test_data()
    
    # 创建股票对象
    stock = Stock(code='TEST', initial_investment=0, max_investment=100000)
    
    # 创建买入策略1 - 每周一买入
    buy_strategy1 = Strategy(
        name='每周一买入',
        type='time_based',
        signal_type=SignalType.BUY,
        params={
            'frequency': 'weekly',
            'trading_day': 0,  # 周一
            'trade_amount': 10000
        },
        enabled=True
    )
    
    # 创建买入策略2 - 每月1日买入
    buy_strategy2 = Strategy(
        name='每月1日买入',
        type='time_based',
        signal_type=SignalType.BUY,
        params={
            'frequency': 'monthly',
            'trading_day': 1,  # 每月1日
            'trade_amount': 20000
        },
        enabled=True
    )
    
    # 创建卖出策略1 - 每周五卖出
    sell_strategy1 = Strategy(
        name='每周五卖出',
        type='time_based',
        signal_type=SignalType.SELL,
        params={
            'frequency': 'weekly',
            'trading_day': 4,  # 周五
            'trade_amount': 15000
        },
        enabled=True
    )
    
    # 创建卖出策略2 - 每月15日卖出
    sell_strategy2 = Strategy(
        name='每月15日卖出',
        type='time_based',
        signal_type=SignalType.SELL,
        params={
            'frequency': 'monthly',
            'trading_day': 15,  # 每月15日
            'trade_amount': 25000
        },
        enabled=True
    )
    
    # 添加策略
    stock.add_strategy(buy_strategy1)
    stock.add_strategy(buy_strategy2)
    stock.add_strategy(sell_strategy1)
    stock.add_strategy(sell_strategy2)
    
    # 生成信号
    signals = stock.get_signals(data)
    
    # 计算交易金额
    trade_amounts = stock.get_trade_amounts(data, signals)
    
    # 分析结果
    print("\n信号分析结果:")
    print(f"总天数: {len(data)}")
    print(f"买入信号天数: {sum(signals > 0)}")
    print(f"卖出信号天数: {sum(signals < 0)}")
    print(f"无信号天数: {sum(signals == 0)}")
    
    # 找出同时有买入和卖出策略的日期
    overlap_dates = []
    for date in data.index:
        buy_signal = False
        sell_signal = False
        
        # 检查买入策略
        for strategy in stock.buy_strategies:
            if strategy.enabled:
                strategy_signals = stock._generate_strategy_signals(data, strategy)
                if date in strategy_signals.index and strategy_signals[date] == 1:
                    buy_signal = True
                    break
        
        # 检查卖出策略
        for strategy in stock.sell_strategies:
            if strategy.enabled:
                strategy_signals = stock._generate_strategy_signals(data, strategy)
                if date in strategy_signals.index and strategy_signals[date] == -1:
                    sell_signal = True
                    break
        
        # 如果同一天既有买入又有卖出信号
        if buy_signal and sell_signal:
            overlap_dates.append(date)
    
    print(f"\n同时有买入和卖出策略的日期数量: {len(overlap_dates)}")
    
    if overlap_dates:
        print("\n同时有买入和卖出策略的日期详情:")
        for date in overlap_dates:
            print(f"日期: {date.strftime('%Y-%m-%d')}, 信号值: {signals[date]}, 交易金额: {trade_amounts[date]}")
            
            # 显示各个策略在该日期的信号
            print("  买入策略信号:")
            for strategy in stock.buy_strategies:
                if strategy.enabled:
                    strategy_signals = stock._generate_strategy_signals(data, strategy)
                    strategy_amounts = stock._calculate_strategy_amounts(data, strategy_signals, strategy, stock.fee_rate)
                    if date in strategy_signals.index and strategy_signals[date] == 1:
                        print(f"    策略 '{strategy.name}': 信号={strategy_signals[date]}, 金额={strategy_amounts[date]}")
            
            print("  卖出策略信号:")
            for strategy in stock.sell_strategies:
                if strategy.enabled:
                    strategy_signals = stock._generate_strategy_signals(data, strategy)
                    strategy_amounts = stock._calculate_strategy_amounts(data, strategy_signals, strategy, stock.fee_rate)
                    if date in strategy_signals.index and strategy_signals[date] == -1:
                        print(f"    策略 '{strategy.name}': 信号={strategy_signals[date]}, 金额={strategy_amounts[date]}")
    
    # 运行回测
    print("\n开始运行回测...")
    portfolio = Portfolio()
    portfolio.add_stock('TEST', initial_investment=0, max_investment=100000)
    portfolio.stocks['TEST'] = stock  # 使用已配置的股票对象
    
    # 准备自定义数据用于回测
    custom_data = {'TEST': data}
    
    backtest_engine = BacktestEngine()
    results = backtest_engine.run_portfolio_backtest(
        portfolio=portfolio,
        symbols=['TEST'],
        start_date='2022-01-01',
        end_date='2022-12-31',
        custom_data=custom_data
    )
    
    # 显示回测结果
    print("\n回测结果:")
    print(f"初始资金: {results['initial_capital']}")
    print(f"最终资产: {results['final_value']}")
    print(f"总收益率: {results['total_return'] * 100:.2f}%")
    
    # 输出交易记录
    trades = results['trades']
    print(f"\n交易记录数量: {len(trades)}")
    
    if trades:
        print("\n交易记录示例:")
        for i, trade in enumerate(trades[:5]):  # 显示前5条交易记录
            print(f"交易 {i+1}: 日期={trade['date'].strftime('%Y-%m-%d')}, 类型={trade['type']}, 股数={trade['shares']}, 价格={trade['price']:.2f}, 金额={trade['value']:.2f}")
    
    # 绘制资产曲线
    plt.figure(figsize=(12, 6))
    plt.plot(results['portfolio_value'], label='资产价值')
    plt.title('资产价值曲线')
    plt.xlabel('日期')
    plt.ylabel('价值')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('strategy_overlay_test_result.png')
    plt.close()
    
    print("\n测试完成! 结果图表已保存为 'strategy_overlay_test_result.png'")

if __name__ == "__main__":
    test_strategy_overlay()
