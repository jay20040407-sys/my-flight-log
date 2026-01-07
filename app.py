import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- 核心配置 ---
FA_API_KEY = "NiJ7hEswTD7KeqMGyRsVhspLW4Nfw3kG"
FA_URL = "https://aeroapi.flightaware.com/aeroapi"

# 設定網頁標題與圖示
st.set_page_config(page_title="我的飛行日誌", page_icon="✈️")
st.title("✈️ 我的個人飛行日誌")

def get_flight_data(ident, date):
    headers = {"x-apikey": FA_API_KEY}
    start = f"{date}T00:00:00Z"
    end = f"{date}T23:59:59Z"
    url = f"{FA_URL}/flights/{ident}?start={start}&end={end}"
    
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            flights = resp.json().get('flights', [])
            return flights[0] if flights else None
    except: return None
    return None

with st.sidebar:
    st.header("🔍 自動抓取設定")
    flight_no = st.text_input("航班號碼", value="BR197").upper()
    target_date = st.date_input("飛行日期", value=datetime.now())

if st.button("啟動全自動檢索"):
    with st.spinner('正在抓取巡航高度與速度數據...'):
        f = get_flight_data(flight_no, str(target_date))
        
    if f:
        # 1. 航空公司自動識別
        airline_map = {"BR": "長榮航空", "CI": "中華航空", "HB": "大灣區航空", "JX": "星宇航空", "CX": "國泰航空"}
        prefix = flight_no[:2]
        airline = airline_map.get(prefix) or f.get('operator_name') or "未知航司"

        # 2. 數據提取
        reg = f.get('registration') or "查無編號"
        # 巡航高度轉換：API 給的是 Flight Level (如 350 代表 35,000 ft)
        alt = f.get('filed_altitude')
        altitude = f"{alt * 100} ft" if alt else "N/A"
        
        # 速度：預計巡航地速
        speed = f.get('filed_airspeed')
        max_speed = f"{speed} kts" if speed else "N/A"

        # 3. 時間與航段
        origin = f.get('origin', {}).get('code_iata') or "???"
        dest = f.get('destination', {}).get('code_iata') or "???"
        dep_z = f.get('actual_off') or f.get('scheduled_off')
        arr_z = f.get('actual_on') or f.get('scheduled_on')

        res = {
            "航班/日期": f"{flight_no} / {target_date}",
            "航段": f"{origin}-{dest}",
            "航空公司": airline,
            "飛機編號": reg,
            "巡航高度": altitude,  # 新增
            "巡航速度": max_speed,  # 新增
            "起降(Zulu)": f"{dep_z.split('T')[1][:5] if dep_z else 'N/A'}Z / {arr_z.split('T')[1][:5] if arr_z else 'N/A'}Z"
        }

        st.success("數據全自動抓取完成！")
        st.table(pd.DataFrame([res]))
        st.download_button("💾 下載 CSV", data=pd.DataFrame([res]).to_csv(index=False).encode('utf-8-sig'), file_name=f"Log_{flight_no}.csv")
    else:
        st.error("查無紀錄，請確認日期在最近 7 天內。")
