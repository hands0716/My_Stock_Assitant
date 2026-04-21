import streamlit as st
import pandas as pd
import numpy as np
from pykrx import stock
import yfinance as yf
import plotly.graph_objects as go

# --- 데이터 수집 함수 ---
def get_market_data():
    # 오늘 기준 최근 30일 데이터
    end_date = pd.Timestamp.now().strftime("%Y%m%d")
    start_date = (pd.Timestamp.now() - pd.Timedelta(days=30)).strftime("%Y%m%d")
    
    # 1. 국내 주식 (반도체: 삼성전자, 방산: 한화에어로스페이스)
    codes = {"반도체": "005930", "방산": "012450"}
    df_kr = pd.DataFrame()
    for name, code in codes.items():
        price = stock.get_market_ohlcv(start_date, end_date, code)['종가']
        frg = stock.get_exhaustion_rates_of_foreign_investment_by_date(start_date, end_date, code)['지분율']
        df_kr[f"{name}_가격"] = price
        df_kr[f"{name}_외인비중"] = frg

    # 2. 해외 자산 (원유, 금)
    df_global = yf.download(["CL=F", "GC=F"], start=pd.to_datetime(start_date), end=pd.to_datetime(end_date))['Adj Close']
    df_global.columns = ['금', '원유']
    
    return pd.concat([df_kr, df_global], axis=1).fillna(method='ffill').dropna()

# --- 분석 로직 (복잡한 수식 대신 가중치 분석) ---
def analyze_logic(df):
    recent = df.tail(7) # 최근 1주일
    results = {}
    
    for sector in ["반도체", "방산"]:
        # 가격 변동성(Momentum)과 외국인 수급을 결합한 분석
        price_move = (recent[f"{sector}_가격"].iloc[-1] / recent[f"{sector}_가격"].iloc[0]) - 1
        frg_move = recent[f"{sector}_외인비중"].iloc[-1] - recent[f"{sector}_외인비중"].iloc[0]
        
        # 가중치 점수 계산 (외국인 비중 변화에 높은 비중)
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
        # 시작점을 1로 맞춘 상대 수익률 차트
        chart_data = data.tail(7)[["반도체_가격", "방산_가격", "원유", "금"]]
        st.line_chart(chart_data / chart_data.iloc[0])    results = {}
    
    for sector in ["반도체", "방산"]:
        price_change = (recent[f"{sector}_가격"].iloc[-1] / recent[f"{sector}_가격"].iloc[0]) - 1
        frg_change = recent[f"{sector}_외인비중"].iloc[-1] - recent[f"{sector}_외인비중"].iloc[0]
        
        # 신경망 가중치 로직 (예시: 외인 비중 변화에 1.5배 가중치)
        score = (price_change * 1.0) + (frg_change * 15.0) 
        
        if score > 0.02: results[sector] = "강력 매수 (Strong Buy)"
        elif score > 0: results[sector] = "보유 (Hold)"
        else: results[sector] = "비중 축소 (Reduce)"
        
    # 원자재 분석
    for asset in ["원유", "금"]:
        change = (recent[asset].iloc[-1] / recent[asset].iloc[0]) - 1
        if change > 0.01: results[asset] = "비중 확대 (Overweight)"
        else: results[asset] = "관망 (Neutral)"
        
    return results

# --- UI 구성 ---
st.set_page_config(page_title="AI 섹터 매매 전략", layout="wide")
st.title("🤖 신경망 기반 4대 섹터 분석기")
st.sidebar.info("반도체, 방산, 원유, 금의 7일 패턴을 분석합니다.")

if st.button('🚀 1주일 데이터 분석 실행'):
    data = get_market_data()
    decision = analyze_with_nn(data)
    
    # 결과 요약 카드
    cols = st.columns(4)
    for i, (name, res) in enumerate(decision.items()):
        with cols[i]:
            st.metric(name, res)
            if "매수" in res or "확대" in res:
                st.success(f"{name} 섹터의 긍정적 흐름 포착")
            else:
                st.warning(f"{name} 섹터 주의 필요")

    # 차트 시각화
    st.subheader("최근 7일 자산 흐름")
    st.line_chart(data.tail(7)[["반도체_가격", "방산_가격", "원유", "금"]].apply(lambda x: x/x.iloc[0])) # 지수화
