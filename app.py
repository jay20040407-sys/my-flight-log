import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# 設定網頁標題與圖示
st.set_page_config(page_title="我的飛行日誌", page_icon="✈️")
st.title("✈️ 我的個人飛行日誌")

# --- 1. 這是你的 Mapping 補完表 (可以在這手動增加更多航班) ---
# 格式: "航班代碼前綴": {"name": "航空公司全名", "default_reg": "備用編號", "offset": 時區偏離小時}
MAPPING = {
    "HB": {"name": "Greater Bay Airlines (大灣區航空)", "reg": "B-KJE", "model": "Boeing 737-800", "offset": 8},
    "JX": {"name": "Starlux Airlines (星宇航空)", "reg": "B-58201", "model": "A321neo", "offset": 8},
    "BR": {"name": "EVA Air (長榮航空)", "reg": "B-16722", "model": "Boeing 777", "offset": 8},
    "CI": {"name": "China Airlines (中華航空)", "reg": "B-18301", "model": "A330-300", "offset": 8}
}

# --- API 設定 ---
RAPID_API_KEY = "d2cfcfb899msh0ee2823290701c7p126029jsn9f6dab4a88df"
AVI_KEY = "a85e1d8cc607a691b63846eea47bd40e"

with st.sidebar:
    st.header("🔍 查詢設定")
    flight_no = st.text_input("航班號碼", value="HB704").upper()
    target_date = st.date_input("飛行日期", value=datetime.now())
    st.info("系統現已具備智慧推斷功能，會自動校正 API 缺失。")

def solve_time(utc_str, local_str, offset):
    """從本地時間強制推算 Zulu 時間"""
    if utc_str and 'T' in utc_str:
        return utc_str.split('T')[1][:5] + "Z"
    if local_str:
        try:
            # 處理格式 2025-12-15T19:27
            dt = datetime.fromisoformat(local_str.split('+')[0].replace('Z', ''))
            z_dt = dt - timedelta(hours=offset)
            return z_dt.strftime('%H:%M') + "Z"
        except: return "N/A"
    return "N/A"

if st.button("全自動智慧檢索"):
    adb_url = f"https://aerodatabox.p.rapidapi.com/flights/number/{flight_no}/{target_date}"
    avi_url = f"http://api.aviationstack.com/v1/flights?access_key={AVI_KEY}&flight_iata={flight_no}"
    
    with st.spinner('正在執行智慧補完演算...'):
        adb_res = requests.get(adb_url, headers={"x-rapidapi-key": RAPID_API_KEY, "x-rapidapi-host": "aerodatabox.p.rapidapi.com"}).json()
        avi_res = requests.get(avi_url).json()

    if adb_res and len(adb_res) > 0:
        f = adb_res[0]
        prefix = flight_no[:2]
        m_info = MAPPING.get(prefix, {"name": f['airline'].get('name'), "reg": "待查", "model": "未知", "offset": 0})

        # 時間補全
        dep_l = f['departure'].get('scheduledTimeLocal') or f['departure'].get('actualTimeLocal')
        arr_l = f['arrival'].get('scheduledTimeLocal') or f['arrival'].get('actualTimeLocal')
        
        z_dep = solve_time(f['departure'].get('actualTimeUtc'), dep_l, m_info['offset'])
        z_arr = solve_time(f['arrival'].get('actualTimeUtc'), arr_l, m_info['offset'])

        # 註冊號與機型智慧補完
        reg = f.get('aircraft', {}).get('reg') or m_info['reg']
        model = f.get('aircraft', {}).get('model') or m_info['model']

        # 飛行時間精算
        duration = "未知"
        try:
            d1 = datetime.fromisoformat(dep_l.split('+')[0])
            d2 = datetime.fromisoformat(arr_l.split('+')[0])
            diff = d2 - d1
            h, m = divmod(int(diff.total_seconds()), 3600)
            duration = f"{h}h {m//60}m"
        except: pass

        res = {
            "航班/日期": f"{flight_no} / {target_date}",
            "飛機編號 (Reg)": reg,
            "機型 (Model)": model,
            "起降(Zulu)": f"{z_dep} / {z_arr}",
            "飛行時間": duration,
            "航空公司": m_info['name']
        }

        st.success("智慧重組完成！")
        st.table(pd.DataFrame([res]))
        st.download_button("💾 下載 CSV", data=pd.DataFrame([res]).to_csv(index=False).encode('utf-8-sig'), file_name=f"Log_{flight_no}.csv")
    else:
        st.error("資料庫完全無此航班紀錄。")
