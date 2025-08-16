# -*- coding: utf-8 -*-
"""
可视化模块
负责生成各种图表和可视化结果
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

from config import VISUALIZATION_CONFIG

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class Visualizer:
    """可视化器"""
    
    def __init__(self):
        """初始化可视化器"""
        self.figure_size = VISUALIZATION_CONFIG['figure_size']
        self.dpi = VISUALIZATION_CONFIG['dpi']
        
        # 设置样式
        try:
            plt.style.use(VISUALIZATION_CONFIG['style'])
        except:
            plt.style.use('default')
        
        # 颜色配置
        self.colors = sns.color_palette(VISUALIZATION_CONFIG['color_palette'], 10)
    
    def plot_portfolio_performance(self, 
                                 results: Dict,
                                 benchmark_name: str = "基准",
                                 save_path: str = None) -> plt.Figure:
        """
        绘制投资组合表现图
        
        Args:
            results: 回测结果
            benchmark_name: 基准名称
            save_path: 保存路径
            
        Returns:
            matplotlib Figure对象
        """
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'{results["strategy_name"]} - 投资组合表现分析', fontsize=16)
        
        # 1. 累积收益曲线
        ax1 = axes[0, 0]
        portfolio_value = results['portfolio_value']
        initial_value = results['initial_capital']
        
        # 计算累积收益率
        cumulative_returns = (portfolio_value / initial_value - 1) * 100
        
        ax1.plot(cumulative_returns.index, cumulative_returns.values, 
                label=results['strategy_name'], color=self.colors[0], linewidth=2)
        
        # 如果有基准数据，添加基准线
        if results.get('benchmark_returns') is not None:
            benchmark_cumulative = (1 + results['benchmark_returns']).cumprod() - 1
            benchmark_cumulative = benchmark_cumulative * 100
            ax1.plot(benchmark_cumulative.index, benchmark_cumulative.values,
                    label=benchmark_name, color=self.colors[1], linewidth=2, alpha=0.8)
        
        ax1.set_title('累积收益率 (%)')
        ax1.set_xlabel('日期')
        ax1.set_ylabel('收益率 (%)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 回撤图
        ax2 = axes[0, 1]
        cumulative_returns_series = (portfolio_value / initial_value)
        running_max = cumulative_returns_series.expanding().max()
        drawdown = (cumulative_returns_series - running_max) / running_max * 100
        
        ax2.fill_between(drawdown.index, drawdown.values, 0, 
                        color=self.colors[2], alpha=0.7, label='回撤')
        ax2.set_title('资产回撤 (%)')
        ax2.set_xlabel('日期')
        ax2.set_ylabel('回撤 (%)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. 收益率分布
        ax3 = axes[1, 0]
        returns = results['returns'] * 100
        
        ax3.hist(returns.dropna(), bins=50, alpha=0.7, color=self.colors[3], edgecolor='black')
        ax3.axvline(returns.mean(), color=self.colors[4], linestyle='--', linewidth=2, label=f'均值: {returns.mean():.2f}%')
        ax3.axvline(returns.median(), color=self.colors[5], linestyle='--', linewidth=2, label=f'中位数: {returns.median():.2f}%')
        
        ax3.set_title('日收益率分布')
        ax3.set_xlabel('日收益率 (%)')
        ax3.set_ylabel('频数')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. 滚动夏普比率
        ax4 = axes[1, 1]
        rolling_returns = results['returns'].rolling(window=252)  # 1年窗口
        rolling_sharpe = rolling_returns.mean() / rolling_returns.std() * np.sqrt(252)
        
        ax4.plot(rolling_sharpe.index, rolling_sharpe.values, 
                color=self.colors[6], linewidth=2)
        ax4.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax4.axhline(y=1, color='red', linestyle='--', alpha=0.5, label='夏普比率=1')
        
        ax4.set_title('滚动夏普比率 (1年窗口)')
        ax4.set_xlabel('日期')
        ax4.set_ylabel('夏普比率')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        # 调整布局
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
        
        return fig
    
    def plot_strategy_comparison(self, 
                               results_dict: Dict[str, Dict],
                               save_path: str = None) -> plt.Figure:
        """
        绘制多策略对比图
        
        Args:
            results_dict: 多个策略的结果字典
            save_path: 保存路径
            
        Returns:
            matplotlib Figure对象
        """
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('多策略表现对比', fontsize=16)
        
        # 准备数据
        strategy_names = list(results_dict.keys())
        colors = self.colors[:len(strategy_names)]
        
        # 1. 累积收益对比
        ax1 = axes[0, 0]
        for i, (name, results) in enumerate(results_dict.items()):
            portfolio_value = results['portfolio_value']
            initial_value = results['initial_capital']
            cumulative_returns = (portfolio_value / initial_value - 1) * 100
            
            ax1.plot(cumulative_returns.index, cumulative_returns.values,
                    label=name, color=colors[i], linewidth=2)
        
        ax1.set_title('累积收益率对比 (%)')
        ax1.set_xlabel('日期')
        ax1.set_ylabel('收益率 (%)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 年化收益率vs波动率散点图
        ax2 = axes[0, 1]
        annual_returns = []
        annual_vols = []
        
        for results in results_dict.values():
            returns = results['returns']
            ann_ret = returns.mean() * 252
            ann_vol = returns.std() * np.sqrt(252)
            annual_returns.append(ann_ret * 100)
            annual_vols.append(ann_vol * 100)
        
        scatter = ax2.scatter(annual_vols, annual_returns, 
                             c=range(len(strategy_names)), 
                             s=100, alpha=0.7, cmap='Set2')
        
        # 添加策略名称标签
        for i, name in enumerate(strategy_names):
            ax2.annotate(name, (annual_vols[i], annual_returns[i]), 
                        xytext=(5, 5), textcoords='offset points')
        
        ax2.set_title('收益风险散点图')
        ax2.set_xlabel('年化波动率 (%)')
        ax2.set_ylabel('年化收益率 (%)')
        ax2.grid(True, alpha=0.3)
        
        # 3. 最大回撤对比
        ax3 = axes[1, 0]
        max_drawdowns = []
        
        for results in results_dict.values():
            portfolio_value = results['portfolio_value']
            cumulative_returns = portfolio_value / results['initial_capital']
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdowns.append(drawdown.min() * 100)
        
        bars = ax3.bar(strategy_names, max_drawdowns, color=colors, alpha=0.7)
        ax3.set_title('最大回撤对比 (%)')
        ax3.set_ylabel('最大回撤 (%)')
        ax3.tick_params(axis='x', rotation=45)
        
        # 在柱状图上添加数值
        for bar, value in zip(bars, max_drawdowns):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{value:.1f}%', ha='center', va='bottom')
        
        # 4. 夏普比率对比
        ax4 = axes[1, 1]
        sharpe_ratios = []
        
        for results in results_dict.values():
            returns = results['returns']
            sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
            sharpe_ratios.append(sharpe)
        
        bars = ax4.bar(strategy_names, sharpe_ratios, color=colors, alpha=0.7)
        ax4.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax4.axhline(y=1, color='red', linestyle='--', alpha=0.5, label='夏普比率=1')
        ax4.set_title('夏普比率对比')
        ax4.set_ylabel('夏普比率')
        ax4.tick_params(axis='x', rotation=45)
        ax4.legend()
        
        # 在柱状图上添加数值
        for bar, value in zip(bars, sharpe_ratios):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., 
                    height + 0.01 if height > 0 else height - 0.05,
                    f'{value:.2f}', ha='center', 
                    va='bottom' if height > 0 else 'top')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
        
        return fig
    
    def plot_trading_signals(self, 
                           results: Dict,
                           save_path: str = None) -> plt.Figure:
        """
        绘制交易信号图
        
        Args:
            results: 回测结果
            save_path: 保存路径
            
        Returns:
            matplotlib Figure对象
        """
        fig, axes = plt.subplots(2, 1, figsize=(15, 10))
        fig.suptitle(f'{results["strategy_name"]} - 交易信号分析', fontsize=16)
        
        # 获取价格数据和信号
        price_data = results['price_data']
        signals = results.get('signals', pd.Series())
        
        if len(price_data.columns) > 0:
            symbol = price_data.columns[0]
            prices = price_data[symbol]
            
            # 1. 价格和交易信号
            ax1 = axes[0]
            ax1.plot(prices.index, prices.values, label='价格', 
                    color=self.colors[0], linewidth=1)
            
            # 标记买入和卖出点
            buy_signals = signals[signals == 1]
            sell_signals = signals[signals == -1]
            
            if len(buy_signals) > 0:
                buy_prices = prices.loc[buy_signals.index]
                ax1.scatter(buy_signals.index, buy_prices.values, 
                           color='green', marker='^', s=100, 
                           label=f'买入信号 ({len(buy_signals)})', zorder=5)
            
            if len(sell_signals) > 0:
                sell_prices = prices.loc[sell_signals.index]
                ax1.scatter(sell_signals.index, sell_prices.values,
                           color='red', marker='v', s=100,
                           label=f'卖出信号 ({len(sell_signals)})', zorder=5)
            
            ax1.set_title(f'{symbol} 价格走势与交易信号')
            ax1.set_xlabel('日期')
            ax1.set_ylabel('价格')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 2. 持仓变化
            ax2 = axes[1]
            positions = results.get('positions', pd.DataFrame())
            
            if not positions.empty and 'total' in positions.columns:
                portfolio_value = positions['total']
                ax2.fill_between(portfolio_value.index, 
                               portfolio_value.values,
                               results['initial_capital'],
                               alpha=0.3, color=self.colors[1], 
                               label='投资组合价值')
                ax2.plot(portfolio_value.index, portfolio_value.values,
                        color=self.colors[1], linewidth=2)
                
                # 添加初始资金线
                ax2.axhline(y=results['initial_capital'], 
                           color='black', linestyle='--', alpha=0.5,
                           label='初始资金')
                
                ax2.set_title('投资组合价值变化')
                ax2.set_xlabel('日期')
                ax2.set_ylabel('价值')
                ax2.legend()
                ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
        
        return fig
    
    def create_interactive_dashboard(self, results: Dict) -> go.Figure:
        """
        创建交互式仪表板
        
        Args:
            results: 回测结果
            
        Returns:
            Plotly Figure对象
        """
        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('投资组合价值', '日收益率', '累积收益率', '回撤'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # 准备数据
        portfolio_value = results['portfolio_value']
        returns = results['returns']
        
        # 1. 投资组合价值
        fig.add_trace(
            go.Scatter(x=portfolio_value.index, y=portfolio_value.values,
                      mode='lines', name='投资组合价值',
                      line=dict(color='blue', width=2)),
            row=1, col=1
        )
        
        # 2. 日收益率
        fig.add_trace(
            go.Scatter(x=returns.index, y=returns.values * 100,
                      mode='lines', name='日收益率',
                      line=dict(color='green', width=1)),
            row=1, col=2
        )
        
        # 3. 累积收益率
        cumulative_returns = (portfolio_value / results['initial_capital'] - 1) * 100
        fig.add_trace(
            go.Scatter(x=cumulative_returns.index, y=cumulative_returns.values,
                      mode='lines', name='累积收益率',
                      line=dict(color='red', width=2)),
            row=2, col=1
        )
        
        # 4. 回撤
        running_max = (portfolio_value / results['initial_capital']).expanding().max()
        drawdown = ((portfolio_value / results['initial_capital']) - running_max) / running_max * 100
        
        fig.add_trace(
            go.Scatter(x=drawdown.index, y=drawdown.values,
                      mode='lines', name='回撤', fill='tonexty',
                      line=dict(color='orange', width=1)),
            row=2, col=2
        )
        
        # 更新布局
        fig.update_layout(
            title=f'{results["strategy_name"]} - 交互式仪表板',
            showlegend=True,
            height=600
        )
        
        # 更新坐标轴
        fig.update_xaxes(title_text="日期", row=1, col=1)
        fig.update_xaxes(title_text="日期", row=1, col=2)
        fig.update_xaxes(title_text="日期", row=2, col=1)
        fig.update_xaxes(title_text="日期", row=2, col=2)
        
        fig.update_yaxes(title_text="价值", row=1, col=1)
        fig.update_yaxes(title_text="收益率 (%)", row=1, col=2)
        fig.update_yaxes(title_text="累积收益率 (%)", row=2, col=1)
        fig.update_yaxes(title_text="回撤 (%)", row=2, col=2)
        
        return fig
    
    def plot_interactive_signals(self, results: Dict) -> go.Figure:
        """
        创建交互式价格和交易信号图表
        
        Args:
            results: 回测结果
            
        Returns:
            plotly Figure对象
        """
        # 获取数据
        price_data = results.get('price_data')
        signals = results.get('signals', pd.Series())
        
        if price_data is None or price_data.empty:
            # 创建空图表
            fig = go.Figure()
            fig.add_annotation(
                text="无价格数据可显示",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            return fig
        
        # 获取第一只股票的数据
        symbol = price_data.columns[0]
        prices = price_data[symbol]
        
        # 创建子图
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=[f'{symbol} 价格走势与交易信号', '交易信号分布'],
            row_heights=[0.7, 0.3]
        )
        
        # 1. 价格曲线
        fig.add_trace(
            go.Scatter(
                x=prices.index,
                y=prices.values,
                mode='lines',
                name='价格',
                line=dict(color='blue', width=2),
                hovertemplate='日期: %{x}<br>价格: ¥%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # 2. 买卖信号点
        if not signals.empty:
            buy_signals = signals[signals == 1]
            sell_signals = signals[signals == -1]
            
            if len(buy_signals) > 0:
                buy_prices = prices.loc[buy_signals.index]
                fig.add_trace(
                    go.Scatter(
                        x=buy_signals.index,
                        y=buy_prices.values,
                        mode='markers',
                        name=f'买入信号 ({len(buy_signals)})',
                        marker=dict(
                            symbol='triangle-up',
                            color='green',
                            size=12,
                            line=dict(color='darkgreen', width=1)
                        ),
                        hovertemplate='买入<br>日期: %{x}<br>价格: ¥%{y:.2f}<extra></extra>'
                    ),
                    row=1, col=1
                )
            
            if len(sell_signals) > 0:
                sell_prices = prices.loc[sell_signals.index]
                fig.add_trace(
                    go.Scatter(
                        x=sell_signals.index,
                        y=sell_prices.values,
                        mode='markers',
                        name=f'卖出信号 ({len(sell_signals)})',
                        marker=dict(
                            symbol='triangle-down',
                            color='red',
                            size=12,
                            line=dict(color='darkred', width=1)
                        ),
                        hovertemplate='卖出<br>日期: %{x}<br>价格: ¥%{y:.2f}<extra></extra>'
                    ),
                    row=1, col=1
                )
            
            # 3. 信号分布图
            signal_colors = ['red' if x == -1 else 'green' if x == 1 else 'gray' for x in signals.values]
            fig.add_trace(
                go.Scatter(
                    x=signals.index,
                    y=signals.values,
                    mode='markers',
                    name='信号分布',
                    marker=dict(color=signal_colors, size=6),
                    showlegend=False,
                    hovertemplate='日期: %{x}<br>信号: %{y}<extra></extra>'
                ),
                row=2, col=1
            )
        
        # 更新布局
        fig.update_layout(
            title=f'{results.get("strategy_name", "策略")} - 交易信号分析',
            height=600,
            showlegend=True,
            hovermode='x unified'
        )
        
        # 更新坐标轴
        fig.update_xaxes(title_text="日期", row=2, col=1)
        fig.update_yaxes(title_text="价格 (¥)", row=1, col=1)
        fig.update_yaxes(title_text="信号", row=2, col=1, tickvals=[-1, 0, 1], ticktext=['卖出', '持有', '买入'])
        
        return fig
    
    def plot_strategy_comparison_interactive(self, results: Dict, benchmark_data: pd.Series = None) -> go.Figure:
        """
        创建交互式策略对比图表
        
        Args:
            results: 回测结果
            benchmark_data: 基准数据
            
        Returns:
            plotly Figure对象
        """
        fig = go.Figure()
        
        # 策略收益曲线
        portfolio_value = results['portfolio_value']
        initial_capital = results['initial_capital']
        
        # 计算累积收益率
        cumulative_returns = (portfolio_value / initial_capital - 1) * 100
        
        fig.add_trace(
            go.Scatter(
                x=cumulative_returns.index,
                y=cumulative_returns.values,
                mode='lines',
                name=f'{results.get("strategy_name", "策略")}',
                line=dict(color='blue', width=3),
                hovertemplate='日期: %{x}<br>累积收益率: %{y:.2f}%<extra></extra>'
            )
        )
        
        # 添加基准对比（买入持有）
        if benchmark_data is not None and not benchmark_data.empty:
            # 计算买入持有收益
            aligned_benchmark = benchmark_data.reindex(portfolio_value.index, method='ffill')
            if not aligned_benchmark.empty and not aligned_benchmark.isna().all():
                benchmark_returns = (aligned_benchmark / aligned_benchmark.iloc[0] - 1) * 100
                
                fig.add_trace(
                    go.Scatter(
                        x=benchmark_returns.index,
                        y=benchmark_returns.values,
                        mode='lines',
                        name='买入持有 (基准)',
                        line=dict(color='gray', width=2, dash='dash'),
                        hovertemplate='日期: %{x}<br>基准收益率: %{y:.2f}%<extra></extra>'
                    )
                )
        
        # 添加零轴线
        fig.add_hline(y=0, line_dash="dot", line_color="black", opacity=0.3)
        
        # 更新布局
        fig.update_layout(
            title='策略 vs 基准对比',
            xaxis_title='日期',
            yaxis_title='累积收益率 (%)',
            height=500,
            showlegend=True,
            hovermode='x unified'
        )
        
        return fig
    
    def plot_correlation_heatmap(self, 
                               returns_data: pd.DataFrame,
                               save_path: str = None) -> plt.Figure:
        """
        绘制相关性热力图
        
        Args:
            returns_data: 收益率数据
            save_path: 保存路径
            
        Returns:
            matplotlib Figure对象
        """
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # 计算相关性矩阵
        correlation_matrix = returns_data.corr()
        
        # 绘制热力图
        sns.heatmap(correlation_matrix, 
                   annot=True, 
                   cmap='RdYlBu_r', 
                   center=0,
                   square=True,
                   fmt='.2f',
                   cbar_kws={"shrink": .8})
        
        plt.title('资产收益率相关性矩阵', fontsize=14)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
        
        return fig
