# -*- coding: utf-8 -*-
"""
配置文件
包含系统各种配置参数
"""

# 数据源配置
DATA_SOURCE = {
    'provider': 'akshare',      # 数据提供商: 'akshare', 'auto'
    'timeout': 10,           # 请求超时时间
    'retry_times': 3,        # 重试次数
    'cache_days': 7,         # 数据缓存天数
    'priority': ['akshare']  # 数据源优先级（只使用AKShare）
}

# 基准指数配置
BENCHMARK_CONFIG = {
    'default': 'sh000300',          # 默认基准指数（沪深300）
    'available_benchmarks': {       # 可用基准指数
        'sh000001': '上证指数',
        'sh000300': '沪深300',
        'sz399001': '深证成指',
        'sz399006': '创业板指',
        'sz399905': '中证500',
        'sz399852': '中证1000'
    },
    'compare_with_benchmark': True,  # 是否与基准对比
    'benchmark_weight': 1.0         # 基准权重（用于计算相对指标）
}

# Web应用配置
WEB_CONFIG = {
    'page_title': '股票回测系统',
    'page_icon': '📈',
    'layout': 'wide',
    'sidebar_state': 'expanded'
}

# 策略参数配置
STRATEGY_PARAMS = {
    'ma_short': 20,
    'ma_long': 60,
    'rsi_period': 14,
    'rsi_oversold': 30,
    'rsi_overbought': 70
}

# ETF配置
ETF_CONFIG = {
    'popular_etfs': {
        '510300': '沪深300ETF',
        '510500': '中证500ETF',
        '159915': '创业板ETF',
        '510050': '上证50ETF',
        '159919': '沪深300ETF',
        '510880': '红利ETF',
        '159928': '消费ETF',
        '159929': '医药ETF',
        '159930': '能源ETF',
        '159931': '金融ETF'
    },
    'etf_categories': {
        '宽基指数': ['510300', '510500', '159915', '510050'],
        '行业主题': ['159928', '159929', '159930', '159931'],
        '策略指数': ['510880']
    }
}

# 新策略系统配置
NEW_STRATEGY_CONFIG = {
    'time_based': {
        'frequencies': ['daily', 'weekly', 'monthly'],
        'frequency_names': {
            'daily': '每日',
            'weekly': '每周', 
            'monthly': '每月'
        },
        'default_trading_day': 1,
        'default_trade_amount': 10000,
        'default_max_position': 1.0,
        'default_position_increment': 0.1
    },
    'macd_pattern': {
        'buy_patterns': ['golden_cross', 'double_golden_cross', 'bullish_divergence'],
        'sell_patterns': ['death_cross', 'double_death_cross', 'bearish_divergence'],
        'pattern_names': {
            'golden_cross': '金叉',
            'double_golden_cross': '二次金叉',
            'bullish_divergence': '底背离',
            'death_cross': '死叉',
            'double_death_cross': '二次死叉',
            'bearish_divergence': '顶背离'
        },
        'default_fast_period': 12,
        'default_slow_period': 26,
        'default_signal_period': 9,
        'default_divergence_lookback': 20,
        'default_double_cross_lookback': 10
    },
    'ma_touch': {
        'available_periods': [5, 10, 20, 30, 60],
        'period_names': {
            5: '5日均线',
            10: '10日均线',
            20: '20日均线',
            30: '30日均线',
            60: '60日均线'
        },
        'default_touch_threshold': 0.02,
        'default_buy_on_touch': True,
        'default_sell_on_touch': True
    },
    'composite': {
        'default_signal_threshold': 0.5,
        'min_strategies': 2,
        'max_strategies': 5
    }
}

# 回测引擎配置
BACKTEST_CONFIG = {
    'commission_rate': 0.0003,  # 手续费率
    'slippage': 0.0001,         # 滑点
    'min_trade_amount': 1000,   # 最小交易金额
    'max_position_per_stock': 0.2,  # 单只股票最大持仓比例
    'risk_free_rate': 0.03,      # 无风险利率
    'initial_capital': 100000,  # 默认初始资金
}

# 数据配置
DATA_CONFIG = {
    'default_start_date': '2020-01-01',
    'default_end_date': '2024-01-01',
    'cache_expire_hours': 24,
    'max_symbols_per_request': 10,
    'retry_times': 3,
    'timeout_seconds': 30
}

# 可视化配置
VISUALIZATION_CONFIG = {
    'chart_height': 600,
    'chart_width': '100%',
    'color_scheme': {
        'buy_signal': '#2ca02c',
        'sell_signal': '#d62728',
        'portfolio_value': '#1f77b4',
        'benchmark': '#ff7f0e',
        'price': '#1f77b4',
        'ma_lines': ['#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    },
    'default_ma_periods': [5, 10, 20, 60]
}
