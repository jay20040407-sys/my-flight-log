import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# 設定網頁標題與圖示
st.set_page_config(page_title="我的飛行日誌", page_icon="✈️")
st.title("✈️ 我的個人飛行日誌")

# --- 後端設定 (隱藏 API Key) ---
AVI_KEY = "a85e1d8cc607a691b63846eea47bd40e"

# --- 側邊欄輸入 ---
with st.sidebar:
    st.header("航班輸入")
    flight_no = st.text_input("航班號碼", value="HB704")
    target_date = st.date_input("飛行日期", value=datetime.now())
    st.info("提示：輸入航班號與日期後點擊下方按鈕。")

def parse_time(t_str):
    if not t_str: return None
    try:
        return datetime.fromisoformat(t_str.replace('Z', '+00:00'))
    except:
        return None

if st.button("查詢並記錄"):
    # 向 API 請求資料
    url = f"http://api.aviationstack.com/v1/flights?access_key={AVI_KEY}&flight_iata={flight_no}"
    
    with st.spinner('正在從雲端抓取數據...'):
        response = requests.get(url)
        data = response.json()
    
    if data.get('data') and len(data['data']) > 0:
        # 尋找指定日期的航班，若找不到則取第一筆
        f = next((i for i in data['data'] if i['flight_date'] == str(target_date)), data['data'][0])
        
        # 時間解析
        dep_dt = parse_time(f['departure']['actual'] or f['departure']['scheduled'])
        arr_dt = parse_time(f['arrival']['actual'] or f['arrival']['scheduled'])
        
        # 計算飛行時間
        duration = "未知"
        if dep_dt and arr_dt:
            diff = arr_dt - dep_dt
            total_seconds = int(diff.total_seconds())
            if total_seconds > 0:
                h, m = divmod(total_seconds, 3600)
                duration = f"{h}h {m//60}m"
        
        # 整理結果資料
        res = {
            "航班/日期": f"{flight_no} / {target_date}",
            "飛機編號": f"{f['aircraft'].get('registration') or '未提供'}",
            "機型": f"{f['aircraft'].get('icao') or f['aircraft'].get('model') or '未知'}",
            "實際起降(Zulu)": f"{dep_dt.strftime('%H:%M') if dep_dt else 'N/A'}Z / {arr_dt.strftime('%H:%M') if arr_dt else 'N/A'}Z",
            "飛行時間": duration,
            "狀態": f.get('flight_status', '未知').upper(),
            "登機門": f"{f['departure'].get('gate') or 'N/A'}"
        }
        
        # 顯示表格
        st.success("查詢成功！")
        st.table(pd.DataFrame([res]))
        
        # 下載 CSV 功能
        csv = pd.DataFrame([res]).to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="下載此筆紀錄 CSV",
            data=csv,
            file_name=f"{flight_no}_{target_date}_log.csv",
            mime="text/csv"
        )
    else:
        st.error("抱歉，找不到該航班的資料。請確認航班號碼是否輸入正確，或該航班是否超出了免費版 API 的查詢範圍。")

st.divider()
st.caption("數據來源：Aviationstack API | 飛行紀錄自動化工具")
