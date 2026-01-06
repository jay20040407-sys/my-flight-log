import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# 設定網頁標題與圖示
st.set_page_config(page_title="我的飛行日誌", page_icon="✈️")
st.title("✈️ 我的個人飛行日誌")

# --- API Keys 設定 ---
# 請確保這兩把 Key 都是有效的
RAPID_API_KEY = "d2cfcfb899msh0ee2823290701c7p126029jsn9f6dab4a88df"
AVI_KEY = "a85e1d8cc607a691b63846eea47bd40e"

with st.sidebar:
    st.header("🔍 航班查詢")
    flight_no = st.text_input("航班號碼", value="HB704").upper()
    target_date = st.date_input("飛行日期", value=datetime.now())
    st.success("目前使用：AeroDataBox + Aviationstack 雙引擎")

def format_zulu(t_str):
    if not t_str: return None
    try:
        return t_str.split('T')[1][:5] + "Z"
    except:
        return None

def calculate_duration(dep_str, arr_str):
    try:
        fmt = "%Y-%m-%dT%H:%M"
        d1 = datetime.strptime(dep_str[:16], fmt)
        d2 = datetime.strptime(arr_str[:16], fmt)
        diff = d2 - d1
        h, m = divmod(int(diff.total_seconds()), 3600)
        return f"{h}h {m//60}m"
    except:
        return "未知"

if st.button("雙引擎即時抓取"):
    # --- 1. 呼叫 AeroDataBox (獲取機型與時間) ---
    adb_url = f"https://aerodatabox.p.rapidapi.com/flights/number/{flight_no}/{target_date}"
    adb_headers = {"x-rapidapi-key": RAPID_API_KEY, "x-rapidapi-host": "aerodatabox.p.rapidapi.com"}
    
    # --- 2. 呼叫 Aviationstack (作為編號備援) ---
    avi_url = f"http://api.aviationstack.com/v1/flights?access_key={AVI_KEY}&flight_iata={flight_no}"
    
    with st.spinner('正在同步全球兩大資料庫...'):
        adb_res = requests.get(adb_url, headers=adb_headers).json()
        avi_res = requests.get(avi_url).json()
        
    if adb_res and len(adb_res) > 0:
        f_adb = adb_res[0]
        f_avi = next((i for i in avi_res.get('data', []) if i['flight_date'] == str(target_date)), {})
        
        # --- 資料組合邏輯 ---
        # 註冊號：優先用 AeroDataBox，沒有就用 Aviationstack
        reg = f_adb.get('aircraft', {}).get('reg') or f_avi.get('aircraft', {}).get('registration') or "⚠️ 待查"
        
        # 機型：優先用 AeroDataBox
        ac_model = f_adb.get('aircraft', {}).get('model') or f_avi.get('aircraft', {}).get('model') or "B737-800"
        
        # 航空公司：強制校正
        airline = "Greater Bay Airlines (大灣區航空)" if flight_no.startswith("HB") else f_adb['airline'].get('name')
        
        # 時間處理 (尋找所有可能的欄位避免 N/A)
        dep_raw = f_adb['departure'].get('actualTimeUtc') or f_adb['departure'].get('scheduledTimeUtc') or f_avi.get('departure', {}).get('scheduled')
        arr_raw = f_adb['arrival'].get('actualTimeUtc') or f_adb['arrival'].get('scheduledTimeUtc') or f_avi.get('arrival', {}).get('scheduled')
        
        dep_z = format_zulu(dep_raw) or "N/A"
        arr_z = format_zulu(arr_raw) or "N/A"
        flight_time = calculate_duration(dep_raw, arr_raw)

        res = {
            "航班/日期": f"{flight_no} / {target_date}",
            "飛機編號 (Reg)": reg,
            "機型 (Model)": ac_model,
            "起降(Zulu)": f"{dep_z} / {arr_z}",
            "飛行時間": flight_time,
            "航空公司": airline
        }
        
        st.success("雙核心抓取完成！資料已校正。")
        st.table(pd.DataFrame([res]))
        st.download_button("💾 下載 CSV", data=pd.DataFrame([res]).to_csv(index=False).encode('utf-8-sig'), file_name=f"FlightLog_{flight_no}.csv")
    else:
        st.error("兩大資料庫均無法找到該航班，請檢查航班號或日期。")
