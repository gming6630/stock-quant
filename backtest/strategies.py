"""内置交易策略"""

import pandas as pd
import numpy as np
from indicators.technical import compute_all


def _ensure_indicators(df):
    """确保数据包含必要的技术指标"""
    required = ["DIF", "DEA", "RSI", "K", "D", "BOLL_UP", "BOLL_DN", "BOLL_MID"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        df = compute_all(df)
    return df


def dual_ma_strategy(df, fast=5, slow=20):
    """
    双均线策略
    快线上穿慢线 → 买入 (1)
    快线下穿慢线 → 卖出 (-1)
    """
    df = df.copy()
    df[f"MA{fast}"] = df["close"].rolling(window=fast).mean()
    df[f"MA{slow}"] = df["close"].rolling(window=slow).mean()
    df["position"] = 0
    df.loc[df[f"MA{fast}"] > df[f"MA{slow}"], "position"] = 1
    df.loc[df[f"MA{fast}"] < df[f"MA{slow}"], "position"] = -1
    df["signal"] = df["position"].diff().fillna(0)
    return df


def macd_strategy(df, fast=12, slow=26, signal=9):
    """
    MACD 策略
    DIF 上穿 DEA → 买入 (1)
    DIF 下穿 DEA → 卖出 (-1)
    """
    df = _ensure_indicators(df).copy()
    df["position"] = 0
    df.loc[df["DIF"] > df["DEA"], "position"] = 1
    df.loc[df["DIF"] < df["DEA"], "position"] = -1
    df["signal"] = df["position"].diff().fillna(0)
    return df


def rsi_strategy(df, period=14, oversold=30, overbought=70):
    """
    RSI 策略
    RSI 从超卖区回升 → 买入
    RSI 从超买区回落 → 卖出
    """
    df = _ensure_indicators(df).copy()
    df["position"] = 0
    # 持有信号：不在超买区且不在超卖区时维持
    df.loc[df["RSI"] < overbought, "position"] = df["position"].shift(1).fillna(0)
    df.loc[df["RSI"] < oversold, "position"] = 1       # 超卖 → 买入
    df.loc[df["RSI"] > overbought, "position"] = 0      # 超买 → 清仓
    df["position"] = df["position"].fillna(0)
    df["signal"] = df["position"].diff().fillna(0)
    return df


def ma_cross_rsi_strategy(df):
    """
    均线金叉 + RSI 确认策略
    MA5 上穿 MA20 且 RSI < 70 → 买入
    MA5 下穿 MA20 或 RSI > 80 → 卖出
    """
    df = _ensure_indicators(df).copy()
    df["MA5"] = df["close"].rolling(5).mean()
    df["MA20"] = df["close"].rolling(20).mean()

    df["position"] = 0
    # 买入条件
    buy = (df["MA5"] > df["MA20"]) & (df["MA5"].shift(1) <= df["MA20"].shift(1)) & (df["RSI"] < 70)
    # 卖出条件
    sell = ((df["MA5"] < df["MA20"]) & (df["MA5"].shift(1) >= df["MA20"].shift(1))) | (df["RSI"] > 80)

    in_position = False
    positions = []
    for i in range(len(df)):
        if buy.iloc[i] and not in_position:
            in_position = True
            positions.append(1)
        elif sell.iloc[i] and in_position:
            in_position = False
            positions.append(0)
        else:
            positions.append(1 if in_position else 0)
    df["position"] = positions
    df["signal"] = df["position"].diff().fillna(0)
    return df


def bollinger_strategy(df, period=20, std=2):
    """
    布林带策略
    价格触碰下轨 → 买入
    价格触碰上轨 → 卖出
    """
    df = _ensure_indicators(df).copy()
    df["position"] = 0
    df.loc[df["close"] >= df["BOLL_UP"], "position"] = 0        # 触及上轨清仓
    df.loc[df["close"] <= df["BOLL_DN"], "position"] = 1        # 触及下轨买入
    # 价格回归中轨维持仓位
    between = (df["close"] > df["BOLL_DN"]) & (df["close"] < df["BOLL_UP"])
    df.loc[between, "position"] = df.loc[between, "position"].fillna(method="ffill")
    df["position"] = df["position"].fillna(0)
    df["signal"] = df["position"].diff().fillna(0)
    return df


# 策略注册表
STRATEGIES = {
    "dual_ma": {"name": "双均线策略", "func": dual_ma_strategy,
                "params": {"fast": 5, "slow": 20}},
    "macd": {"name": "MACD 策略", "func": macd_strategy,
             "params": {"fast": 12, "slow": 26, "signal": 9}},
    "rsi": {"name": "RSI 策略", "func": rsi_strategy,
            "params": {"period": 14, "oversold": 30, "overbought": 70}},
    "ma_rsi": {"name": "均线+RSI 复合策略", "func": ma_cross_rsi_strategy, "params": {}},
    "bollinger": {"name": "布林带策略", "func": bollinger_strategy,
                  "params": {"period": 20, "std": 2}},
}
