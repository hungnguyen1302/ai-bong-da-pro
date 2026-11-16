import streamlit as st
import requests
from groq import Groq
from datetime import datetime

st.set_page_config(page_title="AI Football Analysis Pro - Worldwide", page_icon="⚽", layout="centered")

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
API_FOOTBALL_KEY = st.secrets.get("API_FOOTBALL_KEY", "")
VALID_VIP_CODES = [code.strip() for code in st.secrets["VIP_CODES"].split(",")]

client = Groq(api_key=GROQ_API_KEY)
HEADERS = {"x-apisports-key": API_FOOTBALL_KEY}
BASE_URL = "https://v3.football.api-sports.io"

# Danh sách các ngôn ngữ phổ biến trên thế giới
LANGUAGES = {
    "🇻🇳 Tiếng Việt": "Vietnamese",
    "🇬🇧 English": "English",
    "🇪🇸 Español (Spanish)": "Spanish",
    "🇫🇷 Français (French)": "French",
    "🇩🇪 Deutsch (German)": "German",
    "🇮🇹 Italiano (Italian)": "Italian",
    "🇧🇷 Português (Portuguese)": "Portuguese",
    "🇰🇷 한국어 (Korean)": "Korean",
    "🇯🇵 日本語 (Japanese)": "Japanese",
    "🇹🇭 ไทย (Thai)": "Thai",
    "🇮🇩 Bahasa Indonesia": "Indonesian",
    "🇷🇺 Русский (Russian)": "Russian",
    "🇸🇦 العربية (Arabic)": "Arabic"
}

with st.sidebar:
    selected_lang_label = st.selectbox("🌐 Language / Ngôn ngữ", list(LANGUAGES.keys()))
    target_language = LANGUAGES[selected_lang_label]
    
    st.header("🔐 VIP Activation / Kích hoạt VIP")
    user_code = st.text_input("Enter VIP Code / Nhập mã VIP:", type="password")
    st.markdown("---")
    st.info("💡 **Contact Zalo/Telegram:**\n\n**0827.155.093**")

if user_code not in VALID_VIP_CODES:
    st.warning("🔒 Please enter your **VIP Activation Code** in the sidebar to unlock the system. / Vui lòng nhập mã VIP để mở khóa hệ thống.")
    st.markdown("""
    ### 🌟 Global VIP Perks / Đặc quyền VIP Toàn Cầu:
    * 🌍 **1,000+ Leagues / 1.000+ Giải đấu:** Auto-update standings, form, and H2H.
    * ✍️ **Custom Match Analysis / Phân tích mọi trận:** Input any 2 teams worldwide.
    * 🧠 **AI Tactical Intelligence / Trí tuệ nhân tạo chuyên sâu:** Deep tactical breakdown & score prediction.
    """)
    st.stop()

st.success(f"✅ VIP License Activated! / Đã kích hoạt thành công (Language: {target_language})")

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
    standings_text = "No standings data."
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

    h2h_text = "No head-to-head data."
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

st.title("⚽ AI Global Football Analysis Pro")

tab1, tab2 = st.tabs(["🌍 Auto Data (1,000+ Leagues)", "✍️ Custom Match (2 Teams)"])

with tab1:
    if not API_FOOTBALL_KEY:
        st.error("⚠️ API_FOOTBALL_KEY is missing in Secrets.")
    else:
        POPULAR_LEAGUES = {
            "Premier League (England)": {"id": 39, "season": None, "name": "Premier League"},
            "UEFA Champions League": {"id": 2, "season": None, "name": "UEFA Champions League"},
            "UEFA Europa League": {"id": 3, "season": None, "name": "UEFA Europa League"},
            "V.League 1 (Vietnam)": {"id": 340, "season": None, "name": "V.League 1"},
            "La Liga (Spain)": {"id": 140, "season": None, "name": "La Liga"},
            "Serie A (Italy)": {"id": 135, "season": None, "name": "Serie A"},
            "Bundesliga (Germany)": {"id": 78, "season": None, "name": "Bundesliga"},
            "Ligue 1 (France)": {"id": 61, "season": None, "name": "Ligue 1"},
            "Saudi Pro League": {"id": 307, "season": None, "name": "Saudi Pro League"},
            "J1 League (Japan)": {"id": 98, "season": None, "name": "J1 League"},
            "K League 1 (South Korea)": {"id": 292, "season": None, "name": "K League 1"},
        }

        search_query = st.text_input("🔍 Search any league worldwide (e.g., Brazil, MLS, Argentina...):", "")

        if search_query.strip():
            leagues_dict = search_leagues(search_query.strip())
            if not leagues_dict:
                st.warning("No matching leagues found. Try shorter keywords.")
                st.stop()
        else:
            leagues_dict = POPULAR_LEAGUES

        selected_league_label = st.selectbox("1. Select League / Chọn giải đấu:", list(leagues_dict.keys()))
        league_info = leagues_dict[selected_league_label]
        active_season = league_info["season"] if league_info["season"] else get_current_season(league_info["id"])

        fixtures = get_upcoming_fixtures(league_info["id"], active_season)

        if fixtures:
            fixture_dict = {
                f"{f['teams']['home']['name']} vs {f['teams']['away']['name']} ({f['fixture']['date'][:16].replace('T', ' ')} UTC)": f
                for f in fixtures
            }
            selected_fixture_label = st.selectbox("2. Select Match / Chọn trận đấu:", list(fixture_dict.keys()))
            fx = fixture_dict[selected_fixture_label]
            extra_info_1 = st.text_area("3. Additional info (injuries, tactical news...):", "", key="extra1")

            if st.button("🚀 Analyze Match Now", type="primary", use_container_width=True, key="btn1"):
                with st.spinner("AI is analyzing standings, H2H, and tactics..."):
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
                            {"role": "system", "content": f"You are an Elite International Football Tactical Analyst. You MUST write your entire response strictly in {target_language}. Structure the analysis into 4 professional sections: 1. Squad Strength & Current Form; 2. Head-to-Head & Key Stats; 3. Tactical Hotspots; 4. Match Scenario & Score Prediction."},
                            {"role": "user", "content": prompt}
                        ],
                        model=active_model,
                        temperature=0.6
                    )
                    st.markdown("---")
                    st.markdown(chat_completion.choices[0].message.content)
        else:
            st.info("No upcoming fixtures found for this league.")

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        custom_home = st.text_input("Home Team / Đội nhà:", placeholder="e.g., Real Madrid")
    with col2:
        custom_away = st.text_input("Away Team / Đội khách:", placeholder="e.g., Barcelona")
    custom_league = st.text_input("League / Giải đấu:", placeholder="e.g., El Clasico")
    extra_info_2 = st.text_area("Form or injuries info:", placeholder="e.g., Key player injured...", key="extra2")

    if st.button("🚀 Analyze Custom Match", type="primary", use_container_width=True, key="btn2"):
        if not custom_home.strip() or not custom_away.strip():
            st.warning("Please enter both team names.")
        else:
            with st.spinner("AI is analyzing custom match tactics..."):
                active_model = get_active_groq_model()
                prompt_custom = f"""
                Match analysis: {custom_home} (Home) vs {custom_away} (Away).
                League / Context: {custom_league if custom_league else 'General match'}
                Additional Info: {extra_info_2 if extra_info_2 else 'Standard tactical profile.'}
                """
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": f"You are an Elite International Football Tactical Analyst. You MUST write your entire response strictly in {target_language}. Structure the analysis into 4 professional sections: 1. Squad Strength & Form; 2. Head-to-Head & Stats; 3. Tactical Hotspots; 4. Match Scenario & Score Prediction."},
                        {"role": "user", "content": prompt_custom}
                    ],
                    model=active_model,
                    temperature=0.6
                )
                st.markdown("---")
                st.markdown(chat_completion.choices[0].message.content)
