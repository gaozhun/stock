# -*- coding: utf-8 -*-
"""
策略UI模块
包含策略相关的UI组件和逻辑
"""

import streamlit as st
from typing import Dict, Any
import logging
from stock_strategy import Portfolio, Strategy, SignalType

logger = logging.getLogger(__name__)

def open_strategy_modal(stock_code: str) -> bool:
    """打开添加策略的模态窗口"""
    try:
        modal_key = f"strategy_modal_{stock_code}"
        if modal_key not in st.session_state:
            st.session_state[modal_key] = False
        
        return st.button("➕ 添加策略", key=f"open_modal_{stock_code}")
    except Exception as e:
        logger.error(f"打开策略模态窗口时出错: {e}")
        return False

def render_strategy_params(stock_code: str, strategy_name: str, signal_type: SignalType) -> Dict[str, Any]:
    """渲染策略参数界面"""
    try:
        if strategy_name == 'time_based':
            return render_time_based_params(stock_code, signal_type)
        elif strategy_name == 'macd_pattern':
            return render_macd_pattern_params(stock_code, signal_type)
        elif strategy_name == 'ma_touch':
            return render_ma_touch_params(stock_code, signal_type)
        else:
            logger.warning(f"未知的策略类型: {strategy_name}")
            return {}
    except Exception as e:
        logger.error(f"渲染策略参数时出错: {e}")
        return {}

def render_time_based_params(stock_code: str, signal_type: SignalType) -> Dict[str, Any]:
    """渲染时间条件单策略参数"""
    try:
        strategy_params = {}
        
        col1, col2 = st.columns(2)
        with col1:
            frequency = st.selectbox(
                "交易频率",
                options=['daily', 'weekly', 'monthly'],
                format_func=lambda x: {'daily': '每日', 'weekly': '每周', 'monthly': '每月'}.get(x, x),
                key=f"frequency_{stock_code}_{signal_type.value}_time_based"
            )
            strategy_params['frequency'] = frequency
        
        with col2:
            if frequency in ['weekly', 'monthly']:
                trading_day = st.slider(
                    "第几个交易日", 
                    1, 10, 1,
                    help="选择每周/每月的第几个交易日进行交易",
                    key=f"trading_day_{stock_code}_{signal_type.value}_time_based"
                )
                strategy_params['trading_day'] = trading_day
        
        # 交易金额/数量设置
        col1, col2 = st.columns(2)
        with col1:
            trade_mode = st.radio(
                "交易模式",
                ["按金额", "按股数"],
                horizontal=True,
                key=f"trade_mode_{stock_code}_{signal_type.value}_time_based"
            )
        
        with col2:
            if trade_mode == "按金额":
                trade_amount = st.number_input(
                    "每次交易金额 (¥)", 
                    min_value=1, max_value=100000, 
                    value=10000, step=1000,
                    key=f"trade_amount_{stock_code}_{signal_type.value}_time_based"
                )
                strategy_params['trade_amount'] = trade_amount
                strategy_params['trade_shares'] = None
            else:
                trade_shares = st.number_input(
                    "每次交易股数", 
                    min_value=1, max_value=10000, 
                    value=1000, step=100,
                    key=f"trade_shares_{stock_code}_{signal_type.value}_time_based"
                )
                strategy_params['trade_shares'] = trade_shares
                strategy_params['trade_amount'] = None
        
        return strategy_params
    except Exception as e:
        logger.error(f"渲染时间条件单策略参数时出错: {e}")
        return {}

def render_macd_pattern_params(stock_code: str, signal_type: SignalType) -> Dict[str, Any]:
    """渲染MACD形态策略参数"""
    try:
        strategy_params = {}
        
        # MACD基础参数
        col1, col2, col3 = st.columns(3)
        with col1:
            fast_period = st.slider("快线周期", 5, 20, 12, key=f"fast_period_{stock_code}_{signal_type.value}_macd_pattern")
            strategy_params['fast_period'] = fast_period
        
        with col2:
            slow_period = st.slider("慢线周期", 20, 50, 26, key=f"slow_period_{stock_code}_{signal_type.value}_macd_pattern")
            strategy_params['slow_period'] = slow_period
        
        with col3:
            signal_period = st.slider("信号线周期", 5, 20, 9, key=f"signal_period_{stock_code}_{signal_type.value}_macd_pattern")
            strategy_params['signal_period'] = signal_period
        
        # 形态选择
        st.write(f"**{'买入' if signal_type == SignalType.BUY else '卖出'}形态选择**")
        patterns = []
        col1, col2, col3 = st.columns(3)
        
        if signal_type == SignalType.BUY:
            with col1:
                if st.checkbox("金叉", value=True, key=f"golden_cross_{stock_code}_{signal_type.value}_macd_pattern"):
                    patterns.append('golden_cross')
            
            with col2:
                if st.checkbox("二次金叉", value=False, key=f"double_golden_cross_{stock_code}_{signal_type.value}_macd_pattern"):
                    patterns.append('double_golden_cross')
            
            with col3:
                if st.checkbox("底背离", value=False, key=f"bullish_divergence_{stock_code}_{signal_type.value}_macd_pattern"):
                    patterns.append('bullish_divergence')
            
            strategy_params['buy_patterns'] = patterns
            strategy_params['sell_patterns'] = []
        else:
            with col1:
                if st.checkbox("死叉", value=True, key=f"death_cross_{stock_code}_{signal_type.value}_macd_pattern"):
                    patterns.append('death_cross')
            
            with col2:
                if st.checkbox("二次死叉", value=False, key=f"double_death_cross_{stock_code}_{signal_type.value}_macd_pattern"):
                    patterns.append('double_death_cross')
            
            with col3:
                if st.checkbox("顶背离", value=False, key=f"bearish_divergence_{stock_code}_{signal_type.value}_macd_pattern"):
                    patterns.append('bearish_divergence')
            
            strategy_params['buy_patterns'] = []
            strategy_params['sell_patterns'] = patterns
        
        # 检测参数
        col1, col2 = st.columns(2)
        with col1:
            divergence_lookback = st.slider("背离检测回望期", 10, 50, 20, key=f"divergence_lookback_{stock_code}_{signal_type.value}_macd_pattern")
            strategy_params['divergence_lookback'] = divergence_lookback
        
        with col2:
            double_cross_lookback = st.slider("二次交叉检测回望期", 5, 30, 10, key=f"double_cross_lookback_{stock_code}_{signal_type.value}_macd_pattern")
            strategy_params['double_cross_lookback'] = double_cross_lookback
        
        # 交易金额/数量设置
        col1, col2 = st.columns(2)
        with col1:
            trade_mode = st.radio(
                "交易模式",
                ["按金额", "按股数"],
                horizontal=True,
                key=f"trade_mode_{stock_code}_{signal_type.value}_macd_pattern"
            )
        
        with col2:
            if trade_mode == "按金额":
                trade_amount = st.number_input(
                    "每次交易金额 (¥)", 
                    min_value=1000, max_value=100000, 
                    value=10000, step=1000,
                    key=f"trade_amount_{stock_code}_{signal_type.value}_macd_pattern"
                )
                strategy_params['trade_amount'] = trade_amount
                strategy_params['trade_shares'] = None
            else:
                trade_shares = st.number_input(
                    "每次交易股数", 
                    min_value=100, max_value=10000, 
                    value=1000, step=100,
                    key=f"trade_shares_{stock_code}_{signal_type.value}_macd_pattern"
                )
                strategy_params['trade_shares'] = trade_shares
                strategy_params['trade_amount'] = None
        
        return strategy_params
    except Exception as e:
        logger.error(f"渲染MACD形态策略参数时出错: {e}")
        return {}

def render_ma_touch_params(stock_code: str, signal_type: SignalType) -> Dict[str, Any]:
    """渲染均线触碰策略参数"""
    try:
        strategy_params = {}
        
        # 均线周期选择
        st.write("**均线周期选择**")
        ma_periods = []
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.checkbox("5日均线", value=True, key=f"ma_5_{stock_code}_{signal_type.value}_ma_touch"):
                ma_periods.append(5)
        
        with col2:
            if st.checkbox("10日均线", value=True, key=f"ma_10_{stock_code}_{signal_type.value}_ma_touch"):
                ma_periods.append(10)
        
        with col3:
            if st.checkbox("20日均线", value=True, key=f"ma_20_{stock_code}_{signal_type.value}_ma_touch"):
                ma_periods.append(20)
        
        with col4:
            if st.checkbox("30日均线", value=False, key=f"ma_30_{stock_code}_{signal_type.value}_ma_touch"):
                ma_periods.append(30)
        
        with col5:
            if st.checkbox("60日均线", value=False, key=f"ma_60_{stock_code}_{signal_type.value}_ma_touch"):
                ma_periods.append(60)
        
        strategy_params['ma_periods'] = ma_periods
        
        # 触碰阈值
        touch_threshold = st.slider(
            "触碰阈值 (%)", 
            0.1, 5.0, 2.0, 0.1,
            help="价格与均线的距离百分比，越小越精确",
            key=f"touch_threshold_{stock_code}_{signal_type.value}_ma_touch"
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
                key=f"trade_mode_{stock_code}_{signal_type.value}_ma_touch"
            )
        
        with col2:
            if trade_mode == "按金额":
                trade_amount = st.number_input(
                    "每次交易金额 (¥)", 
                    min_value=1000, max_value=100000, 
                    value=10000, step=1000,
                    key=f"trade_amount_{stock_code}_{signal_type.value}_ma_touch"
                )
                strategy_params['trade_amount'] = trade_amount
                strategy_params['trade_shares'] = None
            else:
                trade_shares = st.number_input(
                    "每次交易股数", 
                    min_value=100, max_value=10000, 
                    value=1000, step=100,
                    key=f"trade_shares_{stock_code}_{signal_type.value}_ma_touch"
                )
                strategy_params['trade_shares'] = trade_shares
                strategy_params['trade_amount'] = None
        
        return strategy_params
    except Exception as e:
        logger.error(f"渲染均线触碰策略参数时出错: {e}")
        return {}

def render_stock_strategy_card(stock_code: str, portfolio: Portfolio) -> None:
    """渲染单只股票的策略卡片"""
    try:
        from ui_components import render_stock_card, render_strategy_card
        
        # 股票卡片标题
        render_stock_card(stock_code)
        
        # 创建两列布局
        col1, col2 = st.columns(2)
        
        # 左侧列 - 基本参数
        with col1:
            initial_investment = st.number_input(
                "初始持仓金额 (¥)",
                min_value=0,
                value=int(portfolio.stocks[stock_code].initial_investment),
                step=1000,
                key=f"initial_investment_{stock_code}"
            )
            portfolio.update_stock_investment(stock_code, initial_investment)
        
        # 右侧列 - 最大投资
        with col2:
            max_investment = st.number_input(
                "最大投资资金 (¥)",
                min_value=100,
                value=int(portfolio.stocks[stock_code].max_investment),
                step=1000,
                key=f"max_investment_{stock_code}"
            )
            portfolio.update_stock_max_investment(stock_code, max_investment)
        
        # 添加策略按钮
        if open_strategy_modal(stock_code):
            st.session_state[f"strategy_modal_{stock_code}"] = True
        
        # 如果模态窗口打开，显示策略添加界面
        if st.session_state.get(f"strategy_modal_{stock_code}", False):
            with st.expander("添加新策略", expanded=True):
                # 策略类型和信号类型选择
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    strategy_type = st.selectbox(
                        "选择策略类型",
                        options=['time_based', 'macd_pattern', 'ma_touch'],
                        format_func=lambda x: {'time_based': '时间条件单', 'macd_pattern': 'MACD形态', 'ma_touch': '均线触碰'}.get(x, x),
                        key=f"strategy_type_{stock_code}"
                    )
                
                with col_b:
                    signal_type = st.selectbox(
                        "信号类型",
                        options=[SignalType.BUY, SignalType.SELL],
                        format_func=lambda x: "买入" if x == SignalType.BUY else "卖出",
                        key=f"signal_type_{stock_code}"
                    )
                
                # 策略参数
                strategy_params = render_strategy_params(stock_code, strategy_type, signal_type)

                # 添加和取消按钮
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("✅ 确认添加", key=f"add_strategy_{stock_code}", use_container_width=True):
                        strategy = Strategy(
                            name=f"{strategy_type}_{signal_type.value}_{len(portfolio.stocks[stock_code].buy_strategies + portfolio.stocks[stock_code].sell_strategies)}",
                            type=strategy_type,
                            signal_type=signal_type,
                            params=strategy_params
                        )
                        portfolio.add_strategy(stock_code, strategy)
                        st.success(f"✅ 策略 {strategy.name} 添加成功！")
                        st.session_state[f"strategy_modal_{stock_code}"] = False
                        st.rerun()
                
                with col_b:
                    if st.button("❌ 取消", key=f"cancel_strategy_{stock_code}", use_container_width=True):
                        st.session_state[f"strategy_modal_{stock_code}"] = False
                        st.rerun()
        
        # 显示已添加的策略
        if stock_code in portfolio.stocks:
            stock = portfolio.stocks[stock_code]
            enabled_strategies = [s for s in stock.buy_strategies + stock.sell_strategies if s.enabled]
            
            if enabled_strategies:
                st.markdown("### 已添加策略")
                
                # 使用列布局显示策略卡片
                cols = st.columns(2)
                
                for i, strategy in enumerate(enabled_strategies):
                    with cols[i % 2]:
                        is_buy = strategy.signal_type == SignalType.BUY
                        render_strategy_card(
                            strategy_name=strategy.name,
                            strategy_type=strategy.type,
                            signal_type=strategy.signal_type.value,
                            params=strategy.params,
                            is_buy=is_buy
                        )
                        
                        # 删除策略按钮
                        if st.button("🗑️ 删除", key=f"delete_strategy_{stock_code}_{i}"):
                            strategy.enabled = False
                            st.success(f"✅ 策略 {strategy.name} 删除成功！")
                            st.rerun()
                            
    except Exception as e:
        logger.error(f"渲染股票策略卡片时出错: {e}")
        st.error(f"渲染股票 {stock_code} 的策略卡片时出错")
