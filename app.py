import streamlit as st
import pandas as pd
import numpy as np
import FinanceDataReader as fdr
import yfinance as yf

# --- 데이터 수집 함수 ---
def get_market_data():
    # 최근 30일 데이터
    end_date = pd.Timestamp.now().strftime("%Y-%m-%d")
    start_date = (pd.Timestamp.now() - pd.Timedelta(days=30)).strftime("%Y-%m-%d")
    
    # 1. 국내 주식 (삼성전자, 한화에어로스페이스)
    samsung = fdr.DataReader('005930', start_date, end_date)['Close']
    hanwha = fdr.DataReader('012450', start_date, end_date)['Close']
    
    df_kr = pd.DataFrame({
        "반도체_가격": samsung,
        "방산_가격": hanwha
    })

    # 2. 해외 자산 (원유, 금) - 'Close' 컬럼 사용으로 수정
    df_global = yf.download(["CL=F", "GC=F"], start=start_date, end=end_date)['Close']
    df_global.columns = ['금', '원유']
    
    return pd.concat([df_kr, df_global], axis=1).fillna(method='ffill').dropna()

# --- 분석 로직 ---
def analyze_logic(df):
    recent = df.tail(7)
    results = {}
    
    for sector in ["반도체", "방산"]:
        change = (recent[f"{sector}_가격"].iloc[-1] / recent[f"{sector}_가격"].iloc[0]) - 1
        if change > 0.02: results[sector] = "강력 매수"
        elif change > -0.01: results[sector] = "보유/관망"
        else: results[sector] = "매도/비중축소"
        
    for asset in ["원유", "금"]:
        change = (recent[asset].iloc[-1] / recent[asset].iloc[0]) - 1
        results[asset] = "비중 확대" if change > 0.01 else "관망"
        
    return results

# --- 웹 화면 구성 ---
st.set_page_config(page_title="주식 섹터 분석기", layout="wide")
st.title("📊 주간 섹터 흐름 분석 (최종 버전)")

if st.button('🚀 최근 1주일 데이터 분석 실행'):
    with st.spinner('데이터를 수집하고 분석 중입니다...'):
        try:
            data = get_market_data()
            decision = analyze_logic(data)
            
            cols = st.columns(4)
            for i, (name, res) in enumerate(decision.items()):
                cols[i].metric(name, res)
                
            st.subheader("📈 최근 7일 상대 수익률 추이")
            chart_data = data.tail(7)[["반도체_가격", "방산_가격", "원유", "금"]]
            st.line_chart(chart_data / chart_data.iloc[0])
            
        except Exception as e:
            st.error(f"데이터 수집 오류 발생: {e}. 잠시 후 다시 시도해 주세요.")
