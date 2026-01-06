import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- 網頁介面設定 ---
st.title("✈️ 我的個人飛行日誌")
st.write("輸入航班資訊，自動抓取數據並記錄。")

# --- 手動輸入區 ---
with st.sidebar:
    st.header("航班輸入")
    avi_key = st.text_input("Aviationstack API Key", value="a85e1d8cc607a691b63846eea47bd40e")
    flight_no = st.text_input("航班號碼", value="BR198")
    target_date = st.date_input("飛行日期", value=datetime.now())
    icao24 = st.text_input("飛機 ICAO24 (可選)", value="88044c")

# --- 核心邏輯 (計算與抓取) ---
def parse_time(t_str):
    if not t_str: return None
    return datetime.fromisoformat(t_str.replace('Z', '+00:00'))

if st.button("開始抓取並紀錄"):
    astack_url = f"http://api.aviationstack.com/v1/flights?access_key={avi_key}&flight_iata={flight_no}"
    data = requests.get(astack_url).json()
    
    if data.get('data'):
        # 過濾日期
        f = next((i for i in data['data'] if i['flight_date'] == str(target_date)), data['data'][0])
        
        # 時間處理
        dep_dt = parse_time(f['departure']['actual'] or f['departure']['scheduled'])
        arr_dt = parse_time(f['arrival']['actual'] or f['arrival']['scheduled'])
        
        # 飛行時間計算
        duration = "未知"
        if dep_dt and arr_dt:
            diff = arr_dt - dep_dt
            h, m = divmod(int(diff.total_seconds()), 3600)
            duration = f"{h}h {m//60}m"
        
        # 顯示結果
        res = {
            "航班/日期": f"{flight_no} / {target_date}",
            "飛機編號": f"{f['aircraft'].get('registration') or 'B-16722'}",
            "實際起降(Zulu)": f"{dep_dt.strftime('%H:%M') if dep_dt else 'N/A'}Z / {arr_dt.strftime('%H:%M') if arr_dt else 'N/A'}Z",
            "飛行時間": duration,
            "最高速度": "530 kts (est)",
            "登機門": f"{f['departure'].get('gate') or 'N/A'}"
        }
        
        st.success("抓取成功！")
        st.table(pd.DataFrame([res]))
        
        # 儲存功能 (在網頁版通常改為下載 CSV)
        df = pd.DataFrame([res])
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("下載此筆紀錄 CSV", data=csv, file_name=f"{flight_no}_log.csv")
    else:
        st.error("找不到航班資料")