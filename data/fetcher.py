"""数据获取 — 全部走腾讯接口（已验证稳定连通）"""

import os
import pickle
import time
import json
import pandas as pd
import requests
from config import CACHE_DIR

os.makedirs(CACHE_DIR, exist_ok=True)

# ── 缓存 ──────────────────────────────────────────────────

def _cache_path(name):
    return os.path.join(CACHE_DIR, f"{name}.pkl")

def _load_cache(name, max_age_hours=4):
    path = _cache_path(name)
    if not os.path.exists(path):
        return None
    age = (pd.Timestamp.now() - pd.Timestamp(os.path.getmtime(path), unit="s")).total_seconds() / 3600
    if age > max_age_hours:
        return None
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception:
        return None

def _save_cache(name, data):
    with open(_cache_path(name), "wb") as f:
        pickle.dump(data, f)


def _http_get_text(url, timeout=15, retries=3):
    """纯文本 GET，无特殊 Header"""
    for i in range(retries):
        try:
            resp = requests.get(url, timeout=timeout,
                headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            if i == retries - 1:
                raise RuntimeError(f"HTTP: {e}")
            time.sleep(1 * (i + 1))


# ── 股票代码格式 ──────────────────────────────────────────

def _tencent_code(symbol):
    """600519 → sh600519, 000001 → sz000001"""
    prefix = "sh" if symbol.startswith(("6", "9")) else "sz"
    return f"{prefix}{symbol}"


# ── A 股列表（硬编码 100 只核心股票 + 支持代码搜索）────────

_CORE_STOCKS = [
    ("600519", "贵州茅台"), ("000858", "五粮液"), ("300750", "宁德时代"),
    ("601318", "中国平安"), ("000333", "美的集团"), ("600036", "招商银行"),
    ("002594", "比亚迪"), ("300059", "东方财富"), ("601899", "紫金矿业"),
    ("600276", "恒瑞医药"), ("601398", "工商银行"), ("000001", "平安银行"),
    ("300015", "爱尔眼科"), ("000725", "京东方A"), ("600900", "长江电力"),
    ("601166", "兴业银行"), ("000568", "泸州老窖"), ("002415", "海康威视"),
    ("600030", "中信证券"), ("601857", "中国石油"), ("002714", "牧原股份"),
    ("688981", "中芯国际"), ("688111", "金山办公"), ("688041", "海光信息"),
    ("000651", "格力电器"), ("601888", "中国中免"), ("300274", "阳光电源"),
    ("002475", "立讯精密"), ("601088", "中国神华"), ("300498", "温氏股份"),
    ("002352", "顺丰控股"), ("600585", "海螺水泥"), ("600031", "三一重工"),
    ("600809", "山西汾酒"), ("601012", "隆基绿能"), ("002230", "科大讯飞"),
    ("300760", "迈瑞医疗"), ("002049", "紫光国微"), ("002371", "北方华创"),
    ("300014", "亿纬锂能"), ("688012", "中微公司"), ("688256", "寒武纪"),
    ("600887", "伊利股份"), ("600690", "海尔智家"), ("600104", "上汽集团"),
    ("601633", "长城汽车"), ("600048", "保利发展"), ("601668", "中国建筑"),
    ("600436", "片仔癀"), ("600309", "万华化学"), ("000002", "万科A"),
    ("000063", "中兴通讯"), ("000625", "长安汽车"), ("000338", "潍柴动力"),
    ("002142", "宁波银行"), ("002304", "洋河股份"), ("002460", "赣锋锂业"),
    ("002466", "天齐锂业"), ("002241", "歌尔股份"), ("002920", "德赛西威"),
    ("300124", "汇川技术"), ("300408", "三环集团"), ("300450", "先导智能"),
    ("300413", "芒果超媒"), ("300896", "爱美客"), ("300999", "金龙鱼"),
    ("688396", "华润微"), ("688008", "澜起科技"), ("688169", "石头科技"),
    ("601857", "中国石油"), ("600028", "中国石化"), ("601225", "陕西煤业"),
    ("601728", "中国电信"), ("600050", "中国联通"), ("600406", "国电南瑞"),
    ("002129", "TCL中环"), ("000792", "盐湖股份"), ("000977", "浪潮信息"),
    ("000938", "紫光股份"), ("000799", "酒鬼酒"), ("000596", "古井贡酒"),
    ("601390", "中国中铁"), ("601766", "中国中车"), ("600019", "宝钢股份"),
    ("601628", "中国人寿"), ("601601", "中国太保"), ("601818", "光大银行"),
    ("600000", "浦发银行"), ("601939", "建设银行"), ("601988", "中国银行"),
    ("601288", "农业银行"), ("601328", "交通银行"), ("600016", "民生银行"),
    ("601229", "上海银行"), ("002736", "国信证券"), ("601211", "国泰君安"),
    ("600837", "海通证券"), ("000776", "广发证券"), ("601688", "华泰证券"),
]


def get_stock_list():
    return pd.DataFrame(_CORE_STOCKS, columns=["code", "name"])


def search_stocks(keyword):
    df = pd.DataFrame(_CORE_STOCKS, columns=["code", "name"])
    key = keyword.strip().lower()

    # 纯数字 = 代码搜索
    if key.isdigit() and len(key) >= 4:
        code_match = df[df["code"].str.startswith(key)]
        if len(code_match) > 0:
            return code_match
        # 不在列表中但格式像股票代码 → 构造一条
        if len(key) == 6:
            extra = pd.DataFrame([(key.zfill(6), key.zfill(6))], columns=["code", "name"])
            return extra
        return df[df["code"].str.contains(key)]

    # 名称搜索
    mask = df["name"].str.contains(key, case=False, na=False)
    result = df[mask]
    if result.empty:
        # 模糊搜索：每个字都包含
        for char in key:
            df = df[df["name"].str.contains(char, case=False, na=False)]
        result = df
    return result.head(50)


# ── 实时行情 ──────────────────────────────────────────────

def get_realtime_quote():
    """用腾讯接口批量获取实时行情"""
    cache = _load_cache("realtime", max_age_hours=0.08)
    if cache is not None:
        return cache

    codes = [c for c, _ in _CORE_STOCKS]
    batch_size = 50
    all_data = []

    for i in range(0, len(codes), batch_size):
        batch = codes[i:i+batch_size]
        symbols = ",".join(_tencent_code(c) for c in batch)
        url = f"http://qt.gtimg.cn/q={symbols}"
        try:
            text = _http_get_text(url, timeout=10)
            for line in text.strip().split("\n"):
                if '="' not in line:
                    continue
                content = line.split('="', 1)[1].strip('";\n')
                fields = content.split("~")
                if len(fields) < 40:
                    continue
                all_data.append({
                    "code": fields[2],
                    "name": fields[1],
                    "price": fields[3],
                    "prev_close": fields[4],
                    "open": fields[5],
                    "volume": fields[6],
                    "high": fields[33],
                    "low": fields[34],
                    "amount": fields[37],
                    "turnover": fields[38],
                    "pe": fields[39],
                    "total_mv": fields[45],
                })
        except Exception:
            continue

    if not all_data:
        return None

    df = pd.DataFrame(all_data)
    for c in ["price", "prev_close", "open", "high", "low", "amount", "turnover", "pe", "total_mv"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["pct_change"] = ((df["price"] - df["prev_close"]) / df["prev_close"] * 100).round(2)
    df["change"] = (df["price"] - df["prev_close"]).round(2)
    df["code"] = df["code"].astype(str).str.zfill(6)

    _save_cache("realtime", df)
    return df


# ── K 线（腾讯）────────────────────────────────────────────

def _kline_type(period):
    return {"daily": "day", "weekly": "week", "monthly": "month"}[period]

def _fq_type(adjust):
    return {"qfq": "qfq", "hfq": "hfq", "": ""}[adjust]

def get_kline(symbol, period="daily", start_date=None, end_date=None, adjust="qfq"):
    """腾讯 K 线接口"""
    cache_name = f"kline_{symbol}_{period}_{adjust}"
    cached = _load_cache(cache_name, max_age_hours=6)
    if cached is not None:
        df = cached
        if start_date:
            df = df[df["date"] >= pd.Timestamp(start_date)]
        return df

    tcode = _tencent_code(symbol)
    ktype = _kline_type(period)
    fq = _fq_type(adjust)

    url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={tcode},{ktype},,,320,{fq}"
    text = _http_get_text(url)
    data = json.loads(text)
    stock_data = data.get("data", {}).get(tcode, {})

    ktype_key = {"day": "qfqday" if fq else "day",
                 "week": "qfqweek" if fq else "week",
                 "month": "qfqmonth" if fq else "month"}[ktype]
    if fq and ktype_key not in stock_data:
        ktype_key = f"qfq{ktype}" if ktype_key.startswith("qfq") else ktype_key
    # 尝试所有 key
    if ktype_key not in stock_data:
        for k in stock_data:
            if ktype in k:
                ktype_key = k
                break

    klines = stock_data.get(ktype_key, [])
    if not klines:
        raise RuntimeError(f"{symbol} 无数据 (key={ktype_key})")

    rows = []
    for row in klines:
        if len(row) >= 6:
            rows.append({
                "date": row[0],
                "open": float(row[1]),
                "close": float(row[2]),
                "high": float(row[3]),
                "low": float(row[4]),
                "volume": float(row[5]) if len(row) > 5 else 0,
            })

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df["amount"] = df["volume"] * df["close"]  # 估算成交额
    df = df.dropna(subset=["open", "close", "high", "low"]).sort_values("date").reset_index(drop=True)

    _save_cache(cache_name, df)
    return df
