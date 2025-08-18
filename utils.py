# -*- coding: utf-8 -*-
"""
工具函数模块
包含应用程序中使用的通用辅助函数
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def format_currency(value: float, currency: str = "¥") -> str:
    """
    格式化货币显示
    
    Args:
        value: 数值
        currency: 货币符号
        
    Returns:
        格式化后的货币字符串
    """
    try:
        if value >= 1e8:
            return f"{currency}{value/1e8:.2f}亿"
        elif value >= 1e4:
            return f"{currency}{value/1e4:.2f}万"
        else:
            return f"{currency}{value:,.2f}"
    except (ValueError, TypeError):
        return f"{currency}0.00"

def format_percentage(value: float) -> str:
    """
    格式化百分比显示
    
    Args:
        value: 小数值
        
    Returns:
        格式化后的百分比字符串
    """
    try:
        return f"{value:.2%}"
    except (ValueError, TypeError):
        return "0.00%"

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    安全的除法运算，避免除零错误
    
    Args:
        numerator: 分子
        denominator: 分母
        default: 除零时的默认值
        
    Returns:
        除法结果
    """
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (ValueError, TypeError):
        return default

def calculate_returns(prices: pd.Series) -> pd.Series:
    """
    计算收益率序列
    
    Args:
        prices: 价格序列
        
    Returns:
        收益率序列
    """
    try:
        if len(prices) < 2:
            return pd.Series(dtype=float)
        return prices.pct_change().dropna()
    except Exception as e:
        logger.error(f"计算收益率时出错: {e}")
        return pd.Series(dtype=float)

def calculate_cumulative_returns(returns: pd.Series) -> pd.Series:
    """
    计算累积收益率
    
    Args:
        returns: 收益率序列
        
    Returns:
        累积收益率序列
    """
    try:
        return (1 + returns).cumprod()
    except Exception as e:
        logger.error(f"计算累积收益率时出错: {e}")
        return pd.Series(dtype=float)

def calculate_drawdown(cumulative_returns: pd.Series) -> pd.Series:
    """
    计算回撤序列
    
    Args:
        cumulative_returns: 累积收益率序列
        
    Returns:
        回撤序列
    """
    try:
        peak = cumulative_returns.expanding(min_periods=1).max()
        return (cumulative_returns / peak - 1)
    except Exception as e:
        logger.error(f"计算回撤时出错: {e}")
        return pd.Series(dtype=float)

def calculate_max_drawdown(cumulative_returns: pd.Series) -> Dict[str, Any]:
    """
    计算最大回撤及其相关信息
    
    Args:
        cumulative_returns: 累积收益率序列
        
    Returns:
        包含最大回撤信息的字典
    """
    try:
        drawdown = calculate_drawdown(cumulative_returns)
        max_dd = drawdown.min()
        max_dd_idx = drawdown.idxmin()
        
        # 找到峰值点
        peak = cumulative_returns.expanding(min_periods=1).max()
        last_peak_idx = peak.loc[:max_dd_idx].idxmax()
        
        # 计算恢复天数
        recovery_days = 0
        recovery_idx = None
        
        if max_dd_idx and max_dd_idx < cumulative_returns.index[-1]:
            recovery_series = cumulative_returns.loc[max_dd_idx:]
            for i, value in enumerate(recovery_series):
                if value >= peak.loc[last_peak_idx]:
                    recovery_days = i
                    recovery_idx = recovery_series.index[i]
                    break
        
        return {
            'max_drawdown': max_dd,
            'max_drawdown_date': max_dd_idx,
            'peak_date': last_peak_idx,
            'recovery_date': recovery_idx,
            'recovery_days': recovery_days
        }
    except Exception as e:
        logger.error(f"计算最大回撤时出错: {e}")
        return {
            'max_drawdown': 0.0,
            'max_drawdown_date': None,
            'peak_date': None,
            'recovery_date': None,
            'recovery_days': 0
        }

def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.03) -> float:
    """
    计算夏普比率
    
    Args:
        returns: 收益率序列
        risk_free_rate: 无风险利率，默认3%
        
    Returns:
        夏普比率
    """
    try:
        if len(returns) < 2:
            return 0.0
        
        excess_returns = returns - risk_free_rate / 252  # 转换为日收益率
        if excess_returns.std() == 0:
            return 0.0
        
        return np.sqrt(252) * excess_returns.mean() / excess_returns.std()
    except Exception as e:
        logger.error(f"计算夏普比率时出错: {e}")
        return 0.0

def calculate_volatility(returns: pd.Series) -> float:
    """
    计算年化波动率
    
    Args:
        returns: 收益率序列
        
    Returns:
        年化波动率
    """
    try:
        if len(returns) < 2:
            return 0.0
        return returns.std() * np.sqrt(252)
    except Exception as e:
        logger.error(f"计算波动率时出错: {e}")
        return 0.0

def calculate_annualized_return(cumulative_return: float, days: int) -> float:
    """
    计算年化收益率
    
    Args:
        cumulative_return: 总收益率
        days: 投资天数
        
    Returns:
        年化收益率
    """
    try:
        if days <= 0:
            return 0.0
        return (1 + cumulative_return) ** (365 / days) - 1
    except Exception as e:
        logger.error(f"计算年化收益率时出错: {e}")
        return 0.0

def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
    """
    验证日期范围的有效性
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        日期范围是否有效
    """
    try:
        if start_date >= end_date:
            logger.warning("开始日期必须早于结束日期")
            return False
        
        if start_date > datetime.now():
            logger.warning("开始日期不能晚于今天")
            return False
        
        if end_date > datetime.now():
            logger.warning("结束日期不能晚于今天")
            return False
        
        return True
    except Exception as e:
        logger.error(f"验证日期范围时出错: {e}")
        return False

def validate_symbols(symbols: List[str]) -> bool:
    """
    验证股票代码列表的有效性
    
    Args:
        symbols: 股票代码列表
        
    Returns:
        股票代码列表是否有效
    """
    try:
        if not symbols:
            logger.warning("股票代码列表不能为空")
            return False
        
        if len(symbols) > 50:  # 限制最大股票数量
            logger.warning("股票数量不能超过50只")
            return False
        
        # 验证股票代码格式（简单验证）
        for symbol in symbols:
            if not symbol or len(symbol) < 6:
                logger.warning(f"无效的股票代码: {symbol}")
                return False
        
        return True
    except Exception as e:
        logger.error(f"验证股票代码时出错: {e}")
        return False
