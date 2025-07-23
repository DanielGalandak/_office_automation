Flask Project Management & Document Platform
Přehled
Tento projekt je webová aplikace postavená na Flasku, určená pro správu projektů, úkolů, dokumentů a komunikaci s LLM API.
V aktuální fázi jsou plně funkční:
•	API pro LLM chat (komunikace s AI přes chat_controller a llm_service).
•	Nahrávání a správa dokumentů (modul document_controller).
Ostatní funkce (projekty, úkoly, uživatelé) jsou implementovány částečně nebo pouze jako prototyp (SQLite kontexty ProjectContext, TaskContext).
________________________________________
Hlavní funkce
•	LLM API chat – integrace s LLM modelem (OpenAI/Anthropic) pro generování odpovědí.
•	Nahrávání a správa souborů – ukládání souborů do složky uploads/ a práce s metadaty.
•	Základní správa projektů a úloh – prototyp CRUD operací nad SQLite databází.
•	Modulární architektura – aplikace je rozdělena do samostatných blueprintů:
/chat, /documents, /projects, /tasks, /users.
•	Jednoduché HTML šablony v templates/ a statické soubory v static/.
________________________________________
Struktura projektu
csharp
ZkopírovatUpravit
app.py               		# Hlavní Flask aplikace (registrace blueprintů)
config.py            		# Konfigurace aplikace
contexts/            	# SQLite kontexty (ProjectContext, TaskContext)
controllers/         	# Logika pro API a webové stránky
models/              	# Datové modely (Document, Project, Task, User)
services/            		# LLM API, PDF generace, file služby
static/              		# CSS/JS
templates/           	# HTML šablony
uploads/             	# Nahrané soubory
temp/                		# Dočasné soubory
________________________________________
Instalace a spuštění
1.	Naklonujte repozitář:
bash
ZkopírovatUpravit
git clone <repo-url>
cd <repo-directory>
2.	Vytvořte a aktivujte virtuální prostředí:
bash
ZkopírovatUpravit
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
3.	Nainstalujte závislosti:
bash
ZkopírovatUpravit
pip install -r requirements.txt
4.	Spusťte aplikaci:
bash
ZkopírovatUpravit
python app.py
Aplikace poběží na http://127.0.0.1:5000/.
________________________________________
Technologie
•	Python 3.10+
•	Flask (Blueprint architektura)
•	SQLite (prototyp databázové vrstvy v contexts/)
•	LLM API (OpenAI/Anthropic) přes llm_service.py
•	PDF generace (pdf_service.py)
•	HTML, CSS, JS pro frontend

