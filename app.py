import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# 設定網頁標題與圖示
st.set_page_config(page_title="我的飛行日誌", page_icon="✈️")
st.title("✈️ 我的個人飛行日誌")

# --- 設定區 ---
# 這是你剛才抓到的 Key
RAPID_API_KEY = "d2cfcfb899msh0ee2823290701c7p126029jsn9f6dab4a88df"

with st.sidebar:
    st.header("🔍 航班查詢")
    flight_no = st.text_input("航班號碼 (如: HB704)", value="HB704").upper()
    target_date = st.date_input("飛行日期", value=datetime.now())
    st.info("AeroDataBox 會提供精準的機身註冊編號。")

if st.button("從高級資料庫抓取數據"):
    # AeroDataBox 查詢網址
    url = f"https://aerodatabox.p.rapidapi.com/flights/number/{flight_no}/{target_date}"
    
    headers = {
        "x-rapidapi-key": RAPID_API_KEY,
        "x-rapidapi-host": "aerodatabox.p.rapidapi.com"
    }
    
    with st.spinner('正在檢索機身詳細資訊...'):
        response = requests.get(url, headers=headers)
        
    if response.status_code == 200:
        data = response.json()
        
        if len(data) > 0:
            # 取得第一筆資料
            f = data[0]
            aircraft = f.get('aircraft', {})
            
            # 格式化時間：AeroDataBox 回傳的是 Zulu Time (UTC)
            def format_zulu(t_str):
                if not t_str: return "N/A"
                # 轉成 HH:MMZ 格式
                return t_str.split('T')[1][:5] + "Z"

            dep_z = format_zulu(f['departure'].get('actualTimeUtc') or f['departure'].get('scheduledTimeUtc'))
            arr_z = format_zulu(f['arrival'].get('actualTimeUtc') or f['arrival'].get('scheduledTimeUtc'))

            res = {
                "航班/日期": f"{flight_no} / {target_date}",
                "飛機編號 (Reg)": aircraft.get('reg', '⚠️ 無法取得'),
                "機型 (Model)": aircraft.get('model', '⚠️ 無法取得'),
                "起降(Zulu)": f"{dep_z} / {arr_z}",
                "狀態": f.get('status', 'Unknown').upper(),
                "航空公司": f['airline'].get('name', 'N/A')
            }
            
            st.success("數據抓取成功！")
            st.table(pd.DataFrame([res]))
            
            # 下載 CSV 功能
            csv = pd.DataFrame([res]).to_csv(index=False).encode('utf-8-sig')
            st.download_button("💾 下載此筆日誌紀錄", data=csv, file_name=f"Log_{flight_no}_{target_date}.csv")
            
            if aircraft.get('reg') == None:
                st.warning("提示：該航班尚未分配機身編號，請於起飛後再試。")
        else:
            st.warning("資料庫中找不到該航班，請確認號碼與日期。")
    elif response.status_code == 404:
        st.error("找不到資料：請確認日期是否在最近幾天內（免費版查詢範圍有限）。")
    else:
        st.error(f"連線失敗 (代碼: {response.status_code})，請確認 API Key 是否有效。")

st.divider()
st.caption("Data Source: AeroDataBox via RapidAPI")
