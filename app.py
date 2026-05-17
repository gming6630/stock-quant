"""股票量化分析系统 — 主入口"""

import streamlit as st

st.set_page_config(
    page_title="股票量化分析系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📈 股票量化分析系统")

st.markdown("""
### 欢迎使用股票量化分析系统

本系统基于 Python + Streamlit + Akshare 构建，提供以下功能：

- **数据浏览** — 搜索股票、查看实时行情、历史K线数据
- **技术指标分析** — MA、MACD、RSI、KDJ、布林带等常用指标可视化
- **策略回测** — 内置双均线、MACD、RSI、布林带等策略，支持自定义参数回测
- **选股筛选** — 基于技术指标筛选符合条件的股票

使用左侧导航栏切换功能页面。
""")

# 侧边栏快速入口
with st.sidebar:
    st.markdown("### ⚙️ 系统设置")
    st.markdown("---")
    st.markdown("""
    **数据来源**: Akshare (免费)
    **回测资金**: 100万 (默认)
    **手续费**: 万三
    """)

    st.markdown("---")
    st.markdown("### 💡 使用提示")
    st.markdown("""
    1. 在「数据浏览」中搜索股票代码或名称
    2. 在「技术指标」中查看多指标分析
    3. 在「策略回测」中测试交易策略
    4. 在「选股筛选」中批量筛选股票
    """)
