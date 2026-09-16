"""
GoalOS Architecture Diagram Generator (draw.io / diagrams.net XML)
Generates a multi-page, production-ready .drawio file representing the GoalOS build:
  Page 1: System Topology & Layered Architecture
  Page 2: Cognitive Multi-Agent & Scoped Tool Loop
  Page 3: Cognitive Memory & 5-Factor Hybrid RAG
"""

import html
import os
import xml.etree.ElementTree as ET


def sanitize(text: str) -> str:
    return html.escape(text).replace("\n", "<br>")

class DrawIOBuilder:
    def __init__(self):
        self.root = ET.Element("mxfile", {
            "host": "app.diagrams.net",
            "modified": "2026-09-05T19:45:00.000Z",
            "agent": "GoalOS System Architect",
            "version": "21.6.8",
            "type": "device"
        })

    def add_page(self, page_id: str, name: str, width: int = 1800, height: int = 1400):
        diagram = ET.SubElement(self.root, "diagram", {"id": page_id, "name": name})
        mxGraphModel = ET.SubElement(diagram, "mxGraphModel", {
            "dx": "1600",
            "dy": "1000",
            "grid": "1",
            "gridSize": "10",
            "guides": "1",
            "tooltips": "1",
            "connect": "1",
            "arrows": "1",
            "fold": "1",
            "page": "1",
            "pageScale": "1",
            "pageWidth": str(width),
            "pageHeight": str(height),
            "math": "0",
            "shadow": "0"
        })
        model_root = ET.SubElement(mxGraphModel, "root")
        ET.SubElement(model_root, "mxCell", {"id": "0"})
        ET.SubElement(model_root, "mxCell", {"id": "1", "parent": "0"})
        return model_root

    @staticmethod
    def add_vertex(parent, cell_id, value, x, y, w, h, style):
        cell = ET.SubElement(parent, "mxCell", {
            "id": cell_id,
            "value": value,
            "style": style,
            "vertex": "1",
            "parent": "1"
        })
        ET.SubElement(cell, "mxGeometry", {
            "x": str(x),
            "y": str(y),
            "width": str(w),
            "height": str(h),
            "as": "geometry"
        })
        return cell

    @staticmethod
    def add_edge(parent, edge_id, value, source, target, style):
        cell = ET.SubElement(parent, "mxCell", {
            "id": edge_id,
            "value": value,
            "style": style,
            "edge": "1",
            "parent": "1",
            "source": source,
            "target": target
        })
        ET.SubElement(cell, "mxGeometry", {
            "relative": "1",
            "as": "geometry"
        })
        return cell

def build_drawio_xml() -> str:
    builder = DrawIOBuilder()

    # Shared Style Palettes (Forest Mist Paper Glass Theme)
    style_header = "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontFamily=Plus Jakarta Sans,sans-serif;"
    
    style_c_green = "rounded=1;whiteSpace=wrap;html=1;fillColor=#F0FDF4;strokeColor=#16A34A;fontColor=#14532D;fontStyle=1;strokeWidth=1.5;shadow=0;"
    style_c_teal = "rounded=1;whiteSpace=wrap;html=1;fillColor=#F0FDFA;strokeColor=#0D9488;fontColor=#115E59;fontStyle=1;strokeWidth=1.5;shadow=0;"
    style_c_blue = "rounded=1;whiteSpace=wrap;html=1;fillColor=#EFF6FF;strokeColor=#2563EB;fontColor=#1E3A8A;fontStyle=1;strokeWidth=1.5;shadow=0;"
    style_c_purple = "rounded=1;whiteSpace=wrap;html=1;fillColor=#FAF5FF;strokeColor=#9333EA;fontColor=#581C87;fontStyle=1;strokeWidth=1.5;shadow=0;"
    style_c_amber = "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFBEB;strokeColor=#D97706;fontColor=#78350F;fontStyle=1;strokeWidth=1.5;shadow=0;"
    style_c_slate = "rounded=1;whiteSpace=wrap;html=1;fillColor=#F8FAFC;strokeColor=#64748B;fontColor=#0F172A;fontStyle=1;strokeWidth=1.5;shadow=0;"
    style_c_dark = "rounded=1;whiteSpace=wrap;html=1;fillColor=#0F172A;strokeColor=#334155;fontColor=#F8FAFC;fontStyle=1;strokeWidth=1.5;shadow=1;"
    
    style_node = "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#CBD5E1;fontColor=#1E293B;strokeWidth=1.2;shadow=1;fontFamily=Plus Jakarta Sans,sans-serif;fontSize=11;"
    style_node_accent = "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#10B981;fontColor=#064E3B;strokeWidth=1.5;shadow=1;fontFamily=Plus Jakarta Sans,sans-serif;fontSize=11;fontStyle=1;"
    style_node_ai = "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#8B5CF6;fontColor=#4C1D95;strokeWidth=1.5;shadow=1;fontFamily=Plus Jakarta Sans,sans-serif;fontSize=11;fontStyle=1;"
    style_db = "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;fillColor=#F1F5F9;strokeColor=#475569;fontColor=#0F172A;strokeWidth=1.5;shadow=1;fontFamily=Plus Jakarta Sans,sans-serif;fontSize=11;fontStyle=1;"
    
    style_edge = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#64748B;strokeWidth=1.5;fontColor=#334155;fontSize=10;fontFamily=Plus Jakarta Sans,sans-serif;"
    style_edge_accent = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#059669;strokeWidth=2;fontColor=#065F46;fontSize=10;fontStyle=1;fontFamily=Plus Jakarta Sans,sans-serif;"
    style_edge_ai = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#7C3AED;strokeWidth=2;dashed=1;fontColor=#5B21B6;fontSize=10;fontStyle=1;fontFamily=Plus Jakarta Sans,sans-serif;"

    # -------------------------------------------------------------
    # PAGE 1: System Topology & Layered Architecture
    # -------------------------------------------------------------
    p1 = builder.add_page("page1", "1. System Topology & Layers", 1850, 1380)

    # Title Banner
    builder.add_vertex(p1, "p1_title", 
        "<b style='font-size:20px; color:#064E3B;'>🎯 GoalOS — High-Level System Topology & Layered Architecture</b><br>"
        "<span style='font-size:12px; color:#475569;'>Local-First Cognitive Operating System • Multi-Horizon Execution • Multi-Agent Supervisor • Hybrid 5-Factor RAG Dual-Persistence</span>",
        40, 20, 1770, 50, style_header)

    # Layer 1: Presentation Plane
    builder.add_vertex(p1, "p1_c1", 
        "1. PRESENTATION PLANE (Client Desktop Web — React 18 + Vite + TypeScript @ Port 5173)\n"
        "Design Tokens: Forest Mist Paper Glass • Tailwind CSS 3 • Lucide Icons • Plus Jakarta Sans & Newsreader",
        40, 90, 1770, 180, style_c_green)

    builder.add_vertex(p1, "p1_v_shell", "<b>Command Shell & Navbar</b><br>Global Horizon Bar<br>Quick Capture Drawer<br>Theme & Status Engine", 60, 140, 180, 110, style_node_accent)
    builder.add_vertex(p1, "p1_v_cal", "<b>Life Calendar View</b><br>70-Year Lifespan Grid<br>Memento Mori Pacing<br>Week Block Modals", 260, 140, 180, 110, style_node)
    builder.add_vertex(p1, "p1_v_jrn", "<b>Daily Journal & Tasks</b><br>Morning / Evening Rituals<br>Habit Consistency Tracker<br>OCR & Audio Ingest UI", 460, 140, 190, 110, style_node)
    builder.add_vertex(p1, "p1_v_gl", "<b>Multi-Horizon Goals</b><br>5-Yr Vision / 1-Yr Targets<br>1-Mo Execution Sprints<br>Milestone Progress Bars", 670, 140, 190, 110, style_node)
    builder.add_vertex(p1, "p1_v_coach", "<b>AI Coach Studio</b><br>Multi-Turn Chat Studio<br>Live Blackboard Viewer<br>Telemetry & Cost Meter", 880, 140, 200, 110, style_node_ai)
    builder.add_vertex(p1, "p1_v_mem", "<b>Cognitive Memories</b><br>Memory Feed & Search<br>Hybrid RAG Inspection<br>Importance & Access Stats", 1100, 140, 190, 110, style_node)
    builder.add_vertex(p1, "p1_v_anl", "<b>Analytics & Patterns</b><br>Longitudinal Health Scores<br>Stalling / Burnout Alerts<br>Velocity Heatmaps", 1310, 140, 190, 110, style_node)
    builder.add_vertex(p1, "p1_v_set", "<b>Settings & Privacy</b><br>Remote AI Opt-in Toggle<br>OpenRouter API Key Form<br>JSON Export & Safe Reset", 1520, 140, 180, 110, style_node)
    builder.add_vertex(p1, "p1_api_client", "<b>Axios API Client</b><br><code>frontend/src/api/client.ts</code><br>Type-Safe Fetchers & Error Interceptors", 1720, 140, 70, 110, style_c_slate)

    # Layer 2: Gateway & Security Plane
    builder.add_vertex(p1, "p1_c2", 
        "2. API GATEWAY & SECURITY PLANE (FastAPI REST Engine @ Port 8000)\n"
        "api/main.py • Invariant: All endpoints enforce Pydantic v2 schemas and deterministic status returns",
        40, 300, 1770, 160, style_c_blue)

    builder.add_vertex(p1, "p1_gw_sec", "<b>Security Middleware</b><br>• CORS Handler<br>• 512KB Body Size Limiter<br>• Constant-Time HMAC Auth", 60, 350, 220, 90, style_c_slate)
    builder.add_vertex(p1, "p1_r_cal", "<b>/calendar</b><br>GET /weeks<br>GET /stats<br>POST /notes", 300, 350, 150, 90, style_node)
    builder.add_vertex(p1, "p1_r_jrn", "<b>/journal</b><br>GET /today<br>POST /log<br>POST /import (OCR)", 470, 350, 160, 90, style_node)
    builder.add_vertex(p1, "p1_r_gl", "<b>/goals</b><br>GET /horizons<br>POST /goal<br>PATCH /milestone", 650, 350, 160, 90, style_node)
    builder.add_vertex(p1, "p1_r_coach", "<b>/coach & /sessions</b><br>POST /chat (Streaming)<br>GET /sessions & /messages<br>GET /telemetry & /metrics", 830, 350, 220, 90, style_node_ai)
    builder.add_vertex(p1, "p1_r_mem", "<b>/memories</b><br>GET /search (Hybrid RAG)<br>POST /store (Dual-Write)<br>DELETE /purge", 1070, 350, 190, 90, style_node)
    builder.add_vertex(p1, "p1_r_anl", "<b>/analytics</b><br>GET /patterns<br>GET /consistency<br>GET /alignment", 1280, 350, 160, 90, style_node)
    builder.add_vertex(p1, "p1_r_set", "<b>/settings & /export</b><br>GET/PUT /preferences<br>GET /export/json<br>POST /reset/safe", 1460, 350, 180, 90, style_node)

    # Layer 3: Cognitive Orchestration Plane
    builder.add_vertex(p1, "p1_c3", 
        "3. COGNITIVE ORCHESTRATION PLANE (Multi-Agent Supervisor & Scoped Toolkits)\n"
        "ai/pipelines/coordinator.py • Dynamic Tool Scoping (40-50% token reduction & anti-hallucination)",
        40, 490, 1770, 190, style_c_purple)

    builder.add_vertex(p1, "p1_coord", "<b>CoordinatorAgent</b><br><code>ai/pipelines/coordinator.py</code><br>Intent Classifier & Router<br>Specialized Agent Supervisor", 60, 540, 240, 120, style_node_ai)
    builder.add_vertex(p1, "p1_t_intent", "<b>Intent Triage Dispatch</b><br>• execution → Daily Habits<br>• goals → Milestones & Pacing<br>• memory → Hybrid RAG Search<br>• calendar → 70-Yr Memento Mori", 320, 540, 240, 120, style_node)
    builder.add_vertex(p1, "p1_t_journal", "<b>JournalToolkit</b><br><code>ai/tools/journal_toolkit.py</code><br>get_today_tasks()<br>update_habit_log()<br>record_evening_retro()", 580, 540, 200, 120, style_node)
    builder.add_vertex(p1, "p1_t_goals", "<b>GoalsToolkit</b><br><code>ai/tools/goals_toolkit.py</code><br>query_horizon_goals()<br>advance_milestone()<br>assess_alignment()", 800, 540, 200, 120, style_node)
    builder.add_vertex(p1, "p1_t_mem", "<b>MemoryToolkit</b><br><code>ai/tools/memory_toolkit.py</code><br>search_semantic_memories()<br>store_user_reflection()<br>fetch_recent_context()", 1020, 540, 200, 120, style_node)
    builder.add_vertex(p1, "p1_t_cal", "<b>CalendarToolkit</b><br><code>ai/tools/calendar_toolkit.py</code><br>get_lifespan_fraction()<br>get_current_week_info()<br>record_weekly_insight()", 1240, 540, 200, 120, style_node)
    builder.add_vertex(p1, "p1_blackboard", "<b>Blackboard & Telemetry</b><br><code>ObservabilityService</code><br>Inter-Agent Context Bus<br>Token & Cost Live Meter", 1460, 540, 220, 120, style_node_ai)

    # Layer 4: Core Domain Services Plane
    builder.add_vertex(p1, "p1_c4", 
        "4. CORE DOMAIN SERVICES PLANE (Business Logic & Deterministic Calculation Engines)\n"
        "services/* • 100% Deterministic Core — All scoring runs offline without remote LLMs",
        40, 710, 1770, 180, style_c_teal)

    builder.add_vertex(p1, "p1_s_cal", "<b>LifeCalendarService</b><br><code>services/life_calendar_service.py</code><br>70-Year Memento Mori Matrix<br>Lifespan % & Era Partitioning", 60, 760, 240, 110, style_node)
    builder.add_vertex(p1, "p1_s_coach", "<b>CoachService (Rule Fallback)</b><br><code>services/coach_service.py</code><br>Deterministic Morning/Evening Rules<br>Zero-Egress Structured Outputs", 320, 760, 250, 110, style_node_accent)
    builder.add_vertex(p1, "p1_s_mem", "<b>MemoryService (Hybrid RAG)</b><br><code>services/memory_service.py</code><br>5-Factor Retrieval Composite<br>MMR Cosine Diversity Filter", 590, 760, 250, 110, style_node_accent)
    builder.add_vertex(p1, "p1_s_pat", "<b>PatternService</b><br><code>services/pattern_service.py</code><br>Longitudinal Trend Mining<br>Stalling & Burnout Detectors", 860, 760, 240, 110, style_node)
    builder.add_vertex(p1, "p1_s_anl", "<b>AnalyticsService</b><br><code>services/analytics_service.py</code><br>Habit Consistency Scoring<br>Goal Velocity & Adherence", 1120, 760, 230, 110, style_node)
    builder.add_vertex(p1, "p1_s_ocr", "<b>JournalImport & LocalOCR</b><br><code>services/journal_import_service.py</code><br>OCR Text Ingest & CSV Importers<br>Regex Multi-Block Date Parser", 1370, 760, 220, 110, style_node)
    builder.add_vertex(p1, "p1_s_port", "<b>DataPortabilityService</b><br><code>services/data_portability_service.py</code><br>Atomic JSON Snapshots<br>Safe Backup Before Database Reset", 1610, 760, 180, 110, style_node)

    # Layer 5: Dual Persistence Plane & External AI Gateway
    builder.add_vertex(p1, "p1_c5", 
        "5. DUAL PERSISTENCE PLANE (Local Sovereign Storage @ Local Filesystem)\n"
        "Invariant: Context managers (with get_db():) • SQLite dictionary rows • Normalized SHA-256 deduplication",
        40, 920, 1160, 380, style_c_slate)

    builder.add_vertex(p1, "p1_sqlite", "<b>SQLite 3 Database (goalos.db)</b><br><code>database/connection.py & migrations.py</code>", 60, 980, 600, 300, style_db)
    builder.add_vertex(p1, "p1_sq_tables", 
        "<b>Relational Tables:</b><br>"
        "• <code>users</code> (Profile, dob, remote_ai_consent)<br>"
        "• <code>daily_logs</code> (Habits, morning/evening retros, mood)<br>"
        "• <code>goals</code> (1-mo, 1-yr, 5-yr, category, status)<br>"
        "• <code>milestones</code> (Target dates, weights, completion)<br>"
        "• <code>memories</code> (Raw text, content_hash, importance)<br>"
        "• <code>coach_sessions</code> & <code>coach_messages</code> (Multi-turn chat)<br>"
        "• <code>ai_telemetry</code> (Tokens, latency_ms, usd_cost)<br>"
        "• <code>scores</code> (Historical consistency indices)", 
        80, 1030, 320, 230, style_node)
    
    builder.add_vertex(p1, "p1_sq_fts5", 
        "<b>FTS5 Full-Text Search Engine:</b><br>"
        "• Virtual Table: <code>memory_fts</code><br>"
        "• Tokenizer: Porter Stemmer + Unicode61<br>"
        "• Fast BM25 Lexical Ranking<br>"
        "• Synchronized via MemoryService Dual-Write", 
        420, 1030, 220, 230, style_node_accent)

    builder.add_vertex(p1, "p1_chroma", "<b>ChromaDB Vector Store (chroma_db/)</b><br><code>all-MiniLM-L6-v2 Embeddings</code>", 700, 980, 480, 300, style_db)
    builder.add_vertex(p1, "p1_chroma_details", 
        "<b>Dense Vector Semantic Engine:</b><br>"
        "• Embedding Model: <code>all-MiniLM-L6-v2</code> (384-dim)<br>"
        "• Metric: Cosine Distance Space<br>"
        "• Collection: <code>goalos_memories</code><br>"
        "• Index Status Guard: Gracefully sets 'pending' if ChromaDB is locked<br>"
        "• Offline Capable: Local PyTorch / ONNX runtime", 
        720, 1030, 440, 230, style_node_ai)

    # External AI Gateway Plane
    builder.add_vertex(p1, "p1_c6", 
        "6. EXTERNAL AI GATEWAY & LOCAL FALLBACK (Zero-Surprise Privacy Boundary)\n"
        "ai/openrouter_client.py • Hard Consent Gate: No network calls unless user opts-in",
        1220, 920, 590, 380, style_c_purple)

    builder.add_vertex(p1, "p1_privacy_gate", "<b>Local Privacy Consent Guard</b><br>Checks <code>remote_ai_consent == True</code> & Valid API Key<br>Instant divert to local rules if offline or unconsented", 1240, 980, 550, 70, style_c_amber)
    builder.add_vertex(p1, "p1_openrouter", 
        "<b>OpenRouter AI Gateway (Remote LLM)</b><br>"
        "• Models: Claude 3.5 Sonnet / Llama 3.3 / Gemini 2.5<br>"
        "• Free-Tier Leaky-Bucket Limiter (≤14 RPM, ≥4.29s gap)<br>"
        "• Auto-Retry: Exponential backoff + jitter on 429/503<br>"
        "• Native Tool-Calling & Streaming API", 
        1240, 1070, 280, 210, style_node_ai)
    builder.add_vertex(p1, "p1_fallback_engine", 
        "<b>Local Deterministic Fallback Engine</b><br>"
        "• 100% Offline Rule Synthesis<br>"
        "• Returns structured GoalOS Coach Output<br>"
        "• Invariant: <code>source = 'deterministic_rules'</code><br>"
        "• Zero latency, zero cost, 100% privacy", 
        1540, 1070, 250, 210, style_node_accent)

    # Connections
    builder.add_edge(p1, "e1", "REST API Calls (Axios JSON)", "p1_api_client", "p1_gw_sec", style_edge_accent)
    builder.add_edge(p1, "e2", "Dispatch", "p1_gw_sec", "p1_r_coach", style_edge)
    builder.add_edge(p1, "e3", "Invoke Supervisor", "p1_r_coach", "p1_coord", style_edge_ai)
    builder.add_edge(p1, "e4", "Triage Intent", "p1_coord", "p1_t_intent", style_edge_ai)
    builder.add_edge(p1, "e5", "Scoped Tool Schema", "p1_t_intent", "p1_t_goals", style_edge)
    builder.add_edge(p1, "e6", "Execute Domain Logic", "p1_t_goals", "p1_s_mem", style_edge)
    builder.add_edge(p1, "e7", "Consent = True", "p1_coord", "p1_privacy_gate", style_edge_ai)
    builder.add_edge(p1, "e8", "LLM Prompt & Tools", "p1_privacy_gate", "p1_openrouter", style_edge_ai)
    builder.add_edge(p1, "e9", "Consent = False / Offline", "p1_privacy_gate", "p1_fallback_engine", style_edge_accent)
    builder.add_edge(p1, "e10", "Dual-Write (FTS5 + SQLite)", "p1_s_mem", "p1_sqlite", style_edge_accent)
    builder.add_edge(p1, "e11", "Vector Embeddings", "p1_s_mem", "p1_chroma", style_edge_ai)


    # -------------------------------------------------------------
    # PAGE 2: Cognitive Multi-Agent & Scoped Tool Loop
    # -------------------------------------------------------------
    p2 = builder.add_page("page2", "2. Multi-Agent & Tool Loop", 1700, 1250)

    builder.add_vertex(p2, "p2_title", 
        "<b style='font-size:20px; color:#4C1D95;'>🤖 GoalOS — Cognitive Multi-Agent Supervisor & Scoped Tool Loop</b><br>"
        "<span style='font-size:12px; color:#475569;'>Dynamic Tool Scoping • Leaky-Bucket Rate Limiter • Non-Blocking Observability & USD Cost Metering</span>",
        40, 20, 1620, 50, style_header)

    # Flow Steps: Left to Right / Top to Bottom
    builder.add_vertex(p2, "p2_user", "<b>User Input / Chat</b><br>Prompt entered in<br><code>AICoachView.tsx</code>", 50, 120, 160, 90, style_c_slate)
    builder.add_vertex(p2, "p2_api", "<b>POST /coach/chat</b><br>FastAPI Gateway validates<br>session ID & auth token", 260, 120, 180, 90, style_c_blue)
    builder.add_vertex(p2, "p2_session_mgr", "<b>Session & Blackboard</b><br>Loads history from<br><code>coach_sessions</code> & <code>coach_messages</code>", 490, 120, 200, 90, style_node)
    builder.add_vertex(p2, "p2_supervisor", "<b>CoordinatorAgent</b><br><code>ai/pipelines/coordinator.py</code><br>Supervisor analyzes intent", 740, 100, 220, 130, style_node_ai)
    
    # Tool Scoping Box
    builder.add_vertex(p2, "p2_box_scoping", "<b>DYNAMIC DOMAIN TOOL SCOPING</b><br>(Token Optimization & Anti-Hallucination Barrier)", 1010, 80, 650, 180, style_c_purple)
    builder.add_vertex(p2, "p2_sc_jrn", "<b>Journal Scope</b><br>get_today_tasks()<br>update_habit_log()", 1030, 140, 140, 100, style_node)
    builder.add_vertex(p2, "p2_sc_gl", "<b>Goals Scope</b><br>query_horizon_goals()<br>advance_milestone()", 1190, 140, 140, 100, style_node)
    builder.add_vertex(p2, "p2_sc_mem", "<b>Memory Scope</b><br>search_hybrid_rag()<br>store_reflection()", 1350, 140, 140, 100, style_node)
    builder.add_vertex(p2, "p2_sc_cal", "<b>Calendar Scope</b><br>get_lifespan_fraction()<br>get_current_week()", 1510, 140, 130, 100, style_node)

    # Privacy Decision Gate
    builder.add_vertex(p2, "p2_decision", 
        "<b>Privacy & Connectivity Check</b><br>"
        "<code>remote_ai_consent == True</code><br>AND <code>OPENROUTER_API_KEY</code> set?", 
        710, 320, 280, 100, style_c_amber)

    # Branch A: Remote LLM Agent
    builder.add_vertex(p2, "p2_box_remote", "<b>BRANCH A: REMOTE AGENT PIPELINE (OpenRouter AI)</b>", 50, 480, 780, 460, style_c_purple)
    builder.add_vertex(p2, "p2_limiter", 
        "<b>Leaky-Bucket Rate Limiter</b><br>"
        "• Capacity: 14 RPM (Free Tier Safe)<br>"
        "• Min Interval: 4.29 seconds<br>"
        "• Jittered Exponential Backoff on 429/503", 
        80, 540, 320, 110, style_node_ai)
    
    builder.add_vertex(p2, "p2_llm_call", 
        "<b>OpenRouter Completion Call</b><br>"
        "• Model: Claude 3.5 Sonnet / Llama 3.3<br>"
        "• Injects Scoped Tools & Context<br>"
        "• Tool-calling Function Parser", 
        450, 540, 350, 110, style_node_ai)

    builder.add_vertex(p2, "p2_tool_exec", 
        "<b>Tool Dispatch & Execution Loop</b><br>"
        "• Executes function call against SQLite / Services<br>"
        "• Returns JSON tool response to model<br>"
        "• Max 3 autonomous tool iterations per turn", 
        450, 690, 350, 110, style_node_accent)

    builder.add_vertex(p2, "p2_blackboard_update", 
        "<b>Inter-Agent Blackboard Sync</b><br>"
        "• Updates dynamic blackboard JSON state<br>"
        "• Stores agent reasoning & intermediate flags", 
        80, 690, 320, 110, style_node)

    builder.add_vertex(p2, "p2_obs", 
        "<b>Observability & Cost Metering</b><br>"
        "• Logs prompt_tokens, completion_tokens, latency_ms<br>"
        "• Calculates USD spend per call<br>"
        "• Emits span to <code>ai_telemetry</code> table", 
        80, 830, 720, 80, style_node_ai)

    # Branch B: Local Deterministic Rule Engine
    builder.add_vertex(p2, "p2_box_local", "<b>BRANCH B: DETERMINISTIC OFFLINE ENGINE (Zero Egress)</b>", 870, 480, 790, 460, style_c_green)
    builder.add_vertex(p2, "p2_rule_engine", 
        "<b>Local Coach Rule Engine</b><br><code>services/coach_service.py</code><br>"
        "• Evaluates morning / evening checklists<br>"
        "• Calculates goal alignment & habit streaks<br>"
        "• Generates structured action recommendations", 
        900, 540, 350, 140, style_node_accent)

    builder.add_vertex(p2, "p2_rule_schema", 
        "<b>Deterministic Schema Guarantee</b><br>"
        "• Emits valid <code>CoachOutput</code> Pydantic model<br>"
        "• <code>fallback_reason: 'offline_or_unconsented'</code><br>"
        "• <code>source: 'deterministic_rules'</code>", 
        1290, 540, 340, 140, style_node)

    builder.add_vertex(p2, "p2_local_metrics", 
        "<b>Zero-Cost Local Logging</b><br>"
        "• 0 tokens consumed • $0.00 spend<br>"
        "• Latency &lt; 15ms total execution time", 
        900, 720, 730, 80, style_node_accent)

    # Response Assembly
    builder.add_vertex(p2, "p2_response", 
        "<b>Unified Response Synthesizer & Client Delivery</b><br>"
        "Appends message to <code>coach_messages</code> • Returns stream/JSON to <code>AICoachView.tsx</code> • Renders Action Badges", 
        300, 980, 1100, 90, style_c_dark)

    # Edges Page 2
    builder.add_edge(p2, "p2_e1", "Prompt", "p2_user", "p2_api", style_edge)
    builder.add_edge(p2, "p2_e2", "Validate", "p2_api", "p2_session_mgr", style_edge)
    builder.add_edge(p2, "p2_e3", "Active Context", "p2_session_mgr", "p2_supervisor", style_edge_ai)
    builder.add_edge(p2, "p2_e4", "Filter Tools", "p2_supervisor", "p2_box_scoping", style_edge_ai)
    builder.add_edge(p2, "p2_e5", "Check Policy", "p2_supervisor", "p2_decision", style_edge)
    builder.add_edge(p2, "p2_e6", "YES (Remote AI)", "p2_decision", "p2_limiter", style_edge_ai)
    builder.add_edge(p2, "p2_e7", "NO (Local Safe)", "p2_decision", "p2_rule_engine", style_edge_accent)
    builder.add_edge(p2, "p2_e8", "Paced Tokens", "p2_limiter", "p2_llm_call", style_edge_ai)
    builder.add_edge(p2, "p2_e9", "Tool Calls", "p2_llm_call", "p2_tool_exec", style_edge)
    builder.add_edge(p2, "p2_e10", "Tool Result", "p2_tool_exec", "p2_llm_call", style_edge)
    builder.add_edge(p2, "p2_e11", "Sync State", "p2_tool_exec", "p2_blackboard_update", style_edge)
    builder.add_edge(p2, "p2_e12", "Span Telemetry", "p2_llm_call", "p2_obs", style_edge_ai)
    builder.add_edge(p2, "p2_e13", "Deliver", "p2_obs", "p2_response", style_edge_ai)
    builder.add_edge(p2, "p2_e14", "Deliver", "p2_rule_schema", "p2_response", style_edge_accent)


    # -------------------------------------------------------------
    # PAGE 3: Cognitive Memory & 5-Factor Hybrid RAG
    # -------------------------------------------------------------
    p3 = builder.add_page("page3", "3. Hybrid RAG & Memory Pipeline", 1700, 1250)

    builder.add_vertex(p3, "p3_title", 
        "<b style='font-size:20px; color:#065F46;'>🧠 GoalOS — Cognitive Memory Dual-Write & 5-Factor Hybrid RAG Pipeline</b><br>"
        "<span style='font-size:12px; color:#475569;'>SHA-256 Deduplication • FTS5 BM25 Lexical + ChromaDB Cosine Semantic • 5-Factor Retrieval Composite • MMR Diversity Filter</span>",
        40, 20, 1620, 50, style_header)

    # Ingestion Pipeline Swimlane
    builder.add_vertex(p3, "p3_c_ingest", "<b>MEMORY INGESTION & DUAL-WRITE PIPELINE (Invariant 1.3)</b>", 40, 90, 1620, 320, style_c_teal)
    
    builder.add_vertex(p3, "p3_raw_in", 
        "<b>Raw Memory Capture</b><br>"
        "• Daily Reflection Note<br>"
        "• Coach Dialogue Insight<br>"
        "• Milestone Breakthrough", 
        60, 150, 210, 100, style_node)

    builder.add_vertex(p3, "p3_hash", 
        "<b>SHA-256 Deduplication Hash</b><br>"
        "<code>hashlib.sha256(\" \".join(text.casefold().split()))</code><br>"
        "Prevents duplicate memory blobs across syncs", 
        310, 150, 300, 100, style_node_accent)

    builder.add_vertex(p3, "p3_dual_write_hub", 
        "<b>MemoryService.store() Transaction Coordinator</b><br>"
        "Coordinates Atomic SQLite insert, FTS5 sync, and vector embedding", 
        650, 150, 360, 100, style_c_green)

    builder.add_vertex(p3, "p3_w_sq", 
        "<b>1. Relational Record</b><br>"
        "Upsert into <code>memories</code> table<br>"
        "(id, text, content_hash, importance)", 
        1050, 130, 260, 75, style_node)

    builder.add_vertex(p3, "p3_w_fts5", 
        "<b>2. FTS5 Indexing</b><br>"
        "Upsert into <code>memory_fts</code><br>"
        "(Porter Stemmer & BM25 Ready)", 
        1050, 220, 260, 75, style_node_accent)

    builder.add_vertex(p3, "p3_w_chroma", 
        "<b>3. ChromaDB Vector Upsert</b><br>"
        "Embed with <code>all-MiniLM-L6-v2</code><br>"
        "If locked, sets <code>index_status = 'pending'</code>", 
        1340, 175, 290, 85, style_node_ai)

    # Retrieval Pipeline Swimlane
    builder.add_vertex(p3, "p3_c_retrieval", "<b>5-FACTOR HYBRID RAG RETRIEVAL & MMR FILTERING (Invariant 3.1)</b>", 40, 440, 1620, 750, style_c_purple)

    builder.add_vertex(p3, "p3_query_in", 
        "<b>Retrieval Query</b><br>"
        "Incoming User Query or Coach Context<br><code>MemoryService.retrieve(query, top_k=5)</code>", 
        60, 510, 280, 90, style_c_slate)

    builder.add_vertex(p3, "p3_par_search", 
        "<b>Parallel Dual-Search Execution</b><br>"
        "Concurrent Lexical BM25 and Dense Vector Similarity Queries", 
        380, 510, 340, 90, style_node)

    builder.add_vertex(p3, "p3_lex_res", 
        "<b>Lexical Search (FTS5)</b><br>"
        "BM25 Ranking Score<br>"
        "Exact terms & code tokens<br>"
        "Normalized Score: <b>S_lex</b> (capped 1.0)", 
        760, 480, 270, 95, style_node_accent)

    builder.add_vertex(p3, "p3_sem_res", 
        "<b>Semantic Search (ChromaDB)</b><br>"
        "Cosine Similarity Score<br>"
        "Concept & synonym matching<br>"
        "Normalized Score: <b>S_sem</b>", 
        760, 600, 270, 95, style_node_ai)

    # 5-Factor Formula Box
    builder.add_vertex(p3, "p3_formula_box", 
        "<b>GOALOS 5-FACTOR RETRIEVAL FORMULA</b><br>"
        "<div style='font-size:13px; font-family:monospace; color:#064E3B; background:#ECFDF5; padding:8px; border-radius:6px; margin:6px 0;'>"
        "S = 0.35·S_sem + 0.15·S_lex + 0.25·S_imp + 0.15·S_rec + 0.10·S_freq"
        "</div>"
        "• <b>S_sem (35%):</b> Dense Cosine Similarity from ChromaDB<br>"
        "• <b>S_lex (15%):</b> BM25 Lexical Keyword Match from SQLite FTS5<br>"
        "• <b>S_imp (25%):</b> Normalized Importance Level (1 to 5 scale)<br>"
        "• <b>S_rec (15%):</b> 30-Day Exponential Half-Life Decay: <code>exp(-0.693 · Δt / 30)</code><br>"
        "• <b>S_freq (10%):</b> Logarithmic Access Frequency: <code>min(1.0, ln(1 + n) / ln(100))</code>", 
        1070, 480, 560, 220, style_c_green)

    # MMR Box
    builder.add_vertex(p3, "p3_mmr_box", 
        "<b>Maximal Marginal Relevance (MMR) Diversity Filter</b><br>"
        "• Cosine Similarity Threshold: <b>cos(v_i, v_selected) &lt; 0.94</b><br>"
        "• Rejects redundant near-duplicate memories (e.g. repeated daily habit notes)<br>"
        "• Maximizes information entropy in LLM prompt window", 
        760, 740, 870, 110, style_c_amber)

    builder.add_vertex(p3, "p3_final_context", 
        "<b>Ranked Cognitive Context Assembly</b><br>"
        "• Top 3-5 Diverse, Highly Relevant, Grounded Memories<br>"
        "• Injected into System Prompt with Exact Timestamp & Citation IDs<br>"
        "• Enforces Zero-Hallucination Invariant", 
        760, 890, 870, 90, style_node_ai)

    # Retrieval Edges
    builder.add_edge(p3, "p3_e1", "Capture", "p3_raw_in", "p3_hash", style_edge)
    builder.add_edge(p3, "p3_e2", "Verified Hash", "p3_hash", "p3_dual_write_hub", style_edge_accent)
    builder.add_edge(p3, "p3_e3", "Write Relational", "p3_dual_write_hub", "p3_w_sq", style_edge)
    builder.add_edge(p3, "p3_e4", "Write Lexical", "p3_dual_write_hub", "p3_w_fts5", style_edge_accent)
    builder.add_edge(p3, "p3_e5", "Write Vector", "p3_dual_write_hub", "p3_w_chroma", style_edge_ai)
    builder.add_edge(p3, "p3_e6", "Search", "p3_query_in", "p3_par_search", style_edge)
    builder.add_edge(p3, "p3_e7", "FTS5 Query", "p3_par_search", "p3_lex_res", style_edge_accent)
    builder.add_edge(p3, "p3_e8", "Cosine Query", "p3_par_search", "p3_sem_res", style_edge_ai)
    builder.add_edge(p3, "p3_e9", "Feed S_lex", "p3_lex_res", "p3_formula_box", style_edge_accent)
    builder.add_edge(p3, "p3_e10", "Feed S_sem", "p3_sem_res", "p3_formula_box", style_edge_ai)
    builder.add_edge(p3, "p3_e11", "Scored Candidates", "p3_formula_box", "p3_mmr_box", style_edge)
    builder.add_edge(p3, "p3_e12", "Deduplicated", "p3_mmr_box", "p3_final_context", style_edge_ai)

    return ET.tostring(builder.root, encoding="utf-8", method="xml").decode("utf-8")

if __name__ == "__main__":
    xml_content = build_drawio_xml()
    out_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "architecture.drawio")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(xml_content)
    print(f"Generated Draw.io diagram at: {os.path.abspath(out_path)}")
