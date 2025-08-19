# -*- coding: utf-8 -*-
"""
结果显示模块
包含所有结果显示相关的函数和逻辑
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Dict, Any, List
import logging

from utils import format_currency, format_percentage, calculate_max_drawdown

logger = logging.getLogger(__name__)

def create_portfolio_value_chart(portfolio_value_df: pd.DataFrame, results: Dict[str, Any]) -> go.Figure:
    """创建投资组合价值变化图"""
    try:
        fig = go.Figure()
        
        # 修改日期格式
        date_labels = portfolio_value_df.index.strftime('%Y.%m.%d')
        
        # 添加投资组合价值曲线
        fig.add_trace(go.Scatter(
            x=date_labels,
            y=portfolio_value_df['投资组合价值'],
            mode='lines',
            name='投资组合价值',
            line=dict(color='#1f77b4', width=2)
        ))
        
        # 添加买入并持有策略曲线
        if '买入并持有' in portfolio_value_df.columns:
            fig.add_trace(go.Scatter(
                x=date_labels,
                y=portfolio_value_df['买入并持有'],
                mode='lines',
                name='买入并持有',
                line=dict(color='#2ca02c', width=2)
            ))
        
        # 添加基准指数曲线
        benchmark_name = st.session_state.get('benchmark_name', '基准指数')

        fig.add_trace(go.Scatter(
            x=date_labels,
            y=portfolio_value_df[benchmark_name],
            mode='lines',
            name=benchmark_name,
            line=dict(color='#ff7f0e', width=2)
        ))
        
        # 添加买入卖出点标记
        if results.get('trades'):
            add_trade_markers(fig, results['trades'], portfolio_value_df)
        
        # 添加收益率曲线到第二个Y轴（只用于计算刻度范围）
        if '投资组合收益率' in portfolio_value_df.columns:
            fig.add_trace(go.Scatter(
                x=date_labels,
                y=portfolio_value_df['投资组合收益率'],
                mode='lines',
                name='投资组合收益率(%)',
                line=dict(color='rgba(0,0,0,0)', width=0),  # 透明线条，实际上是隐藏的
                yaxis='y2',
                showlegend=False  # 不在图例中显示
            ))
        
        # 添加买入并持有收益率曲线（只用于计算刻度范围）
        if '买入并持有收益率' in portfolio_value_df.columns:
            fig.add_trace(go.Scatter(
                x=date_labels,
                y=portfolio_value_df['买入并持有收益率'],
                mode='lines',
                name='买入并持有收益率(%)',
                line=dict(color='rgba(0,0,0,0)', width=0),  # 透明线条，实际上是隐藏的
                yaxis='y2',
                showlegend=False  # 不在图例中显示
            ))
        
        # 添加基准指数收益率曲线（如果有）（只用于计算刻度范围）
        benchmark_returns_columns = [col for col in portfolio_value_df.columns if benchmark_name in col and '收益率' in col]
        for col in benchmark_returns_columns:
            fig.add_trace(go.Scatter(
                x=date_labels,
                y=portfolio_value_df[col],
                mode='lines',
                name=f'{col}',
                line=dict(color='rgba(0,0,0,0)', width=0),  # 透明线条，实际上是隐藏的
                yaxis='y2',
                showlegend=False  # 不在图例中显示
            ))
        
        # 设置图表布局
        fig.update_layout(
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
        
        return fig
    except Exception as e:
        logger.error(f"创建投资组合价值变化图时出错: {e}")
        return go.Figure()

def create_drawdown_chart(portfolio_value_df: pd.DataFrame, results: Dict[str, Any]) -> go.Figure:
    """创建回撤分析图"""
    try:
        fig = go.Figure()
        
        # 计算收益率和回撤
        initial_value = portfolio_value_df['投资组合价值'].iloc[0]
        returns_pct = (portfolio_value_df['投资组合价值'] / initial_value - 1) * 100
        
        # 添加收益率曲线
        fig.add_trace(go.Scatter(
            x=portfolio_value_df.index.strftime('%Y.%m.%d'),
            y=returns_pct.values,
            mode='lines',
            name='收益率(%)',
            line=dict(color='#1f77b4', width=2)
        ))
        
        # 计算最大回撤信息
        max_dd_info = calculate_max_drawdown(returns_pct / 100 + 1)
        
        if max_dd_info['max_drawdown_date']:
            # 添加最大回撤区域标记
            add_drawdown_annotations(fig, max_dd_info, returns_pct)
            
            # 添加最大回撤区域填充 (红色)
            max_dd_idx = max_dd_info['max_drawdown_date']
            last_peak_idx = max_dd_info['peak_date']
            
            if max_dd_idx and last_peak_idx:
                # 获取最大回撤区间的所有数据点
                drawdown_dates = portfolio_value_df.index[(portfolio_value_df.index >= last_peak_idx) & (portfolio_value_df.index <= max_dd_idx)]
                drawdown_returns = returns_pct.loc[drawdown_dates]
                
                # 添加最大回撤区域的填充
                fig.add_trace(go.Scatter(
                    x=drawdown_dates.strftime('%Y.%m.%d'),
                    y=drawdown_returns,
                    fill='tozeroy',
                    fillcolor='rgba(255,0,0,0.15)',
                    line=dict(color='rgba(255,0,0,0)'),
                    name='最大回撤区域',
                    showlegend=True
                ))
                
                # 如果已恢复，添加恢复区域和标记
                recovery_idx = max_dd_info['recovery_date']
                if recovery_idx:
                    # 获取恢复点的收益率
                    recovery_return = returns_pct.loc[recovery_idx]
                    
                    # 添加恢复点标记
                    fig.add_trace(go.Scatter(
                        x=[recovery_idx.strftime('%Y.%m.%d')],
                        y=[recovery_return],
                        mode='markers',
                        name='回撤恢复点',
                        marker=dict(color='green', size=8, symbol='triangle-up'),
                        text=[f'恢复: {recovery_idx.strftime("%Y-%m-%d")}\n收益率: {recovery_return:.2f}%\n恢复天数: {max_dd_info.get("recovery_days", 0)}天'],
                        hoverinfo='text'
                    ))
                    
                    # 获取恢复区间的所有数据点
                    recovery_dates = portfolio_value_df.index[(portfolio_value_df.index >= max_dd_idx) & (portfolio_value_df.index <= recovery_idx)]
                    recovery_returns = returns_pct.loc[recovery_dates]
                    
                    # 添加恢复区域的填充
                    fig.add_trace(go.Scatter(
                        x=recovery_dates.strftime('%Y.%m.%d'),
                        y=recovery_returns,
                        fill='tozeroy',
                        fillcolor='rgba(0,255,0,0.15)',
                        line=dict(color='rgba(0,255,0,0)'),
                        name='回撤恢复区域',
                        showlegend=True
                    ))
                else:
                    # 如果未恢复，显示正在恢复的区域和天数
                    # 计算当前恢复天数
                    current_recovery_days = len(portfolio_value_df.loc[max_dd_idx:].index)
                    
                    # 获取最后一天的收益率
                    last_date = portfolio_value_df.index[-1]
                    last_return = returns_pct.iloc[-1]
                    
                    # 获取恢复区间的所有数据点
                    recovery_dates = portfolio_value_df.index[(portfolio_value_df.index >= max_dd_idx) & (portfolio_value_df.index <= last_date)]
                    recovery_returns = returns_pct.loc[recovery_dates]
                    
                    # 添加正在恢复区域的填充
                    fig.add_trace(go.Scatter(
                        x=recovery_dates.strftime('%Y.%m.%d'),
                        y=recovery_returns,
                        fill='tozeroy',
                        fillcolor='rgba(255,255,0,0.15)',
                        line=dict(color='rgba(255,255,0,0)'),
                        name='正在恢复区域',
                        showlegend=True
                    ))
        
        # 设置图表布局
        fig.update_layout(
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
        
        return fig
    except Exception as e:
        logger.error(f"创建回撤分析图时出错: {e}")
        return go.Figure()

def add_trade_markers(fig: go.Figure, trades: List[Dict], portfolio_value_df: pd.DataFrame) -> None:
    """添加交易标记点"""
    try:
        trades_df = pd.DataFrame(trades)
        
        if len(trades_df.columns) == 7:
            trades_df.columns = ['日期', '股票代码', '交易股数', '价格', '交易金额', '手续费', '类型']
            trades_df['日期'] = pd.to_datetime(trades_df['日期'])
            
            # 买入点
            buy_trades = trades_df[trades_df['类型'] == 'buy']
            if not buy_trades.empty:
                buy_dates = buy_trades['日期'].dt.strftime('%Y.%m.%d').tolist()
                buy_values = []
                buy_texts = []
                
                for date in buy_trades['日期']:
                    if date in portfolio_value_df.index:
                        buy_values.append(portfolio_value_df.loc[date, '投资组合价值'])
                        trade_info = buy_trades[buy_trades['日期'] == date].iloc[0]
                        buy_texts.append(
                            f"买入: {trade_info['股票代码']}<br>" +
                            f"股数: {trade_info['交易股数']:.0f}<br>" +
                            f"价格: ¥{trade_info['价格']:.2f}<br>" +
                            f"金额: ¥{trade_info['交易金额']:.2f}"
                        )
                
                if buy_values:
                    fig.add_trace(go.Scatter(
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
                sell_dates = sell_trades['日期'].dt.strftime('%Y.%m.%d').tolist()
                sell_values = []
                sell_texts = []
                
                for date in sell_trades['日期']:
                    if date in portfolio_value_df.index:
                        sell_values.append(portfolio_value_df.loc[date, '投资组合价值'])
                        trade_info = sell_trades[sell_trades['日期'] == date].iloc[0]
                        sell_texts.append(
                            f"卖出: {trade_info['股票代码']}<br>" +
                            f"股数: {abs(trade_info['交易股数']):.0f}<br>" +
                            f"价格: ¥{trade_info['价格']:.2f}<br>" +
                            f"金额: ¥{abs(trade_info['交易金额']):.2f}"
                        )
                
                if sell_values:
                    fig.add_trace(go.Scatter(
                        x=sell_dates,
                        y=sell_values,
                        mode='markers',
                        name='卖出点',
                        marker=dict(color='red', size=10, symbol='triangle-down'),
                        text=sell_texts,
                        hoverinfo='text'
                    ))
    except Exception as e:
        logger.error(f"添加交易标记点时出错: {e}")

def add_drawdown_annotations(fig: go.Figure, max_dd_info: Dict[str, Any], returns_pct: pd.Series) -> None:
    """添加回撤标注"""
    try:
        max_dd_idx = max_dd_info['max_drawdown_date']
        last_peak_idx = max_dd_info['peak_date']
        recovery_idx = max_dd_info['recovery_date']
        
        if max_dd_idx and last_peak_idx:
            # 获取峰值和谷值的收益率
            peak_return = returns_pct.loc[last_peak_idx]
            bottom_return = returns_pct.loc[max_dd_idx]
            
            # 添加峰值和谷值标记点
            fig.add_trace(go.Scatter(
                x=[last_peak_idx.strftime('%Y.%m.%d'), max_dd_idx.strftime('%Y.%m.%d')],
                y=[peak_return, bottom_return],
                mode='markers',
                name='最大回撤区间',
                marker=dict(color='red', size=8, symbol=['triangle-down', 'triangle-down']),
                text=[f'峰值: {last_peak_idx.strftime("%Y-%m-%d")}\n收益率: {peak_return:.2f}%', 
                      f'谷值: {max_dd_idx.strftime("%Y-%m-%d")}\n收益率: {bottom_return:.2f}%\n最大回撤: {max_dd_info["max_drawdown"]:.2%}'],
                hoverinfo='text'
            ))
            
            # 添加最大回撤标注
            fig.add_annotation(
                x=max_dd_idx.strftime('%Y.%m.%d'),
                y=bottom_return,
                text=f'最大回撤: {max_dd_info["max_drawdown"]:.2%}',
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
    except Exception as e:
        logger.error(f"添加回撤标注时出错: {e}")

def display_results(results: Dict[str, Any]) -> None:
    """显示回测结果"""
    try:
        st.header("📊 回测结果")
        
        # 显示图表部分
        display_portfolio_charts(results)
        
        # 收益分析部分
        display_return_analysis(results)
        
        # 策略对比分析
        if st.session_state.get('benchmark_results') and st.session_state.get('buy_hold_results'):
            display_strategy_comparison(results)
        
        # 显示交易记录
        display_trade_records(results)
        
    except Exception as e:
        logger.error(f"显示结果时出错: {e}")
        st.error("显示结果时出错")

def display_portfolio_charts(results: Dict[str, Any]) -> None:
    """显示投资组合图表"""
    try:
        st.subheader("📈 投资组合价值变化")
        
        if not results['portfolio_value'].empty:
            # 创建数据框
            portfolio_value_df = pd.DataFrame(results['portfolio_value'], columns=['投资组合价值'])
            
            # 调试信息
            logger.info(f"原始投资组合数据形状: {portfolio_value_df.shape}")
            logger.info(f"原始投资组合数据列: {list(portfolio_value_df.columns)}")
            
            # 添加对比数据
            add_comparison_data(portfolio_value_df, results)
            
            # 调试信息
            logger.info(f"添加对比数据后，数据框列: {list(portfolio_value_df.columns)}")
            logger.info(f"数据框形状: {portfolio_value_df.shape}")
            
            
            # 创建Tab页面分别显示价值变化图和回撤分析图
            tab1, tab2 = st.tabs(['价值变化', '回撤分析'])
            
            with tab1:
                fig_value = create_portfolio_value_chart(portfolio_value_df, results)
                st.plotly_chart(fig_value, use_container_width=True)
            
            with tab2:
                fig_drawdown = create_drawdown_chart(portfolio_value_df, results)
                st.plotly_chart(fig_drawdown, use_container_width=True)
        else:
            st.write("无投资组合价值变化数据")
            
    except Exception as e:
        logger.error(f"显示投资组合图表时出错: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        st.error("显示投资组合图表时出错")

def add_comparison_data(portfolio_value_df: pd.DataFrame, results: Dict[str, Any]) -> None:
    """添加对比数据到数据框"""
    try:
        # 使用独立运行的买入并持有策略结果
        if st.session_state.get('buy_hold_results'):
            buy_hold_results = st.session_state.buy_hold_results
            buy_hold_values = buy_hold_results['portfolio_value']
            
            common_index = portfolio_value_df.index.intersection(buy_hold_values.index)
            if not common_index.empty:
                portfolio_value_df['买入并持有'] = buy_hold_values.loc[common_index]
                logger.info(f"成功添加买入并持有策略数据，数据点数量: {len(common_index)}")
        
        # 使用独立运行的基准指数结果
        if st.session_state.get('benchmark_results'):
            benchmark_results = st.session_state.benchmark_results
            benchmark_values = benchmark_results['portfolio_value']
            
            # 获取基准名称
            benchmark_name = st.session_state.get('benchmark_name', '基准指数')
            logger.info(f"正在添加基准指数数据: {benchmark_name}")
            
            common_index = portfolio_value_df.index.intersection(benchmark_values.index)
            if not common_index.empty:
                portfolio_value_df[benchmark_name] = benchmark_values.loc[common_index]
                logger.info(f"成功添加基准指数数据，数据点数量: {len(common_index)}")
            else:
                logger.warning(f"基准指数数据索引不匹配，portfolio索引: {len(portfolio_value_df.index)}, benchmark索引: {len(benchmark_values.index)}")
        else:
            logger.warning("未找到基准指数回测结果")
        
        # 计算收益率
        calculate_returns_columns(portfolio_value_df)
        
        # 调试信息
        logger.info(f"对比数据添加完成，当前数据框列: {list(portfolio_value_df.columns)}")
        logger.info(f"数据框形状: {portfolio_value_df.shape}")
        
    except Exception as e:
        logger.error(f"添加对比数据时出错: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")

def calculate_returns_columns(portfolio_value_df: pd.DataFrame) -> None:
    """计算收益率列"""
    try:
        initial_value = portfolio_value_df['投资组合价值'].iloc[0]
        portfolio_value_df['投资组合收益率'] = (portfolio_value_df['投资组合价值'] / initial_value - 1) * 100
        
        if '买入并持有' in portfolio_value_df.columns:
            buy_hold_initial = portfolio_value_df['买入并持有'].iloc[0]
            portfolio_value_df['买入并持有收益率'] = (portfolio_value_df['买入并持有'] / buy_hold_initial - 1) * 100
        
        benchmark_name = st.session_state.get('benchmark_name', '基准指数')
        benchmark_initial = portfolio_value_df[benchmark_name].iloc[0]
        portfolio_value_df[f'{benchmark_name}收益率'] = (portfolio_value_df[benchmark_name] / benchmark_initial - 1) * 100
            
    except Exception as e:
        logger.error(f"计算收益率列时出错: {e}")

def display_return_analysis(results: Dict[str, Any]) -> None:
    """显示收益分析"""
    try:
        st.subheader("📰 收益分析")
        
        # 创建两列布局
        col1, col2 = st.columns(2)
        
        # 第一列显示基本收益信息
        with col1:
            st.write(f"总初始资金: {format_currency(results['initial_capital'])}")
            st.write(f"最终资产价值: {format_currency(results['final_value'])}")
            st.write(f"总收益率: {format_percentage(results['total_return'])}")
            
            if 'annualized_return' in results:
                st.write(f"年化收益率: {format_percentage(results['annualized_return'])}")
        
        # 第二列显示风险指标
        with col2:
            if 'max_drawdown' in results:
                st.write(f"最大回撤: {format_percentage(results['max_drawdown'])}")
            
            if 'sharpe_ratio' in results:
                st.write(f"夏普比率: {results['sharpe_ratio']:.2f}")
            
            if 'volatility' in results:
                st.write(f"年化波动率: {format_percentage(results['volatility'])}")
            
            if 'max_drawdown_recovery_days' in results:
                st.write(f"最大回撤修复天数: {results['max_drawdown_recovery_days']} 天")
                
    except Exception as e:
        logger.error(f"显示收益分析时出错: {e}")
        st.error("显示收益分析时出错")

def display_strategy_comparison(results: Dict[str, Any]) -> None:
    """显示策略对比分析"""
    try:
        st.subheader("📊 策略对比分析")
        
        # 创建对比表格
        comparison_data = create_comparison_data(results)
        
        # 显示对比表格
        comparison_df = pd.DataFrame(comparison_data)
        st.table(comparison_df)
        
    except Exception as e:
        logger.error(f"显示策略对比分析时出错: {e}")
        st.error("显示策略对比分析时出错")

def create_comparison_data(results: Dict[str, Any]) -> List[Dict[str, str]]:
    """创建对比数据"""
    try:
        comparison_data = []
        
        # 策略数据
        strategy_total_return = results['total_return']
        strategy_annualized = results.get('annualized_return', 0)
        strategy_volatility = results.get('volatility', 0)
        strategy_sharpe = results.get('sharpe_ratio', 0)
        strategy_max_dd = results.get('max_drawdown', 0)
        strategy_recovery_days = results.get('max_drawdown_recovery_days', 0)
        
        # 基准数据
        benchmark_results = st.session_state.benchmark_results
        benchmark_total_return = benchmark_results['total_return']
        benchmark_annualized = benchmark_results.get('annualized_return', 0)
        benchmark_volatility = benchmark_results.get('volatility', 0)
        benchmark_sharpe = benchmark_results.get('sharpe_ratio', 0)
        benchmark_max_dd = benchmark_results.get('max_drawdown', 0)
        benchmark_recovery_days = benchmark_results.get('max_drawdown_recovery_days', 0)
        
        # 买入并持有策略数据
        buy_hold_results = st.session_state.buy_hold_results
        buy_hold_total_return = buy_hold_results['total_return']
        buy_hold_annualized = buy_hold_results.get('annualized_return', 0)
        buy_hold_volatility = buy_hold_results.get('volatility', 0)
        buy_hold_sharpe = buy_hold_results.get('sharpe_ratio', 0)
        buy_hold_max_dd = buy_hold_results.get('max_drawdown', 0)
        buy_hold_recovery_days = buy_hold_results.get('max_drawdown_recovery_days', 0)
        
        # 添加数据到对比表
        comparison_data.extend([
            {
                '策略': '回测策略',
                '总收益率': format_percentage(strategy_total_return),
                '年化收益率': format_percentage(strategy_annualized),
                '年化波动率': format_percentage(strategy_volatility),
                '夏普比率': f"{strategy_sharpe:.2f}",
                '最大回撤': format_percentage(strategy_max_dd),
                '回撤修复天数': f"{strategy_recovery_days}"
            },
            {
                '策略': st.session_state.get('benchmark_name', st.session_state.benchmark_symbol),
                '总收益率': format_percentage(benchmark_total_return),
                '年化收益率': format_percentage(benchmark_annualized),
                '年化波动率': format_percentage(benchmark_volatility),
                '夏普比率': f"{benchmark_sharpe:.2f}",
                '最大回撤': format_percentage(benchmark_max_dd),
                '回撤修复天数': f"{benchmark_recovery_days}"
            },
            {
                '策略': '买入并持有',
                '总收益率': format_percentage(buy_hold_total_return),
                '年化收益率': format_percentage(buy_hold_annualized),
                '年化波动率': format_percentage(buy_hold_volatility),
                '夏普比率': f"{buy_hold_sharpe:.2f}",
                '最大回撤': format_percentage(buy_hold_max_dd),
                '回撤修复天数': f"{buy_hold_recovery_days}"
            }
        ])
        
        return comparison_data
        
    except Exception as e:
        logger.error(f"创建对比数据时出错: {e}")
        return []

def display_trade_records(results: Dict[str, Any]) -> None:
    """显示交易记录"""
    try:
        st.subheader("📝 交易记录")
        
        if results.get('trades'):
            st.write(f"交易记录总数: {len(results['trades'])}")
            
            # 创建交易数据框
            trades_df = create_trades_dataframe(results['trades'])
            
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
            
    except Exception as e:
        logger.error(f"显示交易记录时出错: {e}")
        st.error("显示交易记录时出错")

def create_trades_dataframe(trades: List[Dict]) -> pd.DataFrame:
    """创建交易数据框"""
    try:
        trades_df = pd.DataFrame(trades)
        
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
        
        return trades_df
        
    except Exception as e:
        logger.error(f"创建交易数据框时出错: {e}")
        return pd.DataFrame()
