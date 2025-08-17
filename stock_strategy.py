# -*- coding: utf-8 -*-
"""
股票策略模块 - 每只股票独立的策略系统
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum


class SignalType(Enum):
    """信号类型"""
    BUY = 'buy'      # 买入信号
    SELL = 'sell'    # 卖出信号


@dataclass
class Strategy:
    """策略配置"""
    name: str                # 策略名称
    type: str               # 策略类型
    signal_type: SignalType # 信号类型（买入/卖出）
    params: Dict            # 策略参数
    enabled: bool = True    # 是否启用


class Stock:
    """单只股票的策略容器"""
    
    def __init__(self, code: str, initial_investment: float = 0, max_investment: float = 100000, fee_rate: float = 0.0003):
        """
        初始化股票策略容器
        
        Args:
            code: 股票代码
            initial_investment: 初始持仓金额
            max_investment: 最大投资资金
            fee_rate: 交易手续费率，默认为0.0003（万三）
        """
        self.code = code
        self.initial_investment = initial_investment  # 初始持仓金额
        self.max_investment = max_investment  # 最大投资资金
        self.fee_rate = fee_rate  # 交易手续费率
        self.buy_strategies: List[Strategy] = []   # 买入策略列表
        self.sell_strategies: List[Strategy] = []  # 卖出策略列表
    
    def add_strategy(self, strategy: Strategy) -> None:
        """
        添加策略
        
        Args:
            strategy: 策略配置
        """
        print(f"### 调试信息 - 添加策略 {strategy.name} {strategy.type} {strategy.signal_type}")
        print(f"  买入策略数量: {len(self.buy_strategies)}")
        print(f"  卖出策略数量: {len(self.sell_strategies)}")
        if strategy.signal_type == SignalType.BUY:
            self.buy_strategies.append(strategy)
        else:
            self.sell_strategies.append(strategy)
    
    def remove_strategy(self, strategy_name: str) -> None:
        """
        移除策略
        
        Args:
            strategy_name: 策略名称
            signal_type: 信号类型
        """
        for strategy in self.buy_strategies:
            if strategy.name == strategy_name:
                self.buy_strategies.remove(strategy)
                break
        for strategy in self.sell_strategies:
            if strategy.name == strategy_name:
                self.sell_strategies.remove(strategy)
                break

    def get_enabled_buy_strategie_number(self) -> int:
        """
        获取启用的买入策略数量
        """
        return len([strategy for strategy in self.buy_strategies if strategy.enabled])
    
    def get_enabled_sell_strategie_number(self) -> int:
        """
        获取启用的卖出策略数量
        """
        return len([strategy for strategy in self.sell_strategies if strategy.enabled])
    
    def update_initial_investment(self, initial_investment: float) -> None:
        """
        更新初始持仓金额
        
        Args:
            initial_investment: 新的初始持仓金额
        """
        self.initial_investment = initial_investment

    def update_max_investment(self, max_investment: float) -> None:
        """
        更新最大投资资金
        
        Args:
            max_investment: 新的最大投资资金
        """
        self.max_investment = max_investment
    
    def get_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信号
        
        Args:
            data: 价格数据
            
        Returns:
            交易信号序列 (正值: 买入量, 负值: 卖出量, 0: 持有)
        """
        signals = pd.Series(index=data.index, data=0.0)  # 使用浮点数表示信号强度
        
        # 调试日志：打印策略信息
        print(f"### 调试信息 - 生成信号 for {self.code}")
        print(f"  买入策略数量: {len(self.buy_strategies)}")
        print(f"  卖出策略数量: {len(self.sell_strategies)}")
        
        # 存储每个策略生成的信号和交易量
        all_strategy_signals = []
        
        # 生成买入信号
        for strategy in self.buy_strategies:
            if strategy.enabled:
                print(f"  执行买入策略: {strategy.name}, 类型: {strategy.type}")
                strategy_signals = self._generate_strategy_signals(data, strategy)
                strategy_amounts = self._calculate_strategy_amounts(data, strategy_signals, strategy, self.fee_rate)
                
                # 记录策略信号和交易量
                all_strategy_signals.append({
                    'name': strategy.name,
                    'type': strategy.type,
                    'signal_type': SignalType.BUY,
                    'signals': strategy_signals,
                    'amounts': strategy_amounts
                })
                
                print(f"  策略 {strategy.name} 生成的买入信号数量: {sum(strategy_signals == 1)}")
        
        # 生成卖出信号
        for strategy in self.sell_strategies:
            if strategy.enabled:
                print(f"  执行卖出策略: {strategy.name}, 类型: {strategy.type}")
                strategy_signals = self._generate_strategy_signals(data, strategy)
                strategy_amounts = self._calculate_strategy_amounts(data, strategy_signals, strategy, self.fee_rate)
                
                # 记录策略信号和交易量
                all_strategy_signals.append({
                    'name': strategy.name,
                    'type': strategy.type,
                    'signal_type': SignalType.SELL,
                    'signals': strategy_signals,
                    'amounts': strategy_amounts
                })
                
                print(f"  策略 {strategy.name} 生成的卖出信号数量: {sum(strategy_signals == -1)}")
        
        # 合并信号 - 对于每一天，计算净交易量
        for date in data.index:
            buy_amount = 0.0
            sell_amount = 0.0
            
            # 累计所有买入策略的交易量
            for strategy_info in all_strategy_signals:
                if strategy_info['signal_type'] == SignalType.BUY:
                    if date in strategy_info['amounts'].index and strategy_info['amounts'][date] > 0:
                        buy_amount += strategy_info['amounts'][date]
            
            # 累计所有卖出策略的交易量
            for strategy_info in all_strategy_signals:
                if strategy_info['signal_type'] == SignalType.SELL:
                    if date in strategy_info['amounts'].index and strategy_info['amounts'][date] > 0:
                        sell_amount += strategy_info['amounts'][date]
            
            # 计算净交易量
            if buy_amount > 0 and sell_amount > 0:
                # 同一天既有买入又有卖出信号，计算净交易量
                net_amount = buy_amount - sell_amount
                if net_amount > 0:
                    signals[date] = net_amount  # 净买入
                elif net_amount < 0:
                    signals[date] = net_amount  # 净卖出
                # 如果净交易量为0，保持为0
            elif buy_amount > 0:
                signals[date] = buy_amount  # 只有买入
            elif sell_amount > 0:
                signals[date] = -sell_amount  # 只有卖出
        
        # 打印总信号数量
        print(f"  总买入信号数量: {sum(signals > 0)}")
        print(f"  总卖出信号数量: {sum(signals < 0)}")
        print(f"  净买入金额总和: {sum(signals[signals > 0])}")
        print(f"  净卖出金额总和: {sum(-signals[signals < 0])}")
        
        return signals
    
    def get_trade_amounts(self, data: pd.DataFrame, signals: pd.Series) -> pd.Series:
        """
        计算交易金额/数量，包含手续费
        
        Args:
            data: 价格数据
            signals: 交易信号 (已经通过get_signals生成，包含净交易量信息)
            
        Returns:
            交易金额/数量序列（包含手续费）
        """
        # 在新的实现中，signals已经包含了交易量信息，因此直接返回其绝对值
        # 正值表示买入金额，负值表示卖出金额
        trade_amounts = signals.abs()
        
        # 调试日志
        print(f"  交易金额总和: {sum(trade_amounts)}")
        print(f"  买入交易金额总和: {sum(trade_amounts[signals > 0])}")
        print(f"  卖出交易金额总和: {sum(trade_amounts[signals < 0])}")
        
        return trade_amounts
    
    def _generate_strategy_signals(self, data: pd.DataFrame, strategy: Strategy) -> pd.Series:
        """生成单个策略的信号"""
        # 调试日志
        print(f"    开始生成策略信号: {strategy.name}, 类型: {strategy.type}")
        print(f"    策略参数: {strategy.params}")
        
        signals = pd.Series(index=data.index, data=0)
        
        if strategy.type == 'time_based':
            signals = self._generate_time_based_signals(data, strategy)
        elif strategy.type == 'macd_pattern':
            signals = self._generate_macd_signals(data, strategy)
        elif strategy.type == 'ma_touch':
            signals = self._generate_ma_touch_signals(data, strategy)
        else:
            raise ValueError(f"未知的策略类型: {strategy.type}")
        
        # 打印生成的信号数量
        print(f"    策略 {strategy.name} 生成的买入信号数量: {sum(signals == 1)}")
        print(f"    策略 {strategy.name} 生成的卖出信号数量: {sum(signals == -1)}")
        
        return signals
    
    def _calculate_strategy_amounts(self, data: pd.DataFrame, signals: pd.Series, 
                                  strategy: Strategy, fee_rate: float = 0.0003) -> pd.Series:
        """
        计算单个策略的交易金额/数量，包含手续费
        
        Args:
            data: 价格数据
            signals: 交易信号
            strategy: 策略配置
            fee_rate: 交易手续费率，默认为0.0003（万三）
            
        Returns:
            交易金额/数量序列（包含手续费）
        """
        trade_amounts = pd.Series(index=signals.index, data=0.0)
        
        # 有交易信号的日期
        if strategy.signal_type == SignalType.BUY:
            trade_dates = signals[signals == 1].index
        else:  # 卖出信号
            trade_dates = signals[signals == -1].index
        
        for date in trade_dates:
            # 基础交易金额
            base_amount = 0.0
            
            if strategy.params.get('trade_shares') is not None:
                # 使用固定股数
                shares = strategy.params['trade_shares']
                # 获取当日收盘价
                price = data.loc[date, 'Close']
                # 计算基础交易金额 = 股数 * 价格
                base_amount = shares * price * (1 + fee_rate)
            else:
                # 使用固定金额
                base_amount = strategy.params['trade_amount']
                max_shares = int(base_amount / (data.loc[date, 'Close'] * (1 + fee_rate)))
                base_amount = max_shares * data.loc[date, 'Close'] * (1 + fee_rate)

            trade_amounts[date] = base_amount
            
        return trade_amounts
    
    def _generate_time_based_signals(self, data: pd.DataFrame, strategy: Strategy) -> pd.Series:
        """生成时间条件单的信号"""
        signals = pd.Series(index=data.index, data=0)
        frequency = strategy.params.get('frequency', 'daily')
        trading_day = strategy.params.get('trading_day', 1)
        
        # 根据信号类型设置信号值
        signal_value = 1 if strategy.signal_type == SignalType.BUY else -1

        if frequency == 'daily':
            signals[:] = signal_value  # 每日信号
        elif frequency == 'weekly':
            # 每周信号，选择特定的交易日
            signals[data.index.weekday == trading_day] = signal_value
        elif frequency == 'monthly':
            # 每月信号，选择特定的交易日
            signals[data.index.day == trading_day] = signal_value

        return signals

    def _generate_macd_signals(self, data: pd.DataFrame, strategy: Strategy) -> pd.Series:
        """生成MACD策略的信号"""
        signals = pd.Series(index=data.index, data=0)
        
        # 计算MACD指标
        fast_period = strategy.params.get('fast_period', 12)
        slow_period = strategy.params.get('slow_period', 26)
        signal_period = strategy.params.get('signal_period', 9)
        
        macd, macd_signal, macd_hist = self._calculate_macd(
            data['Close'],
            fast_period,
            slow_period,
            signal_period
        )
        
        # 检测买入和卖出信号
        for i in range(1, len(data)):
            current_date = data.index[i]
            
            # 检测买入形态
            if 'golden_cross' in strategy.params.get('buy_patterns', []):
                if macd.iloc[i] > macd_signal.iloc[i] and macd.iloc[i-1] <= macd_signal.iloc[i-1]:
                    signals[current_date] = 1
            
            # 检测卖出形态
            if 'death_cross' in strategy.params.get('sell_patterns', []):
                if macd.iloc[i] < macd_signal.iloc[i] and macd.iloc[i-1] >= macd_signal.iloc[i-1]:
                    signals[current_date] = -1
        
        return signals

    # Helper method to calculate MACD
    @staticmethod
    def _calculate_macd(prices: pd.Series, fast: int, slow: int, signal: int) -> Tuple[pd.Series, pd.Series, pd.Series]:
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram


class Portfolio:
    """投资组合"""
    
    def __init__(self):
        """初始化投资组合"""
        self.stocks: Dict[str, Stock] = {}
    
    def add_stock(self, code: str, initial_investment: float = 0, max_investment: float = 100000, fee_rate: float = 0.0003) -> None:
        """
        添加股票
        
        Args:
            code: 股票代码
            initial_investment: 初始持仓金额
            max_investment: 最大投资资金
            fee_rate: 交易手续费率，默认为0.0003（万三）
        """
        if code not in self.stocks:
            self.stocks[code] = Stock(code, initial_investment, max_investment, fee_rate)
    
    def remove_stock(self, code: str) -> None:
        """移除股票"""
        if code in self.stocks:
            del self.stocks[code]
    
    def update_stock_investment(self, code: str, initial_investment: float) -> None:
        """
        更新股票的初始持仓金额
        
        Args:
            code: 股票代码
            initial_investment: 新的初始持仓金额
        """
        if code in self.stocks:
            self.stocks[code].update_initial_investment(initial_investment)

    def update_stock_max_investment(self, code: str, max_investment: float) -> None:
        """
        更新股票的最大投资资金
        
        Args:
            code: 股票代码
            max_investment: 新的最大投资资金
        """
        if code in self.stocks:
            self.stocks[code].update_max_investment(max_investment)
            
    def update_stock_fee_rate(self, code: str, fee_rate: float) -> None:
        """
        更新股票的交易手续费率
        
        Args:
            code: 股票代码
            fee_rate: 新的交易手续费率
        """
        if code in self.stocks:
            self.stocks[code].fee_rate = fee_rate
    
    def add_strategy(self, code: str, strategy: Strategy) -> None:
        """为指定股票添加策略"""
        if code not in self.stocks:
            self.add_stock(code)
        self.stocks[code].add_strategy(strategy)
    
    def remove_strategy(self, code: str, strategy_name: str) -> None:
        """移除指定股票的策略"""
        if code in self.stocks:
            self.stocks[code].remove_strategy(strategy_name)
    
    def get_stock_signals(self, code: str, data: pd.DataFrame) -> pd.Series:
        """获取指定股票的信号"""
        if code in self.stocks:
            return self.stocks[code].get_signals(data)
        return pd.Series(index=data.index, data=0)
    
    def get_stock_trade_amounts(self, code: str, data: pd.DataFrame, signals: pd.Series) -> pd.Series:
        """
        获取指定股票的交易金额/数量
        
        Args:
            code: 股票代码
            data: 价格数据
            signals: 交易信号
            
        Returns:
            交易金额/数量序列（包含手续费）
        """
        if code in self.stocks:
            return self.stocks[code].get_trade_amounts(data, signals)
        return pd.Series(index=signals.index, data=0.0)
    
    def get_total_initial_capital(self) -> float:
        """获取总初始资金"""
        return sum(stock.initial_investment for stock in self.stocks.values())