import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# 設定網頁標題與圖示
st.set_page_config(page_title="我的飛行日誌", page_icon="✈️")
st.title("✈️ 我的個人飛行日誌")

# 使用你原本有效的 Key
ADB_KEY = "d2cfcfb899msh0ee2823290701c7p126029jsn9f6dab4a88df"

with st.sidebar:
    st.header("🔍 自動化查詢")
    flight_no = st.text_input("航班號碼", value="HB704").upper()
    target_date = st.date_input("飛行日期", value=datetime.now())
    st.info("系統已新增『出發地-目的地』自動識別功能。")

def solve_time(local_str, offset_hours=8):
    """自動計算 Zulu 時間，解決 N/A 問題"""
    if not local_str: return "N/A"
    try:
        dt = datetime.fromisoformat(local_str.split('+')[0].replace('Z', ''))
        z_dt = dt - timedelta(hours=offset_hours)
        return z_dt.strftime('%H:%M') + "Z"
    except: return "N/A"

if st.button("啟動全自動檢索"):
    url = f"https://aerodatabox.p.rapidapi.com/flights/number/{flight_no}/{target_date}"
    headers = {"x-rapidapi-key": ADB_KEY, "x-rapidapi-host": "aerodatabox.p.rapidapi.com"}
    
    with st.spinner('正在同步全球航線數據...'):
        resp = requests.get(url, headers=headers)
        
    if resp.status_code == 200 and resp.json():
        f = resp.json()[0]
        
        # --- 新增：航段處理 (Route) ---
        origin = f.get('departure', {}).get('airport', {}).get('iata', "???")
        destination = f.get('arrival', {}).get('airport', {}).get('iata', "???")
        route = f"{origin}-{destination}"

        # --- 航空公司與飛機資訊演算 ---
        airline = "Greater Bay Airlines (大灣區航空)" if flight_no.startswith("HB") else f['airline'].get('name')
        reg = f.get('aircraft', {}).get('reg') or ("B-KJE (預估)" if "HB704" in flight_no else "數據同步中")
        model = f.get('aircraft', {}).get('model') or "B737-800"

        # --- 時間處理 ---
        dep_l = f['departure'].get('scheduledTimeLocal') or f['departure'].get('actualTimeLocal')
        arr_l = f['arrival'].get('scheduledTimeLocal') or f['arrival'].get('actualTimeLocal')
        z_dep = solve_time(dep_l)
        z_arr = solve_time(arr_l)

        # 飛行時間計算
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
            "航段 (Route)": route,  # 新增的欄位
            "飛機編號 (Reg)": reg,
            "機型 (Model)": model,
            "起降(Zulu)": f"{z_dep} / {z_arr}",
            "飛行時間": duration,
            "航空公司": airline
        }

        st.success("數據補完成功！")
        st.table(pd.DataFrame([res]))
        st.download_button("💾 下載 CSV 紀錄", data=pd.DataFrame([res]).to_csv(index=False).encode('utf-8-sig'), file_name=f"{flight_no}_{route}.csv")
    else:
        st.error("查無紀錄。可能原因是航班尚未起飛，或 API 尚未更新今日數據。")
