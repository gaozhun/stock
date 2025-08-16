# -*- coding: utf-8 -*-
"""
Web应用界面
使用Streamlit构建的交互式回测界面
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_handler import DataHandler
from strategies import StrategyFactory
from backtest_engine import BacktestEngine
from performance import PerformanceAnalyzer
from visualization import Visualizer
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
def run_backtest_cached(symbols, strategy_name, strategy_params, 
                       start_date, end_date, initial_capital, benchmark):
    """缓存的回测函数"""
    strategy = StrategyFactory.create_strategy(strategy_name, strategy_params)
    engine = BacktestEngine(initial_capital=initial_capital)
    
    results = engine.run_backtest(
        symbols=symbols,
        strategy=strategy,
        start_date=start_date,
        end_date=end_date,
        benchmark=benchmark
    )
    
    return results


def main():
    """主函数"""
    # 标题
    st.title("📈 股票基金回测系统")
    st.markdown("---")
    
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
        
        # 初始资金
        initial_capital = st.number_input(
            "初始资金 ($)",
            value=100000,
            min_value=1000,
            step=1000
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
        
        # 策略选择
        st.subheader("策略设置")
        strategy_name = st.selectbox(
            "选择策略",
            options=['moving_average', 'ma_breakout', 'rsi', 'macd', 'dca', 'mean_reversion'],
            format_func=lambda x: {
                'moving_average': '移动平均',
                'ma_breakout': '均线突破',
                'rsi': 'RSI策略',
                'macd': 'MACD策略',
                'dca': '定投策略',
                'mean_reversion': '均值回归'
            }.get(x, x)
        )
        
        # 策略参数
        strategy_params = {}
        
        if strategy_name == 'moving_average':
            st.subheader("移动平均参数")
            strategy_params['short_window'] = st.slider("短期窗口", 5, 50, 20)
            strategy_params['long_window'] = st.slider("长期窗口", 20, 200, 60)
            
        elif strategy_name == 'ma_breakout':
            st.subheader("均线突破参数")
            strategy_params['ma_period'] = st.slider("均线周期", 5, 100, 20, help="移动平均线的天数，默认20日均线")
            strategy_params['threshold'] = st.slider("突破阈值(%)", 0.0, 10.0, 0.0, 0.1, help="价格需要超过均线多少百分比才触发信号") / 100.0
            
        elif strategy_name == 'rsi':
            st.subheader("RSI参数")
            strategy_params['rsi_period'] = st.slider("RSI周期", 5, 30, 14)
            strategy_params['oversold'] = st.slider("超卖线", 10, 40, 30)
            strategy_params['overbought'] = st.slider("超买线", 60, 90, 70)
            
        elif strategy_name == 'dca':
            st.subheader("定投策略参数")
            
            # 定投频率
            strategy_params['frequency'] = st.selectbox(
                "定投频率",
                options=['daily', 'weekly', 'monthly'],
                format_func=lambda x: {'daily': '每日', 'weekly': '每周', 'monthly': '每月'}.get(x, x)
            )
            
            # 交易日选择
            if strategy_params['frequency'] in ['monthly', 'weekly']:
                strategy_params['trading_day'] = st.slider(
                    "第几个交易日", 
                    1, 10, 1,
                    help="选择每月/每周的第几个交易日进行定投"
                )
            
            # 定投金额
            strategy_params['investment_amount'] = st.number_input(
                "每次定投金额 (¥)", 
                min_value=1000, max_value=100000, 
                value=10000, step=1000,
                help="每次定投投入的资金金额"
            )
            
            # 持仓增量
            strategy_params['position_increment'] = st.slider(
                "每次持仓增量", 
                0.05, 0.5, 0.1, 0.05,
                help="每次定投后持仓比例的增加量"
            )
            
            # 最大持仓
            strategy_params['max_position'] = st.slider(
                "最大持仓比例", 
                0.5, 1.0, 1.0, 0.1,
                help="定投策略的最大持仓比例"
            )
            
        elif strategy_name == 'mean_reversion':
            st.subheader("均值回归参数")
            strategy_params['lookback_period'] = st.slider("回望期", 10, 50, 20)
            strategy_params['entry_threshold'] = st.slider("入场阈值", 1.0, 3.0, 2.0)
    
    # 主界面
    if st.button("🚀 开始回测", type="primary"):
        if not symbols:
            st.error("请输入至少一个股票代码")
            return
        
        if start_date >= end_date:
            st.error("开始日期必须早于结束日期")
            return
        
        # 显示进度
        with st.spinner("正在运行回测，请稍候..."):
            try:
                # 运行回测
                results = run_backtest_cached(
                    symbols=symbols,
                    strategy_name=strategy_name,
                    strategy_params=strategy_params,
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d'),
                    initial_capital=initial_capital,
                    benchmark=benchmark
                )
                
                # 存储结果到session state
                st.session_state.results = results
                st.session_state.show_results = True
                
                st.success("✅ 回测完成！")
                
            except Exception as e:
                st.error(f"❌ 回测失败: {str(e)}")
                return
    
    # 显示结果
    if hasattr(st.session_state, 'show_results') and st.session_state.show_results:
        display_results(st.session_state.results)


def display_results(results):
    """显示回测结果"""
    
    # 计算性能指标
    analyzer = PerformanceAnalyzer()
    metrics = analyzer.calculate_performance_metrics(
        results['returns'],
        results.get('benchmark_returns')
    )
    
    # 关键指标卡片
    st.header("📊 关键指标")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        final_value = results['portfolio_value'].iloc[-1]
        total_return = metrics.get('total_return', 0)
        st.metric(
            label="最终价值",
            value=f"¥{final_value:,.0f}",
            delta=f"{total_return:.1%}"
        )
    
    with col2:
        annual_return = metrics.get('annualized_return', 0)
        st.metric(
            label="年化收益率",
            value=f"{annual_return:.2%}",
            delta=None
        )
    
    with col3:
        sharpe_ratio = metrics.get('sharpe_ratio', 0)
        st.metric(
            label="夏普比率",
            value=f"{sharpe_ratio:.2f}",
            delta=None
        )
    
    with col4:
        max_drawdown = metrics.get('max_drawdown', 0)
        st.metric(
            label="最大回撤",
            value=f"{max_drawdown:.2%}",
            delta=None
        )
    
    # 图表展示
    st.header("📈 表现图表")
    
    tab1, tab2, tab3, tab4 = st.tabs(["投资组合表现", "收益率分析", "风险分析", "交易信号"])
    
    with tab1:
        st.subheader("投资组合价值走势")
        
        # 创建交互式图表
        fig = go.Figure()
        
        # 投资组合价值（策略）
        fig.add_trace(go.Scatter(
            x=results['portfolio_value'].index,
            y=results['portfolio_value'].values,
            mode='lines',
            name='当前策略',
            line=dict(color='blue', width=3),
            hovertemplate='日期: %{x}<br>策略价值: ¥%{y:,.0f}<extra></extra>'
        ))
        
        # 买入持有基准对比（不使用策略的曲线）
        if 'price_data' in results and len(results['symbols']) == 1:
            symbol = results['symbols'][0]
            if symbol in results['price_data'].columns:
                # 计算买入持有价值
                first_price = results['price_data'][symbol].iloc[0]
                buy_hold_shares = results['initial_capital'] / first_price
                buy_hold_value = results['price_data'][symbol] * buy_hold_shares
                
                fig.add_trace(go.Scatter(
                    x=buy_hold_value.index,
                    y=buy_hold_value.values,
                    mode='lines',
                    name='一直持有收益',
                    line=dict(color='gray', width=2, dash='dot'),
                    hovertemplate='日期: %{x}<br>一直持有: ¥%{y:,.0f}<extra></extra>'
                ))
        
        # 基准指数对比
        if results.get('benchmark_returns') is not None:
            benchmark_value = (1 + results['benchmark_returns']).cumprod() * results['initial_capital']
            benchmark_name = results.get("benchmark", "")
            # 转换基准指数名称为中文
            benchmark_names = {
                'sh000300': '沪深300',
                'sh000001': '上证指数',
                'sz399001': '深证成指',
                'sz399006': '创业板指'
            }
            display_name = benchmark_names.get(benchmark_name, benchmark_name)
            
            fig.add_trace(go.Scatter(
                x=benchmark_value.index,
                y=benchmark_value.values,
                mode='lines',
                name=display_name,
                line=dict(color='red', width=2, dash='dash'),
                hovertemplate='日期: %{x}<br>基准价值: ¥%{y:,.0f}<extra></extra>'
            ))
        
        # 添加买卖点标记
        if 'signals' in results and 'price_data' in results and len(results['symbols']) == 1:
            symbol = results['symbols'][0]
            signals = results['signals']
            price_data = results['price_data'][symbol]
            
            # 买入信号
            buy_signals = signals[signals == 1]
            if len(buy_signals) > 0:
                buy_prices = price_data.loc[buy_signals.index]
                # 计算对应的投资组合价值
                buy_portfolio_values = results['portfolio_value'].loc[buy_signals.index]
                fig.add_trace(go.Scatter(
                    x=buy_signals.index,
                    y=buy_portfolio_values.values,
                    mode='markers',
                    name=f'买入信号 ({len(buy_signals)})',
                    marker=dict(
                        symbol='triangle-up',
                        color='green',
                        size=12,
                        line=dict(color='darkgreen', width=2)
                    ),
                    hovertemplate='买入<br>日期: %{x}<br>投资组合价值: ¥%{y:,.0f}<extra></extra>',
                    showlegend=True
                ))
            
            # 卖出信号
            sell_signals = signals[signals == -1]
            if len(sell_signals) > 0:
                sell_prices = price_data.loc[sell_signals.index]
                # 计算对应的投资组合价值
                sell_portfolio_values = results['portfolio_value'].loc[sell_signals.index]
                fig.add_trace(go.Scatter(
                    x=sell_signals.index,
                    y=sell_portfolio_values.values,
                    mode='markers',
                    name=f'卖出信号 ({len(sell_signals)})',
                    marker=dict(
                        symbol='triangle-down',
                        color='red',
                        size=12,
                        line=dict(color='darkred', width=2)
                    ),
                    hovertemplate='卖出<br>日期: %{x}<br>投资组合价值: ¥%{y:,.0f}<extra></extra>',
                    showlegend=True
                ))
        
        # 设置x轴日期格式为中文
        fig.update_xaxes(
            tickformat='%Y年%m月%d日',
            tickangle=45
        )
        
        fig.update_layout(
            title="投资组合表现对比 (含买卖点)",
            xaxis_title="日期",
            yaxis_title="价值 (¥)",
            hovermode='x unified',
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 显示交易统计
        if 'signals' in results:
            signals = results['signals']
            buy_count = (signals == 1).sum()
            sell_count = (signals == -1).sum()
            hold_count = (signals == 0).sum()
            
            # 计算策略vs买入持有的表现
            if 'price_data' in results and len(results['symbols']) == 1:
                symbol = results['symbols'][0]
                if symbol in results['price_data'].columns:
                    first_price = results['price_data'][symbol].iloc[0]
                    last_price = results['price_data'][symbol].iloc[-1]
                    buy_hold_shares = results['initial_capital'] / first_price
                    buy_hold_final = last_price * buy_hold_shares
                    buy_hold_return = (buy_hold_final / results['initial_capital'] - 1) * 100
                    strategy_return = (final_value / results['initial_capital'] - 1) * 100
                    excess_return = strategy_return - buy_hold_return
                    
                    st.info(f"""
                    📊 **交易统计**: 买入信号 {buy_count} 次，卖出信号 {sell_count} 次，持有 {hold_count} 次
                    
                    💰 **收益对比**: 当前策略 {strategy_return:.2f}%，一直持有 {buy_hold_return:.2f}%，超额收益 {excess_return:+.2f}%
                    """)
            else:
                st.info(f"📊 **交易统计**: 买入信号 {buy_count} 次，卖出信号 {sell_count} 次，持有 {hold_count} 次")
    
    with tab2:
        st.subheader("收益率分布")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 日收益率直方图
            fig_hist = px.histogram(
                x=results['returns'] * 100,
                nbins=50,
                title="日收益率分布",
                labels={'x': '日收益率 (%)', 'y': '频数'}
            )
            fig_hist.add_vline(
                x=results['returns'].mean() * 100,
                line_dash="dash",
                line_color="red",
                annotation_text="平均值"
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            # 累积收益率
            cumulative_returns = (results['portfolio_value'] / results['initial_capital'] - 1) * 100
            
            fig_cum = go.Figure()
            fig_cum.add_trace(go.Scatter(
                x=cumulative_returns.index,
                y=cumulative_returns.values,
                mode='lines',
                fill='tozeroy',
                name='累积收益率'
            ))
            
                    # 设置x轴日期格式为中文
        fig_cum.update_xaxes(
            tickformat='%Y年%m月%d日',
            tickangle=45
        )
        
        fig_cum.update_layout(
            title="累积收益率",
            xaxis_title="日期",
            yaxis_title="累积收益率 (%)"
        )
        
        st.plotly_chart(fig_cum, use_container_width=True)
    
    with tab3:
        st.subheader("风险分析")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 回撤图
            portfolio_normalized = results['portfolio_value'] / results['initial_capital']
            running_max = portfolio_normalized.expanding().max()
            drawdown = (portfolio_normalized - running_max) / running_max * 100
            
            fig_dd = go.Figure()
            fig_dd.add_trace(go.Scatter(
                x=drawdown.index,
                y=drawdown.values,
                mode='lines',
                fill='tozeroy',
                name='回撤',
                fillcolor='rgba(255,0,0,0.3)'
            ))
            
            # 设置x轴日期格式为中文
            fig_dd.update_xaxes(
                tickformat='%Y年%m月%d日',
                tickangle=45
            )
            
            fig_dd.update_layout(
                title="资产回撤",
                xaxis_title="日期",
                yaxis_title="回撤 (%)"
            )
            
            st.plotly_chart(fig_dd, use_container_width=True)
        
        with col2:
            # 滚动波动率
            rolling_vol = results['returns'].rolling(window=30).std() * np.sqrt(252) * 100
            
            fig_vol = go.Figure()
            fig_vol.add_trace(go.Scatter(
                x=rolling_vol.index,
                y=rolling_vol.values,
                mode='lines',
                name='滚动波动率'
            ))
            
            # 设置x轴日期格式为中文
            fig_vol.update_xaxes(
                tickformat='%Y年%m月%d日',
                tickangle=45
            )
            
            fig_vol.update_layout(
                title="30日滚动波动率",
                xaxis_title="日期",
                yaxis_title="年化波动率 (%)"
            )
            
            st.plotly_chart(fig_vol, use_container_width=True)
    
    with tab4:
        st.subheader("交易信号分析")
        
        if len(results['symbols']) == 1 and 'price_data' in results:
            symbol = results['symbols'][0]
            price_data = results['price_data'][symbol]
            signals = results.get('signals', pd.Series())
            
            fig_signals = go.Figure()
            
            # 价格线
            fig_signals.add_trace(go.Scatter(
                x=price_data.index,
                y=price_data.values,
                mode='lines',
                name='价格',
                line=dict(color='blue')
            ))
            
            # 买入信号
            buy_signals = signals[signals == 1]
            if len(buy_signals) > 0:
                buy_prices = price_data.loc[buy_signals.index]
                fig_signals.add_trace(go.Scatter(
                    x=buy_signals.index,
                    y=buy_prices.values,
                    mode='markers',
                    name='买入信号',
                    marker=dict(color='green', size=10, symbol='triangle-up')
                ))
            
            # 卖出信号
            sell_signals = signals[signals == -1]
            if len(sell_signals) > 0:
                sell_prices = price_data.loc[sell_signals.index]
                fig_signals.add_trace(go.Scatter(
                    x=sell_signals.index,
                    y=sell_prices.values,
                    mode='markers',
                    name='卖出信号',
                    marker=dict(color='red', size=10, symbol='triangle-down')
                ))
            
            # 设置x轴日期格式为中文
            fig_signals.update_xaxes(
                tickformat='%Y年%m月%d日',
                tickangle=45
            )
            
            fig_signals.update_layout(
                title=f"{symbol} 价格走势与交易信号",
                xaxis_title="日期",
                yaxis_title="价格 (¥)"
            )
            
            st.plotly_chart(fig_signals, use_container_width=True)
    
    # 详细性能报告
    st.header("📋 详细性能报告")
    
    with st.expander("查看完整报告", expanded=False):
        report = analyzer.generate_performance_report(results)
        st.text(report)
    
    # 交易记录
    if results.get('trades'):
        st.header("💼 交易记录")
        
        trades_df = pd.DataFrame(results['trades'])
        if not trades_df.empty:
            # 格式化交易记录，全部中文化
            trades_df['交易日期'] = pd.to_datetime(trades_df['date']).dt.strftime('%Y年%m月%d日')
            trades_df['股票代码'] = trades_df['symbol']
            trades_df['交易类型'] = trades_df['type'].map({'buy': '买入', 'sell': '卖出'})
            trades_df['交易股数'] = trades_df['shares'].round(2)
            trades_df['交易价格'] = trades_df['price'].apply(lambda x: f"¥{x:.2f}")
            trades_df['交易金额'] = trades_df['value'].apply(lambda x: f"¥{x:,.2f}")
            trades_df['手续费'] = trades_df['commission'].apply(lambda x: f"¥{x:.2f}")
            
            # 选择要显示的列
            display_cols = ['交易日期', '股票代码', '交易类型', '交易股数', '交易价格', '交易金额', '手续费']
            display_df = trades_df[display_cols].copy()
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
            
            # 交易汇总统计
            buy_trades = trades_df[trades_df['type'] == 'buy']
            sell_trades = trades_df[trades_df['type'] == 'sell']
            total_commission = trades_df['commission'].sum()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("买入次数", len(buy_trades))
            with col2:
                st.metric("卖出次数", len(sell_trades))
            with col3:
                st.metric("总手续费", f"¥{total_commission:.2f}")
            
            # 下载按钮
            csv = display_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 下载交易记录 (CSV)",
                data=csv,
                file_name="交易记录.csv",
                mime="text/csv"
            )


def sidebar_info():
    """侧边栏信息"""
    with st.sidebar:
        st.markdown("---")
        st.info(
            "💡 **使用提示**\n\n"
            "1. 选择股票代码和时间范围\n"
            "2. 选择合适的交易策略\n"
            "3. 调整策略参数\n"
            "4. 点击开始回测按钮\n"
            "5. 查看结果和分析报告"
        )
        
        st.warning(
            "⚠️ **免责声明**\n\n"
            "本系统仅用于学习和研究目的，"
            "不构成任何投资建议。"
            "投资有风险，入市需谨慎。"
        )


if __name__ == "__main__":
    sidebar_info()
    main()
