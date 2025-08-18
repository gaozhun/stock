# -*- coding: utf-8 -*-
"""
回测运行器模块
包含所有回测相关的函数和逻辑
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any
import logging
from datetime import datetime

from data_handler import DataHandler
from stock_strategy import Portfolio, Strategy, SignalType
from backtest_engine import BacktestEngine
from utils import validate_date_range, validate_symbols

logger = logging.getLogger(__name__)

@st.cache_data
def get_stock_data(symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
    """缓存的数据获取函数"""
    try:
        logger.info(f"获取股票数据: {symbols}, 日期范围: {start_date} 到 {end_date}")
        data_handler = DataHandler()
        return data_handler.get_multiple_stocks(symbols, start_date, end_date)
    except Exception as e:
        logger.error(f"获取股票数据时出错: {e}")
        return {}

@st.cache_data
def get_benchmark_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """获取基准数据"""
    try:
        logger.info(f"获取基准数据: {symbol}, 日期范围: {start_date} 到 {end_date}")
        data_handler = DataHandler()
        return data_handler.get_benchmark_data(start_date, end_date, symbol)
    except Exception as e:
        logger.error(f"获取基准数据时出错: {e}")
        return pd.DataFrame()

def run_backtest_cached(portfolio: Portfolio, symbols: List[str], 
                        start_date: str, end_date: str) -> Dict[str, Any]:
    """运行自定义策略回测"""
    try:
        logger.info(f"开始运行回测，股票数量: {len(symbols)}")
        logger.info(f"开始日期: {start_date}, 结束日期: {end_date}")
        logger.info(f"投资组合中的股票数量: {len(portfolio.stocks)}")
        
        for symbol, stock in portfolio.stocks.items():
            logger.info(f"股票 {symbol}: 买入策略={len(stock.buy_strategies)}, 卖出策略={len(stock.sell_strategies)}")
        
        engine = BacktestEngine()
        results = engine.run_portfolio_backtest(
            portfolio=portfolio,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info("回测完成")
        return results
    except Exception as e:
        logger.error(f"运行回测时出错: {e}")
        raise

def run_benchmark_backtest(symbol: str, start_date: str, end_date: str, 
                          initial_capital: int) -> Dict[str, Any]:
    """运行基准指数回测"""
    try:
        logger.info(f"开始运行基准回测: {symbol}")
        engine = BacktestEngine()
        benchmark_portfolio = Portfolio()
        
        # 为基准指数创建买入并持有策略
        benchmark_portfolio.add_stock(symbol, initial_investment=initial_capital, max_investment=initial_capital)
        
        benchmark_data = get_benchmark_data(symbol, start_date, end_date)
        logger.info(f"基准数据获取完成，数据点数量: {len(benchmark_data)}")
        
        # 获取结果
        results = engine.run_portfolio_backtest(
            portfolio=benchmark_portfolio,
            symbols=[symbol],
            start_date=start_date,
            end_date=end_date,
            custom_data={symbol: benchmark_data}
        )
        
        logger.info("基准回测完成")
        return results
    except Exception as e:
        logger.error(f"运行基准回测时出错: {e}")
        raise

def run_buy_hold_backtest(symbols: List[str], start_date: str, end_date: str, 
                          initial_capitals: List[int]) -> Dict[str, Any]:
    """运行买入并持有策略回测"""
    try:
        logger.info(f"开始运行买入并持有策略回测，股票数量: {len(symbols)}")
        engine = BacktestEngine()
        buy_hold_portfolio = Portfolio()
        
        # 为每个股票创建买入并持有策略
        for symbol, initial_capital in zip(symbols, initial_capitals):
            stock_initial_investment = initial_capital
            buy_hold_portfolio.add_stock(symbol, initial_investment=stock_initial_investment, 
                                       max_investment=stock_initial_investment)
        
        # 获取结果
        results = engine.run_portfolio_backtest(
            portfolio=buy_hold_portfolio,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info("买入并持有策略回测完成")
        return results
    except Exception as e:
        logger.error(f"运行买入并持有策略回测时出错: {e}")
        raise

def run_all_backtests(portfolio: Portfolio, symbols: List[str], start_date: str, 
                      end_date: str, benchmark: str) -> Dict[str, Any]:
    """运行所有回测策略"""
    try:
        logger.info("开始运行所有回测策略")
        
        # 验证输入参数
        if not validate_symbols(symbols):
            raise ValueError("股票代码验证失败")
        
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        if not validate_date_range(start_dt, end_dt):
            raise ValueError("日期范围验证失败")
        
        # 运行自定义策略回测
        logger.info("运行自定义策略回测")
        custom_results = run_backtest_cached(
            portfolio=portfolio,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date
        )
        
        # 运行基准指数回测
        logger.info("运行基准指数回测")
        benchmark_results = run_benchmark_backtest(
            symbol=benchmark,
            start_date=start_date,
            end_date=end_date,
            initial_capital=custom_results['initial_capital']
        )
        
        # 运行买入并持有策略回测
        logger.info("运行买入并持有策略回测")
        initial_capitals = [stock.max_investment for stock in portfolio.stocks.values()]
        buy_hold_results = run_buy_hold_backtest(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            initial_capitals=initial_capitals
        )
        
        logger.info("所有回测策略运行完成")
        
        return {
            'custom_results': custom_results,
            'benchmark_results': benchmark_results,
            'buy_hold_results': buy_hold_results
        }
        
    except Exception as e:
        logger.error(f"运行所有回测策略时出错: {e}")
        raise

def validate_backtest_inputs(symbols: List[str], start_date: str, end_date: str) -> bool:
    """验证回测输入参数"""
    try:
        # 验证股票代码
        if not validate_symbols(symbols):
            return False
        
        # 验证日期范围
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        if not validate_date_range(start_dt, end_dt):
            return False
        
        return True
    except Exception as e:
        logger.error(f"验证回测输入参数时出错: {e}")
        return False
