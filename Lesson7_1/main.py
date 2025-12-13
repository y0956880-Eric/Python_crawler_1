import streamlit as st
import pandas as pd
import time
from crawl4ai import CrawlerRunConfig, CacheMode, JsonCssExtractionStrategy, AsyncWebCrawler
import asyncio

# 匯率資料來源（以台灣銀行匯率網頁為例，可依實際需求更換）
EXCHANGE_URL = "https://rate.bot.com.tw/xrt?Lang=zh-TW"

# 定義爬蟲 schema
schema = {
    "name": "匯率表",
    "baseSelector": "table.table tbody tr",
    "fields": [
        {"name": "幣別", "selector": "div.visible-phone.print_hide span", "type": "text"},
        {"name": "現金買入", "selector": "td[data-table=\"本行現金買入\"]", "type": "text"},
        {"name": "現金賣出", "selector": "td[data-table=\"本行現金賣出\"]", "type": "text"},
        {"name": "即期買入", "selector": "td[data-table=\"本行即期買入\"]", "type": "text"},
        {"name": "即期賣出", "selector": "td[data-table=\"本行即期賣出\"]", "type": "text"},
    ]
}

# 取得匯率資料
@st.cache_data(ttl=600, show_spinner=True)
def get_rates():
    strategy = JsonCssExtractionStrategy(schema)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, extraction_strategy=strategy)
    async def fetch():
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=EXCHANGE_URL, config=run_config)
            data = pd.DataFrame(eval(result.extracted_content))
            return data
    return asyncio.run(fetch())

# Streamlit 介面
st.set_page_config(page_title="台幣匯率轉換", layout="wide")
st.title("台幣匯率轉換工具")

col1, col2 = st.columns(2)

with col1:
    st.header("台幣轉換計算")
    rates = get_rates()
    # 過濾可交易幣別
    tradable = rates[rates["即期賣出"].str.strip() != "-"]
    tradable = tradable.reset_index(drop=True)
    currency = st.selectbox("選擇幣別", tradable["幣別"])
    amount = st.number_input("請輸入台幣金額", min_value=1, value=1000)
    rate = tradable.loc[tradable["幣別"] == currency, "即期賣出"].values[0]
    try:
        rate = float(rate.replace(",", ""))
        result = amount / rate
        st.success(f"{amount} 台幣可兌換 {result:.2f} {currency}")
    except:
        st.warning("暫停交易")
    if st.button("手動更新匯率"):
        st.cache_data.clear()
        st.experimental_rerun()

with col2:
    st.header("匯率表格")
    show = rates.copy()
    # 空值顯示暫停交易
    for col in ["現金買入", "現金賣出", "即期買入", "即期賣出"]:
        show[col] = show[col].apply(lambda x: x if x.strip() != "-" else "暫停交易")
    # 只顯示可交易幣別
    show = show[show["即期賣出"] != "-"]
    st.dataframe(show[["幣別", "現金買入", "現金賣出", "即期買入", "即期賣出"]], use_container_width=True)
