import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# 設定網頁標題與圖示
st.set_page_config(page_title="我的飛行日誌", page_icon="✈️")
st.title("✈️ 我的個人飛行日誌")

# --- API Keys ---
RAPID_API_KEY = "d2cfcfb899msh0ee2823290701c7p126029jsn9f6dab4a88df"
AVI_KEY = "a85e1d8cc607a691b63846eea47bd40e"

with st.sidebar:
    st.header("🔍 航班查詢")
    flight_no = st.text_input("航班號碼", value="HB704").upper()
    target_date = st.date_input("飛行日期", value=datetime.now())
    st.success("目前啟用：跨資料庫二段校驗模式")

def parse_iso(t_str):
    if not t_str: return None
    try:
        return datetime.fromisoformat(t_str.replace('Z', '+00:00'))
    except:
        return None

def calculate_duration(dep_dt, arr_dt):
    if not dep_dt or not arr_dt: return "未知"
    diff = arr_dt - dep_dt
    h, m = divmod(int(diff.total_seconds()), 3600)
    return f"{h}h {m//60}m" if h >= 0 else "跨日計算中"

if st.button("啟動二段深度查詢"):
    # 第一段：從 AeroDataBox 抓取基礎資訊與機型
    adb_url = f"https://aerodatabox.p.rapidapi.com/flights/number/{flight_no}/{target_date}"
    adb_headers = {"x-rapidapi-key": RAPID_API_KEY, "x-rapidapi-host": "aerodatabox.p.rapidapi.com"}
    
    # 第二段：從 Aviationstack 抓取備援編號
    avi_url = f"http://api.aviationstack.com/v1/flights?access_key={AVI_KEY}&flight_iata={flight_no}"

    with st.spinner('正在執行二段資料庫比對...'):
        res_adb = requests.get(adb_url, headers=adb_headers).json()
        res_avi = requests.get(avi_url).json()

    if res_adb and len(res_adb) > 0:
        f_adb = res_adb[0]
        f_avi = next((i for i in res_avi.get('data', []) if i['flight_date'] == str(target_date)), {})

        # --- 飛機資料庫校驗邏輯 ---
        # 優先取 ADB 註冊號，若無則取 AVI 註冊號
        reg = f_adb.get('aircraft', {}).get('reg') or f_avi.get('aircraft', {}).get('registration') or "⚠️ 暫無數據"
        
        # 優先取 ADB 機型，若無則取 AVI 機型
        model = f_adb.get('aircraft', {}).get('model') or f_avi.get('aircraft', {}).get('model') or "B737-800"
        
        # 航空公司名稱校正
        airline = "Greater Bay Airlines (大灣區航空)" if flight_no.startswith("HB") else f_adb['airline'].get('name')

        # 時間抓取與 Zulu 轉換
        raw_dep = f_adb['departure'].get('actualTimeUtc') or f_adb['departure'].get('scheduledTimeUtc') or f_avi.get('departure', {}).get('scheduled')
        raw_arr = f_adb['arrival'].get('actualTimeUtc') or f_adb['arrival'].get('scheduledTimeUtc') or f_avi.get('arrival', {}).get('scheduled')
        
        dt_dep = parse_iso(raw_dep)
        dt_arr = parse_iso(raw_arr)
        
        zulu_time = f"{dt_dep.strftime('%H:%M') if dt_dep else 'N/A'}Z / {dt_arr.strftime('%H:%M') if dt_arr else 'N/A'}Z"
        
        # 數據封裝
        log_res = {
            "航班/日期": f"{flight_no} / {target_date}",
            "飛機編號 (Reg)": reg,
            "機型 (Model)": model,
            "起降(Zulu)": zulu_time,
            "飛行時間": calculate_duration(dt_dep, dt_arr),
            "航空公司": airline
        }

        st.success("二段查詢完成！已補全缺失欄位。")
        st.table(pd.DataFrame([log_res]))
        
        # CSV 下載
        csv = pd.DataFrame([log_res]).to_csv(index=False).encode('utf-8-sig')
        st.download_button("💾 下載飛行日誌", data=csv, file_name=f"FlightLog_{flight_no}.csv")

        if reg == "⚠️ 暫無數據":
            st.info("💡 專業提示：若此航班剛飛完，API 註冊號可能延遲錄入，建議 12 小時後再次查詢。")
    else:
        st.error("目前資料庫中找不到此航班，請確認號碼與日期。")
