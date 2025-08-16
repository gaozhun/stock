# -*- coding: utf-8 -*-
"""
回测引擎模块
负责执行策略回测和生成交易记录
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from data_handler import DataHandler
from strategies import BaseStrategy, StrategyFactory
from config import BACKTEST_CONFIG, BENCHMARK_CONFIG


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_capital: float = None, commission_rate: float = None):
        """
        初始化回测引擎
        
        Args:
            initial_capital: 初始资金
            commission_rate: 手续费率
        """
        self.initial_capital = initial_capital or BACKTEST_CONFIG['initial_capital']
        self.commission_rate = commission_rate or BACKTEST_CONFIG['commission_rate']
        
        # 回测结果
        self.portfolio_value = pd.Series()
        self.positions = pd.DataFrame()
        self.trades = []
        self.cash_history = pd.Series()
        self.holdings_history = pd.Series()
        
        # 数据处理器
        self.data_handler = DataHandler()
    
    def run_backtest(self, 
                    symbols: List[str],
                    strategy: BaseStrategy,
                    start_date: str,
                    end_date: str,
                    benchmark: str = None) -> Dict[str, Any]:
        """
        运行回测
        
        Args:
            symbols: 股票代码列表
            strategy: 交易策略
            start_date: 开始日期
            end_date: 结束日期
            benchmark: 基准指数
            
        Returns:
            回测结果字典
        """
        print(f"开始回测策略: {strategy.name}")
        print(f"股票池: {symbols}")
        print(f"回测期间: {start_date} 至 {end_date}")
        
        # 获取价格数据
        if len(symbols) == 1:
            price_data = self.data_handler.get_stock_data(symbols[0], start_date, end_date)
            price_data = price_data[['Close']].rename(columns={'Close': symbols[0]})
        else:
            price_data = self.data_handler.get_multiple_stocks(symbols, start_date, end_date)
        
        # 获取基准数据
        if benchmark is None:
            benchmark = BENCHMARK_CONFIG.get('default', 'sh000300')
        
        benchmark_data = None
        benchmark_name = BENCHMARK_CONFIG.get('available_benchmarks', {}).get(benchmark, benchmark)
        
        try:
            benchmark_data = self.data_handler.get_benchmark_data(start_date, end_date, benchmark)
            print(f"📊 使用基准指数: {benchmark_name} ({benchmark})")
        except Exception as e:
            print(f"⚠️  无法获取基准数据 {benchmark_name}: {str(e)}")
        
        # 生成交易信号
        if len(symbols) == 1:
            full_data = self.data_handler.get_stock_data(symbols[0], start_date, end_date)
            signals = strategy.generate_signals(full_data)
        else:
            # 对于多股票，使用第一只股票生成信号（可以扩展为更复杂的逻辑）
            full_data = self.data_handler.get_stock_data(symbols[0], start_date, end_date)
            signals = strategy.generate_signals(full_data)
        
        # 计算持仓
        positions = strategy.calculate_positions(signals)
        
        # 获取交易信号（如果策略支持）
        trading_signals = None
        if hasattr(strategy, 'get_trading_signals'):
            trading_signals = strategy.get_trading_signals(signals)
        
        # 执行回测计算
        portfolio_results = self._calculate_portfolio_performance(
            price_data, positions, symbols, trading_signals
        )
        
        # 计算基准表现
        benchmark_returns = None
        if benchmark_data is not None:
            benchmark_returns = benchmark_data['Close'].pct_change().dropna()
        
        # 计算总收益率
        final_value = portfolio_results['portfolio_value'].iloc[-1]
        total_return = (final_value / self.initial_capital) - 1
        
        # 生成回测报告
        results = {
            'strategy_name': strategy.name,
            'symbols': symbols,
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'portfolio_value': portfolio_results['portfolio_value'],
            'returns': portfolio_results['returns'],
            'positions': portfolio_results['positions'],
            'trades': portfolio_results['trades'],
            'benchmark_returns': benchmark_returns,
            'benchmark': benchmark,
            'signals': signals,
            'price_data': price_data
        }
        
        print(f"回测完成! 最终资产价值: ${portfolio_results['portfolio_value'].iloc[-1]:,.2f}")
        return results
    
    def _calculate_portfolio_performance(self, 
                                       price_data: pd.DataFrame,
                                       positions: pd.Series,
                                       symbols: List[str],
                                       signals: pd.Series = None) -> Dict:
        """
        计算投资组合表现
        
        Args:
            price_data: 价格数据
            positions: 持仓信号
            symbols: 股票代码
            
        Returns:
            包含投资组合表现的字典
        """
        # 对齐数据
        common_dates = price_data.index.intersection(positions.index)
        price_data = price_data.loc[common_dates]
        positions = positions.loc[common_dates]
        
        # 初始化变量
        cash = self.initial_capital
        holdings = {symbol: 0.0 for symbol in symbols}
        portfolio_values = []
        cash_history = []
        holdings_history = []
        trades = []
        
        # 逐日计算
        for date in price_data.index:
            current_prices = price_data.loc[date]
            target_position = positions.loc[date]
            
            # 检查是否有交易信号
            has_signal = False
            if signals is not None and date in signals.index:
                has_signal = signals.loc[date] != 0
            
            # 计算当前持仓价值
            current_holdings_value = sum(
                holdings[symbol] * current_prices[symbol] 
                for symbol in symbols
            )
            
            # 计算目标持仓
            total_value = cash + current_holdings_value
            target_holdings_value = total_value * target_position
            
            # 执行交易 - 支持单股票和多股票组合
            if len(symbols) == 1:
                # 单股票策略
                symbol = symbols[0]
                current_price = current_prices[symbol]
                
                # 计算需要调整的股数
                current_shares = holdings[symbol]
                target_shares = target_holdings_value / current_price if current_price > 0 else 0
                shares_to_trade = target_shares - current_shares
                
                # 只在有信号时才执行交易（对于定投策略）
                if abs(shares_to_trade) > 0.001 and has_signal:
                    # 执行交易
                    trade_value = shares_to_trade * current_price
                    commission = abs(trade_value) * self.commission_rate
                    
                    # 更新现金和持仓
                    cash -= (trade_value + commission)
                    holdings[symbol] = target_shares
                    
                    # 记录交易
                    trades.append({
                        'date': date,
                        'symbol': symbol,
                        'shares': shares_to_trade,
                        'price': current_price,
                        'value': trade_value,
                        'commission': commission,
                        'type': 'buy' if shares_to_trade > 0 else 'sell'
                    })
            else:
                # 多股票组合策略 - 等权重分配
                if target_position > 0:  # 只有当信号为正时才执行交易
                    # 计算每只股票的目标分配金额（等权重）
                    per_stock_target = target_holdings_value / len(symbols)
                    
                    total_commission = 0
                    for symbol in symbols:
                        if symbol in current_prices and current_prices[symbol] > 0:
                            current_price = current_prices[symbol]
                            current_shares = holdings[symbol]
                            current_value = current_shares * current_price
                            
                            # 计算目标股数
                            target_shares = per_stock_target / current_price
                            shares_to_trade = target_shares - current_shares
                            
                            if abs(shares_to_trade) > 0.001:  # 最小交易单位
                                # 计算交易费用
                                trade_value = shares_to_trade * current_price
                                commission = abs(trade_value) * self.commission_rate
                                total_commission += commission
                                
                                # 记录交易
                                trades.append({
                                    'date': date,
                                    'symbol': symbol,
                                    'shares': shares_to_trade,
                                    'price': current_price,
                                    'value': trade_value,
                                    'commission': commission,
                                    'type': 'buy' if shares_to_trade > 0 else 'sell'
                                })
                                
                                # 更新持仓
                                holdings[symbol] = target_shares
                    
                    # 更新现金
                    total_investment = sum(holdings[symbol] * current_prices[symbol] 
                                         for symbol in symbols if symbol in current_prices)
                    cash = total_value - total_investment - total_commission
                else:
                    # 清空所有持仓
                    total_commission = 0
                    for symbol in symbols:
                        if holdings[symbol] > 0 and symbol in current_prices:
                            current_price = current_prices[symbol]
                            shares_to_sell = holdings[symbol]
                            
                            if shares_to_sell > 0.001:
                                trade_value = shares_to_sell * current_price
                                commission = trade_value * self.commission_rate
                                total_commission += commission
                                
                                # 记录交易
                                trades.append({
                                    'date': date,
                                    'symbol': symbol,
                                    'shares': -shares_to_sell,
                                    'price': current_price,
                                    'value': -trade_value,
                                    'commission': commission,
                                    'type': 'sell'
                                })
                                
                                # 清空持仓
                                holdings[symbol] = 0
                    
                    # 更新现金
                    total_sale_value = sum(holdings[symbol] * current_prices[symbol] 
                                         for symbol in symbols if symbol in current_prices)
                    cash = total_value - total_sale_value - total_commission
            
            # 重新计算持仓价值
            holdings_value = sum(
                holdings[symbol] * current_prices[symbol] 
                for symbol in symbols
            )
            
            # 记录历史数据
            portfolio_value = cash + holdings_value
            portfolio_values.append(portfolio_value)
            cash_history.append(cash)
            holdings_history.append(holdings_value)
        
        # 转换为Series
        portfolio_series = pd.Series(portfolio_values, index=price_data.index)
        cash_series = pd.Series(cash_history, index=price_data.index)
        holdings_series = pd.Series(holdings_history, index=price_data.index)
        
        # 计算收益率
        returns = portfolio_series.pct_change().dropna()
        
        # 构建持仓DataFrame
        positions_df = pd.DataFrame(index=price_data.index)
        positions_df['cash'] = cash_series
        positions_df['holdings'] = holdings_series
        positions_df['total'] = portfolio_series
        
        return {
            'portfolio_value': portfolio_series,
            'returns': returns,
            'positions': positions_df,
            'trades': trades
        }
    
    def run_multiple_strategies(self,
                              symbols: List[str],
                              strategies: List[BaseStrategy],
                              start_date: str,
                              end_date: str,
                              benchmark: str = None) -> Dict[str, Any]:
        """
        运行多个策略对比
        
        Args:
            symbols: 股票代码列表
            strategies: 策略列表
            start_date: 开始日期
            end_date: 结束日期
            benchmark: 基准指数
            
        Returns:
            包含所有策略结果的字典
        """
        results = {}
        
        for strategy in strategies:
            strategy_result = self.run_backtest(
                symbols, strategy, start_date, end_date, benchmark
            )
            results[strategy.name] = strategy_result
        
        return results
    
    def optimize_strategy(self,
                         symbols: List[str],
                         strategy_name: str,
                         param_grid: Dict[str, List],
                         start_date: str,
                         end_date: str,
                         metric: str = 'sharpe_ratio') -> Dict:
        """
        策略参数优化
        
        Args:
            symbols: 股票代码
            strategy_name: 策略名称
            param_grid: 参数网格
            start_date: 开始日期
            end_date: 结束日期
            metric: 优化指标
            
        Returns:
            最优参数和结果
        """
        from itertools import product
        from performance import PerformanceAnalyzer
        
        # 生成参数组合
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        param_combinations = list(product(*param_values))
        
        best_score = float('-inf')
        best_params = None
        best_result = None
        
        print(f"开始参数优化，共{len(param_combinations)}种组合...")
        
        for i, param_combo in enumerate(param_combinations):
            # 构建参数字典
            params = dict(zip(param_names, param_combo))
            
            try:
                # 创建策略
                strategy = StrategyFactory.create_strategy(strategy_name, params)
                
                # 运行回测
                result = self.run_backtest(symbols, strategy, start_date, end_date)
                
                # 计算性能指标
                analyzer = PerformanceAnalyzer()
                metrics = analyzer.calculate_performance_metrics(result['returns'])
                
                # 获取目标指标
                score = metrics.get(metric, float('-inf'))
                
                # 更新最优结果
                if score > best_score:
                    best_score = score
                    best_params = params
                    best_result = result
                
                print(f"进度: {i+1}/{len(param_combinations)}, 当前{metric}: {score:.4f}")
                
            except Exception as e:
                print(f"参数组合 {params} 失败: {str(e)}")
                continue
        
        return {
            'best_params': best_params,
            'best_score': best_score,
            'best_result': best_result
        }
