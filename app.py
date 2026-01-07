import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- 核心配置 ---
# 已為你填入截圖中獲取的 API Key
FA_API_KEY = "NiJ7hEswTD7KeqMGyRsVhspLW4Nfw3kG"
FA_URL = "https://aeroapi.flightaware.com/aeroapi"

# 設定網頁標題與圖示
st.set_page_config(page_title="我的飛行日誌", page_icon="✈️")
st.title("✈️ 我的個人飛行日誌")

def get_flight_data(ident, date):
    headers = {"x-apikey": FA_API_KEY}
    # 定義查詢日期範圍
    start = f"{date}T00:00:00Z"
    end = f"{date}T23:59:59Z"
    # 使用 Flights 接口獲取最完整的雷達與狀態數據
    url = f"{FA_URL}/flights/{ident}?start={start}&end={end}"
    
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            flights = resp.json().get('flights', [])
            return flights[0] if flights else None
    except:
        return None
    return None

with st.sidebar:
    st.header("🔍 自動抓取設定")
    flight_no = st.text_input("航班號碼", value="HB704").upper()
    target_date = st.date_input("飛行日期", value=datetime.now())
    st.success("數據源：FlightAware 雷達實時數據")

if st.button("全自動深度查詢"):
    with st.spinner('正在連結全球雷達監測網...'):
        f = get_flight_data(flight_no, str(target_date))
        
    if f:
        # 1. 抓取航段 (Origin-Destination)
        origin = f.get('origin', {}).get('code_iata') or "???"
        dest = f.get('destination', {}).get('code_iata') or "???"
        route = f"{origin}-{dest}"

        # 2. 抓取註冊編號與機型 (FlightAware 直接從 ADS-B 訊號提取)
        reg = f.get('registration') or "查無編號"
        model = f.get('aircraft_type') or "B738"
        
        # 3. 處理 Zulu 時間 (FlightAware 原生提供標準 UTC)
        dep_z = f.get('actual_off') or f.get('scheduled_off')
        arr_z = f.get('actual_on') or f.get('scheduled_on')
        
        def format_z(t_str):
            if not t_str: return "N/A"
            return t_str.split('T')[1][:5] + "Z"

        # 4. 計算飛行時間
        duration = "未知"
        if dep_z and arr_z:
            try:
                d1 = datetime.fromisoformat(dep_z.replace('Z', ''))
                d2 = datetime.fromisoformat(arr_z.replace('Z', ''))
                diff = d2 - d1
                h, m = divmod(int(diff.total_seconds()), 3600)
                duration = f"{h}h {m//60}m"
            except: pass

        res = {
            "航班/日期": f"{flight_no} / {target_date}",
            "航段 (Route)": route,
            "飛機編號 (Reg)": reg,
            "機型 (Model)": model,
            "起降(Zulu)": f"{format_z(dep_z)} / {format_z(arr_z)}",
            "飛行時間": duration,
            "航空公司": f.get('operator_name', '大灣區航空' if 'HB' in flight_no else '未知')
        }

        st.success("雷達數據自動對應成功！")
        st.table(pd.DataFrame([res]))
        
        # 下載 CSV，檔名包含航段資訊
        csv_name = f"Log_{flight_no}_{route}_{target_date}.csv"
        st.download_button("💾 下載 CSV 紀錄", data=pd.DataFrame([res]).to_csv(index=False).encode('utf-8-sig'), file_name=csv_name)
    else:
        st.error("查無數據。請確認航班號正確，且該航班已在 FlightAware 資料庫中生成紀錄。")
