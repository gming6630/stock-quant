"""选股筛选页面"""

import streamlit as st
import pandas as pd
from data.fetcher import get_realtime_quote

st.set_page_config(page_title="选股筛选", page_icon="🔍", layout="wide")

st.title("🔍 选股筛选")

st.info("基于实时行情数据进行条件筛选。数据快照每 3 分钟自动刷新。")

# 刷新按钮
col_btn, col_note = st.columns([1, 5])
with col_btn:
    refresh = st.button("🔄 刷新数据", type="primary")
with col_note:
    st.caption("数据来源：东方财富实时行情")

# 筛选条件
with st.expander("⚙️ 筛选条件", expanded=True):
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        price_min = st.number_input("最低价格", 0.0, 10000.0, 0.0, 0.01)
        price_max = st.number_input("最高价格", 0.0, 10000.0, 500.0, 0.01)

    with c2:
        pe_max = st.number_input("市盈率上限", 0.0, 10000.0, 100.0, 0.1,
                                 help="市盈率(动态)不超过该值")
        pb_max = st.number_input("市净率上限", 0.0, 100.0, 10.0, 0.1,
                                 help="市净率不超过该值")

    with c3:
        mv_min = st.number_input("总市值下限 (亿)", 0.0, 100000.0, 0.0, 1.0,
                                 help="总市值不低于该值")
        turnover_min = st.number_input("换手率下限 (%)", 0.0, 100.0, 0.0, 0.1,
                                       help="换手率不低于该值")

    with c4:
        pct_min = st.number_input("涨跌幅下限 (%)", -20.0, 20.0, -10.0, 0.1)
        pct_max = st.number_input("涨跌幅上限 (%)", -20.0, 20.0, 10.0, 0.1)
        top_n = st.number_input("最多显示", 10, 500, 50, 10)

    do_filter = st.button("🔍 开始筛选", type="primary", use_container_width=True)

if not do_filter and not refresh:
    st.markdown("""
    ### 预设筛选模板

    点击以下按钮快速应用常见筛选条件：
    """)

    templates = st.columns(4)
    with templates[0]:
        if st.button("💎 低估值蓝筹", use_container_width=True):
            st.session_state["filter_pe_max"] = 15.0
            st.session_state["filter_pb_max"] = 2.0
            st.session_state["filter_mv_min"] = 100.0
            st.session_state["filter_pct_min"] = -3.0
            st.rerun()
    with templates[1]:
        if st.button("🚀 高成长股", use_container_width=True):
            st.session_state["filter_pe_max"] = 50.0
            st.session_state["filter_turnover_min"] = 3.0
            st.session_state["filter_pct_min"] = 1.0
            st.session_state["filter_mv_min"] = 50.0
            st.rerun()
    with templates[2]:
        if st.button("📉 超跌反弹", use_container_width=True):
            st.session_state["filter_pct_max"] = -3.0
            st.session_state["filter_turnover_min"] = 2.0
            st.session_state["filter_price_max"] = 50.0
            st.rerun()
    with templates[3]:
        if st.button("📊 高换手活跃", use_container_width=True):
            st.session_state["filter_turnover_min"] = 5.0
            st.session_state["filter_pct_min"] = -5.0
            st.session_state["filter_pct_max"] = 5.0
            st.rerun()
else:
    with st.spinner("正在获取实时行情数据..."):
        df = get_realtime_quote()

    if df is None or df.empty:
        st.error("获取实时行情失败，请检查网络连接")
    else:
        st.success(f"已获取 {len(df)} 只股票的实时行情")

        # 执行筛选
        mask = pd.Series(True, index=df.index)

        if price_min > 0:
            mask &= df["price"] >= price_min
        if price_max < 500:
            mask &= df["price"] <= price_max
        if pe_max < 100:
            mask &= df.get("pe", 9999).fillna(9999).astype(float) <= pe_max
        if pb_max < 10:
            mask &= df.get("pb", 999).fillna(999).astype(float) <= pb_max
        if mv_min > 0:
            mask &= df.get("total_mv", 0).fillna(0).astype(float) / 1e8 >= mv_min
        if turnover_min > 0:
            mask &= df.get("turnover", 0).fillna(0).astype(float) >= turnover_min
        if pct_min > -20:
            mask &= df.get("pct_change", -999).fillna(-999).astype(float) >= pct_min
        if pct_max < 20:
            mask &= df.get("pct_change", 999).fillna(999).astype(float) <= pct_max

        # 排除 ST、退市整理
        if "name" in df.columns:
            mask &= ~df["name"].str.contains("ST|退市", na=True)

        result_df = df[mask].copy()

        if result_df.empty:
            st.warning("没有符合条件的股票，请放宽筛选条件")
        else:
            st.subheader(f"筛选结果 — 共 {len(result_df)} 只")

            # 按涨跌幅排序展示
            display_cols = ["code", "name", "price", "pct_change", "change",
                            "volume", "turnover", "pe", "pb", "total_mv"]
            available = [c for c in display_cols if c in result_df.columns]

            display_df = result_df[available].head(top_n).copy()

            # 格式化
            if "price" in display_df.columns:
                display_df["price"] = display_df["price"].astype(float).round(2)
            if "pct_change" in display_df.columns:
                display_df["pct_change"] = display_df["pct_change"].astype(float).round(2)
            if "turnover" in display_df.columns:
                display_df["turnover"] = display_df["turnover"].astype(float).round(2)
            if "pe" in display_df.columns:
                display_df["pe"] = display_df["pe"].astype(float).round(1)
            if "pb" in display_df.columns:
                display_df["pb"] = display_df["pb"].astype(float).round(2)
            if "total_mv" in display_df.columns:
                display_df["total_mv"] = (display_df["total_mv"].astype(float) / 1e8).round(1)

            # 自定义列名
            col_labels = {
                "code": "代码", "name": "名称", "price": "最新价",
                "pct_change": "涨跌幅%", "change": "涨跌额",
                "volume": "成交量", "turnover": "换手率%",
                "pe": "市盈率", "pb": "市净率", "total_mv": "总市值(亿)"
            }
            display_df = display_df.rename(columns={k: v for k, v in col_labels.items() if k in display_df.columns})

            # 高亮样式
            def highlight_pct(val):
                try:
                    v = float(val)
                    if v > 0:
                        return "color: #e53935"
                    elif v < 0:
                        return "color: #43a047"
                except (ValueError, TypeError):
                    pass
                return ""

            st.dataframe(
                display_df.style.map(highlight_pct, subset=["涨跌幅%"] if "涨跌幅%" in display_df.columns else []),
                use_container_width=True,
                height=600,
            )

            # 导出
            csv = display_df.to_csv(index=False)
            st.download_button("⬇ 导出结果 CSV", csv, "stock_screener.csv", "text/csv")
