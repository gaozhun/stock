# -*- coding: utf-8 -*-
"""
Web应用界面 - 重构版本
使用Streamlit构建的交互式回测界面，支持每只股票独立的策略配置
"""

import streamlit as st
import sys
import os
from datetime import datetime, timedelta
import logging

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入配置和模块
from config import WEB_CONFIG
from logging_config import setup_default_logging, get_logger
from ui_components import setup_page_config, apply_custom_css
from backtest_runner import run_all_backtests, validate_backtest_inputs
from strategy_ui import render_stock_strategy_card
from results_display import display_results

# 设置日志
setup_default_logging()
logger = get_logger(__name__)

def render_sidebar() -> tuple:
    """
    渲染侧边栏并返回用户输入参数
    
    Returns:
        tuple: (symbols, start_date, end_date, benchmark)
    """
    try:
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
            
            symbols = get_symbols_from_input_mode(input_mode)
            
            # 显示选择的标的信息
            if symbols:
                st.info(f"已选择 {len(symbols)} 个投资标的: {', '.join(symbols)}")
            
            # 日期范围
            start_date, end_date = get_date_range_inputs()
            
            # 基准指数
            benchmark = get_benchmark_selection()
            
            return symbols, start_date, end_date, benchmark
            
    except Exception as e:
        logger.error(f"渲染侧边栏时出错: {e}")
        st.error("渲染侧边栏时出错")
        return [], datetime.now() - timedelta(days=365), datetime.now(), 'sh000300'

def get_symbols_from_input_mode(input_mode: str) -> list:
    """根据输入模式获取股票代码列表"""
    try:
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
        
        return symbols
        
    except Exception as e:
        logger.error(f"获取股票代码时出错: {e}")
        return []

def get_date_range_inputs() -> tuple:
    """获取日期范围输入"""
    try:
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
        
        return start_date, end_date
        
    except Exception as e:
        logger.error(f"获取日期范围时出错: {e}")
        return datetime.now() - timedelta(days=365), datetime.now()

def get_benchmark_selection() -> str:
    """获取基准指数选择"""
    try:
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
        
        return benchmark
        
    except Exception as e:
        logger.error(f"获取基准指数选择时出错: {e}")
        return 'sh000300'

def manage_portfolio_state(symbols: list) -> None:
    """管理投资组合状态"""
    try:
        from stock_strategy import Portfolio
        
        # 检查是否需要创建新的投资组合
        if 'portfolio' not in st.session_state:
            st.session_state.portfolio = Portfolio()
        
        # 确保所有选中的股票都在投资组合中
        for symbol in symbols:
            if symbol not in st.session_state.portfolio.stocks:
                st.session_state.portfolio.add_stock(symbol)
                logger.info(f"添加了新股票: {symbol}")
        
        # 移除不在当前选择中的股票
        stocks_to_remove = []
        for symbol in st.session_state.portfolio.stocks:
            if symbol not in symbols:
                stocks_to_remove.append(symbol)
        
        for symbol in stocks_to_remove:
            st.session_state.portfolio.remove_stock(symbol)
            logger.info(f"移除了股票: {symbol}")
            
    except Exception as e:
        logger.error(f"管理投资组合状态时出错: {e}")
        st.error("管理投资组合状态时出错")

def render_portfolio_debug_info() -> None:
    """渲染投资组合调试信息"""
    try:
        with st.expander("当前投资组合信息", expanded=False):
            st.write(f"投资组合中的股票数量: {len(st.session_state.portfolio.stocks)}")
            for symbol, stock in st.session_state.portfolio.stocks.items():
                st.write(f"股票 {symbol}:")
                st.write(f"  买入策略数量: {stock.get_enabled_buy_strategie_number()}")
                st.write(f"  卖出策略数量: {stock.get_enabled_sell_strategie_number()}")
                
    except Exception as e:
        logger.error(f"渲染投资组合调试信息时出错: {e}")

def render_strategy_cards(symbols: list) -> None:
    """渲染策略卡片"""
    try:
        for symbol in symbols:
            render_stock_strategy_card(symbol, st.session_state.portfolio)
            
    except Exception as e:
        logger.error(f"渲染策略卡片时出错: {e}")
        st.error("渲染策略卡片时出错")

def run_backtest_and_display_results(symbols: list, start_date: datetime, end_date: datetime, benchmark: str) -> None:
    """运行回测并显示结果"""
    try:
        if not symbols:
            st.error("请输入至少一个股票代码")
            return
        
        if start_date >= end_date:
            st.error("开始日期必须早于结束日期")
            return
        
        # 验证输入参数
        if not validate_backtest_inputs(symbols, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')):
            st.error("输入参数验证失败")
            return
        
        # 显示进度
        with st.spinner("正在运行回测，请稍候..."):
            logger.info("开始运行回测")
            
            # 调试日志：打印投资组合信息
            logger.info(f"投资组合中的股票数量: {len(st.session_state.portfolio.stocks)}")
            
            for symbol, stock in st.session_state.portfolio.stocks.items():
                logger.info(f"股票 {symbol}: 初始投资={stock.initial_investment}, 最大投资={stock.max_investment}")
                logger.info(f"  买入策略数量: {stock.get_enabled_buy_strategie_number()}")
                logger.info(f"  卖出策略数量: {stock.get_enabled_sell_strategie_number()}")
            
            # 运行所有回测策略
            all_results = run_all_backtests(
                portfolio=st.session_state.portfolio,
                symbols=symbols,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                benchmark=benchmark
            )
            
            # 存储结果到session state
            st.session_state.results = all_results['custom_results']
            st.session_state.benchmark_results = all_results['benchmark_results']
            st.session_state.buy_hold_results = all_results['buy_hold_results']
            st.session_state.show_results = True
            
            # 设置基准名称
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
            
            st.success("✅ 回测完成！")
            logger.info("回测完成")
            
    except Exception as e:
        logger.error(f"运行回测时出错: {e}")
        st.error(f"运行回测时出错: {str(e)}")

def main():
    """主函数"""
    try:
        # 设置页面配置
        setup_page_config(WEB_CONFIG)
        
        # 应用自定义CSS
        apply_custom_css()
        
        # 标题和简介
        st.title("📈 股票回测系统")
        st.markdown("""<div style='margin-bottom: 1.5rem;'>一个专业的股票策略回测平台，支持多种交易策略和详细的绩效分析。</div>""", unsafe_allow_html=True)
        
        # 渲染侧边栏并获取参数
        symbols, start_date, end_date, benchmark = render_sidebar()
        
        # 管理投资组合状态
        if symbols:
            manage_portfolio_state(symbols)
            
            # 渲染投资组合调试信息
            render_portfolio_debug_info()
            
            # 渲染策略卡片
            render_strategy_cards(symbols)
            
            # 开始回测按钮
            if st.button("🚀 开始回测", type="primary"):
                run_backtest_and_display_results(symbols, start_date, end_date, benchmark)
            
            # 显示结果
            if hasattr(st.session_state, 'show_results') and st.session_state.show_results:
                display_results(st.session_state.results)
        else:
            st.info("请在侧边栏选择投资标的")
            
    except Exception as e:
        logger.error(f"主函数执行时出错: {e}")
        st.error("应用程序运行出错，请检查日志")

if __name__ == "__main__":
    main()

