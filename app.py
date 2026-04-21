import streamlit as st
import pandas as pd
import numpy as np
from pykrx import stock
import yfinance as yf

# --- 데이터 수집 함수 ---
def get_market_data():
    end_date = pd.Timestamp.now().strftime("%Y%m%d")
    start_date = (pd.Timestamp.now() - pd.Timedelta(days=30)).strftime("%Y%m%d")
    
    # 1. 국내 주식
    codes = {"반도체": "005930", "방산": "012450"}
    df_kr = pd.DataFrame()
    for name, code in codes.items():
        price = stock.get_market_ohlcv(start_date, end_date, code)['종가']
        frg = stock.get_exhaustion_rates_of_foreign_investment_by_date(start_date, end_date, code)['지분율']
        df_kr[f"{name}_가격"] = price
        df_kr[f"{name}_외인비중"] = frg

    # 2. 해외 자산
    df_global = yf.download(["CL=F", "GC=F"], start=pd.to_datetime(start_date), end=pd.to_datetime(end_date))['Adj Close']
    df_global.columns = ['금', '원유']
    
    return pd.concat([df_kr, df_global], axis=1).fillna(method='ffill').dropna()

# --- 분석 로직 ---
def analyze_logic(df):
    recent = df.tail(7)
    results = {}
    
    for sector in ["반도체", "방산"]:
        price_move = (recent[f"{sector}_가격"].iloc[-1] / recent[f"{sector}_가격"].iloc[0]) - 1
        frg_move = recent[f"{sector}_외인비중"].iloc[-1] - recent[f"{sector}_외인비중"].iloc[0]
        score = (price_move * 1.0) + (frg_move * 20.0) 
        
        if score > 0.02: results[sector] = "강력 매수"
        elif score > -0.01: results[sector] = "보유/관망"
        else: results[sector] = "매도/비중축소"
        
    for asset in ["원유", "금"]:
        change = (recent[asset].iloc[-1] / recent[asset].iloc[0]) - 1
        results[asset] = "비중 확대" if change > 0.01 else "관망"
        
    return results

# --- 웹 화면 구성 ---
st.set_page_config(page_title="주식 섹터 분석기", layout="wide")
st.title("📊 주간 섹터 및 외인 수급 분석")

if st.button('🚀 최근 1주일 데이터 분석 실행'):
    with st.spinner('데이터를 분석 중입니다...'):
        data = get_market_data()
        decision = analyze_logic(data)
        
        cols = st.columns(4)
        for i, (name, res) in enumerate(decision.items()):
            cols[i].metric(name, res)
            
        st.subheader("📈 최근 7일 상대 수익률 추이")
        chart_data = data.tail(7)[["반도체_가격", "방산_가격", "원유", "금"]]
        st.line_chart(chart_data / chart_data.iloc[0])
