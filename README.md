# 股票基金回测系统

这是一个功能完整的股票和基金回测系统，专注于中国股市数据分析，支持多种投资策略和性能分析指标。

## 功能特点

- 📈 **专业数据源**: AKShare（中国股市专业数据）
- 🎯 **多种投资策略**: 买入持有、移动平均、RSI、MACD、定投、均值回归等
- 📊 **完整性能分析**: 夏普比率、最大回撤、VaR、索提诺比率等专业指标
- 📉 **丰富可视化**: 交互式图表、回测报告、策略对比分析
- 🌐 **友好界面**: 现代化的Streamlit Web界面
- ⚡ **高性能引擎**: 支持参数优化、多策略并行回测
- 🇨🇳 **本土化**: 完美支持中国A股市场数据和分析
- 💼 **ETF支持**: 全面支持ETF回测，包含宽基、行业、海外、债券四大类ETF
- 🔄 **智能识别**: 自动识别股票和ETF代码，无缝切换数据源
- 🎯 **纯真实数据**: 完全基于AKShare真实市场数据，不使用任何模拟数据

## 系统要求

- **Python版本**: 3.10+ （推荐）
- **操作系统**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **内存**: 建议4GB以上

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 检查环境
```bash
python run.py check
```

### 3. 运行示例
```bash
python run.py example
```

### 4. 启动Web界面
```bash
python run.py web
```

## 使用方法

### 快速启动工具 (推荐)
```bash
python run.py web       # 启动Web界面
python run.py example   # 运行示例
python run.py etf       # 运行ETF示例
python run.py akshare   # 测试AKShare数据源
python run.py check     # 检查依赖
```

### 传统方式
```bash
# Web界面模式
streamlit run web_app.py
```

## 投资策略

- **买入持有策略** (Buy and Hold): 长期持有策略
- **定投策略** (Dollar Cost Averaging): 定期定额投资
- **移动平均策略** (Moving Average): 双均线交叉策略
- **均线突破策略** (MA Breakout): 价格突破20日均线策略
- **RSI策略**: 相对强弱指数策略
- **MACD策略**: 移动平均收敛发散策略
- **均值回归策略**: 价格回归均值策略

## ETF支持

系统全面支持ETF（交易所交易基金）回测，包含17只热门ETF：

### 🏛️ 宽基指数ETF
- **510300**: 沪深300ETF
- **510050**: 上证50ETF
- **510500**: 中证500ETF
- **512100**: 中证1000ETF

### 🏭 行业主题ETF
- **159915**: 创业板ETF
- **588000**: 科创50ETF
- **516100**: 金融科技ETF
- **159928**: 消费ETF
- **512200**: 房地产ETF
- **515170**: 食品饮料ETF

### 🌏 海外市场ETF
- **513100**: 纳指ETF
- **513500**: 标普500ETF
- **159941**: 纳指100ETF

### 💰 债券固收ETF
- **511010**: 国债ETF
- **511260**: 十年国债ETF
- **511220**: 城投债ETF

### ETF分析特色
- ✅ **自动识别**: 系统自动识别ETF代码，使用专用数据接口
- ✅ **分类管理**: 按投资类型分类展示，便于选择
- ✅ **跟踪分析**: 与标的指数对比，分析跟踪误差
- ✅ **组合回测**: 支持多ETF组合投资回测
- ✅ **混合投资**: 支持股票与ETF混合回测

## 性能指标

- **基础指标**: 总收益率、年化收益率、波动率
- **风险指标**: 最大回撤、VaR、下行波动率
- **风险调整收益**: 夏普比率、索提诺比率、卡玛比率
- **交易指标**: 胜率、盈亏比、交易次数

## 数据源说明

系统使用AKShare作为数据源，专注于中国股市：

- **数据源**: AKShare - 中国股票、基金、期货等金融数据
- **数据缓存**: 支持本地数据缓存，减少重复请求
- **自动重试**: 内置重试机制，提高数据获取稳定性

## 项目结构

```
stock/
├── run.py              # 快速启动工具
├── web_app.py          # Web界面
├── data_handler.py     # 数据处理模块
├── strategies.py       # 投资策略模块
├── backtest_engine.py  # 回测引擎
├── performance.py      # 性能分析模块
├── visualization.py    # 可视化模块
├── example.py          # 使用示例
├── etf_example.py      # ETF回测示例
├── test_akshare.py     # AKShare测试
├── config.py           # 配置文件
└── requirements.txt    # 依赖清单
```

## 示例代码

```python
from data_handler import DataHandler
from strategies import BuyAndHoldStrategy
from backtest_engine import BacktestEngine

# 创建数据处理器
data_handler = DataHandler()

# 获取股票数据
data = data_handler.get_stock_data('000001', '2024-01-01', '2024-12-31')

# 创建策略
strategy = BuyAndHoldStrategy()

# 运行回测
engine = BacktestEngine(initial_capital=100000)
results = engine.run_backtest(data, strategy)

print(f"总收益率: {results['total_return']:.2%}")
print(f"夏普比率: {results['sharpe_ratio']:.2f}")
```

### ETF回测示例

```python
from data_handler import DataHandler
from strategies import BuyAndHoldStrategy
from backtest_engine import BacktestEngine

# 创建数据处理器
data_handler = DataHandler()

# ETF回测（沪深300ETF）
etf_data = data_handler.get_etf_data('510300', '2024-01-01', '2024-03-31')

# 创建策略
strategy = BuyAndHoldStrategy()

# 运行回测，与沪深300指数对比
engine = BacktestEngine(initial_capital=100000)
results = engine.run_backtest(
    symbols=['510300'], 
    strategy=strategy,
    start_date='2024-01-01',
    end_date='2024-03-31',
    benchmark='sh000300'
)

print(f"ETF收益率: {results['total_return']:.2%}")
print(f"基准收益率: {benchmark_return:.2%}")
print(f"跟踪误差: {results['total_return'] - benchmark_return:.2%}")
```

## 常见问题

**Q: 为什么不使用yfinance？**  
A: 为了专注于中国股市，我们选择了AKShare作为主要数据源，它为A股市场提供了更专业、更稳定的数据服务。

**Q: 没有网络时可以使用吗？**  
A: 系统需要网络连接以获取AKShare的实时数据。建议在有稳定网络环境下使用以获得最佳体验。

**Q: 支持哪些股票代码？**  
A: 支持所有A股股票代码（6位数字），以及常见美股代码（会自动映射到对应的A股进行演示）。

**Q: 支持ETF投资回测吗？**  
A: 完全支持！系统内置17只热门ETF，涵盖宽基指数、行业主题、海外市场、债券固收四大类，支持ETF与股票混合回测。

## 贡献指南

欢迎提交Issue和Pull Request！

## 许可证

本项目使用MIT许可证。