# -*- coding: utf-8 -*-
"""
Web应用界面 - 重构版本
使用Streamlit构建的交互式回测界面，支持每只股票独立的策略配置
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import sys
import os
from typing import Dict, List, Optional, Tuple

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_handler import DataHandler
from stock_strategy import Stock, Portfolio, Strategy, SignalType
from backtest_engine import BacktestEngine
from config import WEB_CONFIG


# 页面配置
st.set_page_config(
    page_title=WEB_CONFIG['page_title'],
    page_icon=WEB_CONFIG['page_icon'],
    layout=WEB_CONFIG['layout'],
    initial_sidebar_state=WEB_CONFIG['sidebar_state']
)

# 自定义CSS
st.markdown("""
<style>
    .stock-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .strategy-card {
        background-color: #ffffff;
        padding: 0.5rem;
        border-radius: 0.25rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 0.5rem;
    }
    .buy-strategy {
        border-left: 3px solid #2ca02c;
    }
    .sell-strategy {
        border-left: 3px solid #d62728;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1f77b4;
    }
    .success-metric {
        border-left-color: #2ca02c;
    }
    .warning-metric {
        border-left-color: #ff7f0e;
    }
    .danger-metric {
        border-left-color: #d62728;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def get_stock_data(symbols, start_date, end_date):
    """缓存的数据获取函数"""
    data_handler = DataHandler()
    return data_handler.get_multiple_stocks(symbols, start_date, end_date)

@st.cache_data
def get_benchmark_data(symbol: str, start_date: str, end_date: str):
    """获取基准数据"""
    data_handler = DataHandler()
    return data_handler.get_benchmark_data(start_date, end_date, symbol)

# 移除缓存装饰器，确保每次都使用最新的Portfolio对象
def run_backtest_cached(_portfolio: Portfolio,
                       symbols: List[str], start_date: str, end_date: str):
    """回测函数"""
    engine = BacktestEngine()
    
    # 打印调试信息
    print(f"运行回测: 股票数量={len(symbols)}, 开始日期={start_date}, 结束日期={end_date}")
    print(f"Portfolio对象中的股票数量: {len(_portfolio.stocks)}")
    for symbol, stock in _portfolio.stocks.items():
        print(f"股票 {symbol}: 买入策略={len(stock.buy_strategies)}, 卖出策略={len(stock.sell_strategies)}")
    
    results = engine.run_portfolio_backtest(
        portfolio=_portfolio,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date
    )
    
    return results

def run_benchmark_backtest(symbol: str, start_date: str, end_date: str, initial_capital: int):
    """运行基准回测"""
    engine = BacktestEngine()
    benchmark_portfolio = Portfolio()
    
    # 为每个股票创建买入并持有策略
    benchmark_portfolio.add_stock(symbol, initial_investment=initial_capital, max_investment=initial_capital)
    
    benchmark_data = get_benchmark_data(symbol, start_date, end_date)
    # 获取结果
    results = engine.run_portfolio_backtest(
        portfolio=benchmark_portfolio,
        symbols=[symbol],
        start_date=start_date,
        end_date=end_date,
        custom_data={symbol: benchmark_data}
    )
    
    return results

def run_buy_hold_backtest(symbols: List[str], start_date: str, end_date: str, initial_capitals: List[int]):
    """运行买入并持有策略回测"""
    engine = BacktestEngine()
    buy_hold_portfolio = Portfolio()
    
    # 为每个股票创建买入并持有策略
    for symbol, initial_capital in zip(symbols, initial_capitals):
        # 平均分配初始资金
        stock_initial_investment = initial_capital
        buy_hold_portfolio.add_stock(symbol, initial_investment=stock_initial_investment, max_investment=stock_initial_investment)
    
    # 获取结果
    results = engine.run_portfolio_backtest(
        portfolio=buy_hold_portfolio,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date
    )
    
    return results


def render_strategy_params(stock_code: str, strategy_name: str, signal_type: SignalType) -> Dict:
    """
    渲染策略参数界面
    
    Args:
        stock_code: 股票代码
        strategy_name: 策略名称
        signal_type: 信号类型（买入/卖出）
        
    Returns:
        策略参数字典
    """
    strategy_params = {}
    
    if strategy_name == 'time_based':
        st.subheader("⏰ 时间条件单参数")
        
        col1, col2 = st.columns(2)
        with col1:
            frequency = st.selectbox(
                "交易频率",
                options=['daily', 'weekly', 'monthly'],
                format_func=lambda x: {'daily': '每日', 'weekly': '每周', 'monthly': '每月'}.get(x, x),
                key=f"frequency_{stock_code}_{signal_type.value}_{strategy_name}"
            )
            strategy_params['frequency'] = frequency
        
        with col2:
            if frequency in ['weekly', 'monthly']:
                trading_day = st.slider(
                    "第几个交易日", 
                    1, 10, 1,
                    help="选择每周/每月的第几个交易日进行交易",
                    key=f"trading_day_{stock_code}_{signal_type.value}_{strategy_name}"
                )
                strategy_params['trading_day'] = trading_day
        
        # 交易金额/数量设置
        col1, col2 = st.columns(2)
        with col1:
            trade_mode = st.radio(
                "交易模式",
                ["按金额", "按股数"],
                horizontal=True,
                key=f"trade_mode_{stock_code}_{signal_type.value}_{strategy_name}"
            )
        
        with col2:
            if trade_mode == "按金额":
                trade_amount = st.number_input(
                    "每次交易金额 (¥)", 
                    min_value=1000, max_value=100000, 
                    value=10000, step=1000,
                    key=f"trade_amount_{stock_code}_{signal_type.value}_{strategy_name}"
                )
                strategy_params['trade_amount'] = trade_amount
                strategy_params['trade_shares'] = None
            else:
                trade_shares = st.number_input(
                    "每次交易股数", 
                    min_value=100, max_value=10000, 
                    value=1000, step=100,
                    key=f"trade_shares_{stock_code}_{signal_type.value}_{strategy_name}"
                )
                strategy_params['trade_shares'] = trade_shares
                strategy_params['trade_amount'] = None
    
    elif strategy_name == 'macd_pattern':
        st.subheader("📊 MACD形态参数")
        
        # MACD基础参数
        col1, col2, col3 = st.columns(3)
        with col1:
            fast_period = st.slider("快线周期", 5, 20, 12, key=f"fast_period_{stock_code}_{signal_type.value}_{strategy_name}")
            strategy_params['fast_period'] = fast_period
        
        with col2:
            slow_period = st.slider("慢线周期", 20, 50, 26, key=f"slow_period_{stock_code}_{signal_type.value}_{strategy_name}")
            strategy_params['slow_period'] = slow_period
        
        with col3:
            signal_period = st.slider("信号线周期", 5, 20, 9, key=f"signal_period_{stock_code}_{signal_type.value}_{strategy_name}")
            strategy_params['signal_period'] = signal_period
        
        # 形态选择
        st.write(f"**{'买入' if signal_type == SignalType.BUY else '卖出'}形态选择**")
        patterns = []
        col1, col2, col3 = st.columns(3)
        
        if signal_type == SignalType.BUY:
            with col1:
                if st.checkbox("金叉", value=True, key=f"golden_cross_{stock_code}_{signal_type.value}_{strategy_name}"):
                    patterns.append('golden_cross')
            
            with col2:
                if st.checkbox("二次金叉", value=False, key=f"double_golden_cross_{stock_code}_{signal_type.value}_{strategy_name}"):
                    patterns.append('double_golden_cross')
            
            with col3:
                if st.checkbox("底背离", value=False, key=f"bullish_divergence_{stock_code}_{signal_type.value}_{strategy_name}"):
                    patterns.append('bullish_divergence')
            
            strategy_params['buy_patterns'] = patterns
            strategy_params['sell_patterns'] = []
        else:
            with col1:
                if st.checkbox("死叉", value=True, key=f"death_cross_{stock_code}_{signal_type.value}_{strategy_name}"):
                    patterns.append('death_cross')
            
            with col2:
                if st.checkbox("二次死叉", value=False, key=f"double_death_cross_{stock_code}_{signal_type.value}_{strategy_name}"):
                    patterns.append('double_death_cross')
            
            with col3:
                if st.checkbox("顶背离", value=False, key=f"bearish_divergence_{stock_code}_{signal_type.value}_{strategy_name}"):
                    patterns.append('bearish_divergence')
            
            strategy_params['buy_patterns'] = []
            strategy_params['sell_patterns'] = patterns
        
        # 检测参数
        col1, col2 = st.columns(2)
        with col1:
            divergence_lookback = st.slider("背离检测回望期", 10, 50, 20, key=f"divergence_lookback_{stock_code}_{signal_type.value}_{strategy_name}")
            strategy_params['divergence_lookback'] = divergence_lookback
        
        with col2:
            double_cross_lookback = st.slider("二次交叉检测回望期", 5, 30, 10, key=f"double_cross_lookback_{stock_code}_{signal_type.value}_{strategy_name}")
            strategy_params['double_cross_lookback'] = double_cross_lookback
        
        # 交易金额/数量设置
        col1, col2 = st.columns(2)
        with col1:
            trade_mode = st.radio(
                "交易模式",
                ["按金额", "按股数"],
                horizontal=True,
                key=f"trade_mode_{stock_code}_{signal_type.value}_{strategy_name}"
            )
        
        with col2:
            if trade_mode == "按金额":
                trade_amount = st.number_input(
                    "每次交易金额 (¥)", 
                    min_value=1000, max_value=100000, 
                    value=10000, step=1000,
                    key=f"trade_amount_{stock_code}_{signal_type.value}_{strategy_name}"
                )
                strategy_params['trade_amount'] = trade_amount
                strategy_params['trade_shares'] = None
            else:
                trade_shares = st.number_input(
                    "每次交易股数", 
                    min_value=100, max_value=10000, 
                    value=1000, step=100,
                    key=f"trade_shares_{stock_code}_{signal_type.value}_{strategy_name}"
                )
                strategy_params['trade_shares'] = trade_shares
                strategy_params['trade_amount'] = None
    
    elif strategy_name == 'ma_touch':
        st.subheader("📈 均线触碰参数")
        
        # 均线周期选择
        st.write("**均线周期选择**")
        ma_periods = []
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.checkbox("5日均线", value=True, key=f"ma_5_{stock_code}_{signal_type.value}_{strategy_name}"):
                ma_periods.append(5)
        
        with col2:
            if st.checkbox("10日均线", value=True, key=f"ma_10_{stock_code}_{signal_type.value}_{strategy_name}"):
                ma_periods.append(10)
        
        with col3:
            if st.checkbox("20日均线", value=True, key=f"ma_20_{stock_code}_{signal_type.value}_{strategy_name}"):
                ma_periods.append(20)
        
        with col4:
            if st.checkbox("30日均线", value=False, key=f"ma_30_{stock_code}_{signal_type.value}_{strategy_name}"):
                ma_periods.append(30)
        
        with col5:
            if st.checkbox("60日均线", value=False, key=f"ma_60_{stock_code}_{signal_type.value}_{strategy_name}"):
                ma_periods.append(60)
        
        strategy_params['ma_periods'] = ma_periods
        
        # 触碰阈值
        touch_threshold = st.slider(
            "触碰阈值 (%)", 
            0.1, 5.0, 2.0, 0.1,
            help="价格与均线的距离百分比，越小越精确",
            key=f"touch_threshold_{stock_code}_{signal_type.value}_{strategy_name}"
        )
        strategy_params['touch_threshold'] = touch_threshold / 100.0
        
        # 交易行为设置
        if signal_type == SignalType.BUY:
            strategy_params['buy_on_touch'] = True
            strategy_params['sell_on_touch'] = False
        else:
            strategy_params['buy_on_touch'] = False
            strategy_params['sell_on_touch'] = True
        
        # 交易金额/数量设置
        col1, col2 = st.columns(2)
        with col1:
            trade_mode = st.radio(
                "交易模式",
                ["按金额", "按股数"],
                horizontal=True,
                key=f"trade_mode_{stock_code}_{signal_type.value}_{strategy_name}"
            )
        
        with col2:
            if trade_mode == "按金额":
                trade_amount = st.number_input(
                    "每次交易金额 (¥)", 
                    min_value=1000, max_value=100000, 
                    value=10000, step=1000,
                    key=f"trade_amount_{stock_code}_{signal_type.value}_{strategy_name}"
                )
                strategy_params['trade_amount'] = trade_amount
                strategy_params['trade_shares'] = None
            else:
                trade_shares = st.number_input(
                    "每次交易股数", 
                    min_value=100, max_value=10000, 
                    value=1000, step=100,
                    key=f"trade_shares_{stock_code}_{signal_type.value}_{strategy_name}"
                )
                strategy_params['trade_shares'] = trade_shares
                strategy_params['trade_amount'] = None
    
    return strategy_params

def render_stock_strategy_card(stock_code: str, portfolio: Portfolio):
    """渲染单只股票的策略卡片"""
    with st.container():
        st.markdown(f"""
        <div class="stock-card">
            <h4>{stock_code}</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # 初始持仓金额输入框
        initial_investment = st.number_input(
            "初始持仓金额 (¥)",  # 明确单位为人民币
            min_value=0,  # 允许初始投资金额为零
            value=int(portfolio.stocks[stock_code].initial_investment),
            step=1000,
            key=f"initial_investment_{stock_code}"
        )
        portfolio.update_stock_investment(stock_code, initial_investment)
        
        # 最大投资资金输入框
        max_investment = st.number_input(
            "最大投资资金 (¥)",
            min_value=1000,
            value=int(portfolio.stocks[stock_code].max_investment),
            step=1000,
            key=f"max_investment_{stock_code}"
        )
        portfolio.update_stock_max_investment(stock_code, max_investment)
        
        # 添加策略按钮
        col1, col2 = st.columns([3, 1])
        with col1:
            strategy_type = st.selectbox(
                "选择策略类型",
                options=['time_based', 'macd_pattern', 'ma_touch'],
                format_func=lambda x: {'time_based': '时间条件单', 'macd_pattern': 'MACD形态', 'ma_touch': '均线触碰'}.get(x, x),
                key=f"strategy_type_{stock_code}"
            )
        
        with col2:
            signal_type = st.selectbox(
                "信号类型",
                options=[SignalType.BUY, SignalType.SELL],
                format_func=lambda x: "买入" if x == SignalType.BUY else "卖出",
                key=f"signal_type_{stock_code}"
            )
        
        # 策略参数
        strategy_params = render_strategy_params(stock_code, strategy_type, signal_type)
        
        # 添加策略按钮
        if st.button("添加策略", key=f"add_strategy_{stock_code}"):
            strategy = Strategy(
                name=f"{strategy_type}_{signal_type.value}_{len(portfolio.stocks[stock_code].buy_strategies + portfolio.stocks[stock_code].sell_strategies)}",
                type=strategy_type,
                signal_type=signal_type,
                params=strategy_params
            )
            # 确保添加策略直接修改session_state中的portfolio
            portfolio.add_strategy(stock_code, strategy)
            print(f"✅ 策略 {strategy.name} {strategy.type} {strategy.signal_type} 添加成功！")
            print(portfolio.stocks[stock_code].buy_strategies)
            print(portfolio.stocks[stock_code].sell_strategies)
            st.success(f"✅ 策略 {strategy.name} 添加成功！")
            # 强制页面重新加载
            st.rerun()
        
        # 显示已添加的策略
        if stock_code in portfolio.stocks:
            stock = portfolio.stocks[stock_code]
            for i, strategy in enumerate(stock.buy_strategies + stock.sell_strategies):
                if not strategy.enabled:
                    continue
                with st.container():
                    st.markdown(f"""
                    <div class="strategy-card {'buy-strategy' if strategy.signal_type == SignalType.BUY else 'sell-strategy'}">
                        <h4>{strategy.name} ({'买入' if strategy.signal_type == SignalType.BUY else '卖出'})</h4>
                        <p>{str(strategy.params)}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 删除策略按钮
                    if st.button("删除策略", key=f"delete_strategy_{stock_code}_{i}"):
                        # 保存策略名称和类型，以便在回调中使用
                        strategy.enabled = False
                        st.success(f"✅ 策略 {strategy.name} 删除成功！")
                        # 强制页面重新加载
                        st.rerun()

def display_results(results):
    """显示回测结果"""
    st.subheader("回测结果")
    # 显示收益分析部分
    st.subheader("收益分析")
    
    # 创建两列布局
    col1, col2 = st.columns(2)
    
    # 第一列显示基本收益信息
    with col1:
        st.write("总初始资金: ¥{:,.2f}".format(results['initial_capital']))
        st.write("最终资产价值: ¥{:,.2f}".format(results['final_value']))
        st.write("总收益率: {:.2%}".format(results['total_return']))
        
        # 直接使用回测引擎计算的年化收益率
        if 'annualized_return' in results:
            st.write("年化收益率: {:.2%}".format(results['annualized_return']))


    
    # 第二列显示风险指标
    with col2:
        # 直接使用回测引擎计算的风险指标
        if 'max_drawdown' in results:
            st.write("最大回撤: {:.2%}".format(results['max_drawdown']))

        
        if 'sharpe_ratio' in results:
            st.write("夏普比率: {:.2f}".format(results['sharpe_ratio']))

        
        if 'volatility' in results:
            st.write("年化波动率: {:.2%}".format(results['volatility']))
 
        
        if 'max_drawdown_recovery_days' in results:
            st.write("最大回撤修复天数: {} 天".format(results['max_drawdown_recovery_days']))
    
    # 添加与基准和买入持有的对比
    if st.session_state.get('benchmark_results') and st.session_state.get('buy_hold_results'):
        st.subheader("策略对比分析")
        
        # 创建对比表格
        comparison_data = []
        
        # 策略数据 - 使用原始结果
        strategy_total_return = results['total_return']
        strategy_annualized = results.get('annualized_return', 0)
        strategy_volatility = results.get('volatility', 0)
        strategy_sharpe = results.get('sharpe_ratio', 0)
        strategy_max_dd = results.get('max_drawdown', 0)
        
        # 基准数据 - 使用独立运行的基准回测结果
        benchmark_results = st.session_state.benchmark_results
        benchmark_total_return = benchmark_results['total_return']
        benchmark_annualized = benchmark_results.get('annualized_return', 0)
        benchmark_volatility = benchmark_results.get('volatility', 0)
        benchmark_sharpe = benchmark_results.get('sharpe_ratio', 0)
        benchmark_max_dd = benchmark_results.get('max_drawdown', 0)
        
        # 买入并持有策略数据 - 使用独立运行的买入并持有回测结果
        buy_hold_results = st.session_state.buy_hold_results
        buy_hold_total_return = buy_hold_results['total_return']
        buy_hold_annualized = buy_hold_results.get('annualized_return', 0)
        buy_hold_volatility = buy_hold_results.get('volatility', 0)
        buy_hold_sharpe = buy_hold_results.get('sharpe_ratio', 0)
        buy_hold_max_dd = buy_hold_results.get('max_drawdown', 0)
        
        # 获取最大回撤修复天数
        strategy_recovery_days = results.get('max_drawdown_recovery_days', 0)
        benchmark_recovery_days = benchmark_results.get('max_drawdown_recovery_days', 0)
        buy_hold_recovery_days = buy_hold_results.get('max_drawdown_recovery_days', 0)
        
        # 添加数据到对比表
        comparison_data.append({
            '策略': '回测策略',
            '总收益率': f"{strategy_total_return:.2%}",
            '年化收益率': f"{strategy_annualized:.2%}",
            '年化波动率': f"{strategy_volatility:.2%}",
            '夏普比率': f"{strategy_sharpe:.2f}",
            '最大回撤': f"{strategy_max_dd:.2%}",
            '回撤修复天数': f"{strategy_recovery_days}"
        })
        
        comparison_data.append({
            '策略': st.session_state.get('benchmark_name', st.session_state.benchmark_symbol),
            '总收益率': f"{benchmark_total_return:.2%}",
            '年化收益率': f"{benchmark_annualized:.2%}",
            '年化波动率': f"{benchmark_volatility:.2%}",
            '夏普比率': f"{benchmark_sharpe:.2f}",
            '最大回撤': f"{benchmark_max_dd:.2%}",
            '回撤修复天数': f"{benchmark_recovery_days}"
        })
        
        comparison_data.append({
            '策略': '买入并持有',
            '总收益率': f"{buy_hold_total_return:.2%}",
            '年化收益率': f"{buy_hold_annualized:.2%}",
            '年化波动率': f"{buy_hold_volatility:.2%}",
            '夏普比率': f"{buy_hold_sharpe:.2f}",
            '最大回撤': f"{buy_hold_max_dd:.2%}",
            '回撤修复天数': f"{buy_hold_recovery_days}"
        })
        
        # 显示对比表格
        comparison_df = pd.DataFrame(comparison_data)
        st.table(comparison_df)
    # 显示交易记录
    st.subheader("交易记录")
    if results['trades']:
        # 直接显示原始交易记录
        st.write(f"交易记录总数: {len(results['trades'])}")
    
        # 创建交易数据框
        trades_df = pd.DataFrame(results['trades'])
        
        # 重命名列
        trades_df.rename(columns={
            'date': '日期',
            'symbol': '股票代码',
            'shares': '交易股数',
            'price': '价格',
            'value': '交易金额',
            'commission': '手续费',
            'type': '类型'
        }, inplace=True)
        
        # 确保日期列是日期时间类型
        if not pd.api.types.is_datetime64_any_dtype(trades_df['日期']):
            trades_df['日期'] = pd.to_datetime(trades_df['日期'])
        
        # 添加交易类型的中文显示
        trades_df['交易类型'] = trades_df['类型'].map({'buy': '买入', 'sell': '卖出'})
        
        # 统计交易信息
        buy_count = len(trades_df[trades_df['类型'] == 'buy'])
        sell_count = len(trades_df[trades_df['类型'] == 'sell'])
        st.write(f"总交易次数: {len(trades_df)}, 买入次数: {buy_count}, 卖出次数: {sell_count}")
        
        # 显示交易记录表格
        st.dataframe(trades_df[['日期', '股票代码', '交易类型', '交易股数', '价格', '交易金额', '手续费']], use_container_width=True)
        
        # 导出交易记录按钮
        csv = trades_df.to_csv().encode('utf-8')
        st.download_button(
            label="下载交易记录CSV",
            data=csv,
            file_name='交易记录.csv',
            mime='text/csv',
        )

    else:
        st.write("无交易记录")
    
    # 显示投资组合价值变化
    st.subheader("投资组合价值变化")
    if not results['portfolio_value'].empty:
        # 创建数据框
        portfolio_value_df = pd.DataFrame(results['portfolio_value'], columns=['投资组合价值'])
        
        # 使用独立运行的买入并持有策略结果
        if st.session_state.get('buy_hold_results'):
            buy_hold_results = st.session_state.buy_hold_results
            buy_hold_values = buy_hold_results['portfolio_value']
            
            # 确保索引匹配
            common_index = portfolio_value_df.index.intersection(buy_hold_values.index)
            if not common_index.empty:
                # 将买入并持有策略的价值变化添加到数据框
                portfolio_value_df['买入并持有'] = buy_hold_values.loc[common_index]
        
        # 使用独立运行的基准指数结果
        if st.session_state.get('benchmark_results'):
            benchmark_results = st.session_state.benchmark_results
            benchmark_values = benchmark_results['portfolio_value']
            
            # 确保索引匹配
            common_index = portfolio_value_df.index.intersection(benchmark_values.index)
            if not common_index.empty:
                # 添加到数据框
                benchmark_name = st.session_state.get('benchmark_name', '基准指数')
                portfolio_value_df[benchmark_name] = benchmark_values.loc[common_index]
        
        # 修改日期格式
        date_labels = portfolio_value_df.index.strftime('%Y.%m.%d')
        
        # 计算每个策略的收益率百分比
        initial_value = portfolio_value_df['投资组合价值'].iloc[0]
        portfolio_value_df['投资组合收益率'] = (portfolio_value_df['投资组合价值'] / initial_value - 1) * 100
        
        buy_hold_initial = portfolio_value_df['买入并持有'].iloc[0]
        portfolio_value_df['买入并持有收益率'] = (portfolio_value_df['买入并持有'] / buy_hold_initial - 1) * 100
        
        benchmark_name = st.session_state.get('benchmark_name', '基准指数')
        if benchmark_name in portfolio_value_df.columns:
            benchmark_initial = portfolio_value_df[benchmark_name].iloc[0]
            portfolio_value_df[f'{benchmark_name}收益率'] = (portfolio_value_df[benchmark_name] / benchmark_initial - 1) * 100
        
        # 获取最大回撤信息
        results = st.session_state.results
        max_drawdown = results.get('max_drawdown', 0)
        
        # 计算最大回撤区域
        portfolio_returns = results['returns']
        cumulative_returns = (1 + portfolio_returns).cumprod()
        peak = cumulative_returns.expanding(min_periods=1).max()
        drawdown = (cumulative_returns/peak - 1)
        
        # 找到最大回撤的时间点
        max_dd_idx = drawdown.idxmin()
        # 找到最后一次达到峰值的时间点
        last_peak_idx = peak.loc[:max_dd_idx].idxmax()
        
        # 找到从最大回撤点恢复到上一个峰值的时间点
        recovery_idx = None
        recovery_series = cumulative_returns.loc[max_dd_idx:]
        if results.get('max_drawdown_recovery_days', 0) > 0:
            # 已经恢复到峰值
            for i, value in enumerate(recovery_series):
                if value >= peak.loc[last_peak_idx]:
                    recovery_idx = recovery_series.index[i]
                    break
        
        # 创建Tab页面分别显示价值变化图和回撤分析图
        tab1, tab2 = st.tabs(['价值变化', '回撤分析'])
        
        # 在第一个Tab显示价值变化图
        with tab1:
            # 创建价值变化图
            fig_value = go.Figure()
            
            # 添加投资组合价值曲线
            fig_value.add_trace(go.Scatter(
                x=date_labels,
                y=portfolio_value_df['投资组合价值'],
                mode='lines',
                name='投资组合价值',
                line=dict(color='#1f77b4', width=2)
            ))
            
            # 添加买入并持有策略曲线
            fig_value.add_trace(go.Scatter(
                x=date_labels,
                y=portfolio_value_df['买入并持有'],
                mode='lines',
                name='买入并持有',
                line=dict(color='#2ca02c', width=2)
            ))
            
            # 添加基准指数曲线（如果有）
            if benchmark_name in portfolio_value_df.columns:
                fig_value.add_trace(go.Scatter(
                    x=date_labels,
                    y=portfolio_value_df[benchmark_name],
                    mode='lines',
                    name=benchmark_name,
                    line=dict(color='#ff7f0e', width=2)
                ))
                
            # 添加买入卖出点标记
            if results['trades']:
                trades_df = pd.DataFrame(results['trades'])
                
                # 确保trades_df有正确的列名
                if len(trades_df.columns) == 7:
                    trades_df.columns = ['日期', '股票代码', '交易股数', '价格', '交易金额', '手续费', '类型']
                    trades_df['日期'] = pd.to_datetime(trades_df['日期'])
                    
                    # 买入点
                    buy_trades = trades_df[trades_df['类型'] == 'buy']
                    if not buy_trades.empty:
                        # 确保日期格式一致
                        buy_dates = buy_trades['日期'].dt.strftime('%Y.%m.%d').tolist()
                        
                        # 获取对应的价值点
                        buy_values = []
                        buy_texts = []
                        for date in buy_trades['日期']:
                            if date in portfolio_value_df.index:
                                buy_values.append(portfolio_value_df.loc[date, '投资组合价值'])
                                # 获取对应交易的详细信息
                                trade_info = buy_trades[buy_trades['日期'] == date].iloc[0]
                                buy_texts.append(
                                    f"买入: {trade_info['股票代码']}<br>" +
                                    f"股数: {trade_info['交易股数']:.0f}<br>" +
                                    f"价格: ¥{trade_info['价格']:.2f}<br>" +
                                    f"金额: ¥{trade_info['交易金额']:.2f}"
                                )
                        
                        if buy_values:
                            fig_value.add_trace(go.Scatter(
                                x=buy_dates,
                                y=buy_values,
                                mode='markers',
                                name='买入点',
                                marker=dict(color='green', size=10, symbol='triangle-up'),
                                text=buy_texts,
                                hoverinfo='text'
                            ))
                    
                    # 卖出点
                    sell_trades = trades_df[trades_df['类型'] == 'sell']
                    if not sell_trades.empty:
                        # 确保日期格式一致
                        sell_dates = sell_trades['日期'].dt.strftime('%Y.%m.%d').tolist()
                        
                        # 获取对应的价值点
                        sell_values = []
                        sell_texts = []
                        for date in sell_trades['日期']:
                            if date in portfolio_value_df.index:
                                sell_values.append(portfolio_value_df.loc[date, '投资组合价值'])
                                # 获取对应交易的详细信息
                                trade_info = sell_trades[sell_trades['日期'] == date].iloc[0]
                                sell_texts.append(
                                    f"卖出: {trade_info['股票代码']}<br>" +
                                    f"股数: {abs(trade_info['交易股数']):.0f}<br>" +
                                    f"价格: ¥{trade_info['价格']:.2f}<br>" +
                                    f"金额: ¥{abs(trade_info['交易金额']):.2f}"
                                )
                        
                        if sell_values:
                            fig_value.add_trace(go.Scatter(
                                x=sell_dates,
                                y=sell_values,
                                mode='markers',
                                name='卖出点',
                                marker=dict(color='red', size=10, symbol='triangle-down'),
                                text=sell_texts,
                                hoverinfo='text'
                            ))
                            
            # 添加隐藏的收益率曲线到第二个Y轴（只用于计算刻度范围）
            fig_value.add_trace(go.Scatter(
                x=date_labels,
                y=portfolio_value_df['投资组合收益率'],
                mode='lines',
                name='投资组合收益率(%)',
                line=dict(color='rgba(0,0,0,0)', width=0),  # 透明线条，实际上是隐藏的
                yaxis='y2',
                showlegend=False  # 不在图例中显示
            ))
            
            # 添加隐藏的买入并持有收益率曲线（只用于计算刻度范围）
            fig_value.add_trace(go.Scatter(
                x=date_labels,
                y=portfolio_value_df['买入并持有收益率'],
                mode='lines',
                name='买入并持有收益率(%)',
                line=dict(color='rgba(0,0,0,0)', width=0),  # 透明线条，实际上是隐藏的
                yaxis='y2',
                showlegend=False  # 不在图例中显示
            ))
            
            # 添加隐藏的基准指数收益率曲线（如果有）（只用于计算刻度范围）
            if benchmark_name in portfolio_value_df.columns and f'{benchmark_name}收益率' in portfolio_value_df.columns:
                fig_value.add_trace(go.Scatter(
                    x=date_labels,
                    y=portfolio_value_df[f'{benchmark_name}收益率'],
                    mode='lines',
                    name=f'{benchmark_name}收益率(%)',
                    line=dict(color='rgba(0,0,0,0)', width=0),  # 透明线条，实际上是隐藏的
                    yaxis='y2',
                    showlegend=False  # 不在图例中显示
                ))
            
            # 设置价值图的布局
            fig_value.update_layout(
                title='投资组合价值变化',
                hovermode='closest',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                xaxis=dict(
                    title='日期',
                    tickangle=45,
                    tickmode='auto',
                    nticks=20
                ),
                yaxis=dict(
                    title='价值 (¥)',
                    side='left'
                ),
                yaxis2=dict(
                    title='收益率 (%)',
                    side='right',
                    overlaying='y',
                    rangemode='tozero',
                    showgrid=False
                )
            )
                
            # 显示价值变化图
            st.plotly_chart(fig_value, use_container_width=True)
        
        # 在第二个Tab显示回撤分析图
        with tab2:
            # 创建回撤分析图
            fig_drawdown = go.Figure()
            
            # 确保使用所有日期数据
            all_dates = portfolio_value_df.index
            
            # 创建收益率数据
            # 计算相对于初始值的收益率（百分比）
            returns_pct = (cumulative_returns - 1) * 100
            
            # 先创建一个包含所有日期的收益率数据框
            full_returns = pd.Series(index=all_dates, data=np.nan)
            full_returns.loc[returns_pct.index] = returns_pct.values
            # 对缺失的值进行插值
            full_returns = full_returns.interpolate(method='linear')
            
            # 添加收益率曲线
            fig_drawdown.add_trace(go.Scatter(
                x=all_dates.strftime('%Y.%m.%d'),
                y=full_returns.values,
                mode='lines',
                name='收益率(%)',
                line=dict(color='#1f77b4', width=2)
            ))
        
            # 如果有最大回撤区域，添加标记
            if last_peak_idx and max_dd_idx:
                # 获取峰值和谷值的收益率
                peak_return = full_returns.loc[last_peak_idx]
                bottom_return = full_returns.loc[max_dd_idx]
                
                # 添加峰值和谷值标记点
                fig_drawdown.add_trace(go.Scatter(
                    x=[last_peak_idx.strftime('%Y.%m.%d'), max_dd_idx.strftime('%Y.%m.%d')],
                    y=[peak_return, bottom_return],
                    mode='markers',
                    name='最大回撤区间',
                    marker=dict(color='red', size=8, symbol=['triangle-down', 'triangle-down']),
                    text=[f'峰值: {last_peak_idx.strftime("%Y-%m-%d")}\n收益率: {peak_return:.2f}%', 
                          f'谷值: {max_dd_idx.strftime("%Y-%m-%d")}\n收益率: {bottom_return:.2f}%\n最大回撤: {max_drawdown:.2%}'],
                    hoverinfo='text'
                ))
                
                # 在谷值位置添加最大回撤标注
                fig_drawdown.add_annotation(
                    x=max_dd_idx.strftime('%Y.%m.%d'),
                    y=bottom_return,
                    text=f'最大回撤: {max_drawdown:.2%}',
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=2,
                    arrowcolor='red',
                    bgcolor='rgba(255, 255, 255, 0.8)',
                    bordercolor='red',
                    borderwidth=1,
                    borderpad=4,
                    ax=40,
                    ay=-40
                )
                
                # 添加最大回撤区域填充 (红色)
                # 获取最大回撤区间的所有数据点
                drawdown_dates = all_dates[(all_dates >= last_peak_idx) & (all_dates <= max_dd_idx)]
                drawdown_returns = full_returns.loc[drawdown_dates]
                
                # 添加最大回撤区域的填充
                fig_drawdown.add_trace(go.Scatter(
                    x=drawdown_dates.strftime('%Y.%m.%d'),
                    y=drawdown_returns,
                    fill='tozeroy',
                    fillcolor='rgba(255,0,0,0.15)',
                    line=dict(color='rgba(255,0,0,0)'),
                    name='最大回撤区域',
                    showlegend=True
                ))
                
                # 如果已恢复，添加恢复区域和标记
                if recovery_idx:
                    # 获取恢复点的收益率
                    recovery_return = full_returns.loc[recovery_idx]
                    
                    # 添加恢复点标记
                    fig_drawdown.add_trace(go.Scatter(
                        x=[recovery_idx.strftime('%Y.%m.%d')],
                        y=[recovery_return],
                        mode='markers',
                        name='回撤恢复点',
                        marker=dict(color='green', size=8, symbol='triangle-up'),
                        text=[f'恢复: {recovery_idx.strftime("%Y-%m-%d")}\n收益率: {recovery_return:.2f}%\n恢复天数: {results.get("max_drawdown_recovery_days", 0)}天'],
                        hoverinfo='text'
                    ))
                    
                    # 获取恢复区间的所有数据点
                    recovery_dates = all_dates[(all_dates >= max_dd_idx) & (all_dates <= recovery_idx)]
                    recovery_returns = full_returns.loc[recovery_dates]
                    
                    # 添加恢复区域的填充
                    fig_drawdown.add_trace(go.Scatter(
                        x=recovery_dates.strftime('%Y.%m.%d'),
                        y=recovery_returns,
                        fill='tozeroy',
                        fillcolor='rgba(0,255,0,0.15)',
                        line=dict(color='rgba(0,255,0,0)'),
                        name='回撤恢复区域',
                        showlegend=True
                    ))
                    
                    # 添加恢复天数标注
                    fig_drawdown.add_annotation(
                        x=recovery_idx.strftime('%Y.%m.%d'),
                        y=recovery_return,
                        text=f'恢复天数: {results.get("max_drawdown_recovery_days", 0)}天',
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1,
                        arrowwidth=2,
                        arrowcolor='green',
                        bgcolor='rgba(255, 255, 255, 0.8)',
                        bordercolor='green',
                        borderwidth=1,
                        borderpad=4,
                        ax=40,
                        ay=40
                    )
                else:
                    # 如果未恢复，显示正在恢复的区域和天数
                    # 计算当前恢复天数
                    current_recovery_days = len(portfolio_value_df.loc[max_dd_idx:].index)
                    
                    # 获取最后一天的收益率
                    last_date = all_dates[-1]
                    last_return = full_returns.iloc[-1]
                    
                    # 获取恢复区间的所有数据点
                    recovery_dates = all_dates[(all_dates >= max_dd_idx) & (all_dates <= last_date)]
                    recovery_returns = full_returns.loc[recovery_dates]
                    
                    # 添加正在恢复区域的填充
                    fig_drawdown.add_trace(go.Scatter(
                        x=recovery_dates.strftime('%Y.%m.%d'),
                        y=recovery_returns,
                        fill='tozeroy',
                        fillcolor='rgba(255,255,0,0.15)',
                        line=dict(color='rgba(255,255,0,0)'),
                        name='正在恢复区域',
                        showlegend=True
                    ))
                    
                    # 添加当前恢复天数标注
                    fig_drawdown.add_annotation(
                        x=last_date.strftime('%Y.%m.%d'),
                        y=last_return,
                        text=f'当前恢复天数: {current_recovery_days}天',
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1,
                        arrowwidth=2,
                        arrowcolor='orange',
                        bgcolor='rgba(255, 255, 255, 0.8)',
                        bordercolor='orange',
                        borderwidth=1,
                        borderpad=4,
                        ax=40,
                        ay=40
                    )
                    
            # 设置回撤图的布局
            fig_drawdown.update_layout(
                title='收益率与回撤分析',
                xaxis_title='日期',
                yaxis_title='收益率 (%)',
                hovermode='closest',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                xaxis=dict(
                    tickangle=45,
                    tickmode='auto',
                    nticks=20
                )
            )
            
            # 显示回撤分析图
            st.plotly_chart(fig_drawdown, use_container_width=True)
        

    else:
        st.write("无投资组合价值变化数据")


def main():
    """主函数"""
    # 标题
    st.title("📈 股票回测系统")
    # 侧边栏 - 参数设置
    with st.sidebar:
        st.header("📊 回测参数设置")
        
        # 基本参数
        st.subheader("基本设置")
        
        # 选择输入模式
        input_mode = st.radio(
            "选择投资标的类型",
            ["股票代码", "ETF选择", "混合输入"],
            horizontal=True
        )
        
        if input_mode == "股票代码":
            symbols_input = st.text_input(
                "股票代码 (用逗号分隔)", 
                value="000001,000002,000858",
                help="输入A股代码，如: 000001,000002,000858"
            )
            symbols = [s.strip() for s in symbols_input.split(',') if s.strip()]
        
        elif input_mode == "ETF选择":
            from config import ETF_CONFIG
            
            # ETF分类选择
            etf_category = st.selectbox(
                "选择ETF类别",
                ["全部"] + list(ETF_CONFIG['etf_categories'].keys())
            )
            
            # 获取对应的ETF列表
            if etf_category == "全部":
                available_etfs = ETF_CONFIG['popular_etfs']
            else:
                category_codes = ETF_CONFIG['etf_categories'][etf_category]
                available_etfs = {code: ETF_CONFIG['popular_etfs'][code] for code in category_codes}
            
            # ETF多选
            selected_etfs = st.multiselect(
                f"选择ETF ({len(available_etfs)}只可选)",
                options=list(available_etfs.keys()),
                default=[list(available_etfs.keys())[0]] if available_etfs else [],
                format_func=lambda x: f"{x}: {available_etfs.get(x, '')}"
            )
            symbols = selected_etfs
            
        else:  # 混合输入
            symbols_input = st.text_input(
                "股票/ETF代码 (用逗号分隔)", 
                value="000001,510300,002594,159915",
                help="可同时输入股票和ETF代码，如: 000001,510300,002594,159915"
            )
            symbols = [s.strip() for s in symbols_input.split(',') if s.strip()]
        
        # 显示选择的标的信息
        if symbols:
            st.info(f"已选择 {len(symbols)} 个投资标的: {', '.join(symbols)}")
        
        # 日期范围
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "开始日期",
                value=datetime.now() - timedelta(days=365),
                max_value=datetime.now()
            )
        with col2:
            end_date = st.date_input(
                "结束日期",
                value=datetime.now(),
                max_value=datetime.now()
            )
        
        # 基准指数
        benchmark = st.selectbox(
            "基准指数",
            options=['sh000300', 'sh000001', 'sz399001', 'sz399006', 'sz399905', 'sz399852'],
            format_func=lambda x: {
                'sh000300': '沪深300',
                'sh000001': '上证指数',
                'sz399001': '深证成指',
                'sz399006': '创业板指',
                'sz399905': '中证500',
                'sz399852': '中证1000'
            }.get(x, x),
            index=0  # 默认选择沪深300
        )

    # 主界面 - 策略配置
    # 检查是否需要创建新的投资组合
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = Portfolio()
    
    # 确保所有选中的股票都在投资组合中
    for symbol in symbols:
        if symbol not in st.session_state.portfolio.stocks:
            st.session_state.portfolio.add_stock(symbol)
            # st.info(f"添加了新股票: {symbol}")
    
    # 移除不在当前选择中的股票
    stocks_to_remove = []
    for symbol in st.session_state.portfolio.stocks:
        if symbol not in symbols:
            stocks_to_remove.append(symbol)
    
    for symbol in stocks_to_remove:
        st.session_state.portfolio.remove_stock(symbol)
        # st.info(f"移除了股票: {symbol}")
    
    # 调试显示当前投资组合中的股票和策略
    with st.expander("当前投资组合信息", expanded=False):
        st.write(f"投资组合中的股票数量: {len(st.session_state.portfolio.stocks)}")
        for symbol, stock in st.session_state.portfolio.stocks.items():
            st.write(f"股票 {symbol}:")
            st.write(f"  买入策略数量: {stock.get_enabled_buy_strategie_number()}")
            st.write(f"  卖出策略数量: {stock.get_enabled_sell_strategie_number()}")
    
    # 渲染每个股票的策略卡片
    for symbol in symbols:
        render_stock_strategy_card(symbol, st.session_state.portfolio)
    
    # 开始回测按钮
    if st.button("🚀 开始回测", type="primary"):
        if not symbols:
            st.error("请输入至少一个股票代码")
            return
        
        if start_date >= end_date:
            st.error("开始日期必须早于结束日期")
            return
        
        # 显示进度
        with st.spinner("正在运行回测，请稍候..."):
            # 调试日志：打印投资组合信息
            st.write("### 调试信息")
            st.write(f"投资组合中的股票数量: {len(st.session_state.portfolio.stocks)}")
            for symbol, stock in st.session_state.portfolio.stocks.items():
                st.write(f"股票 {symbol}:")
                st.write(f"  初始投资: {stock.initial_investment}")
                st.write(f"  最大投资: {stock.max_investment}")
                st.write(f"  买入策略数量: {stock.get_enabled_buy_strategie_number()}")
                for i, strategy in enumerate(stock.buy_strategies):
                    if strategy.enabled:
                        st.write(f"    买入策略 {i+1}: {strategy.name}, 类型: {strategy.type}")
                        st.write(f"    参数: {strategy.params}")
                st.write(f"  卖出策略数量: {stock.get_enabled_sell_strategie_number()}")
                for i, strategy in enumerate(stock.sell_strategies):
                    if strategy.enabled:
                        st.write(f"    卖出策略 {i+1}: {strategy.name}, 类型: {strategy.type}")
                        st.write(f"    参数: {strategy.params}")
            
            # 运行自定义策略回测
            results = run_backtest_cached(
                _portfolio=st.session_state.portfolio,
                symbols=symbols,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            # 运行买入并持有策略回测
            # 运行基准指数回测
            # 使用相同的初始资金
            all_initial_capital = results['initial_capital']

            # 将基准指数代码和中文名称都保存到session_state
            benchmark_name_map = {
                'sh000300': '沪深300',
                'sh000001': '上证指数',
                'sz399001': '深证成指',
                'sz399006': '创业板指',
                'sz399905': '中证500',
                'sz399852': '中证1000'
            }
            st.session_state.benchmark_symbol = benchmark
            st.session_state.benchmark_name = benchmark_name_map.get(benchmark, benchmark)
            benchmark_results = run_benchmark_backtest(
                symbol=benchmark,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                initial_capital=all_initial_capital
            )
                
            initial_capitals = [stock.max_investment for stock in st.session_state.portfolio.stocks.values()]
            buy_hold_results = run_buy_hold_backtest(
                symbols=symbols,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                initial_capitals=initial_capitals
            )
                    
            # 存储结果到session state
            st.session_state.results = results
            st.session_state.benchmark_results = benchmark_results
            st.session_state.buy_hold_results = buy_hold_results
            st.session_state.show_results = True
            
            st.success("✅ 回测完成！")
    
    # 显示结果
    if hasattr(st.session_state, 'show_results') and st.session_state.show_results:
        display_results(st.session_state.results)


if __name__ == "__main__":
    main()

