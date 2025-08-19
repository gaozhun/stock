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
