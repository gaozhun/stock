# -*- coding: utf-8 -*-
"""
投资策略模块
包含各种投资策略的实现
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from abc import ABC, abstractmethod
from config import STRATEGY_PARAMS


class BaseStrategy(ABC):
    """策略基类"""
    
    def __init__(self, name: str, params: Dict = None):
        """
        初始化策略
        
        Args:
            name: 策略名称
            params: 策略参数
        """
        self.name = name
        self.params = params or {}
        self.positions = pd.Series()
        self.signals = pd.Series()
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信号
        
        Args:
            data: 价格数据
            
        Returns:
            交易信号序列 (1: 买入, -1: 卖出, 0: 持有)
        """
        pass
    
    def calculate_positions(self, signals: pd.Series) -> pd.Series:
        """
        根据信号计算持仓
        
        Args:
            signals: 交易信号
            
        Returns:
            持仓序列 (0-1之间的值)
        """
        positions = pd.Series(index=signals.index, data=0.0)
        current_position = 0.0
        
        for date in signals.index:
            signal = signals[date]
            if signal == 1:  # 买入信号
                current_position = 1.0
            elif signal == -1:  # 卖出信号
                current_position = 0.0
            # 信号为0时保持当前持仓
            
            positions[date] = current_position
        
        return positions
    
    def get_strategy_info(self) -> Dict:
        """获取策略信息"""
        return {
            'name': self.name,
            'params': self.params,
            'type': self.__class__.__name__
        }


class BuyAndHoldStrategy(BaseStrategy):
    """买入持有策略"""
    
    def __init__(self, params: Dict = None):
        super().__init__("买入持有", params)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成买入持有信号"""
        signals = pd.Series(index=data.index, data=0)
        if len(signals) > 0:
            signals.iloc[0] = 1  # 第一天买入
        return signals


class MovingAverageStrategy(BaseStrategy):
    """移动平均策略"""
    
    def __init__(self, params: Dict = None):
        default_params = {
            'short_window': STRATEGY_PARAMS.get('ma_short', 20),
            'long_window': STRATEGY_PARAMS.get('ma_long', 60)
        }
        if params:
            default_params.update(params)
        
        super().__init__("移动平均策略", default_params)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成移动平均交叉信号"""
        short_ma = data['Close'].rolling(window=self.params['short_window']).mean()
        long_ma = data['Close'].rolling(window=self.params['long_window']).mean()
        
        signals = pd.Series(index=data.index, data=0)
        
        # 金叉买入，死叉卖出
        signals[short_ma > long_ma] = 1
        signals[short_ma <= long_ma] = -1
        
        # 去除前面的NaN值
        signals = signals.fillna(0)
        
        return signals


class MovingAverageBreakoutStrategy(BaseStrategy):
    """移动平均线突破策略 - 价格突破均线"""
    
    def __init__(self, params: Dict = None):
        default_params = {
            'ma_period': 20,  # 移动平均线周期，默认20日
            'threshold': 0.0  # 突破阈值，默认0%
        }
        if params:
            default_params.update(params)
            
        super().__init__("移动平均线突破策略", default_params)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成移动平均线突破信号"""
        # 计算移动平均线
        ma = data['Close'].rolling(window=self.params['ma_period']).mean()
        
        # 计算突破阈值
        threshold = self.params['threshold']
        upper_threshold = ma * (1 + threshold)
        lower_threshold = ma * (1 - threshold)
        
        signals = pd.Series(index=data.index, data=0)
        
        # 价格突破均线上方 -> 买入信号
        signals[data['Close'] > upper_threshold] = 1
        
        # 价格跌破均线下方 -> 卖出信号  
        signals[data['Close'] < lower_threshold] = -1
        
        # 去除前面的NaN值
        signals = signals.fillna(0)
        
        return signals


class RSIStrategy(BaseStrategy):
    """RSI策略"""
    
    def __init__(self, params: Dict = None):
        default_params = {
            'rsi_period': STRATEGY_PARAMS.get('rsi_period', 14),
            'oversold': STRATEGY_PARAMS.get('rsi_oversold', 30),
            'overbought': STRATEGY_PARAMS.get('rsi_overbought', 70)
        }
        if params:
            default_params.update(params)
        
        super().__init__("RSI策略", default_params)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成RSI信号"""
        rsi = self._calculate_rsi(data['Close'], self.params['rsi_period'])
        
        signals = pd.Series(index=data.index, data=0)
        
        # RSI超卖买入，超买卖出
        signals[rsi < self.params['oversold']] = 1
        signals[rsi > self.params['overbought']] = -1
        
        return signals.fillna(0)
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi


class MACDStrategy(BaseStrategy):
    """MACD策略"""
    
    def __init__(self, params: Dict = None):
        default_params = {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9
        }
        if params:
            default_params.update(params)
        
        super().__init__("MACD策略", default_params)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成MACD信号"""
        macd, macd_signal = self._calculate_macd(
            data['Close'], 
            self.params['fast_period'],
            self.params['slow_period'],
            self.params['signal_period']
        )
        
        signals = pd.Series(index=data.index, data=0)
        
        # MACD金叉买入，死叉卖出
        signals[macd > macd_signal] = 1
        signals[macd <= macd_signal] = -1
        
        return signals.fillna(0)
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, 
                       slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series]:
        """计算MACD"""
        exp1 = prices.ewm(span=fast).mean()
        exp2 = prices.ewm(span=slow).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal).mean()
        return macd, signal_line


class DollarCostAveragingStrategy(BaseStrategy):
    """定投策略"""
    
    def __init__(self, params: Dict = None):
        default_params = {
            'frequency': 'monthly',      # daily, weekly, monthly
            'trading_day': 1,            # 第几个交易日 (1=第一个, 2=第二个...)
            'investment_amount': 10000,  # 每次定投金额
            'max_position': 1.0,         # 最大持仓比例 (1.0=100%)
            'position_increment': 0.1    # 每次定投增加的持仓比例
        }
        if params:
            default_params.update(params)
        
        super().__init__("定投策略", default_params)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成定投信号"""
        signals = pd.Series(index=data.index, data=0)
        
        if self.params['frequency'] == 'monthly':
            # 每月第N个交易日买入
            monthly_groups = data.groupby(data.index.to_period('M'))
            for month, month_data in monthly_groups:
                if len(month_data) > 0:
                    # 选择该月第N个交易日
                    trading_day = self.params['trading_day'] - 1  # 转换为索引
                    if trading_day < len(month_data):
                        target_date = month_data.index[trading_day]
                        signals[target_date] = 1
        
        elif self.params['frequency'] == 'weekly':
            # 每周第N个交易日买入
            weekly_groups = data.groupby(data.index.to_period('W'))
            for week, week_data in weekly_groups:
                if len(week_data) > 0:
                    # 选择该周第N个交易日
                    trading_day = self.params['trading_day'] - 1  # 转换为索引
                    if trading_day < len(week_data):
                        target_date = week_data.index[trading_day]
                        signals[target_date] = 1
        
        elif self.params['frequency'] == 'daily':
            # 每日买入
            signals[:] = 1
        
        return signals
    
    def calculate_positions(self, signals: pd.Series) -> pd.Series:
        """定投策略的持仓计算（累积持仓）"""
        positions = pd.Series(index=signals.index, data=0.0)
        cumulative_position = 0.0
        
        for date in signals.index:
            if signals[date] == 1:
                # 每次定投增加固定比例，但不超过最大持仓
                cumulative_position = min(
                    cumulative_position + self.params['position_increment'], 
                    self.params['max_position']
                )
            
            positions[date] = cumulative_position
        
        return positions
    
    def get_trading_signals(self, signals: pd.Series) -> pd.Series:
        """获取定投策略的交易信号（只在有信号时交易）"""
        # 对于定投策略，我们只在有买入信号时才交易
        # 这样可以避免回测引擎每天都调整持仓
        return signals
    
    def get_trading_info(self) -> Dict:
        """获取定投策略的交易信息"""
        return {
            'frequency': self.params['frequency'],
            'trading_day': self.params.get('trading_day', 1),
            'investment_amount': self.params.get('investment_amount', 10000),
            'position_increment': self.params.get('position_increment', 0.1),
            'max_position': self.params.get('max_position', 1.0)
        }


class MeanReversionStrategy(BaseStrategy):
    """均值回归策略"""
    
    def __init__(self, params: Dict = None):
        default_params = {
            'lookback_period': 20,
            'entry_threshold': 2.0,  # 标准差倍数
            'exit_threshold': 0.5
        }
        if params:
            default_params.update(params)
        
        super().__init__("均值回归策略", default_params)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成均值回归信号"""
        prices = data['Close']
        
        # 计算移动平均和标准差
        ma = prices.rolling(window=self.params['lookback_period']).mean()
        std = prices.rolling(window=self.params['lookback_period']).std()
        
        # 计算z-score
        z_score = (prices - ma) / std
        
        signals = pd.Series(index=data.index, data=0)
        
        # 价格过低时买入，过高时卖出
        signals[z_score < -self.params['entry_threshold']] = 1
        signals[z_score > self.params['entry_threshold']] = -1
        signals[abs(z_score) < self.params['exit_threshold']] = 0
        
        return signals.fillna(0)


class StrategyFactory:
    """策略工厂类"""
    
    @staticmethod
    def create_strategy(strategy_name: str, params: Dict = None) -> BaseStrategy:
        """
        创建策略实例
        
        Args:
            strategy_name: 策略名称
            params: 策略参数
            
        Returns:
            策略实例
        """
        strategies = {
            'buy_hold': BuyAndHoldStrategy,
            'moving_average': MovingAverageStrategy,
            'ma_breakout': MovingAverageBreakoutStrategy,
            'rsi': RSIStrategy,
            'macd': MACDStrategy,
            'dca': DollarCostAveragingStrategy,
            'mean_reversion': MeanReversionStrategy
        }
        
        if strategy_name not in strategies:
            raise ValueError(f"未知策略: {strategy_name}")
        
        return strategies[strategy_name](params)
    
    @staticmethod
    def get_available_strategies() -> List[str]:
        """获取可用策略列表"""
        return [
            'buy_hold', 'moving_average', 'rsi', 
            'macd', 'dca', 'mean_reversion'
        ]
    
    @staticmethod
    def get_strategy_descriptions() -> Dict[str, str]:
        """获取策略描述"""
        return {
            'buy_hold': '买入并持有策略',
            'moving_average': '移动平均线策略',
            'rsi': 'RSI相对强弱指标策略',
            'macd': 'MACD指标策略',
            'dca': '定投策略',
            'mean_reversion': '均值回归策略'
        }
