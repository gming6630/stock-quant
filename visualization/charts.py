"""可视化图表模块 — 基于 Plotly"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


def kline_chart(df, title="K 线图", ma_lines=None, volume=True,
                macd=False, rsi=False, kdj=False, boll=False):
    """
    K 线图（支持叠加技术指标）
    """
    # ── 动态计算 row 数量与高度 ──
    row_sections = [("main", 0.50)]  # K线主图
    if volume:
        row_sections.append(("volume", 0.15))
    if macd:
        row_sections.append(("macd", 0.15))
    if rsi:
        row_sections.append(("rsi", 0.10))
    if kdj:
        row_sections.append(("kdj", 0.10))

    total_rows = len(row_sections)
    row_heights = [s[1] for s in row_sections]

    fig = make_subplots(
        rows=total_rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=row_heights,
    )

    # row index map
    row_idx = {name: i + 1 for i, (name, _) in enumerate(row_sections)}
    cur = 1

    # ── Row: K线 ──
    fig.add_trace(
        go.Candlestick(
            x=df["date"], open=df["open"], high=df["high"],
            low=df["low"], close=df["close"],
            name="K线", showlegend=True
        ),
        row=cur, col=1
    )

    colors = ["#FF6B6B", "#4ECDC4", "#FFE66D", "#A8E6CF", "#FF8B94", "#B8A9C9"]
    if ma_lines:
        for i, p in enumerate(ma_lines):
            col_name = f"MA{p}"
            if col_name in df.columns:
                fig.add_trace(
                    go.Scatter(x=df["date"], y=df[col_name],
                               mode="lines", name=col_name,
                               line=dict(width=1.2, color=colors[i % len(colors)])),
                    row=cur, col=1
                )

    if boll and "BOLL_UP" in df.columns:
        fig.add_trace(
            go.Scatter(x=df["date"], y=df["BOLL_UP"], mode="lines",
                       name="BOLL上轨", line=dict(dash="dash", width=1, color="gray"),
                       showlegend=False),
            row=cur, col=1
        )
        fig.add_trace(
            go.Scatter(x=df["date"], y=df["BOLL_DN"], mode="lines",
                       name="BOLL下轨", line=dict(dash="dash", width=1, color="gray"),
                       fill="tonexty", fillcolor="rgba(128,128,128,0.1)",
                       showlegend=False),
            row=cur, col=1
        )
        fig.add_trace(
            go.Scatter(x=df["date"], y=df["BOLL_MID"], mode="lines",
                       name="BOLL中轨", line=dict(width=1, color="gray"),
                       showlegend=False),
            row=cur, col=1
        )
    cur += 1

    # ── Row: 成交量 ──
    if volume:
        vol_colors = ["#ef5350" if df["close"].iloc[i] >= df["open"].iloc[i] else "#26a69a"
                       for i in range(len(df))]
        fig.add_trace(
            go.Bar(x=df["date"], y=df["volume"], name="成交量",
                   marker=dict(color=vol_colors), showlegend=False),
            row=cur, col=1
        )
        fig.update_yaxes(title_text="成交量", row=cur, col=1)
        cur += 1

    # ── Row: MACD ──
    if macd and "DIF" in df.columns:
        macd_vals = df["MACD"].fillna(0)
        fig.add_trace(
            go.Bar(x=df["date"], y=macd_vals, name="MACD柱",
                   marker=dict(color=["#ef5350" if v >= 0 else "#26a69a" for v in macd_vals]),
                   showlegend=False),
            row=cur, col=1
        )
        fig.add_trace(
            go.Scatter(x=df["date"], y=df["DIF"], mode="lines",
                       name="DIF", line=dict(width=1.5, color="#2196F3")),
            row=cur, col=1
        )
        fig.add_trace(
            go.Scatter(x=df["date"], y=df["DEA"], mode="lines",
                       name="DEA", line=dict(width=1.5, color="#FF9800")),
            row=cur, col=1
        )
        fig.add_hline(y=0, line=dict(dash="dot", width=1, color="gray"),
                      row=cur, col=1)
        cur += 1

    # ── Row: RSI ──
    if rsi and "RSI" in df.columns:
        fig.add_trace(
            go.Scatter(x=df["date"], y=df["RSI"], mode="lines",
                       name="RSI", line=dict(width=1.5, color="#9C27B0")),
            row=cur, col=1
        )
        fig.add_hline(y=70, line=dict(dash="dash", width=1, color="red"),
                      row=cur, col=1)
        fig.add_hline(y=30, line=dict(dash="dash", width=1, color="green"),
                      row=cur, col=1)
        fig.add_hline(y=50, line=dict(dash="dot", width=0.5, color="gray"),
                      row=cur, col=1)
        cur += 1

    # ── Row: KDJ ──
    if kdj and "K" in df.columns:
        fig.add_trace(
            go.Scatter(x=df["date"], y=df["K"], mode="lines",
                       name="K", line=dict(width=1.5, color="#2196F3")),
            row=cur, col=1
        )
        fig.add_trace(
            go.Scatter(x=df["date"], y=df["D"], mode="lines",
                       name="D", line=dict(width=1.5, color="#FF9800")),
            row=cur, col=1
        )
        fig.add_trace(
            go.Scatter(x=df["date"], y=df["J"], mode="lines",
                       name="J", line=dict(width=1.5, color="#E91E63")),
            row=cur, col=1
        )
        fig.add_hline(y=80, line=dict(dash="dash", width=1, color="red"),
                      row=cur, col=1)
        fig.add_hline(y=20, line=dict(dash="dash", width=1, color="green"),
                      row=cur, col=1)

    # 布局
    fig.update_layout(
        title=title,
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        height=200 + 150 * total_rows,
        hovermode="x unified",
        legend=dict(orientation="h", y=1.12),
        margin=dict(l=10, r=10, t=50, b=10),
    )
    fig.update_yaxes(title_text="价格", row=1, col=1)

    return fig


def equity_curve_chart(result_df):
    """
    回测净值曲线对比图
    result_df: backtest engine 输出的结果 DataFrame
    """
    fig = go.Figure()

    # 策略净值
    fig.add_trace(go.Scatter(
        x=result_df["date"], y=result_df["equity"],
        mode="lines", name="策略净值",
        line=dict(width=2, color="#2196F3"),
        hovertemplate="日期: %{x}<br>净值: %{y:,.0f}<extra></extra>"
    ))

    # 基准净值（买入持有）
    fig.add_trace(go.Scatter(
        x=result_df["date"], y=result_df["benchmark"],
        mode="lines", name="买入持有",
        line=dict(width=1.5, color="#BDBDBD", dash="dash"),
        hovertemplate="日期: %{x}<br>基准: %{y:,.0f}<extra></extra>"
    ))

    # 回撤区域
    equity = result_df["equity"].values
    rolling_max = np.maximum.accumulate(equity)
    drawdown = (equity - rolling_max) / rolling_max * 100

    # 回撤曲线（叠加在右轴）
    fig.add_trace(go.Scatter(
        x=result_df["date"], y=drawdown,
        mode="lines", name="回撤%",
        line=dict(width=1, color="rgba(244,67,54,0.5)"),
        fill="tozeroy", fillcolor="rgba(244,67,54,0.1)",
        yaxis="y2",
        hovertemplate="日期: %{x}<br>回撤: %{y:.1f}%<extra></extra>"
    ))

    fig.update_layout(
        title="回测净值曲线",
        xaxis=dict(title=""),
        yaxis=dict(title="净值", side="left"),
        yaxis2=dict(title="回撤 (%)", side="right", overlaying="y", range=[drawdown.min() * 1.2, 0]),
        template="plotly_white",
        height=450,
        hovermode="x unified",
        legend=dict(orientation="h", y=1.12),
        margin=dict(l=10, r=10, t=50, b=10),
    )

    return fig


def drawdown_chart(result_df):
    """独立的回撤曲线图"""
    equity = result_df["equity"].values
    rolling_max = np.maximum.accumulate(equity)
    drawdown_pct = (equity - rolling_max) / rolling_max * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=result_df["date"], y=drawdown_pct,
        mode="lines", name="回撤",
        fill="tozeroy", fillcolor="rgba(244,67,54,0.2)",
        line=dict(width=1, color="#F44336"),
        hovertemplate="日期: %{x}<br>回撤: %{y:.2f}%<extra></extra>"
    ))
    fig.update_layout(
        title="回撤曲线",
        yaxis=dict(title="回撤 (%)", ticksuffix="%"),
        template="plotly_white",
        height=300,
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig


def monthly_returns_heatmap(result_df):
    """月度收益率热力图"""
    df = result_df.copy()
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    monthly = df.groupby(["year", "month"])["strategy_return"].apply(
        lambda x: (1 + x).prod() - 1
    ).unstack()
    monthly.index = monthly.index.astype(str)

    fig = go.Figure(data=go.Heatmap(
        z=monthly.values * 100,
        x=["1月", "2月", "3月", "4月", "5月", "6月",
           "7月", "8月", "9月", "10月", "11月", "12月"][:monthly.shape[1]],
        y=monthly.index,
        colorscale="RdYlGn",
        zmid=0,
        text=[[f"{v:.1f}%" if not np.isnan(v) else "" for v in row] for row in monthly.values],
        texttemplate="%{text}",
        hovertemplate="%{y}年%{x}<br>收益率: %{z:.2f}%<extra></extra>"
    ))
    fig.update_layout(
        title="月度收益率热力图",
        template="plotly_white",
        height=300,
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig


def signal_chart(df):
    """交易信号标记图"""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["date"], y=df["close"],
        mode="lines", name="收盘价",
        line=dict(width=1.5, color="#333"),
    ))

    # 买入信号
    buys = df[df["signal"] > 0]
    if len(buys) > 0:
        fig.add_trace(go.Scatter(
            x=buys["date"], y=buys["close"],
            mode="markers", name="买入",
            marker=dict(symbol="triangle-up", size=12, color="#4CAF50"),
        ))

    # 卖出信号
    sells = df[df["signal"] < 0]
    if len(sells) > 0:
        fig.add_trace(go.Scatter(
            x=sells["date"], y=sells["close"],
            mode="markers", name="卖出",
            marker=dict(symbol="triangle-down", size=12, color="#F44336"),
        ))

    fig.update_layout(
        title="交易信号",
        template="plotly_white",
        height=400,
        hovermode="x unified",
        legend=dict(orientation="h", y=1.12),
        margin=dict(l=10, r=10, t=50, b=10),
    )

    return fig


def indicator_overview_chart(df):
    """技术指标全景图 — 价格 + MACD + RSI + KDJ + 成交量 全部展示"""
    fig = make_subplots(
        rows=5, cols=1, shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.35, 0.15, 0.15, 0.15, 0.15],
        subplot_titles=("价格 / 布林带", "成交量", "MACD", "RSI", "KDJ"),
    )

    # Row 1: K线 + 布林带 + 均线
    fig.add_trace(go.Scatter(x=df["date"], y=df["close"], mode="lines",
                              name="收盘", line=dict(width=1.5, color="#333")), row=1, col=1)
    if "BOLL_UP" in df.columns:
        fig.add_trace(go.Scatter(x=df["date"], y=df["BOLL_UP"], mode="lines",
                                  name="上轨", line=dict(dash="dash", width=1, color="gray"),
                                  showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=df["date"], y=df["BOLL_DN"], mode="lines",
                                  name="下轨", line=dict(dash="dash", width=1, color="gray"),
                                  fill="tonexty", fillcolor="rgba(128,128,128,0.08)",
                                  showlegend=False), row=1, col=1)

    # Row 2: 成交量
    vol_colors = ["#ef5350" if df["close"].iloc[i] >= df["open"].iloc[i] else "#26a69a"
                  for i in range(len(df))]
    fig.add_trace(go.Bar(x=df["date"], y=df["volume"], name="量",
                          marker=dict(color=vol_colors), showlegend=False), row=2, col=1)

    # Row 3: MACD
    if "DIF" in df.columns:
        fig.add_trace(go.Bar(x=df["date"], y=df["MACD"].fillna(0), name="MACD柱",
                              marker=dict(color=["#ef5350" if v >= 0 else "#26a69a" for v in df["MACD"].fillna(0)]),
                              showlegend=False), row=3, col=1)
        fig.add_trace(go.Scatter(x=df["date"], y=df["DIF"], mode="lines",
                                  name="DIF", line=dict(width=1, color="#2196F3")), row=3, col=1)
        fig.add_trace(go.Scatter(x=df["date"], y=df["DEA"], mode="lines",
                                  name="DEA", line=dict(width=1, color="#FF9800")), row=3, col=1)

    # Row 4: RSI
    if "RSI" in df.columns:
        fig.add_trace(go.Scatter(x=df["date"], y=df["RSI"], mode="lines",
                                  name="RSI", line=dict(width=1.5, color="#9C27B0")), row=4, col=1)
        fig.add_hline(y=70, line=dict(dash="dash", width=1, color="red"), row=4, col=1)
        fig.add_hline(y=30, line=dict(dash="dash", width=1, color="green"), row=4, col=1)

    # Row 5: KDJ
    if "K" in df.columns:
        fig.add_trace(go.Scatter(x=df["date"], y=df["K"], mode="lines",
                                  name="K", line=dict(width=1, color="#2196F3")), row=5, col=1)
        fig.add_trace(go.Scatter(x=df["date"], y=df["D"], mode="lines",
                                  name="D", line=dict(width=1, color="#FF9800")), row=5, col=1)
        fig.add_hline(y=80, line=dict(dash="dash", width=1, color="red"), row=5, col=1)
        fig.add_hline(y=20, line=dict(dash="dash", width=1, color="green"), row=5, col=1)

    fig.update_layout(
        height=800,
        template="plotly_white",
        hovermode="x unified",
        showlegend=False,
        margin=dict(l=10, r=10, t=40, b=10),
    )

    return fig
