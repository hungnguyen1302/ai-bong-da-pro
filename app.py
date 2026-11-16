import streamlit as st
import requests
from groq import Groq
from datetime import datetime

st.set_page_config(page_title="AI Phân Tích Bóng Đá Toàn Cầu", page_icon="⚽", layout="centered")

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
API_FOOTBALL_KEY = st.secrets["API_FOOTBALL_KEY"]
VALID_VIP_CODES = [code.strip() for code in st.secrets["VIP_CODES"].split(",")]

client = Groq(api_key=GROQ_API_KEY)
HEADERS = {"x-apisports-key": API_FOOTBALL_KEY}
BASE_URL = "https://v3.football.api-sports.io"

st.title("⚽ AI Chuyên Gia Phân Tích Bóng Đá Toàn Cầu")

with st.sidebar:
    st.header("🔐 Kích hoạt tài khoản VIP")
    user_code = st.text_input("Nhập Mã Kích Hoạt của bạn:", type="password")
    st.markdown("---")
    st.info("💡 **Chưa có mã sử dụng?**\n\nLiên hệ Zalo: **0386600108** để mua mã kích hoạt.")

if user_code not in VALID_VIP_CODES:
    st.warning("🔒 Vui lòng nhập **Mã Kích Hoạt VIP** ở thanh menu bên trái để mở khóa hệ thống phân tích 1.000+ giải đấu toàn cầu.")
    st.markdown("""
    ### Tính năng dành cho thành viên VIP:
    * 🌍 **Phủ sóng toàn cầu:** Đầy đủ V-League, Ngoại Hạng Anh, C1/C2/C3, Saudi Pro League, J-League, K-League, MLS...
    * 📊 **Dữ liệu thời gian thực:** Tự động cập nhật bảng xếp hạng, phong độ và lịch sử đối đầu (H2H).
    * 🧠 **Phân tích chiến thuật chuyên sâu:** Bóc tách sơ đồ, điểm nóng sân cỏ và dự đoán kịch bản tỷ số.
    """)
    st.stop()

st.success("✅ Đã kích hoạt bản quyền VIP Toàn Cầu!")

@st.cache_data(ttl=3600)
def get_active_groq_model():
    models = client.models.list().data
    chat_models = [
        m.id for m in models 
        if not any(x in m.id.lower() for x in ["whisper", "guard", "tts", "embed"])
    ]
    for preferred in ["llama", "gpt", "qwen", "gemma", "deepseek", "mixtral"]:
        for m_id in chat_models:
            if preferred in m_id.lower():
                return m_id
    return chat_models[0] if chat_models else "llama-3.1-8b-instant"

@st.cache_data(ttl=86400)
def search_leagues(keyword):
    res = requests.get(f"{BASE_URL}/leagues", headers=HEADERS, params={"search": keyword})
    if res.status_code == 200:
        data = res.json().get("response", [])
        results = {}
        for item in data[:25]:
            league = item["league"]
            country = item["country"]["name"]
            seasons = [s["year"] for s in item.get("seasons", []) if s.get("current")]
            season_year = seasons[0] if seasons else datetime.now().year
            label = f"{league['name']} ({country}) - Mùa {season_year}"
            results[label] = {"id": league["id"], "season": season_year, "name": league["name"]}
        return results
    return {}

@st.cache_data(ttl=3600)
def get_upcoming_fixtures(league_id, season):
    res = requests.get(
        f"{BASE_URL}/fixtures",
        headers=HEADERS,
        params={"league": league_id, "season": season, "next": 15}
    )
    return res.json().get("response", []) if res.status_code == 200 else []

@st.cache_data(ttl=3600)
def get_standings_and_h2h(league_id, season, home_id, away_id):
    standings_text = "Không có dữ liệu bảng xếp hạng."
    res_st = requests.get(f"{BASE_URL}/standings", headers=HEADERS, params={"league": league_id, "season": season})
    if res_st.status_code == 200:
        resp = res_st.json().get("response", [])
        if resp:
            groups = resp[0]["league"]["standings"]
            if groups:
                lines = []
                for r in groups[0]:
                    lines.append(f"Hạng {r['rank']}: {r['team']['name']} ({r['points']}đ | {r['all']['played']} trận | BT-BB: {r['all']['goals']['for']}:{r['all']['goals']['against']} | Phong độ: {r.get('form', 'N/A')})")
                standings_text = "\n".join(lines)

    h2h_text = "Chưa có dữ liệu đối đầu."
    res_h2h = requests.get(f"{BASE_URL}/fixtures/headtohead", headers=HEADERS, params={"h2h": f"{home_id}-{away_id}", "last": 5})
    if res_h2h.status_code == 200:
        h2h_list = res_h2h.json().get("response", [])
        if h2h_list:
            h2h_lines = [
                f"- {m['fixture']['date'][:10]}: {m['teams']['home']['name']} {m['goals']['home']} - {m['goals']['away']} {m['teams']['away']['name']}"
                for m in h2h_list
            ]
            h2h_text = "\n".join(h2h_lines)

    return standings_text, h2h_text

# Danh sách giải phổ biến mặc định + Ô tìm kiếm mọi giải thế giới
POPULAR_LEAGUES = {
    "Ngoại Hạng Anh - Premier League (England)": {"id": 39, "season": 2026, "name": "Premier League"},
    "Cúp C1 - UEFA Champions League (World)": {"id": 2, "season": 2026, "name": "UEFA Champions League"},
    "Cúp C2 - UEFA Europa League (World)": {"id": 3, "season": 2026, "name": "UEFA Europa League"},
    "V-League 1 (Vietnam)": {"id": 340, "season": 2026, "name": "V.League 1"},
    "La Liga (Spain)": {"id": 140, "season": 2026, "name": "La Liga"},
    "Serie A (Italy)": {"id": 135, "season": 2026, "name": "Serie A"},
    "Bundesliga (Germany)": {"id": 78, "season": 2026, "name": "Bundesliga"},
    "Ligue 1 (France)": {"id": 61, "season": 2026, "name": "Ligue 1"},
    "Saudi Pro League (Saudi Arabia)": {"id": 307, "season": 2026, "name": "Pro League"},
    "J1 League (Japan)": {"id": 98, "season": 2026, "name": "J1 League"},
    "K League 1 (South Korea)": {"id": 292, "season": 2026, "name": "K League 1"},
}

search_query = st.text_input("🔍 Tìm kiếm giải đấu bất kỳ trên thế giới (ví dụ: Vietnam, Brazil, MLS, Cup...):", "")

if search_query.strip():
    leagues_dict = search_leagues(search_query.strip())
    if not leagues_dict:
        st.warning("Không tìm thấy giải đấu phù hợp, thử gõ từ khóa tiếng Anh ngắn gọn hơn (ví dụ: England, Japan, Liga...).")
        st.stop()
else:
    leagues_dict = POPULAR_LEAGUES

selected_league_label = st.selectbox("1. Chọn giải đấu:", list(leagues_dict.keys()))
league_info = leagues_dict[selected_league_label]

fixtures = get_upcoming_fixtures(league_info["id"], league_info["season"])

if fixtures:
    fixture_dict = {
        f"{f['teams']['home']['name']} vs {f['teams']['away']['name']} ({f['fixture']['date'][:16].replace('T', ' ')} UTC)": f
        for f in fixtures
    }
    selected_fixture_label = st.selectbox("2. Chọn trận đấu sắp diễn ra:", list(fixture_dict.keys()))
    fx = fixture_dict[selected_fixture_label]
    extra_info = st.text_area("3. Thông tin bổ sung (chấn thương, thẻ phạt, tính chất trận đấu...):", "")

    if st.button("🚀 Phân tích trận đấu ngay", type="primary", use_container_width=True):
        with st.spinner("AI đang tổng hợp BXH, lịch sử đối đầu và phân tích chiến thuật..."):
            home_team = fx["teams"]["home"]
            away_team = fx["teams"]["away"]
            standings_text, h2h_text = get_standings_and_h2h(
                league_info["id"], league_info["season"], home_team["id"], away_team["id"]
            )
            active_model = get_active_groq_model()

            prompt = f"""
            Phân tích trận đấu: {home_team['name']} (Chủ nhà) vs {away_team['name']} (Khách).
            Giải đấu: {league_info['name']} - Vòng: {fx['league'].get('round', 'N/A')}
            
            Bảng xếp hạng & Phong độ hiện tại:
            {standings_text}
            
            Lịch sử 5 lần đối đầu gần nhất (H2H):
            {h2h_text}
            
            Thông tin bổ sung: {extra_info if extra_info else 'Không có'}
            """
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Bạn là Chuyên gia Phân tích Chiến thuật Bóng đá Quốc tế. Hãy phân tích trận đấu sắc bén bằng tiếng Việt theo 4 mục: 1. Tương quan lực lượng & Phong độ; 2. Lịch sử đối đầu & Thống kê then chốt; 3. Điểm nóng chiến thuật; 4. Kịch bản & Dự đoán tỷ số."},
                    {"role": "user", "content": prompt}
                ],
                model=active_model,
                temperature=0.6
            )
            st.markdown("---")
            st.markdown(chat_completion.choices[0].message.content)
else:
    st.info("Hiện chưa có lịch thi đấu sắp tới cho giải này (hoặc giải đang trong kỳ nghỉ giữa mùa). Hãy thử tìm một giải khác ở ô tìm kiếm phía trên.")
