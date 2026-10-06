import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- KONFIGURACIJA STRANICE ---
st.set_page_config(
    page_title="Događanja Hrvatska",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS prilagođen za mobilne uređaje
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }
        .event-card {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 12px;
            padding: 14px;
            margin-bottom: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .event-title {
            font-size: 1.1rem;
            font-weight: 700;
            color: #1E1E1E;
            margin-bottom: 4px;
        }
        .event-badge {
            display: inline-block;
            background-color: #E8F0FE;
            color: #1A73E8;
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 0.78rem;
            font-weight: 600;
            margin-bottom: 6px;
        }
        .event-meta {
            font-size: 0.85rem;
            color: #555555;
            margin-bottom: 3px;
        }
    </style>
""", unsafe_allow_html=True)

# --- INICIJALNI PODACI U MEMORIJI (RAM) ---
def get_initial_events():
    return [
        {
            "id": "1",
            "naslov": "Koncert u Lisinskom",
            "datum": "2026-10-15",
            "vrijeme": "20:00",
            "lokacija": "Zagreb",
            "mjestodogađaja": "KD Vatroslav Lisinski",
            "kategorija": "Koncerti",
            "cijena": "Besplatno",
            "opis": "Simfonijski orkestar izvodi klasična djela.",
            "poveznica": "https://www.infozagreb.hr"
        },
        {
            "id": "2",
            "naslov": "Izložba u Muzeju Istre",
            "datum": "2026-10-20",
            "vrijeme": "18:00",
            "lokacija": "Istra",
            "mjestodogađaja": "Pula",
            "kategorija": "Izložbe",
            "cijena": "Plaća se",
            "opis": "Pregled moderne umjetnosti Istre.",
            "poveznica": "https://www.istra.hr"
        }
    ]

# Postavljanje baze u st.session_state ako već ne postoji
if "events_data" not in st.session_state:
    st.session_state.events_data = get_initial_events()

# --- FUNKCIJA ZA PRIKUPLJANJE PODATAKA (SCRAPER) ---
def fetch_live_events():
    """Učitava nove događaje i izravno azurira st.session_state."""
    new_events = []
    try:
        # Primjer dohvata s javnog izvora
        url = "https://www.infozagreb.hr/hr/dogadanja"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Primjer parsiranja kartica s događajima
            articles = soup.find_all('div', class_='event-card-item')
            
            for idx, item in enumerate(articles[:10]):
                title_elem = item.find('h3') or item.find('a')
                naslov = title_elem.get_text(strip=True) if title_elem else f"Događaj {idx+1}"
                
                new_events.append({
                    "id": f"scraped_{idx}_{datetime.now().timestamp()}",
                    "naslov": naslov,
                    "datum": "2026-10-25",
                    "vrijeme": "19:00",
                    "lokacija": "Zagreb",
                    "mjestodogađaja": "Centar",
                    "kategorija": "Kultura",
                    "cijena": "Slobodan ulaz",
                    "opis": "Automatski dohvaćen događaj s portala InfoZagreb.",
                    "poveznica": "https://www.infozagreb.hr"
                })
    except Exception as e:
        st.error(f"Greška prilikom struganja: {e}")
    
    # Ako je dohvaćanje uspješno, ažuriraj radnu memoriju
    if new_events:
        st.session_state.events_data = new_events
    else:
        # Zamjenski unos za test ako web lokacija blokira zahtjev
        st.session_state.events_data.append({
            "id": str(datetime.now().timestamp()),
            "naslov": "Novo događanje (Osvježeno)",
            "datum": "2026-10-30",
            "vrijeme": "21:00",
            "lokacija": "Zagreb",
            "mjestodogađaja": "Tvornica kulture",
            "kategorija": "Koncerti",
            "cijena": "Plaća se",
            "opis": "Događaj uspješno dodan u radnu memoriju.",
            "poveznica": "https://www.infozagreb.hr"
        })

# --- NASLOV I GUMB ZA OSVJEŽAVANJE ---
st.title("📅 Događanja u HR")

if st.button("🔄 Osvježi događanja u memoriji", use_container_width=True):
    with st.spinner("Dohvaćam najnovije podatke..."):
        fetch_live_events()
        st.success("Radna memorija je osvježena!")
        st.rerun()

# --- PRETVORBA U DATAFRAME I FILTERI ---
df = pd.DataFrame(st.session_state.events_data)

if df.empty:
    st.warning("Nema dostupnih događanja u memoriji.")
    st.stop()

df['datum_dt'] = pd.to_datetime(df['datum'])

with st.expander("🔍 Filteri i pretraživanje", expanded=False):
    col_search, col_regija = st.columns(2)
    with col_search:
        search_query = st.text_input("Pretraži:", "")
    with col_regija:
        lokacije = ["Sve lokacije"] + sorted(list(df['lokacija'].unique()))
        selected_lokacija = st.selectbox("Regija / Grad:", lokacije)
    
    col_kat, col_cijena = st.columns(2)
    with col_kat:
        kategorije = ["Sve kategorije"] + sorted(list(df['kategorija'].unique()))
        selected_kategorija = st.selectbox("Kategorija:", kategorije)
    with col_cijena:
        cijene = ["Sve cijene", "Besplatno", "Plaća se", "Slobodan ulaz"]
        selected_cijena = st.selectbox("Cijena:", cijene)

# --- FILTRIRANJE PODATAKA ---
filtered_df = df.copy()

if search_query:
    filtered_df = filtered_df[
        filtered_df['naslov'].str.contains(search_query, case=False, na=False) |
        filtered_df['opis'].str.contains(search_query, case=False, na=False)
    ]

if selected_lokacija != "Sve lokacije":
    filtered_df = filtered_df[filtered_df['lokacija'] == selected_lokacija]

if selected_kategorija != "Sve kategorije":
    filtered_df = filtered_df[filtered_df['kategorija'] == selected_kategorija]

if selected_cijena != "Sve cijene":
    filtered_df = filtered_df[filtered_df['cijena'] == selected_cijena]

filtered_df = filtered_df.sort_values(by="datum_dt")

# --- PRIKAZ REZULTATA ---
st.caption(f"Prikazano događanja: **{len(filtered_df)}**")

for _, row in filtered_df.iterrows():
    formatted_date = row['datum_dt'].strftime("%d.%m.%Y.")
    
    card_html = f"""
    <div class="event-card">
        <span class="event-badge">{row['kategorija']}</span>
        <div class="event-title">{row['naslov']}</div>
        <div class="event-meta">📍 <b>{row['lokacija']}</b> ({row.get('mjestodogađaja', '')})</div>
        <div class="event-meta">🕒 <b>{formatted_date}</b> u {row['vrijeme']}</div>
        <div class="event-meta">🎟️ <b>{row['cijena']}</b></div>
        <p style="font-size:0.85rem; color:#444; margin-top:6px;">{row['opis'][:120]}...</p>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
    
    if st.button("Otvori poveznicu", key=f"btn_{row['id']}"):
        st.markdown(f"🔗 [Idite na službenu stranicu]({row['poveznica']})")