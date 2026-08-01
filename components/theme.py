"""GoalOS visual design tokens and global CSS."""



COLORS = {

  "bg": "#f8f9fc",

  "surface": "#ffffff",

  "surface_2": "#f4f4f5",

  "border": "#e4e4e7",

  "nav_bg": "#ffffff",

  "text": "#18181b",

  "muted": "#71717a",

  "accent": "#6366f1",

  "accent_2": "#4f46e5",

  "success": "#059669",

  "warning": "#d97706",

  "danger": "#dc2626",

  "info": "#0284c7",

}



PLOTLY_LAYOUT = {

  "template": "plotly_white",

  "paper_bgcolor": "rgba(0,0,0,0)",

  "plot_bgcolor": "rgba(0,0,0,0)",

  "font": {"family": "Inter, system-ui, sans-serif", "color": COLORS["muted"], "size": 12},

  "margin": {"l": 12, "r": 12, "t": 28, "b": 12},

  "xaxis": {"gridcolor": "#e4e4e7", "zerolinecolor": "#e4e4e7"},

  "yaxis": {"gridcolor": "#e4e4e7", "zerolinecolor": "#e4e4e7"},

}



THEME_CSS = f"""

<style>

  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');



  :root {{

    --bg: {COLORS["bg"]};

    --surface: {COLORS["surface"]};

    --surface-2: {COLORS["surface_2"]};

    --border: {COLORS["border"]};

    --text: {COLORS["text"]};

    --muted: {COLORS["muted"]};

    --accent: {COLORS["accent"]};

    --accent-2: {COLORS["accent_2"]};

    --success: {COLORS["success"]};

    --warning: {COLORS["warning"]};

    --danger: {COLORS["danger"]};

  }}



  .stApp {{

    background: radial-gradient(ellipse 120% 80% at 50% -20%, #eef2ff 0%, var(--bg) 55%);

    color: var(--text);

    font-family: 'Inter', system-ui, sans-serif;

  }}



  #MainMenu, footer, header[data-testid="stHeader"] {{

    visibility: hidden;

    height: 0;

  }}



  section[data-testid="stSidebar"],

  [data-testid="stSidebarCollapsedControl"],

  button[kind="header"] {{

    display: none !important;

  }}



  [data-testid="stAppViewContainer"] {{

    margin-left: 0 !important;

    width: 100% !important;

  }}



  .block-container {{

    padding-top: 0.5rem;

    padding-bottom: 3rem;

    max-width: 1100px;

  }}



  .goalos-topnav-shell {{

    background: {COLORS["nav_bg"]};

    border-bottom: 1px solid {COLORS["border"]};

    padding: 0.65rem 0 0.75rem 0;

    margin: -0.5rem -1rem 1.25rem -1rem;

    box-shadow: 0 1px 12px rgba(15, 23, 42, 0.06);

  }}



  .goalos-topnav-shell a {{

    color: #52525b !important;

    font-weight: 500 !important;

    font-size: 0.86rem !important;

    text-decoration: none !important;

    border-radius: 8px !important;

    padding: 0.4rem 0.25rem !important;

    transition: color 0.15s ease, background 0.15s ease;

  }}



  .goalos-topnav-shell a:hover {{

    color: var(--accent-2) !important;

    background: rgba(99, 102, 241, 0.08) !important;

  }}



  .goalos-topnav-shell [data-testid="stPageLink-NavLink"] {{

    background: transparent !important;

    border: none !important;

    justify-content: center !important;

  }}



  .goalos-topnav-brand {{

    text-align: center;

    font-size: 1.15rem;

    font-weight: 700;

    letter-spacing: -0.02em;

    margin-bottom: 0.35rem;

    color: var(--text);

  }}



  h1, h2, h3, h4, h5, h6,

  [data-testid="stMarkdown"] h1,

  [data-testid="stMarkdown"] h2,

  [data-testid="stMarkdown"] h3 {{

    color: var(--text) !important;

    font-weight: 700 !important;

    letter-spacing: -0.02em;

  }}



  p, label, .stCaption, [data-testid="stMarkdown"] p {{

    color: var(--muted);

  }}



  [data-testid="stMetric"] {{

    background: var(--surface);

    border: 1px solid var(--border);

    border-radius: 14px;

    padding: 0.85rem 1rem;

    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);

  }}



  [data-testid="stMetricLabel"] {{

    color: var(--muted) !important;

    font-size: 0.78rem !important;

    text-transform: uppercase;

    letter-spacing: 0.06em;

  }}



  [data-testid="stMetricValue"] {{

    color: var(--text) !important;

    font-weight: 700 !important;

  }}



  [data-testid="stMetricDelta"] {{

    font-weight: 600 !important;

  }}



  .stButton > button {{

    border-radius: 10px;

    border: 1px solid var(--border);

    background: var(--surface);

    color: var(--text);

    font-weight: 600;

    transition: all 0.15s ease;

  }}



  .stButton > button:hover {{

    border-color: var(--accent);

    color: var(--accent-2);

    background: #eef2ff;

  }}



  .stButton > button[kind="primary"],
  .stButton > button[data-testid="stBaseButton-primary"],
  button[kind="primary"],
  button[data-testid="stBaseButton-primary"],
  button[kind="primaryFormSubmit"],
  button[data-testid="stFormSubmitButton"] > button,
  [data-testid="stFormSubmitButton"] button {{
    background: linear-gradient(135deg, #4f46e5, #3730a3) !important;
    border: none !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
  }}

  .stButton > button[kind="primary"] *,
  .stButton > button[data-testid="stBaseButton-primary"] *,
  button[kind="primary"] *,
  button[data-testid="stBaseButton-primary"] *,
  button[kind="primaryFormSubmit"] *,
  button[data-testid="stFormSubmitButton"] > button *,
  [data-testid="stFormSubmitButton"] button * {{
    color: #ffffff !important;
    font-weight: 700 !important;
  }}

  .stButton > button[kind="primary"]:hover,
  .stButton > button[data-testid="stBaseButton-primary"]:hover,
  [data-testid="stFormSubmitButton"] button:hover {{
    color: #ffffff !important;
    filter: brightness(1.15) !important;
    box-shadow: 0 4px 14px rgba(79, 70, 229, 0.4) !important;
  }}



  .stTextInput input, .stTextArea textarea, .stNumberInput input,

  [data-baseweb="select"] > div {{

    background: var(--surface) !important;

    border: 1px solid var(--border) !important;

    border-radius: 10px !important;

    color: var(--text) !important;

  }}



  .stTabs [data-baseweb="tab-list"] {{

    gap: 6px;

    background: transparent;

  }}



  .stTabs [data-baseweb="tab"] {{

    background: var(--surface);

    border-radius: 10px;

    border: 1px solid var(--border);

    color: var(--muted);

    padding: 0.4rem 0.9rem;

  }}



  .stTabs [aria-selected="true"] {{

    background: #eef2ff !important;

    color: var(--accent-2) !important;

    border-color: var(--accent) !important;

  }}



  div[data-testid="stExpander"] {{

    background: var(--surface);

    border: 1px solid var(--border);

    border-radius: 14px;

  }}



  [data-testid="stChatMessage"] {{

    background: var(--surface);

    border: 1px solid var(--border);

    border-radius: 14px;

  }}



  .goalos-page-header {{

    margin-bottom: 1.75rem;

  }}



  .goalos-page-header h1 {{

    font-size: 2rem;

    margin: 0 0 0.35rem 0;

    background: linear-gradient(135deg, #18181b 0%, #4f46e5 100%);

    -webkit-background-clip: text;

    -webkit-text-fill-color: transparent;

    background-clip: text;

  }}



  .goalos-page-header p {{

    margin: 0;

    color: var(--muted);

    font-size: 0.95rem;

  }}



  .goalos-card {{

    background: linear-gradient(180deg, var(--surface) 0%, var(--surface-2) 100%);

    border: 1px solid var(--border);

    border-radius: 16px;

    padding: 1.1rem 1.25rem;

    margin-bottom: 0.85rem;

    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);

  }}



  .goalos-card-accent {{

    border-left: 3px solid var(--accent);

  }}



  .goalos-card-success {{

    border-left: 3px solid var(--success);

  }}



  .goalos-card-warning {{

    border-left: 3px solid var(--warning);

  }}



  .goalos-card-danger {{

    border-left: 3px solid var(--danger);

  }}



  .goalos-hero {{

    background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 45%, #f5f3ff 100%);

    border: 1px solid #c7d2fe;

    border-radius: 18px;

    padding: 1.5rem 1.75rem;

    margin-bottom: 1.25rem;

    box-shadow: 0 8px 24px rgba(79, 70, 229, 0.08);

  }}



  .goalos-hero-label {{

    font-size: 0.72rem;

    text-transform: uppercase;

    letter-spacing: 0.1em;

    color: #4338ca;

    margin-bottom: 0.5rem;

    font-weight: 600;

  }}



  .goalos-hero-text {{

    font-size: 1.35rem;

    font-weight: 600;

    color: #1e1b4b;

    line-height: 1.45;

    margin: 0;

  }}



  .goalos-stat {{

    background: var(--surface);

    border: 1px solid var(--border);

    border-radius: 14px;

    padding: 1rem 1.1rem;

    text-align: left;

    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);

  }}



  .goalos-stat-label {{

    font-size: 0.72rem;

    text-transform: uppercase;

    letter-spacing: 0.08em;

    color: var(--muted);

    margin-bottom: 0.35rem;

  }}



  .goalos-stat-value {{

    font-size: 1.75rem;

    font-weight: 700;

    color: var(--text);

    line-height: 1;

  }}



  .goalos-stat-delta {{

    font-size: 0.8rem;

    margin-top: 0.35rem;

    font-weight: 600;

  }}



  .goalos-stat-delta.up {{ color: var(--success); }}

  .goalos-stat-delta.down {{ color: var(--danger); }}



  .goalos-section {{

    margin: 1.75rem 0 0.85rem 0;

  }}



  .goalos-section h3 {{

    font-size: 0.82rem !important;

    text-transform: uppercase;

    letter-spacing: 0.1em;

    color: var(--muted) !important;

    margin: 0 0 0.15rem 0 !important;

    font-weight: 600 !important;

  }}



  .goalos-badge {{

    display: inline-block;

    padding: 0.2rem 0.55rem;

    border-radius: 999px;

    font-size: 0.72rem;

    font-weight: 600;

    text-transform: uppercase;

    letter-spacing: 0.04em;

    margin-right: 0.35rem;

  }}



  .goalos-badge-career {{ background: #eef2ff; color: #4338ca; border: 1px solid #c7d2fe; }}

  .goalos-badge-health {{ background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }}

  .goalos-badge-learning {{ background: #eff6ff; color: #0369a1; border: 1px solid #bae6fd; }}

  .goalos-badge-personal {{ background: #fdf4ff; color: #a21caf; border: 1px solid #f5d0fe; }}

  .goalos-badge-financial {{ background: #fffbeb; color: #b45309; border: 1px solid #fde68a; }}

  .goalos-badge-default {{ background: #f4f4f5; color: var(--muted); border: 1px solid var(--border); }}



  .goalos-progress {{

    height: 6px;

    background: #e4e4e7;

    border-radius: 999px;

    overflow: hidden;

    margin: 0.65rem 0;

  }}



  .goalos-progress-bar {{

    height: 100%;

    background: linear-gradient(90deg, var(--accent-2), var(--accent));

    border-radius: 999px;

  }}



  .goalos-empty {{

    text-align: center;

    padding: 2.5rem 1.5rem;

    background: var(--surface);

    border: 1px dashed var(--border);

    border-radius: 16px;

    color: var(--muted);

  }}



  .goalos-empty h4 {{

    color: var(--text) !important;

    margin: 0 0 0.5rem 0 !important;

  }}



  .goalos-nav-card {{

    background: var(--surface);

    border: 1px solid var(--border);

    border-radius: 14px;

    padding: 1.1rem;

    height: 100%;

    transition: border-color 0.15s ease, box-shadow 0.15s ease;

    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);

  }}



  .goalos-nav-card:hover {{

    border-color: var(--accent);

    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.08);

  }}



  .goalos-nav-card h4 {{

    margin: 0 0 0.35rem 0 !important;

    color: var(--text) !important;

    font-size: 1rem !important;

  }}



  .goalos-nav-card p {{

    margin: 0;

    font-size: 0.85rem;

    color: var(--muted);

  }}



  .goalos-sidebar-brand {{

    padding: 0.5rem 0 1.25rem 0;

    border-bottom: 1px solid var(--border);

    margin-bottom: 1rem;

  }}



  .goalos-sidebar-brand h2 {{

    margin: 0;

    font-size: 1.35rem;

    background: linear-gradient(135deg, #18181b, #4f46e5);

    -webkit-background-clip: text;

    -webkit-text-fill-color: transparent;

    background-clip: text;

  }}



  .goalos-sidebar-brand p {{

    margin: 0.2rem 0 0 0;

    font-size: 0.78rem;

    color: var(--muted);

  }}



  .goalos-coach-item {{

    margin: 0.5rem 0;

    padding: 0.65rem 0.85rem;

    background: #f4f4f5;

    border-radius: 10px;

    border-left: 2px solid var(--accent);

    font-size: 0.9rem;

    color: var(--text);

  }}



  .goalos-coach-label {{

    font-size: 0.72rem;

    text-transform: uppercase;

    letter-spacing: 0.08em;

    color: var(--accent-2);

    margin-bottom: 0.25rem;

    font-weight: 600;

  }}

</style>

"""


