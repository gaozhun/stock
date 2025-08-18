# -*- coding: utf-8 -*-
"""
UI组件模块
包含应用程序中使用的通用UI组件和CSS样式
"""

import streamlit as st
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def get_custom_css() -> str:
    """获取自定义CSS样式"""
    return """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        .stock-card {
            background-color: #f8f9fa;
            padding: 1.2rem;
            border-radius: 0.7rem;
            border-left: 5px solid #4e73df;
            margin-bottom: 1.5rem;
            box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
        }
        .strategy-card {
            background-color: #ffffff;
            padding: 0.8rem 1rem;
            border-radius: 0.5rem;
            border: 1px solid #e3e6f0;
            margin-bottom: 0.8rem;
            box-shadow: 0 0.1rem 0.3rem rgba(0,0,0,.05);
            transition: all 0.2s ease-in-out;
        }
        .strategy-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 0.3rem 0.6rem rgba(0,0,0,.1);
        }
        .buy-strategy {
            border-left: 4px solid #1cc88a;
        }
        .sell-strategy {
            border-left: 4px solid #e74a3b;
        }
        .metric-card {
            background-color: #f8f9fa;
            padding: 1.2rem;
            border-radius: 0.7rem;
            box-shadow: 0 0.15rem 0.5rem 0 rgba(58, 59, 69, 0.15);
        }
        .success-metric {
            border-left: 5px solid #1cc88a;
        }
        .warning-metric {
            border-left: 5px solid #f6c23e;
        }
        .danger-metric {
            border-left: 5px solid #e74a3b;
        }
        
        .stButton>button {
            border-radius: 0.5rem;
            font-weight: 500;
            transition: all 0.2s;
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 0.3rem 0.6rem rgba(0,0,0,.1);
        }
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
        }
        .stTabs [data-baseweb="tab"] {
            height: 3rem;
            white-space: pre-wrap;
            border-radius: 4px 4px 0px 0px;
            padding: 0px 1rem;
            font-weight: 500;
        }
        
        .dataframe {
            border-collapse: collapse;
            margin: 1rem 0;
            font-size: 0.9rem;
            border-radius: 0.5rem;
            overflow: hidden;
            box-shadow: 0 0.15rem 0.5rem rgba(0,0,0,0.1);
        }
        .dataframe thead th {
            background-color: #4e73df;
            color: white;
            font-weight: 500;
            text-align: left;
            padding: 0.75rem 1rem;
        }
        .dataframe tbody tr:nth-of-type(even) {
            background-color: #f8f9fa;
        }
        .dataframe tbody tr:hover {
            background-color: #eaecf4;
        }
        .dataframe td {
            padding: 0.75rem 1rem;
            border-top: 1px solid #e3e6f0;
        }
    </style>
    """

def render_stock_card(stock_code: str) -> None:
    """渲染股票卡片标题"""
    try:
        st.markdown(f"""
        <div class="stock-card">
            <h3>📊 {stock_code}</h3>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"渲染股票卡片时出错: {e}")
        st.subheader(f"📊 {stock_code}")

def render_strategy_card(strategy_name: str, strategy_type: str, 
                        signal_type: str, params: Dict[str, Any], 
                        is_buy: bool = True) -> None:
    """渲染策略卡片"""
    try:
        strategy_type_name = {
            'time_based': '时间条件单', 
            'macd_pattern': 'MACD形态', 
            'ma_touch': '均线触碰'
        }.get(strategy_type, strategy_type)
        
        formatted_params = []
        for k, v in params.items():
            if isinstance(v, list):
                formatted_params.append(f"{k}: {', '.join(map(str, v))}")
            else:
                formatted_params.append(f"{k}: {v}")
        
        card_class = "buy-strategy" if is_buy else "sell-strategy"
        signal_text = "📈 买入" if is_buy else "📉 卖出"
        
        st.markdown(f"""
        <div class="strategy-card {card_class}">
            <h4>{signal_text} - {strategy_type_name}</h4>
            <p>{'; '.join(formatted_params)}</p>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"渲染策略卡片时出错: {e}")
        signal_text = "买入" if is_buy else "卖出"
        st.write(f"{signal_text} - {strategy_type}")

def render_metric_card(title: str, value: str, metric_type: str = "default") -> None:
    """
    渲染指标卡片
    
    Args:
        title: 指标标题
        value: 指标值
        metric_type: 指标类型 (default, success, warning, danger)
    """
    try:
        metric_class = f"metric-card {metric_type}-metric" if metric_type != "default" else "metric-card"
        st.markdown(f"""
        <div class="{metric_class}">
            <h4>{title}</h4>
            <p style="font-size: 1.5rem; font-weight: bold; margin: 0;">{value}</p>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"渲染指标卡片时出错: {e}")
        st.metric(title, value)

def render_info_box(message: str, message_type: str = "info") -> None:
    """
    渲染信息提示框
    
    Args:
        message: 提示信息
        message_type: 信息类型 (info, success, warning, error)
    """
    try:
        if message_type == "info":
            st.info(message)
        elif message_type == "success":
            st.success(message)
        elif message_type == "warning":
            st.warning(message)
        elif message_type == "error":
            st.error(message)
        else:
            st.info(message)
    except Exception as e:
        logger.error(f"渲染信息提示框时出错: {e}")
        st.write(message)

def render_progress_bar(current: int, total: int, description: str = "处理中...") -> None:
    """
    渲染进度条
    
    Args:
        current: 当前进度
        total: 总进度
        description: 进度描述
    """
    try:
        if total > 0:
            progress = current / total
            st.progress(progress, text=description)
        else:
            st.progress(0, text=description)
    except Exception as e:
        logger.error(f"渲染进度条时出错: {e}")
        st.write(f"{description}: {current}/{total}")

def render_download_button(data: str, filename: str, button_text: str = "下载") -> None:
    """
    渲染下载按钮
    
    Args:
        data: 要下载的数据
        filename: 文件名
        button_text: 按钮文本
    """
    try:
        st.download_button(
            label=button_text,
            data=data,
            file_name=filename,
            mime='text/csv',
        )
    except Exception as e:
        logger.error(f"渲染下载按钮时出错: {e}")
        st.write(f"无法创建下载按钮: {filename}")

def setup_page_config(config: Dict[str, Any]) -> None:
    """设置页面配置"""
    try:
        st.set_page_config(
            page_title=config.get('page_title', '股票回测系统'),
            page_icon=config.get('page_icon', '📈'),
            layout=config.get('layout', 'wide'),
            initial_sidebar_state=config.get('sidebar_state', 'expanded')
        )
    except Exception as e:
        logger.error(f"设置页面配置时出错: {e}")

def apply_custom_css() -> None:
    """应用自定义CSS样式"""
    try:
        st.markdown(get_custom_css(), unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"应用自定义CSS时出错: {e}")
