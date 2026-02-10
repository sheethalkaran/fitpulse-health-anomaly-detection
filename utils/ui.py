import streamlit as st

def load_premium_css():
    #External libs (Fonts + Icons)
    st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"
          crossorigin="anonymous" referrerpolicy="no-referrer" />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap"
          rel="stylesheet">

    <!-- ✅ Streamlit uses Google Material Icons internally -->
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet">

    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    
    /*Fix Streamlit expander icons showing text like "arrow_right" */
    [data-testid="stExpanderToggleIcon"] {
    font-family: "Material Symbols Rounded" !important;
    font-variation-settings: "FILL" 0, "wght" 500, "GRAD" 0, "opsz" 24;
    }

    * { font-family: 'Inter', sans-serif !important; }

    /* ✅ HIDE ONLY Sidebar Nav weird extra text */
    [data-testid="stSidebarNav"]::before {
        display: none !important;
    }

    /* ==========================================================
       ✅ FIX 1: Sidebar Collapse Button (Stable + Always Visible)
       ========================================================== */
    [data-testid="stSidebarCollapseButton"]{
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 44px !important;
        height: 44px !important;
        border-radius: 12px !important;
        background: rgba(59, 130, 246, 0.12) !important;
        border: 1px solid rgba(59, 130, 246, 0.25) !important;
        box-shadow: 0 6px 16px rgba(59, 130, 246, 0.18) !important;
        cursor: pointer !important;
    }

    /* ✅ Always show SVG icon */
    [data-testid="stSidebarCollapseButton"] svg{
        display: block !important;
        width: 22px !important;
        height: 22px !important;
        opacity: 1 !important;
        visibility: visible !important;
    }

    /* ✅ Remove any weird text like ">" or icon names */
    [data-testid="stSidebarCollapseButton"] span{
        display: none !important;
    }

    /* ==========================================================
       ✅ FIX 2: Expander icon overwrite issue (arrow_right text)
       ========================================================== */
    [data-testid="stExpanderToggleIcon"]{
        font-family: "Material Icons" !important;
    }

    /* ✅ Smooth scroll */
    html { scroll-behavior: smooth; }

    /* ✅ OPTIMIZED KEYFRAMES */
    @keyframes gradientShift {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }

    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes pulseGlow {
        0%, 100% { box-shadow: 0 20px 40px rgba(59, 130, 246, 0.2); }
        50% { box-shadow: 0 20px 40px rgba(59, 130, 246, 0.4); }
    }

    @keyframes shimmer {
        0% { background-position: -200% center; }
        100% { background-position: 200% center; }
    }

    @keyframes slideInRight {
    from { transform: translateX(-20px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
    }

    /* ✅ Top-down popup animation for alerts/results */
    @keyframes slideDownFade {
    from { transform: translate(-50%, -40px); opacity: 0; }
    to { transform: translate(-50%, 0); opacity: 1; }
    }

    @keyframes ripple {
        0% { transform: scale(0); opacity: 0.5; }
        100% { transform: scale(40); opacity: 0; }
    }

    @keyframes glow {
        0%, 100% { filter: brightness(1); }
        50% { filter: brightness(1.2); }
    }

    /* ✅ MAIN BACKGROUND */
    .stApp {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 25%, #faf5ff 50%, #f0f9ff 75%, #e0f2fe 100%) !important;
        background-size: 400% 400%;
        animation: gradientShift 20s ease infinite;
    }

    /* ✅ SIDEBAR */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.98) 100%) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 10px 0 30px rgba(59, 130, 246, 0.1);
        animation: slideInRight 0.5s ease-out;
    }

    section[data-testid="stSidebar"] * {
        color: #1e293b !important;
    }

    /* ✅ Sidebar Nav */
    section[data-testid="stSidebarNav"] {
        padding: 20px !important;
    }

    section[data-testid="stSidebarNav"] a {
        display: flex !important;
        align-items: center !important;
        gap: 12px !important;
        padding: 14px 16px !important;
        border-radius: 16px !important;
        margin: 8px 0 !important;
        font-weight: 600 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        background: transparent !important;
        border: 1px solid transparent !important;
        animation: fadeInUp 0.6s ease-out forwards;
        opacity: 0;
        cursor: pointer !important;
    }

    section[data-testid="stSidebarNav"] a:nth-child(1) { animation-delay: 0.1s; }
    section[data-testid="stSidebarNav"] a:nth-child(2) { animation-delay: 0.2s; }
    section[data-testid="stSidebarNav"] a:nth-child(3) { animation-delay: 0.3s; }
    section[data-testid="stSidebarNav"] a:nth-child(4) { animation-delay: 0.4s; }
    section[data-testid="stSidebarNav"] a:nth-child(5) { animation-delay: 0.5s; }

    section[data-testid="stSidebarNav"] a:hover {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%) !important;
        transform: translateX(8px) scale(1.02) !important;
        border: 1px solid rgba(59, 130, 246, 0.2) !important;
    }

    section[data-testid="stSidebarNav"] li[data-selected="true"] a {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
        color: white !important;
        box-shadow: 0 10px 20px rgba(59, 130, 246, 0.3);
        animation: pulseGlow 2s ease-in-out infinite !important;
    }

    /* ✅ HEADER */
    .topbar {
        padding: 25px 30px;
        border-radius: 24px;
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.9) 0%, rgba(168, 85, 247, 0.9) 50%, rgba(236, 72, 153, 0.9) 100%);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: white;
        margin-bottom: 30px;
        overflow: hidden;
        position: relative;
        animation: fadeInUp 0.8s ease-out, pulseGlow 3s ease-in-out infinite;
    }

    .topbar::after {
        content: '';
        position: absolute;
        top: 0; left: -100%;
        width: 100%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        animation: shimmer 3s infinite;
    }

    .topbar h2 {
        margin: 0;
        font-weight: 900;
        font-size: 2.2rem;
        color: white;
        animation: fadeInUp 0.9s ease-out, glow 3s ease-in-out infinite;
    }

    .topbar p {
        margin: 8px 0 0 0;
        opacity: 0.9;
        font-size: 1.05rem;
        font-weight: 500;
        color: white;
        animation: fadeInUp 1s ease-out;
    }

    /* ✅ GLASS CARD */
    .glass {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.1);
        color: #1e293b;
        animation: fadeInUp 0.6s ease-out;
        transition: all 0.3s ease;
    }

    .glass:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(59, 130, 246, 0.2);
    }

    /* KPI CARD */
    .kpi {
        border-radius: 20px;
        padding: 24px;
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.4);
        box-shadow: 0 15px 35px rgba(59, 130, 246, 0.1);
        color: #1e293b;
        position: relative;
        overflow: hidden;
        animation: fadeInUp 0.7s ease-out;
        transition: all 0.3s ease;
        will-change: transform;
    }

    .kpi:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 25px 50px rgba(59, 130, 246, 0.2);
    }

    .kpi::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 4px;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        transition: all 0.3s ease;
    }

    .kpi:hover::before {
        height: 6px;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6, #3b82f6);
        background-size: 200% 100%;
        animation: shimmer 2s infinite;
    }

    .kpi-title {
        font-size: 14px;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }

    .kpi-value {
        font-size: 32px;
        font-weight: 800;
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 8px 0;
        transition: all 0.3s ease;
    }

    .kpi-sub {
        font-size: 13px;
        color: #94a3b8;
        margin-top: 8px;
        font-weight: 500;
    }

    /* ✅ BUTTON */
    div.stButton > button {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
        color: white !important;
        border-radius: 14px !important;
        font-weight: 700 !important;
        border: none !important;
        padding: 14px 24px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 10px 20px rgba(59, 130, 246, 0.3) !important;
        position: relative;
        overflow: hidden;
        animation: fadeInUp 1s ease-out;
        cursor: pointer !important;
    }

    div.stButton > button::after {
        content: '';
        position: absolute;
        top: 50%; left: 50%;
        width: 5px; height: 5px;
        background: rgba(255, 255, 255, 0.5);
        opacity: 0;
        border-radius: 100%;
        transform: scale(0) translate(-50%);
        transform-origin: 50% 50%;
    }

    div.stButton > button:focus:not(:active)::after {
        animation: ripple 1s ease-out;
    }

    div.stButton > button:hover {
        transform: translateY(-3px) scale(1.05) !important;
        box-shadow: 0 15px 30px rgba(59, 130, 246, 0.4) !important;
    }

    div.stButton > button:active {
        transform: translateY(-1px) scale(0.98) !important;
    }

    /* ✅ FILE UPLOADER */
    section[data-testid="stFileUploaderDropzone"] {
        background: rgba(255, 255, 255, 0.7) !important;
        border: 2px dashed rgba(59, 130, 246, 0.3) !important;
        border-radius: 20px !important;
        animation: fadeInUp 1.2s ease-out;
        transition: all 0.3s ease !important;
    }

    section[data-testid="stFileUploaderDropzone"]:hover {
        border-color: #3b82f6 !important;
        border-style: solid !important;
        transform: translateY(-3px);
        box-shadow: 0 15px 30px rgba(59, 130, 246, 0.15) !important;
    }

    section[data-testid="stFileUploaderDropzone"] button {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
        color: white !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        border: none !important;
        padding: 12px 24px !important;
        transition: all 0.3s ease !important;
    }

    section[data-testid="stFileUploaderDropzone"] button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3) !important;
    }

    /* ✅ PERFORMANCE */
    * { will-change: auto; }
    .kpi, .glass, div.stButton > button { will-change: transform; }

    /* ✅ Global popup container (top-down slide) */
    .popup-container {
        position: fixed;
        top: 80px; /* moved slightly down for better visibility */
        left: 50%;
        transform: translateX(-50%);
        z-index: 9999;
        max-width: 520px;
        width: calc(100% - 32px);
        pointer-events: none;
    }

    .popup-card {
        background: rgba(255, 255, 255, 0.98);
        backdrop-filter: blur(18px);
        border-radius: 18px;
        border: 1px solid rgba(148, 163, 184, 0.4);
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.25);
        padding: 16px 18px;
        display: flex;
        gap: 12px;
        align-items: flex-start;
        animation: slideDownFade 0.55s cubic-bezier(0.22, 0.61, 0.36, 1) forwards;
        pointer-events: auto;
    }

    .popup-icon {
        width: 32px;
        height: 32px;
        border-radius: 999px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        flex-shrink: 0;
    }

    .popup-content-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 4px;
    }

    .popup-content-body {
        font-size: 0.9rem;
        color: #475569;
    }

    .popup-meta {
        margin-top: 6px;
        font-size: 0.78rem;
        color: #9ca3af;
    }

    .popup-close {
        margin-left: auto;
        border-radius: 999px;
        border: none;
        width: 26px;
        height: 26px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(148, 163, 184, 0.12);
        color: #6b7280;
        cursor: pointer;
        font-size: 14px;
        transition: all 0.2s ease;
    }

    .popup-close:hover {
        background: rgba(148, 163, 184, 0.24);
        color: #111827;
        transform: scale(1.05);
    }
    /* ✅ 1) Hide the whole expander icon area (this is where "arrow_right" is coming) */
[data-testid="stExpanderToggleIcon"]{
    display: none !important;
}

/* ✅ 2) Add spacing so title doesn't shift left */
div[data-testid="stExpander"] summary{
    padding-left: 12px !important;
}

/* ✅ 3) Add clean arrow icon manually (professional look) */
div[data-testid="stExpander"] summary::before{
    content: "▶" !important;
    margin-right: 10px !important;
    font-size: 14px !important;
    color: #64748b !important;
}

/* ✅ 4) When expander is open show down arrow */
div[data-testid="stExpander"] details[open] summary::before{
    content: "▼" !important;
}
/* ✅ Remove ONLY the "arrow_right" text (not the title) */
[data-testid="stExpanderToggleIcon"] span {
    font-size: 0 !important;
    display: inline-block !important;
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
}

    </style>
    """, unsafe_allow_html=True)


def render_header():
    st.markdown("""
    <div class="topbar">
        <h2>Health Analytics Dashboard</h2>
        <p>Real-time Health Monitoring • Predictive Analytics</p>
        <div style="display:flex; gap:12px; margin-top:16px; flex-wrap:wrap;">
            <span style="background: rgba(255,255,255,0.2); padding:6px 12px; border-radius:20px; font-size:0.9rem;">Data Collection</span>
            <span style="background: rgba(255,255,255,0.2); padding:6px 12px; border-radius:20px; font-size:0.9rem;">Analysis</span>
            <span style="background: rgba(255,255,255,0.2); padding:6px 12px; border-radius:20px; font-size:0.9rem;">Visualization</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    
    
def kpi_card(title, value, sub=""):
    st.markdown(f"""
    <div class="kpi">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)


