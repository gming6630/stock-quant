"""数据浏览页面"""

import streamlit as st
import pandas as pd
from data.fetcher import get_kline, search_stocks
from visualization.charts import kline_chart

st.set_page_config(page_title="数据浏览", page_icon="📈", layout="wide")

st.title("📈 数据浏览")

# 从 query params 获取热门按钮点击
qp = st.query_params
default_code = qp.get("code", "")

# 搜索栏
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    keyword = st.text_input(
        "🔍 输入股票代码或名称",
        placeholder="例如：贵州茅台 或 600519",
        value=default_code if default_code else "",
        key="search_keyword",
    )
with col2:
    period = st.selectbox(
        "周期", ["daily", "weekly", "monthly"],
        format_func=lambda x: {"daily": "日线", "weekly": "周线", "monthly": "月线"}[x],
    )
with col3:
    adjust = st.selectbox(
        "复权", ["qfq", "hfq", ""],
        format_func=lambda x: {"qfq": "前复权", "hfq": "后复权", "": "不复权"}[x],
    )

if not keyword:
    st.info("👆 输入股票代码或名称开始搜索")

    # 热门股票
    cols = st.columns(5)
    hot_stocks = [
        ("600519", "贵州茅台"), ("000858", "五粮液"), ("300750", "宁德时代"),
        ("601318", "中国平安"), ("000333", "美的集团"), ("600036", "招商银行"),
        ("002594", "比亚迪"), ("300059", "东方财富"), ("601899", "紫金矿业"),
        ("600276", "恒瑞医药"),
    ]
    for i, (code, name) in enumerate(hot_stocks):
        with cols[i % 5]:
            if st.button(name, key=f"hot_{code}", use_container_width=True):
                st.query_params["code"] = code
                st.rerun()

else:
    results = search_stocks(keyword)

    if results.empty:
        st.warning(f"未找到匹配 '{keyword}' 的股票")
    else:
        st.success(f"找到 {len(results)} 只匹配股票")

        if len(results) > 1:
            options = [f"{r['code']} - {r['name']}" for _, r in results.head(20).iterrows()]
            selected = st.selectbox("选择股票", options)
            symbol = selected.split(" - ")[0]
        else:
            symbol = results.iloc[0]["code"]

        name = results[results["code"] == symbol]["name"].values[0]

        with st.spinner(f"正在加载 {name}({symbol}) 数据..."):
            df = get_kline(symbol, period=period, adjust=adjust)

        if df is None or df.empty:
            st.error("数据为空")
        else:
            days_ago = min(365, len(df))
            date_range = st.slider(
                "时间范围",
                min_value=df["date"].min().date(),
                max_value=df["date"].max().date(),
                value=(max(df["date"].min().date(), df["date"].max().date() - pd.Timedelta(days=days_ago)),
                       df["date"].max().date()),
            )
            mask = (df["date"].dt.date >= date_range[0]) & (df["date"].dt.date <= date_range[1])
            df_view = df[mask].copy()

            st.subheader(f"{name} ({symbol})")

            c1, c2, c3, c4, c5 = st.columns(5)
            latest = df_view.iloc[-1]
            prev = df_view.iloc[-2]
            chg = (latest["close"] - prev["close"]) / prev["close"] * 100
            c1.metric("最新价", f"{latest['close']:.2f}", f"{chg:+.2f}%")
            c2.metric("最高", f"{latest['high']:.2f}")
            c3.metric("最低", f"{latest['low']:.2f}")
            c4.metric("成交量", f"{latest.get('volume', 0)/1e6:.1f}M")
            c5.metric("日期", str(latest["date"].date()))

            fig = kline_chart(df_view, title=f"{name} ({symbol})", ma_lines=[5, 10, 20, 60])
            st.plotly_chart(fig, use_container_width=True)

            with st.expander("📋 原始数据"):
                st.dataframe(df_view.sort_values("date", ascending=False), use_container_width=True)
                st.download_button("⬇ 下载 CSV", df_view.to_csv(index=False), f"{symbol}.csv")
