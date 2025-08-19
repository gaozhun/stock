# -*- coding: utf-8 -*-
"""
回测引擎模块 - 重构版本
支持每只股票独立的策略配置和结果展示
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from data_handler import DataHandler
from stock_strategy import Strategy, SignalType
from stock_strategy import Portfolio, Stock


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_capital: float = None):
        """
        初始化回测引擎
        
        Args:
            initial_capital: 初始资金
        """
        
        # 回测结果
        self.portfolio_value = pd.Series()
        self.positions = pd.DataFrame()
        self.trades = []
        self.cash_history = pd.Series()
        self.holdings_history = pd.Series()
        
        # 数据处理器
        self.data_handler = DataHandler()
    
    def run_portfolio_backtest(self,
                         portfolio: Portfolio,
                         symbols: List[str],
                         start_date: str,
                         end_date: str,
                         benchmark: str = None,
                         custom_data: Dict[str, pd.DataFrame] = None) -> Dict[str, Any]:
        """
        运行投资组合回测
        
        Args:
            portfolio: 投资组合
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            benchmark: 基准指数
            custom_data: 自定义价格数据，用于测试
            
        Returns:
            回测结果字典
        """
        print(f"开始回测投资组合策略")
        print(f"股票池: {symbols}")
        print(f"回测期间: {start_date} 至 {end_date}")
        
        # 调试日志：打印投资组合信息
        print("### 调试信息 - 投资组合详情")
        print(f"投资组合中的股票数量: {len(portfolio.stocks)}")
        for symbol, stock in portfolio.stocks.items():
            print(f"股票 {symbol}:")
            print(f"  初始投资: {stock.initial_investment}")
            print(f"  最大投资: {stock.max_investment}")
            print(f"  买入策略数量: {len(stock.buy_strategies)}")
            for i, strategy in enumerate(stock.buy_strategies):
                print(f"    买入策略 {i+1}: {strategy.name}, 类型: {strategy.type}")
                print(f"    参数: {strategy.params}")
            print(f"  卖出策略数量: {len(stock.sell_strategies)}")
            for i, strategy in enumerate(stock.sell_strategies):
                print(f"    卖出策略 {i+1}: {strategy.name}, 类型: {strategy.type}")
                print(f"    参数: {strategy.params}")
        
        # 获取所有股票的价格数据
        price_data = {}
        for symbol in symbols:
            # 如果提供了自定义数据，则使用自定义数据
            if custom_data and symbol in custom_data:
                data = custom_data[symbol]
                print(f"使用自定义数据: {symbol}")
            else:
                # 否则从数据源获取数据
                data = self.data_handler.get_stock_data(symbol, start_date, end_date)
            
            price_data[symbol] = data
            
            # 打印实际数据范围
            if not data.empty:
                actual_start = data.index.min().strftime('%Y-%m-%d')
                actual_end = data.index.max().strftime('%Y-%m-%d')
                print(f"股票 {symbol} 实际数据区间: {actual_start} 至 {actual_end}")
        
        # 获取基准数据
        benchmark_data = None
        if benchmark:
            try:
                benchmark_data = self.data_handler.get_benchmark_data(start_date, end_date, benchmark)
                print(f"📊 使用基准指数: {benchmark}")
            except Exception as e:
                print(f"⚠️  无法获取基准数据 {benchmark}: {str(e)}")
        
        # 初始化结果容器
        stock_results = {}
        portfolio_trades = []
        portfolio_values = pd.Series(index=price_data[symbols[0]].index, data=0.0)
        portfolio_positions = pd.DataFrame(index=price_data[symbols[0]].index)
        
        # 为每只股票运行回测
        for symbol in symbols:
            # 运行单只股票回测
            stock_result = self._run_single_stock_backtest(
                symbol=symbol,
                price_data=price_data[symbol],
                stock=portfolio.stocks[symbol]
            )
            
            # 保存结果
            stock_results[symbol] = stock_result
            portfolio_trades.extend(stock_result['trades'])
            portfolio_values += stock_result['portfolio_value']
            portfolio_positions[symbol] = stock_result['positions']['holdings']
        
        # 计算投资组合收益率
        portfolio_returns = portfolio_values.pct_change().dropna()
        
        # 计算基准收益率
        benchmark_returns = None
        if benchmark_data is not None:
            benchmark_returns = benchmark_data['Close'].pct_change().dropna()
        
        # 生成回测报告
        # 使用最大投资资金作为初始资金
        max_investment = sum(stock.max_investment for stock in portfolio.stocks.values())
        initial_capital = max_investment
        
        final_value = portfolio_values.iloc[-1]
        
        # 计算总收益率，避免除以零
        if initial_capital > 0:
            total_return = (final_value / initial_capital) - 1
        else:
            total_return = 0
        
        # 计算年化收益率
        days = len(portfolio_values)
        years = days / 252.0
        annualized_return = 0
        if years > 0 and total_return > -1:  # 避免负收益率的年化计算问题
            annualized_return = (1 + total_return) ** (1 / years) - 1
        
        # 计算风险指标
        volatility = portfolio_returns.std() * np.sqrt(252)  # 年化波动率
        
        # 计算最大回撤
        cumulative_returns = (1 + portfolio_returns).cumprod()
        peak = cumulative_returns.expanding(min_periods=1).max()
        drawdown = (cumulative_returns/peak - 1)
        max_drawdown = drawdown.min()
        
        # 计算夏普比率
        risk_free_rate = 0.02  # 无风险利率假设为2%
        sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0
        
        # 计算最大回撤修复时间
        max_drawdown_recovery_days = 0
        if max_drawdown < 0:
            # 找到最大回撤的时间点
            max_dd_idx = drawdown.idxmin()
            # 找到最后一次达到峰值的时间点
            last_peak_idx = peak.loc[:max_dd_idx].idxmax()
            
            # 找到从最大回撤点恢复到上一个峰值的时间点
            recovery_series = cumulative_returns.loc[max_dd_idx:]
            recovery_idx = None
            
            # 检查是否已经恢复
            if recovery_series.max() >= peak.loc[last_peak_idx]:
                # 已经恢复到峰值
                for i, value in enumerate(recovery_series):
                    if value >= peak.loc[last_peak_idx]:
                        recovery_idx = recovery_series.index[i]
                        break
                
                if recovery_idx is not None and recovery_idx != max_dd_idx:
                    # 计算从最大回撤到恢复的天数
                    max_drawdown_recovery_days = len(recovery_series.loc[max_dd_idx:recovery_idx])
            else:
                # 到回测结束仍未恢复到峰值，标记为未恢复
                max_drawdown_recovery_days = -1  # 使用-1表示未恢复
        
        results = {
            'portfolio_value': portfolio_values, # 投资组合价值
            'returns': portfolio_returns, # 投资组合收益率
            'positions': portfolio_positions, # 持仓情况
            'trades': portfolio_trades, # 交易记录
            'benchmark_returns': benchmark_returns, # 基准收益率
            'benchmark': benchmark, # 基准指数
            'stock_results': stock_results, # 股票回测结果
            'initial_capital': initial_capital, # 初始资金
            'final_value': final_value, # 最终资产价值
            'total_return': total_return, # 总收益率
            'annualized_return': annualized_return, # 年化收益率
            'volatility': volatility, # 年化波动率
            'max_drawdown': max_drawdown, # 最大回撤
            'sharpe_ratio': sharpe_ratio, # 夏普比率
            'max_drawdown_recovery_days': max_drawdown_recovery_days # 最大回撤修复天数
        }
        
        print(f"回测完成! 最终资产价值: ¥{portfolio_values.iloc[-1]:,.2f}")
        return results
    
    def _run_single_stock_backtest(self,
                             symbol: str,
                             price_data: pd.DataFrame,
                             stock: Stock) -> Dict[str, Any]:
        """
        运行单只股票回测
        
        Args:
            symbol: 股票代码
            price_data: 价格数据
            stock: 股票实例
            
        Returns:
            回测结果字典
        """
        # 生成交易信号 - 新的信号包含了交易量信息
        signals = stock.get_signals(price_data)
        # 获取交易金额 - 现在直接使用信号中的交易量信息
        trade_amounts = stock.get_trade_amounts(price_data, signals)
        
        # 初始化变量
        cash = stock.max_investment  # 使用最大投资资金作为初始现金
        portfolio_values = [] # 记录每日总资产价值
        cash_history = [] # 记录每日现金
        holdings_history = [] # 记录每日持仓价值
        holdings_shares_history = []  # 记录每日持仓份额
        trades = []  # 初始化交易记录
        
        # 初始持仓份额（如果有初始投资，则转换为份额）
        holdings_shares = 0
        initial_investment = stock.initial_investment
        print(f"初始投资: {initial_investment}")
        if initial_investment > 0:
            # 计算初始持仓份额
            initial_price = price_data.iloc[0]['Close']
            
            # 计算最大可购买的整数股数，考虑手续费
            # 公式：shares * price * (1 + fee_rate) <= initial_investment
            # 即：shares <= initial_investment / (price * (1 + fee_rate))
            holdings_shares = int(initial_investment / (initial_price * (1 + stock.fee_rate)))
            
            # 实际购买金额
            actual_investment = holdings_shares * initial_price
            # 计算手续费
            commission = actual_investment * stock.fee_rate
            
            # 记录初始购买交易
            trade_date = price_data.index[0]
            trades.append({
                'date': trade_date,
                'symbol': symbol,
                'shares': holdings_shares,  # 整数股数
                'price': initial_price,
                'value': actual_investment,
                'commission': commission,  # 标准手续费
                'type': 'buy'
            })
            
            # 从现金中扣除实际投资和手续费
            total_cost = actual_investment + commission
            cash -= total_cost
            
            print(f"初始持仓: {symbol} - {holdings_shares}股, 价格: ¥{initial_price:.2f}, 实际金额: ¥{actual_investment:.2f}, 手续费: ¥{commission:.2f}")
        
        # 逐日回测
        for date in price_data.index:
            current_price = price_data.loc[date, 'Close']
            signal = signals.loc[date]
            trade_amount = trade_amounts.loc[date]
            
            # 计算当前持仓价值
            holdings_value = holdings_shares * current_price
            
            # 执行交易
            if signal != 0 and trade_amount > 0:
                
                # 只有当交易金额大于最小交易金额时才执行交易
                if signal > 0:  # 买入信号 - 现在signal是净交易量
                    # 计算最大可购买的整数股数，考虑手续费
                    # 公式：shares * price * (1 + fee_rate) <= trade_amount
                    # 即：shares <= trade_amount / (price * (1 + fee_rate))
                    # 同时不能超过可用现金
                    max_shares_by_trade_amount = trade_amount / (current_price * (1 + stock.fee_rate))
                    max_shares_by_cash = cash / (current_price * (1 + stock.fee_rate))
                    max_shares = min(max_shares_by_trade_amount, max_shares_by_cash)
                    integer_shares = int(max_shares)  # 取整数部分

                else:  # 卖出信号 - 现在signal是负值，表示净卖出量
                    # 计算可卖出的最大整数股数
                    max_shares = min(holdings_shares, trade_amount / current_price)
                    integer_shares = -int(max_shares)  # 取整数部分，负值表示卖出
                    
                # 检查是否可以执行交易
                if integer_shares != 0:  # 只有当整数股数
                    # 计算交易金额和手续费
                    trade_value = integer_shares * current_price
                    commission = abs(trade_value) * stock.fee_rate
                    
                    # 更新现金和持仓
                    cash -= (trade_value + commission)
                    holdings_shares += integer_shares
                    
                    # 记录交易
                    trades.append({
                        'date': date,
                        'symbol': symbol,
                        'shares': integer_shares,
                        'price': current_price,
                        'value': trade_value,
                        'commission': commission,
                        'type': 'buy' if integer_shares > 0 else 'sell'
                    })    
            # 记录每日数据
            holdings_value = holdings_shares * current_price  # 重新计算当前持仓价值
            portfolio_value = cash + holdings_value  # 计算总资产价值
            
            # 记录历史数据
            portfolio_values.append(portfolio_value)
            cash_history.append(cash)
            holdings_history.append(holdings_value)
            holdings_shares_history.append(holdings_shares)
        
        # 转换为Series和DataFrame
        portfolio_series = pd.Series(portfolio_values, index=price_data.index)
        cash_series = pd.Series(cash_history, index=price_data.index)
        holdings_series = pd.Series(holdings_history, index=price_data.index)
        holdings_shares_series = pd.Series(holdings_shares_history, index=price_data.index)
        
        # Debug: Display holdings_series content
        print("### Debug: holdings_shares_series 内容")
        print(holdings_shares_series)
        
        # 计算收益率
        returns = portfolio_series.pct_change().dropna()
        
        # 构建持仓DataFrame
        positions_df = pd.DataFrame(index=price_data.index)
        positions_df['cash'] = cash_series
        positions_df['holdings'] = holdings_series
        positions_df['shares'] = holdings_shares_series
        positions_df['total'] = portfolio_series
        
        # Debug: Display positions_df content
        print("### Debug1: positions_df 内容")
        print(positions_df)
        
        return {
            'portfolio_value': portfolio_series,
            'returns': returns,
            'positions': positions_df,
            'trades': trades,
            'signals': signals,
            'price_data': price_data
        }