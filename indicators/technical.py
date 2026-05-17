"""技术指标计算模块"""

import pandas as pd
import numpy as np


# ── 均线 ──────────────────────────────────────────────────

def ma(df, periods=None):
    """移动平均线 MA"""
    if periods is None:
        periods = [5, 10, 20, 60]
    result = df.copy()
    for p in periods:
        result[f"MA{p}"] = result["close"].rolling(window=p).mean()
    return result


def ema(df, periods=None):
    """指数移动平均线 EMA"""
    if periods is None:
        periods = [12, 26]
    result = df.copy()
    for p in periods:
        result[f"EMA{p}"] = result["close"].ewm(span=p, adjust=False).mean()
    return result


# ── MACD ──────────────────────────────────────────────────

def macd(df, fast=12, slow=26, signal=9):
    """MACD 指标"""
    result = df.copy()
    result["EMA_fast"] = result["close"].ewm(span=fast, adjust=False).mean()
    result["EMA_slow"] = result["close"].ewm(span=slow, adjust=False).mean()
    result["DIF"] = result["EMA_fast"] - result["EMA_slow"]
    result["DEA"] = result["DIF"].ewm(span=signal, adjust=False).mean()
    result["MACD"] = 2 * (result["DIF"] - result["DEA"])
    return result


# ── RSI ───────────────────────────────────────────────────

def rsi(df, period=14):
    """RSI 相对强弱指标"""
    result = df.copy()
    delta = result["close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    result["RSI"] = 100 - (100 / (1 + rs))
    return result


# ── KDJ ───────────────────────────────────────────────────

def kdj(df, n=9, k_smooth=3, d_smooth=3):
    """KDJ 随机指标"""
    result = df.copy()
    low_n = result["low"].rolling(window=n).min()
    high_n = result["high"].rolling(window=n).max()
    rsv = ((result["close"] - low_n) / (high_n - low_n).replace(0, np.nan)) * 100
    result["K"] = rsv.ewm(alpha=1 / k_smooth, adjust=False).mean()
    result["D"] = result["K"].ewm(alpha=1 / d_smooth, adjust=False).mean()
    result["J"] = 3 * result["K"] - 2 * result["D"]
    return result


# ── 布林带 ────────────────────────────────────────────────

def bollinger(df, period=20, std=2):
    """布林带 BOLL"""
    result = df.copy()
    result["BOLL_MID"] = result["close"].rolling(window=period).mean()
    std_val = result["close"].rolling(window=period).std()
    result["BOLL_UP"] = result["BOLL_MID"] + std * std_val
    result["BOLL_DN"] = result["BOLL_MID"] - std * std_val
    result["BOLL_WIDTH"] = (result["BOLL_UP"] - result["BOLL_DN"]) / result["BOLL_MID"] * 100
    return result


# ── ATR ───────────────────────────────────────────────────

def atr(df, period=14):
    """ATR 平均真实波幅"""
    result = df.copy()
    result["TR"] = np.maximum(
        result["high"] - result["low"],
        np.maximum(
            abs(result["high"] - result["close"].shift(1)),
            abs(result["low"] - result["close"].shift(1))
        )
    )
    result["ATR"] = result["TR"].ewm(alpha=1 / period, adjust=False).mean()
    return result


# ── OBV ───────────────────────────────────────────────────

def obv(df):
    """OBV 能量潮"""
    result = df.copy()
    result["OBV"] = (np.sign(result["close"].diff()) * result["volume"]).fillna(0).cumsum()
    return result


# ── 成交量加权均价 ─────────────────────────────────────────

def vwap(df):
    """VWAP 成交量加权平均价格"""
    result = df.copy()
    result["VWAP"] = ((result["high"] + result["low"] + result["close"]) / 3 * result["volume"]).cumsum() / \
                     result["volume"].cumsum()
    return result


# ── 全部指标 ──────────────────────────────────────────────

def compute_all(df):
    """计算所有技术指标并合并"""
    df = ma(df)
    df = macd(df)
    df = rsi(df)
    df = kdj(df)
    df = bollinger(df)
    df = atr(df)
    df = obv(df)
    df = vwap(df)
    return df


# ── 趋势与信号 ────────────────────────────────────────────

def detect_signals(df):
    """
    基于技术指标生成交易信号
    返回包含金叉/死叉、超买/超卖等信号的 DataFrame
    """
    df = df.copy()

    # 确保有指标数据
    if "DIF" not in df.columns:
        df = compute_all(df)

    # MACD 金叉/死叉
    df["MACD_CROSS"] = 0
    df.loc[(df["DIF"] > df["DEA"]) & (df["DIF"].shift(1) <= df["DEA"].shift(1)), "MACD_CROSS"] = 1   # 金叉
    df.loc[(df["DIF"] < df["DEA"]) & (df["DIF"].shift(1) >= df["DEA"].shift(1)), "MACD_CROSS"] = -1  # 死叉

    # MA 金叉/死叉 (MA5 与 MA20)
    if "MA5" in df.columns and "MA20" in df.columns:
        df["MA_CROSS"] = 0
        df.loc[(df["MA5"] > df["MA20"]) & (df["MA5"].shift(1) <= df["MA20"].shift(1)), "MA_CROSS"] = 1
        df.loc[(df["MA5"] < df["MA20"]) & (df["MA5"].shift(1) >= df["MA20"].shift(1)), "MA_CROSS"] = -1

    # RSI 超买/超卖
    df["RSI_STATE"] = "normal"
    df.loc[df["RSI"] > 70, "RSI_STATE"] = "overbought"
    df.loc[df["RSI"] < 30, "RSI_STATE"] = "oversold"

    # KDJ 超买/超卖
    df["KDJ_STATE"] = "normal"
    df.loc[(df["K"] > 80) & (df["D"] > 80), "KDJ_STATE"] = "overbought"
    df.loc[(df["K"] < 20) & (df["D"] < 20), "KDJ_STATE"] = "oversold"

    # 布林带位置
    df["BOLL_POS"] = "middle"
    df.loc[df["close"] > df["BOLL_UP"], "BOLL_POS"] = "above_upper"
    df.loc[df["close"] < df["BOLL_DN"], "BOLL_POS"] = "below_lower"

    # 综合信号评分
    df["SIGNAL"] = 0
    df.loc[df["MACD_CROSS"] == 1, "SIGNAL"] += 2
    df.loc[df["MACD_CROSS"] == -1, "SIGNAL"] -= 2
    df.loc[df["RSI_STATE"] == "oversold", "SIGNAL"] += 1
    df.loc[df["RSI_STATE"] == "overbought", "SIGNAL"] -= 1
    if "MA_CROSS" in df.columns:
        df.loc[df["MA_CROSS"] == 1, "SIGNAL"] += 2
        df.loc[df["MA_CROSS"] == -1, "SIGNAL"] -= 2

    return df
