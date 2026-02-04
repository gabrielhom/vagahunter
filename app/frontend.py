import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Config
API_URL = "http://localhost:8000"
st.set_page_config(page_title="VagaHunter", page_icon="🏹", layout="wide")

st.title("🏹 VagaHunter Dashboard")
st.markdown("Monitoramento de vagas remotas em tempo real.")

# Sidebar - Search Controls
with st.sidebar:
    st.header("Busca")
    query = st.text_input("Tecnologia (ex: Python)", value="Python")
    if st.button("Buscar Novas Vagas"):
        with st.spinner(f"Buscando vagas de {query}..."):
            try:
                response = requests.post(f"{API_URL}/jobs/search?query={query}")
                if response.status_code == 200:
                    new_jobs = response.json()
                    st.success(f"{len(new_jobs)} vagas encontradas!")
                else:
                    st.error("Erro na busca.")
            except Exception as e:
                st.error(f"Erro de conexão: {e}")

# Main Content - Jobs List
st.subheader("Vagas Cadastradas")

try:
    # Fetch jobs from local API
    response = requests.get(f"{API_URL}/jobs?limit=100")
    if response.status_code == 200:
        jobs = response.json()
        
        if jobs:
            # Convert to DataFrame for easier display
            df = pd.DataFrame(jobs)
            
            # Format display
            display_df = df[['title', 'company', 'source', 'is_remote', 'match_score', 'match_reason', 'url']].copy()
            display_df['is_remote'] = display_df['is_remote'].apply(lambda x: "✅" if x else "❌")
            
            # Interactive Table
            st.dataframe(
                display_df,
                column_config={
                    "url": st.column_config.LinkColumn("Link"),
                    "match_score": st.column_config.ProgressColumn(
                        "Match",
                        help="Score calculado por IA",
                        format="%d",
                        min_value=0,
                        max_value=100,
                    ),
                    "match_reason": st.column_config.TextColumn("Motivo IA"),
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Nenhuma vaga no banco de dados. Use a busca ao lado!")
    else:
        st.error("Erro ao carregar vagas.")
except Exception as e:
    st.error(f"API Offline? {e}")
