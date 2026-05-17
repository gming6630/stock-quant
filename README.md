# 股票量化分析系统

基于 Python + Streamlit + 腾讯/东方财富数据源的 A 股量化分析 Web 应用。

## 功能

- **数据浏览** — 搜索股票、查看实时行情、历史 K 线数据
- **技术指标分析** — MA、MACD、RSI、KDJ、布林带、ATR、OBV、VWAP
- **策略回测** — 双均线、MACD、RSI、布林带、均线+RSI 复合策略
- **选股筛选** — 按价格、市盈率、市净率、市值、换手率等筛选

## 本地运行

```bash
git clone <repo-url>
cd stock_quant
pip install -r requirements.txt
streamlit run app.py
```

打开 http://localhost:8501

## Streamlit Cloud 部署

1. 将本项目推送到 **公开** GitHub 仓库
2. 访问 [share.streamlit.io](https://share.streamlit.io)
3. 点击 "New app"，选择你的仓库、分支、主文件 `app.py`
4. 点击 "Deploy"

部署后即可获得 `https://xxx.streamlit.app` 公网地址。

## 数据来源

- K 线数据：腾讯财经 (web.ifzq.gtimg.cn)
- 实时行情：腾讯行情 (qt.gtimg.cn)
- 无需注册，无需 API Key

## 回测说明

- 默认初始资金 100 万，可自定义
- 手续费万三，含千分之一滑点
- 支持日线/周线/月线回测
- 输出：夏普比率、最大回撤、年化收益、胜率、月度热力图
