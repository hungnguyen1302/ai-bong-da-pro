import streamlit as st
import requests
from groq import Groq
from datetime import datetime

st.set_page_config(page_title="AI Football Analysis Pro - Global", page_icon="⚽", layout="centered")

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
API_FOOTBALL_KEY = st.secrets.get("API_FOOTBALL_KEY", "")
VALID_VIP_CODES = [code.strip() for code in st.secrets["VIP_CODES"].split(",")]

client = Groq(api_key=GROQ_API_KEY)
HEADERS = {"x-apisports-key": API_FOOTBALL_KEY}
BASE_URL = "https://v3.football.api-sports.io"

# Từ điển đa ngôn ngữ (Tiếng Việt & Tiếng Anh)
LANG = {
    "vi": {
        "title": "⚽ AI Chuyên Gia Phân Tích Bóng Đá Toàn Cầu",
        "sidebar_header": "🔐 Kích hoạt tài khoản VIP",
        "input_code": "Nhập Mã Kích Hoạt của bạn:",
        "contact_zalo": "💡 **Chưa có mã sử dụng?**\n\nLiên hệ Zalo: **0827.155.093** để mua mã kích hoạt.",
        "locked_warning": "🔒 Vui lòng nhập **Mã Kích Hoạt VIP** ở thanh menu bên trái để mở khóa hệ thống.",
        "locked_features": "### Đặc quyền dành cho thành viên VIP:\n* 🌍 **Kho dữ liệu 1.000+ giải đấu:** Tự động cập nhật BXH, phong độ và đối đầu (H2H).\n* ✍️ **Phân tích mọi trận đấu tùy chọn:** Tự nhập tên 2 đội bóng bất kỳ trên toàn thế giới.\n* 🧠 **Siêu trí tuệ nhân tạo chuyên sâu:** Bóc tách chiến thuật và dự đoán kịch bản tỷ số.",
        "success": "✅ Đã kích hoạt bản quyền VIP Toàn Cầu!",
        "tab1": "🌍 Dữ liệu Tự động (1.000+ Giải)",
        "tab2": "✍️ Nhập tên 2 Đội Bất Kỳ",
        "search_label": "🔍 Tìm kiếm giải đấu bất kỳ trên thế giới (VD: Vietnam, Brazil, MLS...):",
        "search_not_found": "Không tìm thấy giải đấu phù hợp, thử gõ từ khóa tiếng Anh ngắn gọn hơn.",
        "select_league": "1. Chọn giải đấu:",
        "select_match": "2. Chọn trận đấu sắp diễn ra:",
        "extra_info": "3. Thông tin bổ sung (chấn thương, thẻ phạt, tính chất trận đấu...):",
        "analyze_btn": "🚀 Phân tích trận đấu ngay",
        "analyzing": "AI đang tổng hợp BXH, lịch sử đối đầu và phân tích chiến thuật...",
        "no_fixtures": "Hiện chưa có lịch thi đấu sắp tới cho giải này. Hãy thử tab **✍️ Nhập tên 2 Đội Bất Kỳ**!",
        "custom_home": "Đội chủ nhà:",
        "custom_away": "Đội khách:",
        "custom_league": "Tên giải đấu / Bối cảnh:",
        "custom_extra": "Thông tin phong độ, chấn thương gần đây (nếu có):",
        "custom_btn": "🚀 Phân tích trận đấu tùy chọn",
        "custom_warning": "Vui lòng nhập đầy đủ tên cả 2 đội bóng.",
        "custom_loading": "AI đang phân tích chiến thuật và tương quan hai đội...",
        "system_prompt": "Bạn là Chuyên gia Phân tích Chiến thuật Bóng đá Quốc tế. Hãy phân tích trận đấu sắc bén bằng tiếng Việt theo 4 mục: 1. Tương quan lực lượng & Phong độ; 2. Lịch sử đối đầu & Thống kê then chốt; 3. Điểm nóng chiến thuật; 4. Kịch bản & Dự đoán tỷ số."
    },
    "en": {
        "title": "⚽ AI Global Football Analysis Pro",
        "sidebar_header": "🔐 Activate VIP Account",
        "input_code": "Enter your VIP Activation Code:",
        "contact_zalo": "💡 **No activation code?**\n\nContact via Zalo/Telegram: **09xx.xxx.xxx** to purchase.",
        "locked_warning": "🔒 Please enter your **VIP Activation Code** in the left sidebar to unlock the system.",
        "locked_features": "### VIP Member Perks:\n* 🌍 **1,000+ Leagues Database:** Auto-update standings, form, and H2H.\n* ✍️ **Custom Match Analysis:** Input any 2 teams worldwide.\n* 🧠 **Advanced AI Intelligence:** Tactical breakdown & precise score prediction.",
        "success": "✅ Global VIP License Activated Successfully!",
        "tab1": "🌍 Auto Data (1,000+ Leagues)",
        "tab2": "✍️ Custom 2 Teams",
        "search_label": "🔍 Search any league worldwide (e.g., Premier League, Brazil, MLS...):",
        "search_not_found": "No matching leagues found. Try shorter English keywords.",
        "select_league": "1. Select League:",
        "select_match": "2. Select Upcoming Match:",
        "extra_info": "3. Additional Info (injuries, cards, match importance...):",
        "analyze_btn": "🚀 Analyze Match Now",
        "analyzing": "AI is compiling standings, H2H, and tactical breakdown...",
        "no_fixtures": "No upcoming fixtures for this league. Try the **✍️ Custom 2 Teams** tab!",
        "custom_home": "Home Team:",
        "custom_away": "Away Team:",
        "custom_league": "League / Context:",
        "custom_extra": "Recent form or injury news (optional):",
        "custom_btn": "🚀 Analyze Custom Match",
        "custom_warning": "Please enter the names of both teams.",
        "custom_loading": "AI is analyzing tactics and head-to-head match-up...",
        "system_prompt": "You are an International Football Tactical Analyst. Analyze the match sharply in English across 4 sections: 1. Squad Strength & Current Form; 2. Head-to-Head & Key Stats; 3. Tactical Hotspots; 4. Match Scenario & Score Prediction."
    }
}

# Chọn ngôn ngữ ở sidebar
with st.sidebar:
    lang_choice = st.selectbox("🌐 Ngôn ngữ / Language", ["Tiếng Việt", "English"])
    lang_key = "vi" if lang_choice == "Tiếng Việt" else "en"
    t = LANG[lang_key]

    st.header(t["sidebar_header"])
    user_code = st.text_input(t["input_code"], type="password")
    st.markdown("---")
    st.info(t["contact_zalo"])

st.title(t["title"])

if user_code not in VALID_VIP_CODES:
    st.warning(t["locked_warning"])
    st.markdown(t["locked_features"])
    st.stop()

st.success(t["success"])

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
def get_current_season(league_id):
    res = requests.get(f"{BASE_URL}/leagues", headers=HEADERS, params={"id": league_id, "current": "true"})
    if res.status_code == 200:
        resp = res.json().get("response", [])
        if resp and resp[0].get("seasons"):
            return resp[0]["seasons"][0]["year"]
    return datetime.now().year

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
            label = f"{league['name']} ({country}) - {season_year}"
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
    standings_text = "No standings data available."
    res_st = requests.get(f"{BASE_URL}/standings", headers=HEADERS, params={"league": league_id, "season": season})
    if res_st.status_code == 200:
        resp = res_st.json().get("response", [])
        if resp:
            groups = resp[0]["league"]["standings"]
            if groups:
                lines = []
                for r in groups[0]:
                    lines.append(f"Rank {r['rank']}: {r['team']['name']} ({r['points']} pts | Played: {r['all']['played']} | GF-GA: {r['all']['goals']['for']}:{r['all']['goals']['against']} | Form: {r.get('form', 'N/A')})")
                standings_text = "\n".join(lines)

    h2h_text = "No head-to-head data available."
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

tab1, tab2 = st.tabs([t["tab1"], t["tab2"]])

with tab1:
    if not API_FOOTBALL_KEY:
        st.error("⚠️ API_FOOTBALL_KEY is not configured in Secrets.")
    else:
        POPULAR_LEAGUES = {
            "Premier League (England)": {"id": 39, "season": None, "name": "Premier League"},
            "UEFA Champions League (World)": {"id": 2, "season": None, "name": "UEFA Champions League"},
            "UEFA Europa League (World)": {"id": 3, "season": None, "name": "UEFA Europa League"},
            "V.League 1 (Vietnam)": {"id": 340, "season": None, "name": "V.League 1"},
            "La Liga (Spain)": {"id": 140, "season": None, "name": "La Liga"},
            "Serie A (Italy)": {"id": 135, "season": None, "name": "Serie A"},
            "Bundesliga (Germany)": {"id": 78, "season": None, "name": "Bundesliga"},
            "Ligue 1 (France)": {"id": 61, "season": None, "name": "Ligue 1"},
            "Saudi Pro League (Saudi Arabia)": {"id": 307, "season": None, "name": "Pro League"},
            "J1 League (Japan)": {"id": 98, "season": None, "name": "J1 League"},
            "K League 1 (South Korea)": {"id": 292, "season": None, "name": "K League 1"},
        }

        search_query = st.text_input(t["search_label"], "")

        if search_query.strip():
            leagues_dict = search_leagues(search_query.strip())
            if not leagues_dict:
                st.warning(t["search_not_found"])
                st.stop()
        else:
            leagues_dict = POPULAR_LEAGUES

        selected_league_label = st.selectbox(t["select_league"], list(leagues_dict.keys()))
        league_info = leagues_dict[selected_league_label]
        active_season = league_info["season"] if league_info["season"] else get_current_season(league_info["id"])

        fixtures = get_upcoming_fixtures(league_info["id"], active_season)

        if fixtures:
            fixture_dict = {
                f"{f['teams']['home']['name']} vs {f['teams']['away']['name']} ({f['fixture']['date'][:16].replace('T', ' ')} UTC)": f
                for f in fixtures
            }
            selected_fixture_label = st.selectbox(t["select_match"], list(fixture_dict.keys()))
            fx = fixture_dict[selected_fixture_label]
            extra_info_1 = st.text_area(t["extra_info"], "", key="extra1")

            if st.button(t["analyze_btn"], type="primary", use_container_width=True, key="btn1"):
                with st.spinner(t["analyzing"]):
                    home_team = fx["teams"]["home"]
                    away_team = fx["teams"]["away"]
                    standings_text, h2h_text = get_standings_and_h2h(
                        league_info["id"], active_season, home_team["id"], away_team["id"]
                    )
                    active_model = get_active_groq_model()

                    prompt = f"""
                    Match: {home_team['name']} (Home) vs {away_team['name']} (Away).
                    League: {league_info['name']} (Season {active_season}) - Round: {fx['league'].get('round', 'N/A')}
                    
                    Standings & Form:
                    {standings_text}
                    
                    Head-to-Head (Last 5 matches):
                    {h2h_text}
                    
                    Additional Info: {extra_info_1 if extra_info_1 else 'None'}
                    """
                    chat_completion = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": t["system_prompt"]},
                            {"role": "user", "content": prompt}
                        ],
                        model=active_model,
                        temperature=0.6
                    )
                    st.markdown("---")
                    st.markdown(chat_completion.choices[0].message.content)
        else:
            st.info(t["no_fixtures"])

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        custom_home = st.text_input(t["custom_home"], placeholder="e.g., Arsenal")
    with col2:
        custom_away = st.text_input(t["custom_away"], placeholder="e.g., Chelsea")
    custom_league = st.text_input(t["custom_league"], placeholder="e.g., Premier League")
    extra_info_2 = st.text_area(t["custom_extra"], placeholder="e.g., Key players injured...", key="extra2")

    if st.button(t["custom_btn"], type="primary", use_container_width=True, key="btn2"):
        if not custom_home.strip() or not custom_away.strip():
            st.warning(t["custom_warning"])
        else:
            with st.spinner(t["custom_loading"]):
                active_model = get_active_groq_model()
                prompt_custom = f"""
                Match analysis: {custom_home} (Home) vs {custom_away} (Away).
                League / Context: {custom_league if custom_league else 'General match'}
                Additional Info: {extra_info_2 if extra_info_2 else 'Standard tactical profile.'}
                """
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": t["system_prompt"]},
                        {"role": "user", "content": prompt_custom}
                    ],
                    model=active_model,
                    temperature=0.6
                )
                st.markdown("---")
                st.markdown(chat_completion.choices[0].message.content)
