"""技术指标分析页面"""

import streamlit as st
import pandas as pd
from data.fetcher import search_stocks, get_kline
from indicators.technical import compute_all, detect_signals
from visualization.charts import kline_chart, indicator_overview_chart

st.set_page_config(page_title="技术指标分析", page_icon="📊", layout="wide")

st.title("📊 技术指标分析")

# 股票选择
col1, col2 = st.columns([3, 1])
with col1:
    keyword = st.text_input("股票代码或名称", placeholder="例如：600519", key="indicator_keyword")
with col2:
    lookback = st.number_input("回看天数", min_value=60, max_value=2000, value=365, step=30)

if not keyword:
    st.info("👆 请输入股票代码开始技术分析")
else:
    results = search_stocks(keyword)
    if results.empty:
        st.error("未找到匹配股票")
    else:
        if len(results) > 1:
            options = [f"{r['code']} - {r['name']}" for _, r in results.head(10).iterrows()]
            selected = st.selectbox("选择股票", options, key="indicator_select")
            symbol, name = selected.split(" - ", 1)
        else:
            symbol = results.iloc[0]["code"]
            name = results.iloc[0]["name"]

        with st.spinner(f"正在计算 {symbol} 技术指标..."):
            try:
                df = get_kline(symbol, period="daily", adjust="qfq")
            except Exception as e:
                st.error(f"获取数据失败: {e}")
                st.info("💡 可能是网络波动或接口限流，请稍后重试")
                st.stop()
            if df is not None and not df.empty:
                df = df.tail(lookback).copy()
                df = compute_all(df)
                df = detect_signals(df)

        if df is None or df.empty:
            st.error("返回数据为空")
        else:
            # 最新信号
            latest = df.iloc[-1]
            st.subheader(f"{name} ({symbol}) — 最新信号")

            sig_cols = st.columns(6)
            with sig_cols[0]:
                rsi_val = latest.get("RSI", 0)
                rsi_delta = "🟢 超卖" if rsi_val < 30 else ("🔴 超买" if rsi_val > 70 else "⚪ 正常")
                st.metric("RSI", f"{rsi_val:.1f}", rsi_delta)
            with sig_cols[1]:
                macd_val = latest.get("MACD", 0)
                st.metric("MACD柱", f"{macd_val:.3f}")
            with sig_cols[2]:
                dif = latest.get("DIF", 0)
                dea = latest.get("DEA", 0)
                st.metric("DIF/DEA", f"{dif:.3f}/{dea:.3f}", "金叉↑" if dif > dea else "死叉↓")
            with sig_cols[3]:
                k = latest.get("K", 0)
                d = latest.get("D", 0)
                kdj_state = "超买" if k > 80 and d > 80 else ("超卖" if k < 20 and d < 20 else "正常")
                st.metric("KDJ (K/D)", f"{k:.1f}/{d:.1f}", kdj_state)
            with sig_cols[4]:
                close = latest["close"]
                boll_up = latest.get("BOLL_UP", close)
                boll_dn = latest.get("BOLL_DN", close)
                pos = "上轨附近" if close >= boll_up * 0.98 else ("下轨附近" if close <= boll_dn * 1.02 else "中轨附近")
                st.metric("布林带位置", pos)
            with sig_cols[5]:
                signal_score = latest.get("SIGNAL", 0)
                emoji = "🟢" if signal_score > 1 else ("🔴" if signal_score < -1 else "⚪")
                st.metric("综合信号", f"{signal_score}", emoji)

            st.divider()

            # 图表模式选择
            chart_mode = st.radio(
                "图表模式",
                ["K线 + 指标", "指标全景图", "纯K线"],
                horizontal=True,
                key="chart_mode"
            )

            if chart_mode == "K线 + 指标":
                sub_col1, sub_col2, sub_col3, sub_col4 = st.columns(4)
                with sub_col1:
                    show_macd = st.checkbox("MACD", True)
                with sub_col2:
                    show_rsi = st.checkbox("RSI", True)
                with sub_col3:
                    show_kdj = st.checkbox("KDJ", False)
                with sub_col4:
                    show_boll = st.checkbox("布林带", False)

                fig = kline_chart(
                    df, title=f"{name} ({symbol}) 技术分析",
                    ma_lines=[5, 10, 20, 60],
                    macd=show_macd, rsi=show_rsi, kdj=show_kdj, boll=show_boll
                )
                st.plotly_chart(fig, use_container_width=True)

            elif chart_mode == "指标全景图":
                fig = indicator_overview_chart(df)
                st.plotly_chart(fig, use_container_width=True)

            else:
                fig = kline_chart(df, title=f"{name} ({symbol}) K线图", ma_lines=[5, 10, 20])
                st.plotly_chart(fig, use_container_width=True)

            # 指标数据表
            with st.expander("📋 指标数据"):
                show_cols = ["date", "close", "RSI", "DIF", "DEA", "MACD", "K", "D", "J", "SIGNAL"]
                available = [c for c in show_cols if c in df.columns]
                st.dataframe(df[available].tail(60).sort_values("date", ascending=False),
                             use_container_width=True)
