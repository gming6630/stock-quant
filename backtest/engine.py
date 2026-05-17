"""向量化回测引擎"""

import pandas as pd
import numpy as np
from config import INITIAL_CAPITAL, COMMISSION_RATE, SLIPPAGE, RISK_FREE_RATE


def run_backtest(df, strategy_func, strategy_params=None,
                 initial_capital=INITIAL_CAPITAL,
                 commission=COMMISSION_RATE,
                 slippage=SLIPPAGE):
    """
    向量化回测引擎

    参数:
        df: K 线 DataFrame，必须包含 open, high, low, close, volume, date
        strategy_func: 策略函数，接受 df 和 params，返回带 position/signal 列的 DataFrame
        strategy_params: 策略参数字典
        initial_capital: 初始资金
        commission: 手续费率
        slippage: 滑点

    返回:
        result_df: 逐日回测结果
        metrics: 绩效指标字典
    """
    if strategy_params is None:
        strategy_params = {}

    # 执行策略
    strategy_df = strategy_func(df, **strategy_params)

    # 构建回测结果
    result = pd.DataFrame(index=df.index)
    result["date"] = df["date"]
    result["close"] = df["close"]
    result["signal"] = strategy_df.get("signal", 0)
    result["position"] = strategy_df.get("position", 0)

    # 只做多（position 为 0 或 1）
    result["position"] = result["position"].clip(0, 1)

    # 计算收益率
    result["return"] = df["close"].pct_change().fillna(0)

    # 滑点影响
    result["slippage_cost"] = abs(result["signal"]) * slippage

    # 策略收益（不含手续费）
    result["strategy_return"] = result["position"].shift(1).fillna(0) * result["return"]
    result["strategy_return"] = result["strategy_return"] - result["slippage_cost"]

    # 扣除手续费
    result["commission_cost"] = abs(result["signal"]) * commission
    result["strategy_return"] = result["strategy_return"] - result["commission_cost"]

    # 累计收益
    result["cum_return"] = (1 + result["return"]).cumprod()
    result["cum_strategy"] = (1 + result["strategy_return"]).cumprod()

    # 净值
    result["equity"] = initial_capital * result["cum_strategy"]
    result["benchmark"] = initial_capital * result["cum_return"]

    # 计算指标
    metrics = compute_metrics(result, initial_capital)

    return result, metrics


def compute_metrics(result, initial_capital):
    """计算绩效指标"""
    n_days = len(result)
    if n_days == 0:
        return {}

    # 年化参数
    trading_days = 252
    years = n_days / trading_days

    # 最终净值
    final_equity = result["equity"].iloc[-1]
    final_benchmark = result["benchmark"].iloc[-1]

    # 收益率
    total_return = (final_equity / initial_capital - 1) * 100
    annual_return = (final_equity / initial_capital) ** (1 / max(years, 0.25)) - 1

    # 基准收益
    benchmark_return = (final_benchmark / initial_capital - 1) * 100

    # 夏普比率
    excess = result["strategy_return"] - RISK_FREE_RATE / trading_days
    sharpe = np.sqrt(trading_days) * excess.mean() / excess.std() if excess.std() > 0 else 0

    # 最大回撤
    equity_curve = result["equity"]
    rolling_max = equity_curve.cummax()
    drawdown = (equity_curve - rolling_max) / rolling_max
    max_drawdown = drawdown.min() * 100
    max_dd_date = result.loc[drawdown.idxmin(), "date"] if not drawdown.empty else None

    # 胜率
    trades = result[result["signal"] > 0]
    if len(trades) > 0:
        trade_returns = []
        for idx in trades.index:
            pos = result.loc[idx:, "position"]
            exit_idx = pos[pos == 0].index
            if len(exit_idx) > 0:
                exit_i = exit_idx[0]
                ret = result.loc[idx:exit_i, "return"].sum()
                trade_returns.append(ret)
        if trade_returns:
            win_rate = sum(1 for r in trade_returns if r > 0) / len(trade_returns) * 100
            avg_win = np.mean([r for r in trade_returns if r > 0]) * 100 if any(r > 0 for r in trade_returns) else 0
            avg_loss = np.mean([r for r in trade_returns if r < 0]) * 100 if any(r < 0 for r in trade_returns) else 0
        else:
            win_rate = avg_win = avg_loss = 0
    else:
        win_rate = avg_win = avg_loss = 0

    # 卡玛比率
    calmar = annual_return / abs(max_drawdown / 100) if max_drawdown != 0 else 0

    # 交易次数
    trade_count = int(result["signal"].abs().sum() / 2)

    return {
        "初始资金": f"{initial_capital:,.0f}",
        "最终净值": f"{final_equity:,.0f}",
        "总收益率": f"{total_return:.2f}%",
        "年化收益率": f"{annual_return * 100:.2f}%",
        "基准收益率": f"{benchmark_return:.2f}%",
        "超额收益": f"{total_return - benchmark_return:.2f}%",
        "夏普比率": f"{sharpe:.2f}",
        "最大回撤": f"{max_drawdown:.2f}%",
        "最大回撤日期": str(max_dd_date.date()) if max_dd_date else "N/A",
        "卡玛比率": f"{calmar:.2f}",
        "胜率": f"{win_rate:.1f}%",
        "平均盈利": f"{avg_win:.2f}%",
        "平均亏损": f"{avg_loss:.2f}%",
        "交易次数": trade_count,
        "回测天数": n_days,
    }
