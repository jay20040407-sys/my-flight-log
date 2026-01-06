import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# 設定網頁標題與圖示
st.set_page_config(page_title="我的飛行日誌", page_icon="✈️")
st.title("✈️ 我的個人飛行日誌")

# --- API 設定 ---
RAPID_API_KEY = "d2cfcfb899msh0ee2823290701c7p126029jsn9f6dab4a88df"
AVI_KEY = "a85e1d8cc607a691b63846eea47bd40e"

with st.sidebar:
    st.header("🔍 航班查詢")
    flight_no = st.text_input("航班號碼", value="HB704").upper()
    target_date = st.date_input("飛行日期", value=datetime.now())
    st.info("系統將自動跨庫比對並校正時區。")

def safe_parse_zulu(utc_str, local_str):
    """通用時間補完邏輯"""
    if utc_str: 
        return utc_str.split('T')[1][:5] + "Z"
    if local_str:
        try:
            # 假設大多數亞洲航班為 UTC+8，若無 Zulu 則自動換算
            dt = datetime.fromisoformat(local_str.split('+')[0].replace('Z', ''))
            z_dt = dt - timedelta(hours=8) 
            return z_dt.strftime('%H:%M') + "Z"
        except: return "N/A"
    return "N/A"

def get_airline_name(code, api_name):
    """航空公司名稱自動修正表"""
    mapping = {
        "HB": "Greater Bay Airlines (大灣區航空)",
        "JX": "Starlux Airlines (星宇航空)",
        "BR": "EVA Air (長榮航空)",
        "CI": "China Airlines (中華航空)"
    }
    prefix = code[:2]
    return mapping.get(prefix, api_name)

if st.button("全自動深度檢索"):
    # 兩大 API 同時啟動
    adb_url = f"https://aerodatabox.p.rapidapi.com/flights/number/{flight_no}/{target_date}"
    avi_url = f"http://api.aviationstack.com/v1/flights?access_key={AVI_KEY}&flight_iata={flight_no}"
    
    with st.spinner('系統正在跨資料庫重組數據...'):
        adb_res = requests.get(adb_url, headers={"x-rapidapi-key": RAPID_API_KEY, "x-rapidapi-host": "aerodatabox.p.rapidapi.com"}).json()
        avi_res = requests.get(avi_url).json()

    if adb_res and len(adb_res) > 0:
        f_adb = adb_res[0]
        f_avi = next((i for i in avi_res.get('data', []) if i['flight_date'] == str(target_date)), {})

        # --- 數據優先級提取 ---
        reg = f_adb.get('aircraft', {}).get('reg') or f_avi.get('aircraft', {}).get('registration') or "⚠️ 數據未同步"
        model = f_adb.get('aircraft', {}).get('model') or f_avi.get('aircraft', {}).get('model') or "待確認"
        
        # 時間與時長
        dep_u = f_adb['departure'].get('actualTimeUtc') or f_adb['departure'].get('scheduledTimeUtc')
        dep_l = f_adb['departure'].get('scheduledTimeLocal') or f_avi.get('departure', {}).get('scheduled')
        arr_u = f_adb['arrival'].get('actualTimeUtc') or f_adb['arrival'].get('scheduledTimeUtc')
        arr_l = f_adb['arrival'].get('scheduledTimeLocal') or f_avi.get('arrival', {}).get('scheduled')

        z_dep = safe_parse_zulu(dep_u, dep_l)
        z_arr = safe_parse_zulu(arr_u, arr_l)

        # 計算飛行時間
        duration = "未知"
        try:
            d1 = datetime.fromisoformat(dep_l.split('+')[0])
            d2 = datetime.fromisoformat(arr_l.split('+')[0])
            diff = d2 - d1
            duration = f"{diff.seconds // 3600}h {(diff.seconds // 60) % 60}m"
        except: pass

        res = {
            "航班/日期": f"{flight_no} / {target_date}",
            "飛機編號 (Reg)": reg,
            "機型 (Model)": model,
            "起降(Zulu)": f"{z_dep} / {z_arr}",
            "飛行時間": duration,
            "航空公司": get_airline_name(flight_no, f_adb['airline'].get('name'))
        }

        st.table(pd.DataFrame([res]))
        st.download_button("💾 下載 CSV 紀錄", data=pd.DataFrame([res]).to_csv(index=False).encode('utf-8-sig'), file_name=f"Log_{flight_no}.csv")
    else:
        st.error("全球資料庫暫無此航班紀錄，請確認號碼或待起飛後重試。")
