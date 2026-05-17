"""全局配置"""

# 默认参数
DEFAULT_INDEX = "000300"       # 默认沪深300
DEFAULT_PERIOD = "daily"       # 日线
DEFAULT_LOOKBACK = 365         # 默认回看天数
RISK_FREE_RATE = 0.03          # 无风险利率 3%

# 技术指标默认参数
MA_PERIODS = [5, 10, 20, 60]   # 均线周期
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
RSI_PERIOD = 14
KDJ_N = 9
BOLL_PERIOD = 20
BOLL_STD = 2

# 初始资金
INITIAL_CAPITAL = 1_000_000     # 100万

# 回测手续费
COMMISSION_RATE = 0.0003        # 万三
SLIPPAGE = 0.001               # 千分之一滑点

# 缓存路径
CACHE_DIR = ".cache"
