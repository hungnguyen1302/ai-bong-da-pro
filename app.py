import streamlit as st
import requests
from groq import Groq
from datetime import datetime

st.set_page_config(page_title="AI Phân Tích Bóng Đá Toàn Cầu Pro", page_icon="⚽", layout="centered")

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
API_FOOTBALL_KEY = st.secrets.get("API_FOOTBALL_KEY", "")
VALID_VIP_CODES = [code.strip() for code in st.secrets["VIP_CODES"].split(",")]

client = Groq(api_key=GROQ_API_KEY)
HEADERS = {"x-apisports-key": API_FOOTBALL_KEY}
BASE_URL = "https://v3.football.api-sports.io"

st.title("⚽ AI Chuyên Gia Phân Tích Bóng Đá Toàn Cầu")

with st.sidebar:
    st.header("🔐 Kích hoạt tài khoản VIP")
    user_code = st.text_input("Nhập Mã Kích Hoạt của bạn:", type="password")
    st.markdown("---")
    st.info("💡 **Chưa có mã sử dụng?**\n\nLiên hệ Zalo: **0827.155.093** để mua mã kích hoạt.")

if user_code not in VALID_VIP_CODES:
    st.warning("🔒 Vui lòng nhập **Mã Kích Hoạt VIP** ở thanh menu bên trái để mở khóa hệ thống.")
    st.markdown("""
    ### Đặc quyền dành cho thành viên VIP:
    * 🌍 **Kho dữ liệu 1.000+ giải đấu:** Tự động cập nhật BXH, phong độ và đối đầu (H2H) của V-League, Ngoại Hạng Anh, C1/C2, Saudi Pro League, J-League, K-League...
    * ✍️ **Phân tích mọi trận đấu tùy chọn:** Tự nhập tên 2 đội bóng bất kỳ trên toàn thế giới để AI bóc tách chiến thuật ngay lập tức.
    * 🧠 **Siêu trí tuệ nhân tạo chuyên sâu:** Đọc vị điểm nóng sân cỏ và dự đoán kịch bản tỷ số sắc bén.
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

tab1, tab2 = st.tabs(["🌍 Dữ liệu Tự động (1.000+ Giải)", "✍️ Nhập tên 2 Đội Bất Kỳ"])

with tab1:
    if not API_FOOTBALL_KEY:
        st.error("⚠️ Chưa cấu hình API_FOOTBALL_KEY trong Secrets. Bạn vẫn có thể dùng tab 'Nhập tên 2 Đội Bất Kỳ' bên cạnh!")
    else:
        POPULAR_LEAGUES = {
            "Ngoại Hạng Anh - Premier League (England)": {"id": 39, "season": None, "name": "Premier League"},
            "Cúp C1 - UEFA Champions League": {"id": 2, "season": None, "name": "UEFA Champions League"},
            "Cúp C2 - UEFA Europa League": {"id": 3, "season": None, "name": "UEFA Europa League"},
            "V-League 1 (Vietnam)": {"id": 340, "season": None, "name": "V.League 1"},
            "La Liga (Spain)": {"id": 140, "season": None, "name": "La Liga"},
            "Serie A (Italy)": {"id": 135, "season": None, "name": "Serie A"},
            "Bundesliga (Germany)": {"id": 78, "season": None, "name": "Bundesliga"},
            "Ligue 1 (France)": {"id": 61, "season": None, "name": "Ligue 1"},
            "Saudi Pro League (Saudi Arabia)": {"id": 307, "season": None, "name": "Pro League"},
            "J1 League (Japan)": {"id": 98, "season": None, "name": "J1 League"},
            "K League 1 (South Korea)": {"id": 292, "season": None, "name": "K League 1"},
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
        active_season = league_info["season"] if league_info["season"] else get_current_season(league_info["id"])

        fixtures = get_upcoming_fixtures(league_info["id"], active_season)

        if fixtures:
            fixture_dict = {
                f"{f['teams']['home']['name']} vs {f['teams']['away']['name']} ({f['fixture']['date'][:16].replace('T', ' ')} UTC)": f
                for f in fixtures
            }
            selected_fixture_label = st.selectbox("2. Chọn trận đấu sắp diễn ra:", list(fixture_dict.keys()))
            fx = fixture_dict[selected_fixture_label]
            extra_info_1 = st.text_area("3. Thông tin bổ sung (chấn thương, thẻ phạt, tính chất trận đấu...):", "", key="extra1")

            if st.button("🚀 Phân tích trận đấu ngay", type="primary", use_container_width=True, key="btn1"):
                with st.spinner("AI đang tổng hợp BXH, lịch sử đối đầu và phân tích chiến thuật..."):
                    home_team = fx["teams"]["home"]
                    away_team = fx["teams"]["away"]
                    standings_text, h2h_text = get_standings_and_h2h(
                        league_info["id"], active_season, home_team["id"], away_team["id"]
                    )
                    active_model = get_active_groq_model()

                    prompt = f"""
                    Phân tích trận đấu: {home_team['name']} (Chủ nhà) vs {away_team['name']} (Khách).
                    Giải đấu: {league_info['name']} (Mùa {active_season}) - Vòng: {fx['league'].get('round', 'N/A')}
                    
                    Bảng xếp hạng & Phong độ hiện tại:
                    {standings_text}
                    
                    Lịch sử 5 lần đối đầu gần nhất (H2H):
                    {h2h_text}
                    
                    Thông tin bổ sung: {extra_info_1 if extra_info_1 else 'Không có'}
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
            st.info("Hiện chưa có lịch thi đấu sắp tới cho giải này. Bạn có thể chuyển sang tab **✍️ Nhập tên 2 Đội Bất Kỳ** bên cạnh để phân tích ngay!")

with tab2:
    st.markdown("Nhập tên 2 đội bóng bất kỳ trên thế giới (giao hữu, giải trẻ, bóng đá nữ, giải quốc nội...) để AI phân tích chuyên sâu:")
    col1, col2 = st.columns(2)
    with col1:
        custom_home = st.text_input("Đội chủ nhà:", placeholder="Ví dụ: Hà Nội FC")
    with col2:
        custom_away = st.text_input("Đội khách:", placeholder="Ví dụ: Công An Hà Nội")
    custom_league = st.text_input("Tên giải đấu / Bối cảnh:", placeholder="Ví dụ: Vòng 8 V-League 2026")
    extra_info_2 = st.text_area("Thông tin phong độ, chấn thương gần đây (nếu có):", placeholder="Ví dụ: Hà Nội FC vắng tiền đạo chủ lực, CAHN vừa thắng 2 trận liên tiếp...", key="extra2")

    if st.button("🚀 Phân tích trận đấu tùy chọn", type="primary", use_container_width=True, key="btn2"):
        if not custom_home.strip() or not custom_away.strip():
            st.warning("Vui lòng nhập đầy đủ tên cả 2 đội bóng.")
        else:
            with st.spinner("AI đang phân tích chiến thuật và tương quan hai đội..."):
                active_model = get_active_groq_model()
                prompt_custom = f"""
                Phân tích trận đấu bóng đá: {custom_home} (Chủ nhà) vs {custom_away} (Khách).
                Giải đấu / Bối cảnh: {custom_league if custom_league else 'Không rõ'}
                Thông tin phong độ & lực lượng bổ sung: {extra_info_2 if extra_info_2 else 'Dựa trên dữ liệu chuyên môn tổng hợp về phong cách thi đấu và đẳng cấp hai đội.'}
                """
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "Bạn là Chuyên gia Phân tích Chiến thuật Bóng đá Quốc tế. Hãy phân tích trận đấu sắc bén bằng tiếng Việt theo 4 mục: 1. Tương quan lực lượng & Phong cách thi đấu; 2. Lịch sử & Thống kê đáng chú ý; 3. Điểm nóng chiến thuật; 4. Kịch bản & Dự đoán tỷ số."},
                        {"role": "user", "content": prompt_custom}
                    ],
                    model=active_model,
                    temperature=0.6
                )
                st.markdown("---")
                st.markdown(chat_completion.choices[0].message.content)
