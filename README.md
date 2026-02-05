# VagaHunter API 🏹

API REST para monitoramento e agregação de vagas de emprego remotas.

![Demo](example.gif)

## 🚀 Features
- **Busca de Vagas:** Agrega vagas do Programathor (Scraping Inteligente).
- **Análise com IA:** Integração com **Google Gemini 2.0** para dar nota de Match (0-100) para cada vaga.
- **Dashboard:** Interface interativa em Streamlit (Mobile Friendly).
- **Banco de Dados:** Histórico em SQLite.
- **API REST:** FastAPI com Clean Architecture.

## 🛠️ Como rodar (Sem Docker)
1. **Configurar variáveis de ambiente (.env):**
   ```bash
   GEMINI_API_KEY="sua-chave-gemini" # obrigatório para análise de IA
   DATABASE_URL="sqlite:///./data/sql_app.db" # opcional; use PostgreSQL em produção
   ```
2. **Instalar dependências:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Rodar o servidor:**
   ```bash
   uvicorn app.main:app --reload
   ```
4. **Abrir dashboard (opcional):**
   ```bash
   streamlit run app/frontend.py
   ```
5. **Acessar Docs:**
   Abra http://localhost:8000/docs

## 🏗️ Estrutura
- `app/models`: Modelos do Banco de Dados.
- `app/routers`: Endpoints da API.
- `app/services`: Lógica de Scraping e Busca.

## 🗄️ Banco de Dados & Deploy
- Default: SQLite em `./data/sql_app.db` (auto-criado).
- Produção: defina `DATABASE_URL` (ex.: `postgresql+psycopg2://user:pass@host:5432/db`).
- Rode migrações/backup conforme o provider escolhido.
