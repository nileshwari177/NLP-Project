import streamlit as st
import sys
import os
import time

# ── Add v1 folder to path so we can import your actual Python files ──
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'v1'))

from extractor import extract_entities
from ir_builder import build_ir
from compiler import compile_mysql

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="NLP → SQL",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────
#  CUSTOM CSS  (same dark theme as HTML file)
# ─────────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Syne:wght@400;700;800&display=swap" rel="stylesheet"/>

<style>
/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }

:root {
  --bg:       #0a0e1a;
  --surface:  #111827;
  --surface2: #1a2235;
  --border:   #1e2d45;
  --accent:   #00e5ff;
  --accent2:  #7c3aed;
  --green:    #00ff88;
  --red:      #ff4466;
  --text:     #e2e8f0;
  --muted:    #64748b;
}

/* Hide streamlit defaults */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2rem 4rem !important; max-width: 960px !important; }

/* App background + grid */
.stApp {
  background-color: var(--bg) !important;
  font-family: 'JetBrains Mono', monospace !important;
}
.stApp::before {
  content: '';
  position: fixed; inset: 0;
  background-image:
    linear-gradient(rgba(0,229,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,229,255,0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none; z-index: 0;
}

/* Glowing orbs */
.stApp::after {
  content: '';
  position: fixed;
  width: 350px; height: 350px;
  background: radial-gradient(circle, rgba(124,58,237,0.18) 0%, transparent 70%);
  top: -80px; left: -80px;
  border-radius: 50%;
  pointer-events: none; z-index: 0;
  animation: drift 12s ease-in-out infinite alternate;
}
@keyframes drift { to { transform: translate(60px, 80px); } }

/* Text inputs */
.stTextArea textarea {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 14px !important;
  caret-color: var(--accent) !important;
}
.stTextArea textarea:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 1px var(--accent) !important;
}

/* Button */
.stButton > button {
  background: var(--accent) !important;
  color: #000 !important;
  font-family: 'Syne', sans-serif !important;
  font-weight: 700 !important;
  font-size: 14px !important;
  letter-spacing: 1px !important;
  border: none !important;
  border-radius: 8px !important;
  padding: 10px 28px !important;
  width: 100% !important;
  transition: all 0.2s !important;
  cursor: pointer !important;
}
.stButton > button:hover {
  background: #33eeff !important;
  box-shadow: 0 6px 20px rgba(0,229,255,0.3) !important;
  transform: translateY(-1px) !important;
}

/* Chips / sample queries */
.chip-row { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0 20px; }
.chip {
  background: var(--surface2);
  border: 1px solid var(--border);
  color: var(--muted);
  font-size: 11px;
  padding: 5px 14px;
  border-radius: 20px;
  cursor: pointer;
  font-family: 'JetBrains Mono', monospace;
  transition: all 0.2s;
}
.chip:hover { border-color: var(--accent); color: var(--accent); }

/* Pipeline bar */
.pipeline {
  display: flex; align-items: center; justify-content: center;
  gap: 8px; flex-wrap: wrap; margin: 20px 0 30px;
}
.pipe-step {
  font-size: 11px; padding: 5px 16px; border-radius: 20px;
  border: 1px solid var(--border);
  color: var(--muted); background: var(--surface);
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 1px; transition: all 0.3s;
}
.pipe-step.active {
  border-color: var(--accent); color: var(--accent);
  background: rgba(0,229,255,0.07);
  box-shadow: 0 0 12px rgba(0,229,255,0.2);
}
.pipe-arrow { color: var(--muted); font-size: 14px; }

/* Stage cards */
.stage-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px; overflow: hidden;
  margin-bottom: 16px; height: 100%;
}
.stage-header {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
  background: var(--surface2);
  font-size: 11px; letter-spacing: 2px; text-transform: uppercase;
  color: var(--muted);
}
.dot { width:7px; height:7px; border-radius:50%; display:inline-block; }
.dot-yellow { background: #facc15; }
.dot-purple { background: var(--accent2); }
.stage-body { padding: 14px 16px; font-size: 12px; line-height: 1.9; }

.entity-key { color: var(--muted); display: inline-block; min-width: 110px; }
.entity-val { color: var(--accent); }
.entity-none { color: var(--muted); font-style: italic; }
.entity-green { color: var(--green); }

/* SQL card */
.sql-card {
  background: var(--surface);
  border: 1px solid var(--accent);
  border-radius: 10px; overflow: hidden;
  box-shadow: 0 0 20px rgba(0,229,255,0.12);
  margin-bottom: 16px;
}
.sql-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 20px;
  border-bottom: 1px solid var(--border);
  background: rgba(0,229,255,0.05);
}
.sql-title {
  font-family: 'Syne', sans-serif; font-weight: 700;
  font-size: 13px; color: var(--accent);
  letter-spacing: 2px; text-transform: uppercase;
}
.sql-body { padding: 20px 24px; }
.sql-query {
  font-size: 15px; line-height: 1.9; word-break: break-all;
  font-family: 'JetBrains Mono', monospace;
}
.kw  { color: #00e5ff; font-weight: 600; }
.fn  { color: #f472b6; }
.tb  { color: #00ff88; }
.nm  { color: #fb923c; }
.sc  { color: #00e5ff; }

/* Error card */
.error-card {
  background: rgba(255,68,102,0.08);
  border: 1px solid #ff4466;
  border-radius: 10px; padding: 16px 20px;
  color: #ff4466; font-size: 13px;
}

/* History */
.history-item {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px; padding: 12px 16px;
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 8px; cursor: pointer; transition: all 0.2s;
  gap: 12px;
}
.history-item:hover { border-color: var(--accent); }
.history-q  { font-size: 12px; color: var(--muted); flex:1; }
.history-sql { font-size: 11px; color: var(--accent); }

/* Header */
.logo-tag {
  display: inline-block; font-size: 11px; letter-spacing: 4px;
  text-transform: uppercase; color: var(--accent);
  border: 1px solid var(--accent); padding: 4px 12px;
  border-radius: 2px; margin-bottom: 14px; opacity: 0.8;
}
h1.nlp-title {
  font-family: 'Syne', sans-serif !important; font-size: 3rem !important;
  font-weight: 800 !important; line-height: 1.1 !important;
  background: linear-gradient(135deg, #fff 30%, #00e5ff 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; margin-bottom: 8px !important;
}
.subtitle { color: var(--muted); font-size: 13px; letter-spacing: 1px; margin-bottom: 0; }

/* Input label */
.input-label {
  font-size: 11px; letter-spacing: 2px; text-transform: uppercase;
  color: var(--muted); margin-bottom: 8px;
  display: flex; align-items: center; gap: 8px;
}
.input-label::before {
  content: ''; width:6px; height:6px; border-radius:50%;
  background: var(--accent); display:inline-block;
}

/* Divider */
.divider { border: none; border-top: 1px solid var(--border); margin: 28px 0; }

/* Selectbox hack */
.stSelectbox > div > div {
  background: var(--surface2) !important;
  border-color: var(--border) !important;
  color: var(--text) !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────
if 'history'      not in st.session_state: st.session_state.history = []
if 'query_input'  not in st.session_state: st.session_state.query_input = ''
if 'result'       not in st.session_state: st.session_state.result = None
if 'pipeline_step'not in st.session_state: st.session_state.pipeline_step = 0


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
TABLES = ['students', 'cars', 'employees', 'products']

def highlight_sql(sql: str) -> str:
    """Syntax-highlight SQL string → HTML"""
    keywords = ['SELECT','FROM','WHERE','ORDER BY','LIMIT','AND','OR','BETWEEN','ASC','DESC','NOT']
    fns      = ['AVG','SUM','COUNT','MAX','MIN']
    h = sql
    for f in fns:
        h = h.replace(f, f'<span class="fn">{f}</span>')
    for k in keywords:
        h = h.replace(k, f'<span class="kw">{k}</span>')
    for t in TABLES:
        h = h.replace(t, f'<span class="tb">{t}</span>')
    # numbers
    import re
    h = re.sub(r'\b(\d+\.?\d*)\b', r'<span class="nm">\1</span>', h)
    # semicolon
    if h.endswith(';'):
        h = h[:-1] + '<span class="sc">;</span>'
    return h


def render_pipeline(step: int):
    steps = ['Entity Extraction', 'IR Builder', 'SQL Compiler']
    html = '<div class="pipeline">'
    for i, s in enumerate(steps):
        cls = 'pipe-step active' if i < step else 'pipe-step'
        html += f'<span class="{cls}">{s}</span>'
        if i < len(steps)-1:
            html += '<span class="pipe-arrow">→</span>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_entities(e: dict) -> str:
    def row(k, v, color='entity-val'):
        if v is None or v == '' or v == []:
            return f'<div><span class="entity-key">{k}</span><span class="entity-none">None</span></div>'
        return f'<div><span class="entity-key">{k}</span><span class="{color}">{v}</span></div>'

    html = ''
    html += row('table',       e.get('table'))
    html += row('column',      e.get('column'))
    html += row('aggregation', e.get('aggregation'))
    html += row('limit',       e.get('limit'))
    html += row('direction',   e.get('direction'))

    where = e.get('where', [])
    if where:
        html += '<div><span class="entity-key">where</span><span class="entity-val">[</span></div>'
        for w in where:
            val = f"{w['value'][0]} AND {w['value'][1]}" if isinstance(w['value'], (list,tuple)) else w['value']
            html += f'<div style="padding-left:16px"><span class="entity-green">  {w["column"]} {w["operator"]} {val}</span></div>'
        html += '<div><span class="entity-val">]</span></div>'
    else:
        html += row('where', None)
    return html


def render_ir(ir: dict) -> str:
    def row(k, v):
        if v is None or v == '' or v == []:
            return f'<div><span class="entity-key">{k}</span><span class="entity-none">None</span></div>'
        return f'<div><span class="entity-key">{k}</span><span class="entity-val">{v}</span></div>'

    html = ''
    html += row('select',      ', '.join(ir.get('select', ['*'])))
    html += row('aggregation', ir.get('aggregation'))
    html += row('table',       ir.get('table'))
    ob = ir.get('order_by')
    html += row('order_by',    f"{ob['column']} {ob['direction']}" if ob else None)
    html += row('limit',       ir.get('limit'))

    where = ir.get('where', [])
    if where:
        html += '<div><span class="entity-key">where</span><span class="entity-val">[</span></div>'
        for w in where:
            val = f"{w['value'][0]} AND {w['value'][1]}" if isinstance(w['value'], (list,tuple)) else w['value']
            html += f'<div style="padding-left:16px"><span class="entity-green">  {w["column"]} {w["operator"]} {val}</span></div>'
        html += '<div><span class="entity-val">]</span></div>'
    return html


# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; margin-bottom:36px; animation: fadeDown 0.6s ease both;">

  <h1 class="nlp-title">English → SQL</h1>
  <p class="subtitle">Type a question in plain English. Get a MySQL query instantly.</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  PIPELINE INDICATOR
# ─────────────────────────────────────────────
pipeline_placeholder = st.empty()
with pipeline_placeholder:
    render_pipeline(st.session_state.pipeline_step)


# ─────────────────────────────────────────────
#  SAMPLE QUERY CHIPS
# ─────────────────────────────────────────────
SAMPLES = [
    "Show me top 5 students with highest CGPA",
    "What is the average marks of students?",
    "Find cars with price greater than 50000",
    "Count the number of employees",
    "Products with rating between 4 and 5",
]

# ─────────────────────────────────────────────
#  INPUT BOX  (textarea + RUN button inside)
# ─────────────────────────────────────────────
st.markdown('<div class="input-label">Natural Language Query</div>', unsafe_allow_html=True)

# Extra CSS: shrink the button column and overlap it visually inside textarea
st.markdown("""
<style>
/* Make the textarea taller and leave room on right for button */
div[data-testid="stTextArea"] textarea {
  padding-right: 105px !important;
  min-height: 100px !important;
  border-radius: 12px !important;
  background: #111827 !important;
  border: 1px solid #1e2d45 !important;
  resize: none !important;
  font-size: 14px !important;
}
div[data-testid="stTextArea"]:focus-within textarea {
  border-color: #00e5ff !important;
  box-shadow: 0 0 0 1px rgba(0,229,255,0.4) !important;
}
/* Move the button column up and overlap textarea */
.run-overlap {
  margin-top: -82px !important;
  padding-right: 6px !important;
  position: relative;
  z-index: 10;
}
.run-overlap button {
  background: #00e5ff !important;
  color: green !important;
  font-family: 'Syne', sans-serif !important;
  font-weight: 700 !important;
  font-size: 13px !important;
  letter-spacing: 1px !important;
  border: none !important;
  border-radius: 8px !important;
  padding: 12px 18px !important;
  width: 100% !important;
  cursor: pointer !important;
}
.run-overlap button:hover {
  background: #33eeff !important;
  box-shadow: 0 4px 16px rgba(0,229,255,0.35) !important;
}
</style>
""", unsafe_allow_html=True)

col_input, col_btn = st.columns([5, 1])
with col_input:
    query = st.text_area(
        label="",
        value=st.session_state.query_input,
        placeholder='e.g. Show me top 10 students with highest CGPA',
        height=100,
        key="query_box",
        label_visibility="collapsed"
    )
with col_btn:
    st.markdown('<div class="run-overlap">', unsafe_allow_html=True)
    run = st.button("▶ Generate SQL", key="run_btn")
    st.markdown('</div>', unsafe_allow_html=True)

# ── Chips below textarea ──
st.markdown("""
<style>
/* Style streamlit chip buttons */
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button {
  background: #1a2235 !important;
  border: 1px solid #1e2d45 !important;
  color: #64748b !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 11px !important;
  padding: 5px 14px !important;
  border-radius: 20px !important;
  width: auto !important;
  transition: all 0.2s !important;
}
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button:hover {
  border-color: #00e5ff !important;
  color: #00e5ff !important;
  background: rgba(0,229,255,0.06) !important;
  box-shadow: none !important;
  transform: none !important;
}
</style>
""", unsafe_allow_html=True)

chip_cols = st.columns([0.5] + [2]*len(SAMPLES))
with chip_cols[0]:
    st.markdown('<div style="color:#64748b;font-size:12px;padding-top:6px">Try:</div>', unsafe_allow_html=True)
for i, sample in enumerate(SAMPLES):
    with chip_cols[i+1]:
        if st.button(sample, key=f"chip_{i}"):
            st.session_state.query_input = sample
            st.rerun()


# ─────────────────────────────────────────────
#  PIPELINE EXECUTION
# ─────────────────────────────────────────────
if run and query.strip():

    # Step 1 — Entity Extraction
    with pipeline_placeholder:
        render_pipeline(1)
    time.sleep(0.3)

    try:
        entities = extract_entities(query)
    except Exception as ex:
        entities = {}
        st.markdown(f'<div class="error-card">⚠ Extractor error: {ex}</div>', unsafe_allow_html=True)
        st.stop()

    # Step 2 — IR Builder
    with pipeline_placeholder:
        render_pipeline(2)
    time.sleep(0.3)

    try:
        ir = build_ir(entities)
    except Exception as ex:
        ir = None
        st.markdown(f'<div class="error-card">⚠ IR Builder error: {ex}</div>', unsafe_allow_html=True)
        st.stop()

    # Step 3 — SQL Compiler
    with pipeline_placeholder:
        render_pipeline(3)
    time.sleep(0.3)

    try:
        sql = compile_mysql(ir)
    except Exception as ex:
        sql = None
        st.markdown(f'<div class="error-card">⚠ Compiler error: {ex}</div>', unsafe_allow_html=True)
        st.stop()

    st.session_state.result = { 'query': query, 'entities': entities, 'ir': ir, 'sql': sql }
    st.session_state.pipeline_step = 3

    # Save to history (max 5)
    st.session_state.history.insert(0, { 'query': query, 'sql': sql })
    if len(st.session_state.history) > 5:
        st.session_state.history.pop()


# ─────────────────────────────────────────────
#  RESULTS
# ─────────────────────────────────────────────
if st.session_state.result:
    r = st.session_state.result
    entities = r['entities']
    ir       = r['ir']
    sql      = r['sql']

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    if not sql or not ir:
        st.markdown("""
        <div class="error-card">
          ⚠ Could not identify a table. Try mentioning:
          <strong>students, cars, employees,</strong> or <strong>products</strong>.
        </div>""", unsafe_allow_html=True)
    else:
        # ── Stage cards side by side ──
        # c1, c2 = st.columns(2)

        # with c1:
        #     st.markdown(f"""
        #     <div class="stage-card">
        #       <div class="stage-header">
        #         <span class="dot dot-yellow"></span> Extracted Entities
        #       </div>
        #       <div class="stage-body">{render_entities(entities)}</div>
        #     </div>""", unsafe_allow_html=True)

        # with c2:
        #     st.markdown(f"""
        #     <div class="stage-card">
        #       <div class="stage-header">
        #         <span class="dot dot-purple"></span> Intermediate Representation
        #       </div>
        #       <div class="stage-body">{render_ir(ir)}</div>
        #     </div>""", unsafe_allow_html=True)

        # ── SQL Output card with copy button in header ──
        st.markdown(f"""
        <div class="sql-card">
          <div class="sql-header">
            <span class="sql-title">⬡ Generated SQL</span>
            <button onclick="
              navigator.clipboard.writeText(`{sql}`);
              this.innerText='✓ COPIED';
              this.style.borderColor='#00ff88';
              this.style.color='#00ff88';
              setTimeout(()=>{{this.innerText='⎘ COPY';this.style.borderColor='';this.style.color='';}},2000)
            " style="
              background:transparent;
              border:1px solid #1e2d45;
              color:#64748b;
              font-family:'JetBrains Mono',monospace;
              font-size:11px;
              padding:5px 14px;
              border-radius:6px;
              cursor:pointer;
              letter-spacing:1px;
              transition:all 0.2s;
            ">⎘ COPY</button>
          </div>
          <div class="sql-body">
            <div class="sql-query">{highlight_sql(sql)}</div>
          </div>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  HISTORY
# ─────────────────────────────────────────────
if st.session_state.history:
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:12px">⟳ Recent Queries</div>', unsafe_allow_html=True)

    for i, h in enumerate(st.session_state.history):
        col_q, col_s, col_btn2 = st.columns([3, 3, 1])
        with col_q:
            st.markdown(f'<div style="color:#64748b;font-size:12px;padding:8px 0">{h["query"]}</div>', unsafe_allow_html=True)
        with col_s:
            st.markdown(f'<div style="color:#00e5ff;font-size:11px;padding:8px 0;font-family:monospace">{h["sql"]}</div>', unsafe_allow_html=True)
        with col_btn2:
            if st.button("↩ Use", key=f"hist_{i}"):
                st.session_state.query_input = h['query']
                st.rerun()