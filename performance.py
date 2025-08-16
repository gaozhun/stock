# -*- coding: utf-8 -*-
"""
性能分析模块
计算各种投资组合性能指标
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        """初始化性能分析器"""
        self.risk_free_rate = 0.02  # 无风险利率（年化）
    
    def calculate_performance_metrics(self, 
                                    returns: pd.Series,
                                    benchmark_returns: pd.Series = None) -> Dict:
        """
        计算完整的性能指标
        
        Args:
            returns: 策略收益率
            benchmark_returns: 基准收益率
            
        Returns:
            性能指标字典
        """
        if len(returns) == 0:
            return {}
        
        # 基础收益指标
        metrics = self._calculate_return_metrics(returns)
        
        # 风险指标
        metrics.update(self._calculate_risk_metrics(returns))
        
        # 风险调整收益指标
        metrics.update(self._calculate_risk_adjusted_metrics(returns))
        
        # 回撤指标
        metrics.update(self._calculate_drawdown_metrics(returns))
        
        # 如果有基准，计算相对指标
        if benchmark_returns is not None:
            metrics.update(self._calculate_relative_metrics(returns, benchmark_returns))
        
        return metrics
    
    def _calculate_return_metrics(self, returns: pd.Series) -> Dict:
        """计算收益相关指标"""
        total_return = (1 + returns).prod() - 1
        
        # 年化收益率
        days = len(returns)
        years = days / 252.0  # 假设一年252个交易日
        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        
        # 月度收益统计
        monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'average_return': returns.mean(),
            'median_return': returns.median(),
            'best_day': returns.max(),
            'worst_day': returns.min(),
            'positive_days': (returns > 0).sum(),
            'negative_days': (returns < 0).sum(),
            'win_rate': (returns > 0).mean(),
            'avg_win': returns[returns > 0].mean() if (returns > 0).any() else 0,
            'avg_loss': returns[returns < 0].mean() if (returns < 0).any() else 0,
            'best_month': monthly_returns.max() if len(monthly_returns) > 0 else 0,
            'worst_month': monthly_returns.min() if len(monthly_returns) > 0 else 0
        }
    
    def _calculate_risk_metrics(self, returns: pd.Series) -> Dict:
        """计算风险相关指标"""
        # 波动率
        volatility = returns.std()
        annualized_volatility = volatility * np.sqrt(252)
        
        # 下行风险
        negative_returns = returns[returns < 0]
        downside_deviation = negative_returns.std() if len(negative_returns) > 0 else 0
        annualized_downside_deviation = downside_deviation * np.sqrt(252)
        
        # VaR和CVaR
        var_95 = returns.quantile(0.05)
        var_99 = returns.quantile(0.01)
        cvar_95 = returns[returns <= var_95].mean() if (returns <= var_95).any() else var_95
        cvar_99 = returns[returns <= var_99].mean() if (returns <= var_99).any() else var_99
        
        # 偏度和峰度
        skewness = returns.skew()
        kurtosis = returns.kurtosis()
        
        return {
            'volatility': volatility,
            'annualized_volatility': annualized_volatility,
            'downside_deviation': downside_deviation,
            'annualized_downside_deviation': annualized_downside_deviation,
            'var_95': var_95,
            'var_99': var_99,
            'cvar_95': cvar_95,
            'cvar_99': cvar_99,
            'skewness': skewness,
            'kurtosis': kurtosis
        }
    
    def _calculate_risk_adjusted_metrics(self, returns: pd.Series) -> Dict:
        """计算风险调整收益指标"""
        # 年化指标
        annualized_return = returns.mean() * 252
        annualized_volatility = returns.std() * np.sqrt(252)
        
        # 夏普比率
        sharpe_ratio = (annualized_return - self.risk_free_rate) / annualized_volatility if annualized_volatility > 0 else 0
        
        # 索提诺比率
        negative_returns = returns[returns < 0]
        downside_deviation = negative_returns.std() if len(negative_returns) > 0 else annualized_volatility
        annualized_downside_deviation = downside_deviation * np.sqrt(252)
        sortino_ratio = (annualized_return - self.risk_free_rate) / annualized_downside_deviation if annualized_downside_deviation > 0 else 0
        
        # 卡玛比率（需要最大回撤）
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown < 0 else 0
        
        return {
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio
        }
    
    def _calculate_drawdown_metrics(self, returns: pd.Series) -> Dict:
        """计算回撤相关指标"""
        # 计算累积收益
        cumulative_returns = (1 + returns).cumprod()
        
        # 计算回撤
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        
        # 最大回撤
        max_drawdown = drawdown.min()
        max_drawdown_date = drawdown.idxmin()
        
        # 回撤持续期
        drawdown_periods = []
        in_drawdown = False
        start_date = None
        
        for date, dd in drawdown.items():
            if dd < 0 and not in_drawdown:
                # 开始回撤
                in_drawdown = True
                start_date = date
            elif dd == 0 and in_drawdown:
                # 回撤结束
                in_drawdown = False
                if start_date:
                    drawdown_periods.append((date - start_date).days)
        
        # 平均和最长回撤期
        avg_drawdown_duration = np.mean(drawdown_periods) if drawdown_periods else 0
        max_drawdown_duration = max(drawdown_periods) if drawdown_periods else 0
        
        # 当前回撤
        current_drawdown = drawdown.iloc[-1]
        
        return {
            'max_drawdown': max_drawdown,
            'max_drawdown_date': max_drawdown_date,
            'current_drawdown': current_drawdown,
            'avg_drawdown_duration': avg_drawdown_duration,
            'max_drawdown_duration': max_drawdown_duration,
            'drawdown_periods_count': len(drawdown_periods)
        }
    
    def _calculate_relative_metrics(self, 
                                  returns: pd.Series,
                                  benchmark_returns: pd.Series) -> Dict:
        """计算相对基准的指标"""
        # 对齐数据
        common_dates = returns.index.intersection(benchmark_returns.index)
        if len(common_dates) == 0:
            return {}
        
        strategy_returns = returns.loc[common_dates]
        benchmark_returns = benchmark_returns.loc[common_dates]
        
        # 超额收益
        excess_returns = strategy_returns - benchmark_returns
        
        # 跟踪误差
        tracking_error = excess_returns.std() * np.sqrt(252)
        
        # 信息比率
        information_ratio = excess_returns.mean() * 252 / tracking_error if tracking_error > 0 else 0
        
        # 贝塔系数
        covariance = np.cov(strategy_returns, benchmark_returns)[0][1]
        benchmark_variance = benchmark_returns.var()
        beta = covariance / benchmark_variance if benchmark_variance > 0 else 1
        
        # 阿尔法
        benchmark_annualized = benchmark_returns.mean() * 252
        strategy_annualized = strategy_returns.mean() * 252
        alpha = strategy_annualized - (self.risk_free_rate + beta * (benchmark_annualized - self.risk_free_rate))
        
        # 相关系数
        correlation = strategy_returns.corr(benchmark_returns)
        
        # 基准相对表现
        strategy_total = (1 + strategy_returns).prod() - 1
        benchmark_total = (1 + benchmark_returns).prod() - 1
        excess_return = strategy_total - benchmark_total
        
        return {
            'alpha': alpha,
            'beta': beta,
            'correlation': correlation,
            'tracking_error': tracking_error,
            'information_ratio': information_ratio,
            'excess_return': excess_return,
            'benchmark_return': benchmark_total
        }
    
    def generate_performance_report(self, 
                                  results: Dict,
                                  benchmark_name: str = "基准") -> str:
        """
        生成性能报告文本
        
        Args:
            results: 回测结果
            benchmark_name: 基准名称
            
        Returns:
            格式化的性能报告
        """
        metrics = self.calculate_performance_metrics(
            results['returns'],
            results.get('benchmark_returns')
        )
        
        report = f"""
=== {results['strategy_name']} 性能报告 ===

【基本信息】
股票代码: {', '.join(results['symbols'])}
回测期间: {results['start_date']} 至 {results['end_date']}
初始资金: ${results['initial_capital']:,.2f}
最终价值: ${results['portfolio_value'].iloc[-1]:,.2f}

【收益指标】
总收益率: {metrics.get('total_return', 0):.2%}
年化收益率: {metrics.get('annualized_return', 0):.2%}
胜率: {metrics.get('win_rate', 0):.2%}
最佳单日: {metrics.get('best_day', 0):.2%}
最差单日: {metrics.get('worst_day', 0):.2%}

【风险指标】
年化波动率: {metrics.get('annualized_volatility', 0):.2%}
最大回撤: {metrics.get('max_drawdown', 0):.2%}
VaR (95%): {metrics.get('var_95', 0):.2%}
偏度: {metrics.get('skewness', 0):.2f}
峰度: {metrics.get('kurtosis', 0):.2f}

【风险调整收益】
夏普比率: {metrics.get('sharpe_ratio', 0):.2f}
索提诺比率: {metrics.get('sortino_ratio', 0):.2f}
卡玛比率: {metrics.get('calmar_ratio', 0):.2f}
"""
        
        # 添加相对基准指标
        if 'benchmark_returns' in results and results['benchmark_returns'] is not None:
            report += f"""
【相对{benchmark_name}表现】
阿尔法: {metrics.get('alpha', 0):.2%}
贝塔: {metrics.get('beta', 0):.2f}
相关性: {metrics.get('correlation', 0):.2f}
跟踪误差: {metrics.get('tracking_error', 0):.2%}
信息比率: {metrics.get('information_ratio', 0):.2f}
超额收益: {metrics.get('excess_return', 0):.2%}
"""
        
        return report
    
    def compare_strategies(self, results_dict: Dict[str, Dict]) -> pd.DataFrame:
        """
        比较多个策略的表现
        
        Args:
            results_dict: 策略结果字典
            
        Returns:
            策略比较表
        """
        comparison_data = []
        
        for strategy_name, results in results_dict.items():
            metrics = self.calculate_performance_metrics(
                results['returns'],
                results.get('benchmark_returns')
            )
            
            comparison_data.append({
                '策略名称': strategy_name,
                '总收益率': f"{metrics.get('total_return', 0):.2%}",
                '年化收益率': f"{metrics.get('annualized_return', 0):.2%}",
                '年化波动率': f"{metrics.get('annualized_volatility', 0):.2%}",
                '夏普比率': f"{metrics.get('sharpe_ratio', 0):.2f}",
                '最大回撤': f"{metrics.get('max_drawdown', 0):.2%}",
                '卡玛比率': f"{metrics.get('calmar_ratio', 0):.2f}",
                '胜率': f"{metrics.get('win_rate', 0):.2%}"
            })
        
        return pd.DataFrame(comparison_data).set_index('策略名称')


class RiskManager:
    """风险管理器"""
    
    def __init__(self, max_position_size: float = 0.1, 
                 max_sector_exposure: float = 0.3,
                 max_single_loss: float = 0.05):
        """
        初始化风险管理器
        
        Args:
            max_position_size: 最大单个持仓比例
            max_sector_exposure: 最大行业暴露度
            max_single_loss: 最大单笔损失
        """
        self.max_position_size = max_position_size
        self.max_sector_exposure = max_sector_exposure
        self.max_single_loss = max_single_loss
    
    def check_position_limits(self, positions: Dict[str, float]) -> Dict[str, float]:
        """检查并调整持仓限制"""
        adjusted_positions = {}
        
        for symbol, position in positions.items():
            # 限制单个持仓大小
            adjusted_position = min(position, self.max_position_size)
            adjusted_positions[symbol] = adjusted_position
        
        return adjusted_positions
    
    def calculate_portfolio_risk(self, returns: pd.DataFrame, 
                               positions: Dict[str, float]) -> Dict:
        """计算投资组合风险"""
        # 计算协方差矩阵
        cov_matrix = returns.cov() * 252  # 年化
        
        # 计算投资组合方差
        weights = np.array(list(positions.values()))
        portfolio_variance = np.dot(weights, np.dot(cov_matrix.values, weights))
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        return {
            'portfolio_volatility': portfolio_volatility,
            'individual_contributions': {
                symbol: weight * np.sqrt(cov_matrix.loc[symbol, symbol])
                for symbol, weight in positions.items()
            }
        }
