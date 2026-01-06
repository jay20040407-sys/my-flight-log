import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# 設定網頁標題與圖示
st.set_page_config(page_title="我的飛行日誌", page_icon="✈️")
st.title("✈️ 我的個人飛行日誌")

# --- 設定區 ---
RAPID_API_KEY = "d2cfcfb899msh0ee2823290701c7p126029jsn9f6dab4a88df"

with st.sidebar:
    st.header("🔍 航班查詢")
    flight_no = st.text_input("航班號碼 (如: HB704)", value="HB704").upper()
    target_date = st.date_input("飛行日期", value=datetime.now())
    st.info("已加入航空公司名稱校正與時間補完邏輯。")

def format_zulu(t_str):
    if not t_str: return None
    try:
        # 處理 2025-12-15T19:27+08:00 或 2025-12-15T11:27Z 格式
        t_part = t_str.split('T')[1]
        return t_part[:5] + "Z"
    except:
        return None

def calculate_duration(dep_str, arr_str):
    try:
        # 解析 ISO 格式時間計算時差
        fmt = "%Y-%m-%dT%H:%M"
        d1 = datetime.strptime(dep_str[:16], fmt)
        d2 = datetime.strptime(arr_str[:16], fmt)
        diff = d2 - d1
        h, m = divmod(int(diff.total_seconds()), 3600)
        return f"{h}h {m//60}m"
    except:
        return "未知"

if st.button("從高級資料庫抓取數據"):
    url = f"https://aerodatabox.p.rapidapi.com/flights/number/{flight_no}/{target_date}"
    headers = {"x-rapidapi-key": RAPID_API_KEY, "x-rapidapi-host": "aerodatabox.p.rapidapi.com"}
    
    with st.spinner('正在檢索並校正數據...'):
        response = requests.get(url, headers=headers)
        
    if response.status_code == 200:
        data = response.json()
        if len(data) > 0:
            f = data[0]
            aircraft = f.get('aircraft', {})
            
            # --- 1. 航空公司校正 ---
            airline_name = f['airline'].get('name', 'N/A')
            if flight_no.startswith("HB"): airline_name = "Greater Bay Airlines (大灣區航空)"
            
            # --- 2. 時間補完邏輯 ---
            # 優先找 UTC 實際，次之 UTC 預計，最後找本地時間
            dep_raw = f['departure'].get('actualTimeUtc') or f['departure'].get('scheduledTimeUtc') or f['departure'].get('scheduledTimeLocal')
            arr_raw = f['arrival'].get('actualTimeUtc') or f['arrival'].get('scheduledTimeUtc') or f['arrival'].get('scheduledTimeLocal')
            
            dep_z = format_zulu(dep_raw) or "N/A"
            arr_z = format_zulu(arr_raw) or "N/A"
            
            # --- 3. 飛行時間計算 ---
            flight_time = calculate_duration(dep_raw, arr_raw) if dep_raw and arr_raw else "未知"

            res = {
                "航班/日期": f"{flight_no} / {target_date}",
                "飛機編號 (Reg)": aircraft.get('reg') or "⚠️ 待查 (建議用 FR24)",
                "機型 (Model)": aircraft.get('model', 'Boeing 737-800'),
                "起降(Zulu)": f"{dep_z} / {arr_z}",
                "飛行時間": flight_time,
                "航空公司": airline_name
            }
            
            st.success("數據抓取成功！已過濾掉狀態欄位。")
            st.table(pd.DataFrame([res]))
            st.download_button("💾 下載 CSV", data=pd.DataFrame([res]).to_csv(index=False).encode('utf-8-sig'), file_name=f"Log_{flight_no}.csv")
        else:
            st.warning("查無資料，請確認日期是否正確。")
    else:
        st.error(f"連線失敗: {response.status_code}")
