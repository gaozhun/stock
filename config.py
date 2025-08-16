# -*- coding: utf-8 -*-
"""
配置文件
包含系统的各种配置参数
"""

# 数据源配置
DATA_SOURCE = {
    'provider': 'akshare',      # 数据提供商: 'akshare', 'auto'
    'timeout': 10,           # 请求超时时间
    'retry_times': 3,        # 重试次数
    'cache_days': 7,         # 数据缓存天数
    'priority': ['akshare']  # 数据源优先级（只使用AKShare）
}

# 回测配置
BACKTEST_CONFIG = {
    'initial_capital': 100000,    # 初始资金
    'commission_rate': 0.001,     # 手续费率
    'min_position': 0.01,         # 最小持仓比例
    'max_position': 1.0,          # 最大持仓比例
    'slippage_rate': 0.0005,      # 滑点率
    'benchmark': 'sh000300'       # 基准指数（沪深300）
}

# 策略参数
STRATEGY_PARAMS = {
    'ma_short': 20,              # 短期移动平均
    'ma_long': 60,               # 长期移动平均
    'rsi_period': 14,            # RSI周期
    'rsi_oversold': 30,          # RSI超卖线
    'rsi_overbought': 70,        # RSI超买线
    'rebalance_freq': 'monthly'   # 再平衡频率
}

# 可视化配置
VISUALIZATION_CONFIG = {
    'figure_size': (12, 8),
    'dpi': 100,
    'style': 'seaborn-v0_8',
    'color_palette': 'Set2'
}

# Web应用配置
WEB_CONFIG = {
    'page_title': '股票基金回测系统',
    'page_icon': '📈',
    'layout': 'wide',
    'sidebar_state': 'expanded'
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

# ETF配置
ETF_CONFIG = {
    'popular_etfs': {
        # 宽基指数ETF
        '510300': '沪深300ETF',
        '159919': '沪深300ETF',
        '510050': '上证50ETF',
        '510500': '中证500ETF',
        '512100': '中证1000ETF',
        
        # 行业ETF
        '159915': '创业板ETF',
        '588000': '科创50ETF',
        '516100': '金融科技ETF',
        '159928': '消费ETF',
        '512200': '房地产ETF',
        '515170': '食品饮料ETF',
        
        # 海外ETF
        '513100': '纳指ETF',
        '513500': '标普500ETF',
        '159941': '纳指100ETF',
        
        # 债券ETF
        '511010': '国债ETF',
        '511260': '十年国债ETF',
        '511220': '城投债ETF'
    },
    'etf_categories': {
        '宽基指数': ['510300', '159919', '510050', '510500', '512100'],
        '行业主题': ['159915', '588000', '516100', '159928', '512200', '515170'],
        '海外市场': ['513100', '513500', '159941'],
        '债券固收': ['511010', '511260', '511220']
    },
    'default_etf': '510300'  # 默认ETF（沪深300ETF）
}
