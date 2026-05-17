"""策略回测页面"""

import streamlit as st
import pandas as pd
from data.fetcher import search_stocks, get_kline
from backtest.engine import run_backtest
from backtest.strategies import STRATEGIES
from visualization.charts import equity_curve_chart, drawdown_chart, monthly_returns_heatmap

st.set_page_config(page_title="策略回测", page_icon="💰", layout="wide")

st.title("💰 策略回测")

# 两栏布局
left, right = st.columns([1, 2])

with left:
    st.subheader("⚙️ 回测设置")

    # 股票选择
    keyword = st.text_input("股票代码或名称", placeholder="例如：600519", key="backtest_keyword")
    symbol = None

    if keyword:
        results = search_stocks(keyword)
        if not results.empty:
            if len(results) > 1:
                options = [f"{r['code']} - {r['name']}" for _, r in results.head(10).iterrows()]
                selected = st.selectbox("选择股票", options, key="backtest_select")
                symbol = selected.split(" - ")[0]
            else:
                symbol = results.iloc[0]["code"]

    # 策略选择
    strategy_key = st.selectbox(
        "选择策略",
        list(STRATEGIES.keys()),
        format_func=lambda x: STRATEGIES[x]["name"]
    )

    # 策略参数
    st.markdown("**策略参数**")
    default_params = STRATEGIES[strategy_key]["params"]
    user_params = {}

    if strategy_key == "dual_ma":
        user_params["fast"] = st.slider("快线周期", 3, 30, default_params.get("fast", 5))
        user_params["slow"] = st.slider("慢线周期", 10, 120, default_params.get("slow", 20))
    elif strategy_key == "macd":
        user_params["fast"] = st.slider("快线 (DIF)", 5, 30, default_params.get("fast", 12))
        user_params["slow"] = st.slider("慢线 (DEA)", 10, 60, default_params.get("slow", 26))
        user_params["signal"] = st.slider("信号线", 3, 20, default_params.get("signal", 9))
    elif strategy_key == "rsi":
        user_params["period"] = st.slider("RSI 周期", 5, 30, default_params.get("period", 14))
        user_params["oversold"] = st.slider("超卖阈值", 15, 40, default_params.get("oversold", 30))
        user_params["overbought"] = st.slider("超买阈值", 60, 85, default_params.get("overbought", 70))
    elif strategy_key == "bollinger":
        user_params["period"] = st.slider("布林带周期", 10, 50, default_params.get("period", 20))
        user_params["std"] = st.slider("标准差倍数", 1.0, 3.0, default_params.get("std", 2.0), 0.1)

    # 回测资金
    capital = st.number_input("初始资金 (万元)", min_value=1, max_value=10000, value=100, step=10) * 10000

    # 运行按钮
    run_bt = st.button("🚀 开始回测", type="primary", use_container_width=True)

with right:
    if not run_bt or not symbol:
        st.info("👈 在左侧设置回测参数，然后点击「开始回测」")

        # 策略说明
        with st.expander("📖 策略说明"):
            st.markdown("""
            **双均线策略**: 短期均线上穿长期均线买入，下穿卖出。适合趋势行情。

            **MACD 策略**: DIF 上穿 DEA 买入，下穿卖出。经典趋势跟踪策略。

            **RSI 策略**: RSI 低于超卖线买入，高于超买线卖出。适合震荡行情。

            **均线+RSI 复合**: 均线金叉且 RSI 未过热时买入。过滤假信号。

            **布林带策略**: 价格触及下轨买入，触及上轨卖出。均值回归策略。
            """)
    else:
        with st.spinner(f"正在回测 {symbol}..."):
            # 获取数据
            try:
                df = get_kline(symbol, period="daily", adjust="qfq")
            except Exception as e:
                st.error(f"获取数据失败: {e}")
                st.stop()

            if df is None or df.empty:
                st.error("返回数据为空")
            else:
                # 运行回测
                strategy_func = STRATEGIES[strategy_key]["func"]
                result, metrics = run_backtest(
                    df, strategy_func, strategy_params=user_params,
                    initial_capital=capital
                )

                if result is None or result.empty:
                    st.error("回测失败")
                else:
                    # 绩效指标
                    st.subheader("📊 绩效指标")

                    m_cols = st.columns(4)
                    metric_items = list(metrics.items())
                    for i, (k, v) in enumerate(metric_items[:8]):
                        with m_cols[i % 4]:
                            st.metric(k, v)

                    m_cols2 = st.columns(4)
                    for i, (k, v) in enumerate(metric_items[8:16]):
                        with m_cols2[i % 4]:
                            st.metric(k, v)

                    st.divider()

                    # 净值曲线
                    st.plotly_chart(equity_curve_chart(result), use_container_width=True)

                    # 回撤和月度热力图
                    dr_col1, dr_col2 = st.columns(2)
                    with dr_col1:
                        st.plotly_chart(drawdown_chart(result), use_container_width=True)
                    with dr_col2:
                        if len(result) > 60:
                            st.plotly_chart(monthly_returns_heatmap(result), use_container_width=True)
                        else:
                            st.info("数据不足一季，无法生成月度热力图")

                    # 详细数据
                    with st.expander("📋 回测明细数据"):
                        detail_df = result[["date", "close", "position", "signal",
                                            "return", "strategy_return", "equity", "benchmark"]].copy()
                        detail_df["return"] = (detail_df["return"] * 100).round(3)
                        detail_df["strategy_return"] = (detail_df["strategy_return"] * 100).round(3)
                        detail_df["equity"] = detail_df["equity"].round(0)
                        st.dataframe(detail_df.sort_values("date", ascending=False),
                                     use_container_width=True)
