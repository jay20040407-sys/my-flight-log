import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# 設定網頁標題與圖示
st.set_page_config(page_title="我的飛行日誌", page_icon="✈️")
st.title("✈️ 我的個人飛行日誌")

# --- 後端設定 ---
AVI_KEY = "a85e1d8cc607a691b63846eea47bd40e"

# --- 側邊欄輸入 ---
with st.sidebar:
    st.header("1. 航班基本資訊")
    flight_no = st.text_input("航班號碼", value="HB704")
    target_date = st.date_input("飛行日期", value=datetime.now())
    
    st.header("2. 手動校正 (若 API 沒抓到請填寫)")
    manual_reg = st.text_input("手動填寫飛機編號 (如: B-KJE)", value="")
    manual_type = st.text_input("手動填寫機型 (如: Boeing 737-800)", value="")
    
    st.info("提示：如果查詢結果顯示『未提供』，請在上方手動輸入後重新查詢。")

def parse_time(t_str):
    if not t_str: return None
    try:
        return datetime.fromisoformat(t_str.replace('Z', '+00:00'))
    except:
        return None

if st.button("查詢並記錄"):
    url = f"http://api.aviationstack.com/v1/flights?access_key={AVI_KEY}&flight_iata={flight_no}"
    
    with st.spinner('正在從雲端抓取數據...'):
        try:
            response = requests.get(url)
            data = response.json()
        except:
            st.error("連線 API 失敗")
            st.stop()
    
    if data.get('data') and len(data['data']) > 0:
        # 尋找指定日期的航班
        f = next((i for i in data['data'] if i['flight_date'] == str(target_date)), data['data'][0])
        
        # 時間解析與計算
        dep_dt = parse_time(f['departure']['actual'] or f['departure']['scheduled'])
        arr_dt = parse_time(f['arrival']['actual'] or f['arrival']['scheduled'])
        
        duration = "未知"
        if dep_dt and arr_dt:
            diff = arr_dt - dep_dt
            total_seconds = int(diff.total_seconds())
            if total_seconds > 0:
                h, m = divmod(total_seconds, 3600)
                duration = f"{h}h {m//60}m"
        
        # 優先使用手動輸入的資料，若無則使用 API 資料
        final_reg = manual_reg if manual_reg else (f['aircraft'].get('registration') or "未提供")
        final_type = manual_type if manual_type else (f['aircraft'].get('icao') or f['aircraft'].get('model') or "未提供")
        
        # 整理結果資料
        res = {
            "航班/日期": f"{flight_no} / {target_date}",
            "飛機編號": final_reg,
            "機型": final_type,
            "實際起降(Zulu)": f"{dep_dt.strftime('%H:%M') if dep_dt else 'N/A'}Z / {arr_dt.strftime('%H:%M') if arr_dt else 'N/A'}Z",
            "飛行時間": duration,
            "狀態": f.get('flight_status', '未知').upper(),
            "登機門": f"{f['departure'].get('gate') or 'N/A'}"
        }
        
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
        st.error("找不到該航班資料。")

st.divider()
st.caption("數據來源：Aviationstack API | 飛行紀錄自動化工具")
