import streamlit as st
import requests
from groq import Groq

st.set_page_config(page_title="AI Phân Tích Bóng Đá Pro", page_icon="⚽", layout="centered")

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
FOOTBALL_API_KEY = st.secrets["FOOTBALL_API_KEY"]
VALID_VIP_CODES = [code.strip() for code in st.secrets["VIP_CODES"].split(",")]

client = Groq(api_key=GROQ_API_KEY)
HEADERS = {"X-Auth-Token": FOOTBALL_API_KEY}

LEAGUES = {
    "Ngoại Hạng Anh (Premier League)": "PL",
    "Cúp C1 Châu Âu (Champions League)": "CL",
    "VĐQG Tây Ban Nha (La Liga)": "PD",
    "VĐQG Đức (Bundesliga)": "BL1",
    "VĐQG Ý (Serie A)": "SA",
    "VĐQG Pháp (Ligue 1)": "FL1"
}

st.title("⚽ AI Chuyên Gia Phân Tích Bóng Đá")

with st.sidebar:
    st.header("🔐 Kích hoạt tài khoản VIP")
    user_code = st.text_input("Nhập Mã Kích Hoạt của bạn:", type="password")
    st.markdown("---")
    st.info("💡 **Chưa có mã sử dụng?**\n\nLiên hệ Zalo: **09xx.xxx.xxx** để mua mã kích hoạt.")

if user_code not in VALID_VIP_CODES:
    st.warning("🔒 Vui lòng nhập **Mã Kích Hoạt VIP** ở thanh menu bên trái để mở khóa hệ thống phân tích.")
    st.markdown("""
    ### Tính năng dành cho thành viên VIP:
    * 📊 **Dữ liệu thời gian thực:** Tự động cập nhật bảng xếp hạng, hiệu số và phong độ 5 trận gần nhất.
    * 🧠 **Phân tích chiến thuật chuyên sâu:** Đọc vị sơ đồ, điểm nóng sân cỏ và tương quan lực lượng.
    * 🎯 **Kịch bản & Dự đoán tỷ số:** Đánh giá khách quan dựa trên xác suất thống kê.
    """)
    st.stop()

st.success("✅ Đã kích hoạt bản quyền VIP!")

@st.cache_data(ttl=3600)
def get_active_groq_model():
    models = client.models.list().data
    chat_models = [
        m.id for m in models 
        if "whisper" not in m.id.lower() 
        and "guard" not in m.id.lower() 
        and "tts" not in m.id.lower()
        and "embed" not in m.id.lower()
    ]
    for preferred in ["llama", "gpt", "qwen", "gemma", "deepseek", "mixtral"]:
        for m_id in chat_models:
            if preferred in m_id.lower():
                return m_id
    return chat_models[0] if chat_models else "llama-3.1-8b-instant"

@st.cache_data(ttl=3600)
def get_matches(league_code):
    url = f"https://api.football-data.org/v4/competitions/{league_code}/matches?status=SCHEDULED"
    res = requests.get(url, headers=HEADERS)
    return res.json().get("matches", [])[:15] if res.status_code == 200 else []

@st.cache_data(ttl=3600)
def get_standings(league_code):
    url = f"https://api.football-data.org/v4/competitions/{league_code}/standings"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        standings = res.json().get("standings", [])
        if standings:
            table = standings[0].get("table", [])
            return "\n".join([
                f"Hạng {r['position']}: {r['team']['name']} ({r['points']}đ / {r['playedGames']} trận | BT-BB: {r['goalsFor']}:{r['goalsAgainst']} | Phong độ: {r.get('form', 'N/A')})"
                for r in table
            ])
    return "Không có dữ liệu."

selected_league = st.selectbox("1. Chọn giải đấu:", list(LEAGUES.keys()))
league_code = LEAGUES[selected_league]
matches = get_matches(league_code)

if matches:
    match_dict = {f"{m['homeTeam']['name']} vs {m['awayTeam']['name']} ({m['utcDate'][:10]})": m for m in matches}
    selected_label = st.selectbox("2. Chọn trận đấu:", list(match_dict.keys()))
    match_data = match_dict[selected_label]
    extra_info = st.text_area("3. Thông tin bổ sung (chấn thương, thẻ phạt...):", "")

    if st.button("🚀 Phân tích trận đấu ngay", type="primary", use_container_width=True):
        with st.spinner("AI đang phân tích dữ liệu trận đấu..."):
            standings_text = get_standings(league_code)
            active_model = get_active_groq_model()
            prompt = f"""
            Phân tích trận đấu: {match_data['homeTeam']['name']} (Chủ nhà) vs {match_data['awayTeam']['name']} (Khách).
            Giải: {selected_league} - Vòng {match_data.get('matchday', 'N/A')}
            Bảng xếp hạng & Phong độ hiện tại:
            {standings_text}
            Thông tin bổ sung: {extra_info if extra_info else 'Không có'}
            """
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Bạn là Chuyên gia Phân tích Chiến thuật Bóng đá. Hãy phân tích trận đấu theo 4 mục: 1. Tương quan lực lượng & Phong độ; 2. Điểm nóng chiến thuật; 3. Thống kê then chốt; 4. Kịch bản & Dự đoán tỷ số. Trình bày sắc bén bằng tiếng Việt."},
                    {"role": "user", "content": prompt}
                ],
                model=active_model,
                temperature=0.6
            )
            st.markdown("---")
            st.markdown(chat_completion.choices[0].message.content)
else:
    st.info("Hiện chưa có lịch thi đấu sắp tới cho giải này.")
