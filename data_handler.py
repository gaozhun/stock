# -*- coding: utf-8 -*-
"""
数据处理模块
负责股票和基金数据的获取、处理和存储
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import pickle
from typing import Dict, List, Optional, Tuple
from config import DATA_SOURCE


try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False


class DataHandler:
    """数据处理器"""
    
    def __init__(self, cache_dir: str = "cache"):
        """
        初始化数据处理器
        
        Args:
            cache_dir: 缓存目录
        """
        self.cache_dir = cache_dir
        self.cache_days = DATA_SOURCE['cache_days']
        
        # 创建缓存目录
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def get_stock_data(self, 
                      symbol: str, 
                      start_date: str, 
                      end_date: str,
                      use_cache: bool = True,
                      auto_fallback: bool = True) -> pd.DataFrame:
        """
        获取股票数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            use_cache: 是否使用缓存
            auto_fallback: 保留参数（向后兼容）
            
        Returns:
            包含OHLCV数据的DataFrame
        """
        # 检查是否为ETF代码
        if self.is_etf_code(symbol):
            return self.get_etf_data(symbol, start_date, end_date, use_cache)
        
        # 根据配置选择数据源
        provider = DATA_SOURCE.get('provider', 'auto')
        
        if provider == 'auto':
            # 自动选择数据源
            return self._get_data_auto(symbol, start_date, end_date, use_cache, auto_fallback)
        elif provider == 'akshare':
            return self._get_stock_data_akshare(symbol, start_date, end_date, use_cache, auto_fallback)
        else:
            raise ValueError(f"不支持的数据源: {provider}")
    
    def _get_data_auto(self, symbol: str, start_date: str, end_date: str, 
                      use_cache: bool, auto_fallback: bool) -> pd.DataFrame:
        """自动选择数据源获取数据"""
        # 目前只使用AKShare
        try:
            print(f"尝试使用 AKShare 获取 {symbol} 数据...")
            return self._get_stock_data_akshare(symbol, start_date, end_date, use_cache, False)
        except Exception as e:
            print(f"  AKShare 获取失败: {str(e)}")
            raise Exception("AKShare数据源不可用")
    
    def _get_stock_data_akshare(self, symbol: str, start_date: str, end_date: str,
                               use_cache: bool, auto_fallback: bool) -> pd.DataFrame:
        """使用AKShare获取股票数据"""
        if not AKSHARE_AVAILABLE:
            raise Exception("AKShare未安装，请运行: pip install akshare")
        
        cache_file = os.path.join(self.cache_dir, f"ak_{symbol}_{start_date}_{end_date}.pkl")
        
        # 检查缓存
        if use_cache and os.path.exists(cache_file):
            cache_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if datetime.now() - cache_time < timedelta(days=self.cache_days):
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
        
        try:
            # 转换股票代码格式
            ak_symbol = self._convert_to_akshare_symbol(symbol)
            print(f"  转换代码 {symbol} -> {ak_symbol}")
            
            # 获取数据
            data = ak.stock_zh_a_hist(symbol=ak_symbol, start_date=start_date.replace('-', ''), 
                                     end_date=end_date.replace('-', ''), adjust="qfq")
            
            if data.empty:
                raise ValueError(f"无法获取{symbol}的AKShare数据")
            
            # 转换格式为标准OHLCV格式
            data = self._convert_akshare_format(data)
            
            # 清理数据
            data = self._clean_data(data)
            
            if len(data) == 0:
                raise ValueError(f"获取到的{symbol}数据为空")
            
            print(f"  AKShare成功获取 {len(data)} 条数据")
            
            # 缓存数据
            if use_cache:
                with open(cache_file, 'wb') as f:
                    pickle.dump(data, f)
            
            return data
            
        except Exception as e:
            error_msg = f"AKShare获取{symbol}数据失败: {str(e)}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
    

    def _convert_to_akshare_symbol(self, symbol: str) -> str:
        """转换股票代码为AKShare格式"""
        symbol = symbol.upper().strip()
        
        # 美股代码映射到中国股票代码（用于演示）
        us_to_cn_mapping = {
            'AAPL': '000001',   # 苹果 -> 平安银行
            'MSFT': '000002',   # 微软 -> 万科A  
            'GOOGL': '000858',  # 谷歌 -> 五粮液
            'AMZN': '000001',   # 亚马逊 -> 平安银行
            'TSLA': '002594'    # 特斯拉 -> 比亚迪
        }
        
        # 如果在映射中，使用映射后的代码
        if symbol in us_to_cn_mapping:
            print(f"    将美股代码 {symbol} 映射为中国股票 {us_to_cn_mapping[symbol]}")
            return us_to_cn_mapping[symbol]
        
        # 如果是6位数字，直接使用
        if len(symbol) == 6 and symbol.isdigit():
            return symbol
        
        # 如果包含.SZ或.SH等后缀，去掉后缀
        if '.' in symbol:
            symbol = symbol.split('.')[0]
        
        # 默认返回原代码
        return symbol
    
    def _convert_akshare_format(self, data: pd.DataFrame) -> pd.DataFrame:
        """转换AKShare数据格式为标准OHLCV格式"""
        # AKShare返回的列名通常是中文
        column_mapping = {
            '日期': 'Date',
            '开盘': 'Open',
            '最高': 'High', 
            '最低': 'Low',
            '收盘': 'Close',
            '成交量': 'Volume',
            '成交额': 'Amount'
        }
        
        # 重命名列
        for chinese_col, english_col in column_mapping.items():
            if chinese_col in data.columns:
                data = data.rename(columns={chinese_col: english_col})
        
        # 设置日期索引
        if 'Date' in data.columns:
            data['Date'] = pd.to_datetime(data['Date'])
            data.set_index('Date', inplace=True)
        elif '日期' in data.index.names:
            data.index = pd.to_datetime(data.index)
        
        # 确保数值类型正确
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
        
        # 只保留需要的列
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        available_cols = [col for col in required_cols if col in data.columns]
        data = data[available_cols]
        
        return data
    
    def get_multiple_stocks(self, 
                          symbols: List[str], 
                          start_date: str, 
                          end_date: str,
                          price_column: str = 'Close') -> pd.DataFrame:
        """
        获取多只股票的数据
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            price_column: 价格列名
            
        Returns:
            多只股票价格的DataFrame
        """
        price_data = {}
        
        for symbol in symbols:
            try:
                data = self.get_stock_data(symbol, start_date, end_date)
                price_data[symbol] = data[price_column]
            except Exception as e:
                print(f"警告: 获取{symbol}数据失败 - {str(e)}")
                continue
        
        if not price_data:
            raise ValueError("未能获取任何股票数据")
        
        # 合并数据
        combined_data = pd.DataFrame(price_data)
        combined_data = combined_data.dropna()  # 去除缺失值
        
        return combined_data
    
    def calculate_returns(self, prices: pd.DataFrame) -> pd.DataFrame:
        """
        计算收益率
        
        Args:
            prices: 价格数据
            
        Returns:
            收益率数据
        """
        return prices.pct_change().dropna()
    
    def get_index_data(self, index_code: str, start_date: str, end_date: str, use_cache: bool = True) -> pd.DataFrame:
        """
        获取指数数据
        
        Args:
            index_code: 指数代码 (如 'sh000300', 'sh000001', 'sz399001', 'sz399006')
            start_date: 开始日期 'YYYY-MM-DD'
            end_date: 结束日期 'YYYY-MM-DD'
            use_cache: 是否使用缓存
            
        Returns:
            包含指数OHLCV数据的DataFrame
        """
        if not AKSHARE_AVAILABLE:
            raise Exception("AKShare未安装，无法获取指数数据")
        
        # 检查缓存
        cache_file = os.path.join(self.cache_dir, f"idx_{index_code}_{start_date}_{end_date}.pkl")
        if use_cache and os.path.exists(cache_file):
            cache_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if datetime.now() - cache_time < timedelta(days=self.cache_days):
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
        
        try:
            print(f"正在获取指数 {index_code} 数据...")
            
            # 直接使用AKShare获取指数数据（不经过股票代码转换）
            data = ak.stock_zh_index_daily(symbol=index_code)
            
            if data is None or data.empty:
                raise ValueError(f"无法获取指数{index_code}的数据")
            
            # 转换数据格式
            data = self._convert_index_format(data, start_date, end_date)
            data = self._clean_data(data)
            
            print(f"  成功获取 {len(data)} 条指数数据")
            
            # 缓存数据
            if use_cache and len(data) > 0:
                with open(cache_file, 'wb') as f:
                    pickle.dump(data, f)
            
            return data
            
        except Exception as e:
            error_msg = f"AKShare获取指数{index_code}数据失败: {str(e)}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)

    def _convert_index_format(self, data: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
        """转换AKShare指数数据格式"""
        # 设置日期为索引
        data['date'] = pd.to_datetime(data['date'])
        data.set_index('date', inplace=True)
        
        # 筛选日期范围
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        data = data[(data.index >= start_dt) & (data.index <= end_dt)]
        
        # 列名转换为标准格式
        data.columns = data.columns.str.capitalize()
        
        return data

    def get_benchmark_data(self, start_date: str, end_date: str, benchmark: str = None) -> pd.DataFrame:
        """
        获取基准指数数据（兼容原接口）
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            benchmark: 基准指数代码
            
        Returns:
            基准指数数据DataFrame
        """
        from config import BENCHMARK_CONFIG
        
        # 如果未指定基准，使用默认基准
        if benchmark is None:
            benchmark = BENCHMARK_CONFIG.get('default', 'sh000300')
        
        return self.get_index_data(benchmark, start_date, end_date)

    def get_benchmark_info(self) -> Dict[str, str]:
        """获取支持的基准指数信息"""
        return {
            'sh000001': '上证指数',
            'sh000300': '沪深300',
            'sz399001': '深证成指', 
            'sz399006': '创业板指',
            'sz399905': '中证500',
            'sz399852': '中证1000'
        }

    def get_etf_data(self, etf_code: str, start_date: str, end_date: str, use_cache: bool = True) -> pd.DataFrame:
        """
        获取ETF数据
        
        Args:
            etf_code: ETF代码 (如 '510300', '159915')
            start_date: 开始日期 'YYYY-MM-DD'
            end_date: 结束日期 'YYYY-MM-DD'
            use_cache: 是否使用缓存
            
        Returns:
            包含ETF OHLCV数据的DataFrame
        """
        if not AKSHARE_AVAILABLE:
            raise Exception("AKShare未安装，无法获取ETF数据")
        
        # 检查缓存
        cache_file = os.path.join(self.cache_dir, f"etf_{etf_code}_{start_date}_{end_date}.pkl")
        if use_cache and os.path.exists(cache_file):
            cache_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if datetime.now() - cache_time < timedelta(days=self.cache_days):
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
        
        try:
            print(f"正在获取ETF {etf_code} 数据...")
            
            # 转换日期格式为AKShare需要的格式
            start_date_ak = start_date.replace('-', '')
            end_date_ak = end_date.replace('-', '')
            
            # 使用AKShare获取ETF历史数据
            data = ak.fund_etf_hist_em(symbol=etf_code, start_date=start_date_ak, end_date=end_date_ak)
            
            if data is None or data.empty:
                raise ValueError(f"无法获取ETF {etf_code}的数据")
            
            # 转换数据格式
            data = self._convert_etf_format(data)
            data = self._clean_data(data)
            
            print(f"  成功获取 {len(data)} 条ETF数据")
            
            # 缓存数据
            if use_cache and len(data) > 0:
                with open(cache_file, 'wb') as f:
                    pickle.dump(data, f)
            
            return data
            
        except Exception as e:
            error_msg = f"AKShare获取ETF {etf_code}数据失败: {str(e)}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)

    def _convert_etf_format(self, data: pd.DataFrame) -> pd.DataFrame:
        """转换AKShare ETF数据格式"""
        # 重命名列名为标准格式
        column_mapping = {
            '日期': 'Date',
            '开盘': 'Open',
            '收盘': 'Close',
            '最高': 'High',
            '最低': 'Low',
            '成交量': 'Volume'
        }
        
        # 重命名存在的列
        for old_col, new_col in column_mapping.items():
            if old_col in data.columns:
                data.rename(columns={old_col: new_col}, inplace=True)
        
        # 设置日期为索引
        if 'Date' in data.columns:
            data['Date'] = pd.to_datetime(data['Date'])
            data.set_index('Date', inplace=True)
        
        # 确保必需的列存在
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_columns:
            if col not in data.columns:
                if col == 'Volume':
                    data[col] = 0  # 如果没有成交量数据，设为0
                else:
                    raise ValueError(f"ETF数据缺少必需列: {col}")
        
        # 只保留OHLCV列
        data = data[required_columns]
        
        return data

    def get_etf_list(self, category: str = None) -> Dict[str, str]:
        """
        获取ETF列表
        
        Args:
            category: ETF分类 ('宽基指数', '行业主题', '海外市场', '债券固收')
            
        Returns:
            ETF代码和名称的字典
        """
        from config import ETF_CONFIG
        
        if category is None:
            return ETF_CONFIG['popular_etfs']
        elif category in ETF_CONFIG['etf_categories']:
            category_codes = ETF_CONFIG['etf_categories'][category]
            return {code: ETF_CONFIG['popular_etfs'][code] for code in category_codes}
        else:
            return {}

    def get_etf_info(self, etf_code: str) -> Dict:
        """
        获取ETF信息
        
        Args:
            etf_code: ETF代码
            
        Returns:
            ETF信息字典
        """
        from config import ETF_CONFIG
        
        # 从配置中获取基本信息
        etf_name = ETF_CONFIG['popular_etfs'].get(etf_code, f'ETF_{etf_code}')
        
        # 判断ETF类别
        etf_category = 'Unknown'
        for category, codes in ETF_CONFIG['etf_categories'].items():
            if etf_code in codes:
                etf_category = category
                break
        
        return {
            'name': etf_name,
            'code': etf_code,
            'category': etf_category,
            'type': 'ETF'
        }

    def is_etf_code(self, symbol: str) -> bool:
        """
        判断是否为ETF代码
        
        Args:
            symbol: 股票/ETF代码
            
        Returns:
            是否为ETF代码
        """
        from config import ETF_CONFIG
        return symbol in ETF_CONFIG['popular_etfs']

    def get_stock_info(self, symbol: str) -> Dict:
        """
        获取股票信息
        
        Args:
            symbol: 股票代码
            
        Returns:
            股票信息字典
        """
        # 检查是否为ETF代码
        if self.is_etf_code(symbol):
            return self.get_etf_info(symbol)
        
        # 使用AKShare获取股票信息
        try:
            return self._get_stock_info_akshare(symbol)
        except Exception as e:
            raise Exception(f"无法获取股票{symbol}信息: {str(e)}")
    
    def _get_stock_info_akshare(self, symbol: str) -> Dict:
        """使用AKShare获取股票信息"""
        if not AKSHARE_AVAILABLE:
            raise Exception("AKShare未安装")
        
        try:
            ak_symbol = self._convert_to_akshare_symbol(symbol)
            
            # 获取股票基本信息
            stock_info = ak.stock_individual_info_em(symbol=ak_symbol)
            
            if stock_info.empty:
                raise ValueError("无法获取股票信息")
            
            # 解析股票信息
            info_dict = {}
            for _, row in stock_info.iterrows():
                info_dict[row['item']] = row['value']
            
            return {
                'name': info_dict.get('股票简称', symbol),
                'sector': info_dict.get('行业', 'Unknown'),
                'industry': info_dict.get('细分行业', 'Unknown'),
                'market_cap': self._parse_market_cap(info_dict.get('总市值', '0')),
                'pe_ratio': self._parse_number(info_dict.get('市盈率', '0')),
                'dividend_yield': 0
            }
        except Exception as e:
            raise Exception(f"AKShare获取股票信息失败: {str(e)}")
    

    def _parse_market_cap(self, value_str: str) -> float:
        """解析市值字符串"""
        try:
            if isinstance(value_str, (int, float)):
                return float(value_str)
            
            value_str = str(value_str).strip()
            if '万亿' in value_str:
                return float(value_str.replace('万亿', '')) * 1e12
            elif '千亿' in value_str:
                return float(value_str.replace('千亿', '')) * 1e11
            elif '百亿' in value_str:
                return float(value_str.replace('百亿', '')) * 1e10
            elif '亿' in value_str:
                return float(value_str.replace('亿', '')) * 1e8
            else:
                return float(value_str)
        except:
            return 0
    
    def _parse_number(self, value_str: str) -> float:
        """解析数值字符串"""
        try:
            if isinstance(value_str, (int, float)):
                return float(value_str)
            
            # 移除非数字字符（除了小数点）
            import re
            value_str = re.sub(r'[^\d.-]', '', str(value_str))
            return float(value_str) if value_str else 0
        except:
            return 0
    
    def _clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        清理数据
        
        Args:
            data: 原始数据
            
        Returns:
            清理后的数据
        """
        # 去除缺失值
        data = data.dropna()
        
        # 确保索引是日期类型
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)
        
        # 排序
        data = data.sort_index()
        
        # 去除重复日期
        data = data[~data.index.duplicated(keep='first')]
        
        return data
    

    def calculate_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标
        
        Args:
            data: OHLCV数据
            
        Returns:
            包含技术指标的数据
        """
        result = data.copy()
        
        # 移动平均线
        result['SMA_20'] = result['Close'].rolling(window=20).mean()
        result['SMA_60'] = result['Close'].rolling(window=60).mean()
        result['EMA_12'] = result['Close'].ewm(span=12).mean()
        result['EMA_26'] = result['Close'].ewm(span=26).mean()
        
        # MACD
        result['MACD'] = result['EMA_12'] - result['EMA_26']
        result['MACD_Signal'] = result['MACD'].ewm(span=9).mean()
        result['MACD_Histogram'] = result['MACD'] - result['MACD_Signal']
        
        # RSI
        result['RSI'] = self._calculate_rsi(result['Close'])
        
        # 布林带
        result['BB_Upper'], result['BB_Middle'], result['BB_Lower'] = self._calculate_bollinger_bands(result['Close'])
        
        # 成交量指标
        result['Volume_SMA'] = result['Volume'].rolling(window=20).mean()
        
        return result
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, 
                                  std_dev: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算布林带"""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower
