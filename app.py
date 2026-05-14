"""HVAC Fault Detection System - Streamlit Dashboard"""
import streamlit as st
import os, sys, collections, datetime, json, joblib, random, base64, math
import pandas as pd
from dotenv import load_dotenv

load_dotenv(override=True)
GROK_API_KEY = os.getenv("GROK_API_KEY", "")
GROK_BASE_URL = os.getenv("GROK_BASE_URL", "https://api.x.ai/v1")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-3")

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

st.set_page_config(page_title="HVAC Fault Detection System", page_icon="🔧", layout="wide", initial_sidebar_state="expanded")

# ── Video Intro Splash Screen ───────────────────────────────────────────────
import streamlit.components.v1 as components

if "intro_played" not in st.session_state:
    st.session_state.intro_played = False

if not st.session_state.intro_played:
    st.markdown("""
    <style>
      @keyframes introFadeBounce {
        0%, 100% { opacity: 0.5; } 50% { opacity: 1; }
      }
      @keyframes introArrowDrop {
        0% { transform: rotate(45deg) translateY(-4px); opacity: 0; }
        60% { opacity: 1; }
        100% { transform: rotate(45deg) translateY(4px); opacity: 0; }
      }
      #hvac-intro-overlay {
        position: fixed;
        top: 0; left: 0;
        width: 100vw; height: 100vh;
        background: #07131f;
        z-index: 999999;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        transition: opacity 0.6s ease, visibility 0.6s ease;
        overflow: hidden;
      }
      #hvac-intro-overlay.dismissed {
        opacity: 0;
        visibility: hidden;
        pointer-events: none;
      }
      #hvac-intro-video {
        width: 100%;
        height: 100%;
        object-fit: cover;
        position: absolute;
        top: 0; left: 0;
      }
      #hvac-scroll-hint {
        position: absolute;
        bottom: 36px;
        left: 50%;
        transform: translateX(-50%);
        color: rgba(255,255,255,0.7);
        font-family: 'DM Sans', sans-serif;
        font-size: 13px;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
        animation: introFadeBounce 2s ease-in-out infinite;
        z-index: 2;
      }
      .intro-scroll-arrow {
        width: 20px; height: 20px;
        border-right: 2px solid rgba(255,255,255,0.6);
        border-bottom: 2px solid rgba(255,255,255,0.6);
        transform: rotate(45deg);
        animation: introArrowDrop 1.4s ease-in-out infinite;
      }
      #hvac-skip-btn {
        position: absolute;
        top: 24px; right: 32px;
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.25);
        color: white;
        font-family: 'DM Sans', sans-serif;
        font-size: 13px;
        padding: 7px 18px;
        border-radius: 20px;
        cursor: pointer;
        z-index: 3;
        transition: background 0.2s;
      }
      #hvac-skip-btn:hover { background: rgba(255,255,255,0.22); }
    </style>
    
    <div id="hvac-intro-overlay">
      <video
        id="hvac-intro-video"
        src="app/static/3dimage.mp4"
        autoplay
        muted
        playsinline
        preload="auto"
      ></video>
    
      <div id="hvac-scroll-hint">
        <span>Scroll to enter</span>
        <div class="intro-scroll-arrow"></div>
      </div>
    
      <button id="hvac-skip-btn">Skip ›</button>
    </div>
    """, unsafe_allow_html=True)
    
    components.html("""
    <script>
    (function() {
      function initIntro() {
        try {
          const D = window.parent.document;
          const overlay = D.getElementById('hvac-intro-overlay');
          if (!overlay) return; // Wait for it to render
          
          clearInterval(checkInterval);
    
          function dismiss() {
            if (overlay.classList.contains('dismissed')) return;
            overlay.classList.add('dismissed');
            try { window.parent.scrollTo({ top: 0, behavior: 'smooth' }); } catch(e) {}
            setTimeout(function() { overlay.style.display = 'none'; }, 650);
          }
    
          // Skip button
          var skipBtn = D.getElementById('hvac-skip-btn');
          if (skipBtn) skipBtn.addEventListener('click', dismiss);
    
          // Dismiss on scroll (parent window)
          window.parent.addEventListener('wheel', dismiss, { once: true });
          window.parent.addEventListener('touchmove', dismiss, { once: true });
    
          // Auto-dismiss when video ends
          var vid = D.getElementById('hvac-intro-video');
          if (vid) vid.addEventListener('ended', dismiss);
    
          // Fallback: auto-dismiss after 12s
          setTimeout(dismiss, 12000);
          
        } catch(e) {
          console.error("Intro script error:", e);
          clearInterval(checkInterval);
        }
      }
    
      var checkInterval = setInterval(initIntro, 100);
      
      setTimeout(function() {
        try {
          const overlay = window.parent.document.getElementById('hvac-intro-overlay');
          if (overlay) overlay.style.display = 'none';
        } catch(e) {}
      }, 10000);
    })();
    </script>
    """, height=0, width=0)
    
    # Mark as played so it never renders again for this session
    st.session_state.intro_played = True

components.html("""
<script>
(function() {
    // 1. Time Update
    setInterval(() => {
        try {
            const doc = window.parent.document;
            const now = new Date();
            const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
            const d = now.getDate().toString().padStart(2, '0');
            const m = months[now.getMonth()];
            const y = now.getFullYear();
            const dateStr = `${d} ${m} ${y}`;

            let h = now.getHours();
            const ampm = h >= 12 ? 'PM' : 'AM';
            h = h % 12;
            h = h ? h : 12;
            const hStr = h.toString().padStart(2, '0');
            const minStr = now.getMinutes().toString().padStart(2, '0');
            const secStr = now.getSeconds().toString().padStart(2, '0');
            const timeStr = `${hStr}:${minStr}:${secStr} ${ampm}`;
            
            const nativeEl = doc.getElementById('live-time-native');
            if (nativeEl) {
                nativeEl.innerHTML = `<strong>${dateStr}</strong><br><span>${timeStr}</span>`;
            }
            
            const bannerEl = doc.getElementById('live-time-banner');
            if (bannerEl) {
                bannerEl.innerHTML = `${dateStr}&nbsp;&nbsp;${timeStr}`;
            }

            // Sync Dashboard Parameter Trends (Last 24 Hours) X-axis with the clock
            const trendTicks = doc.querySelectorAll('.trend-label-dash');
            if (trendTicks.length === 7) {
                for (let i = 0; i < 7; i++) {
                    const offsetHours = 24 - (i * 4);
                    const t = new Date(now.getTime() - offsetHours * 60 * 60 * 1000);
                    let th = t.getHours();
                    const tampm = th >= 12 ? 'PM' : 'AM';
                    th = th % 12;
                    th = th ? th : 12;
                    const hStr2 = th.toString().padStart(2, '0');
                    const minStr2 = t.getMinutes().toString().padStart(2, '0');
                    trendTicks[i].textContent = `${hStr2}:${minStr2} ${tampm}`;
                }
            }
        } catch(e) {}
    }, 1000);

    // 2. Custom Hamburger
    try {
        const D = window.parent.document;
        if (!D.getElementById('custom-hvac-hamburger')) {
            const btn = D.createElement('button');
            btn.id = 'custom-hvac-hamburger';
            btn.innerHTML = '✕';
            Object.assign(btn.style, {
                position: 'fixed',
                top: '12px',
                left: '236px',
                zIndex: '999999',
                background: '#07131f',
                color: '#2f8df5',
                border: '1px solid #20364d',
                borderRadius: '6px',
                width: '40px',
                height: '40px',
                fontSize: '20px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'left 0.3s ease'
            });
            
            let sidebarOpen = true; // Streamlit initial state is expanded
            
            btn.onclick = function() {
                const sidebar = D.querySelector('[data-testid="stSidebar"]');
                if (!sidebar) return;
                
                if (!sidebar.style.transition.includes('margin-left')) {
                    sidebar.style.transition = 'margin-left 0.3s ease-in-out';
                }
                
                sidebarOpen = !sidebarOpen;
                
                if (sidebarOpen) {
                    sidebar.style.setProperty('margin-left', '0px', 'important');
                    btn.innerHTML = '✕';
                    btn.style.left = '236px';
                } else {
                    sidebar.style.setProperty('margin-left', '-220px', 'important');
                    btn.innerHTML = '☰';
                    btn.style.left = '16px';
                }
            };
            
            D.body.appendChild(btn);
            
            // Force state continuously in case Streamlit re-renders elements
            setInterval(function() {
                const sidebar = D.querySelector('[data-testid="stSidebar"]');
                if (sidebar) {
                    if (sidebarOpen) {
                        sidebar.style.setProperty('margin-left', '0px', 'important');
                        if (btn.innerHTML !== '✕') btn.innerHTML = '✕';
                        if (btn.style.left !== '236px') btn.style.left = '236px';
                    } else {
                        sidebar.style.setProperty('margin-left', '-220px', 'important');
                        if (btn.innerHTML !== '☰') btn.innerHTML = '☰';
                        if (btn.style.left !== '16px') btn.style.left = '16px';
                    }
                }
            }, 100);
        }
    } catch(e) {}
})();
</script>
""", height=0, width=0)


from utils.simulator import SensorSimulator
from utils.visualizations import (
    plot_sparkline, plot_risk_gauge, plot_live_trends, plot_full_sensor_trends, 
    plot_probability_chart, plot_confusion_matrix, plot_accuracy_comparison,
    plot_feature_importance, plot_correlation_heatmap, plot_shap_summary, plot_metrics_history,
    FAULT_COLORS, COLORS
)
from utils.alert_engine import evaluate_alerts, AI_EXPLANATIONS, RECOMMENDED_ACTIONS, FAULT_COMPONENT, SEVERITY_ICONS
from model.predict import predict_fault, load_model, clear_model_cache
from utils.preprocess import get_feature_names, validate_input, FEATURE_RANGES, load_dataset, preprocess_features
from utils.stitch_connector import log_prediction
from model.train import train_model, DEFAULT_HYPERPARAMS, get_metrics_history

# ── Global CSS ──────────────────────────────────────────────────────────────
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&family=DM+Sans:wght@400;500;600&display=swap');
:root{--bg-primary:#0b0f1a;--bg-card:#0f1623;--bg-surface:#131d2e;--border:#1c2e47;--text-primary:#dce8f5;--text-secondary:#6b8299;--accent-blue:#3b9eff;--accent-green:#22d46b;--accent-orange:#f5a623;--accent-red:#e84040;--accent-yellow:#f5d020;--accent-purple:#9b72f5;--accent-cyan:#00c8e0}
/* Hide Streamlit chrome that causes the top empty strip */
#MainMenu { display: none !important; }
header[data-testid="stHeader"] { display: none !important; }
div[data-testid="stToolbar"] { display: none !important; }
div[data-testid="stDecoration"] { display: none !important; }
div[data-testid="stStatusWidget"] { display: none !important; }
.stDeployButton { display: none !important; }
/* Push content to very top & fill full width */
.main .block-container {
  padding-top: 0 !important;
  margin-top: 0 !important;
  padding-left: 1rem !important;
  padding-right: 1rem !important;
  max-width: 100% !important;
  width: 100% !important;
}
/* Remove default app root left padding */
.stApp > div:first-child { padding-left: 0 !important; }
/* Flush column containers */
div[data-testid="stHorizontalBlock"] { gap: 0.5rem !important; padding: 0 !important; }
div[data-testid="column"] { padding-left: 6px !important; padding-right: 6px !important; min-width: 0 !important; }
/* Tighten vertical spacing */
div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] { gap: 0.3rem !important; }
/* Tighten plotly chart containers */
div[data-testid="stPlotlyChart"] { margin-top: 0 !important; margin-bottom: 0 !important; }
div[data-testid="stPlotlyChart"] > div { margin: 0 !important; padding: 0 !important; }

/* Native title overrides to remove default h1 margins */
.native-title-main { margin: 0 !important; padding: 0 !important; font-family: 'Barlow', sans-serif !important; font-size: 1.6rem !important; color: #dce8f5 !important; font-weight: 700 !important; }
.native-title-sub { margin: 0 !important; padding: 0 !important; font-family: 'DM Sans', sans-serif !important; font-size: 0.85rem !important; color: #6b8299 !important; }

.stApp{background:linear-gradient(135deg,#0b0f1a 0%,#0f1623 50%,#0b0f1a 100%)}
section[data-testid="stSidebar"]{background:#080d18 !important;border-right:1px solid #1c2e47;}
section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] * {
    font-family: 'DM Sans', sans-serif !important;
    color: #dce8f5 !important;
}
/* Unified button styling */
div[data-testid="stButton"] > button {
  background: linear-gradient(135deg, #1a3a5c, #1e4a7a) !important;
  border: 1px solid #3b9eff !important;
  color: #dce8f5 !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 0.9rem !important;
  font-weight: 600 !important;
  border-radius: 8px !important;
  padding: 8px 18px !important;
  transition: all 0.2s ease !important;
  width: 100%;
}
div[data-testid="stButton"] > button:hover {
  background: linear-gradient(135deg, #1e4a7a, #2860a8) !important;
  border-color: #5ab0ff !important;
  color: #ffffff !important;
  box-shadow: 0 0 12px rgba(59,158,255,0.35) !important;
}
div[data-testid="stButton"] > button[kind="primary"] {
  background: linear-gradient(135deg, #1565c0, #1976d2) !important;
  border-color: #42a5f5 !important;
  color: #ffffff !important;
}
/* Sidebar nav button override */
section[data-testid="stSidebar"] .stButton > button {
  background: transparent !important;
  border: none !important;
  border-left: 3px solid transparent !important;
  box-shadow: none !important;
  color: #a8bcd4 !important;
  justify-content: flex-start !important;
  text-align: left !important;
  padding: 10px 16px !important;
  border-radius: 8px !important;
  font-size: 0.95rem !important;
  font-weight: 500 !important;
  transition: all 0.2s ease !important;
}
section[data-testid="stSidebar"] .stButton > button * {
  white-space: nowrap !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
  background: rgba(59,158,255,0.08) !important;
  border-left: 3px solid rgba(59,158,255,0.5) !important;
  color: #ffffff !important;
  box-shadow: none !important;
}
.site-meta-label {font-size: 0.7rem;letter-spacing: 0.1em;text-transform: uppercase;color: #6b8299 !important;margin: 0;}
.site-meta-value {font-size: 0.85rem;color: #3b9eff !important;font-weight: 600;margin: 2px 0 12px;}

h1,h2,h3{font-family:'Barlow',sans-serif !important;color:#dce8f5 !important}
p,span,label,.stMarkdown{font-family:'DM Sans',sans-serif !important}
/* Keep Material Icons intact */
span[class^="st-"], span[class*="material"], i { font-family: inherit !important; }
.card{background:linear-gradient(135deg,#0f1623,#131d2e);border:1px solid #1c2e47;border-radius:12px;padding:20px;margin-bottom:12px;box-shadow:0 4px 20px rgba(0,0,0,0.25)}
/* KPI card responsive flex */
.kpi-card{background:linear-gradient(135deg,#0f1623,#131d2e);border:1px solid #1c2e47;border-radius:14px;padding:14px 18px;text-align:center;min-width:120px;flex:1 1 120px;margin-bottom:0 !important}
.kpi-label{font-family:'DM Sans',sans-serif;font-size:0.7rem;letter-spacing:0.08em;text-transform:uppercase;color:#6b8299;margin:0}
.kpi-value{font-family:'Barlow',sans-serif;font-size:1.9rem;font-weight:700;margin:2px 0}
.kpi-unit{font-family:'DM Sans',sans-serif;font-size:0.8rem;color:#6b8299}
/* Bug 6: Header banner flush to top */
.header-banner{background:linear-gradient(90deg,#080d18 0%,#0f1623 50%,#080d18 100%);border:1px solid #1c2e47;border-radius:12px;padding:14px 24px;margin-top:0;margin-bottom:18px;display:flex;align-items:center;justify-content:space-between}
.header-title{color:#dce8f5;font-size:1.5rem;font-weight:700;margin:0;font-family:'Barlow',sans-serif}
.header-sub{color:#6b8299;font-size:0.85rem;margin:2px 0 0;font-family:'DM Sans',sans-serif}
/* Unified ONLINE / OFFLINE badge */
@keyframes pulse-green { 0%,100%{opacity:1;box-shadow:0 0 0 0 rgba(34,212,107,0.6)} 50%{opacity:0.7;box-shadow:0 0 0 5px rgba(34,212,107,0)} }
.online-badge { display:inline-flex;align-items:center;gap:6px;background:rgba(34,212,107,0.12);border:1px solid #22d46b;border-radius:20px;padding:4px 14px;color:#22d46b;font-family:'Barlow',sans-serif;font-size:0.85rem;font-weight:700;letter-spacing:0.08em; }
.pulse-dot { width:8px;height:8px;border-radius:50%;background:#22d46b;animation:pulse-green 1.5s ease-in-out infinite;flex-shrink:0; }
.offline-badge { display:inline-flex;align-items:center;gap:6px;background:rgba(232,64,64,0.12);border:1px solid #e84040;border-radius:20px;padding:4px 14px;color:#e84040;font-family:'Barlow',sans-serif;font-size:0.85rem;font-weight:700;letter-spacing:0.08em; }
.alert-item{display:flex;align-items:flex-start;gap:10px;padding:10px 14px;border-bottom:1px solid #1c2e47}
.alert-title{color:#dce8f5;font-weight:600;font-size:0.85rem;margin:0;font-family:'DM Sans',sans-serif}
.alert-msg{color:#6b8299;font-size:0.75rem;margin:0}
.alert-time{color:#6b8299;font-size:0.7rem;margin-left:auto;white-space:nowrap}
div.stProgress>div>div{background:linear-gradient(90deg,#3b9eff,#00c8e0) !important}
.section-title{font-family:'Barlow',sans-serif;font-size:0.85rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#6b8299;margin-bottom:10px}

/* Task 3: Confidence Bar */
.confidence-bar-track { width: 100%; height: 8px; background: #1c2e47; border-radius: 4px; overflow: hidden; margin: 4px 0 2px; }
.confidence-bar-fill { height: 100%; border-radius: 4px; transition: width 0.4s ease, background 0.4s ease; }
.risk-info-panel { text-align: center; }
.risk-info-label { font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase; color: #6b8299; margin: 12px 0 2px; }
/* Fix text overflow on risk-component */
.risk-component { font-family: 'Barlow', sans-serif; font-size: clamp(0.9rem, 1.5vw, 1.3rem); font-weight: 700; margin: 0 0 4px; word-break: keep-all; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ttf-value { font-family: 'Barlow', sans-serif; font-size: 1.3rem; font-weight: 700; margin: 2px 0; }
.confidence-value { font-family: 'Barlow', sans-serif; font-size: 1rem; color: #dce8f5; margin: 0 0 8px; font-weight: 600; }

/* Task 4: AI Insights Chat & Card */
.insight-card { background: linear-gradient(135deg, #0f1623, #131d2e); border: 1px solid #1c2e47; border-left: 4px solid #3b9eff; border-radius: 12px; padding: 20px 24px; margin: 12px 0; }
.insight-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.insight-icon { font-size: 1.4rem; }
.insight-title { font-family: 'Barlow', sans-serif; font-size: 1rem; font-weight: 600; color: #3b9eff; }
.insight-body { font-family: 'DM Sans', sans-serif; font-size: 0.9rem; color: #dce8f5; line-height: 1.7; }
div[data-testid="stChatMessage"] { background: #0f1623 !important; border: 1px solid #1c2e47 !important; border-radius: 10px !important; margin-bottom: 8px !important; }
div[data-testid="stChatInput"] textarea { background: #131d2e !important; border: 1px solid #1c2e47 !important; color: #dce8f5 !important; font-family: 'DM Sans', sans-serif !important; }


</style>""", unsafe_allow_html=True)

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700;800&family=DM+Sans:wght@400;500;600;700&display=swap');
:root{
  --hvac-bg:#07131f; --hvac-panel:#0d1b2b; --hvac-panel-2:#102236;
  --hvac-border:#20364d; --hvac-muted:#93a9bd; --hvac-text:#f3f7fb;
  --hvac-blue:#2f8df5; --hvac-green:#54d764; --hvac-yellow:#ffbc22;
  --hvac-orange:#ff7a18; --hvac-red:#ff4d4d; --hvac-purple:#9d65ff;
}
footer, #MainMenu, header[data-testid="stHeader"], .stDeployButton {display:none !important;}

.stApp {background:#07131f !important;color:var(--hvac-text);}
.block-container {max-width:100% !important;width:100% !important;padding:0 1rem 10px 1rem !important;margin-top:0 !important;}
div[data-testid="stToolbar"], [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"], div[data-testid="stDecoration"], div[data-testid="stStatusWidget"] {display:none !important; color: transparent !important; opacity: 0 !important;}
section[data-testid="stSidebar"] {
  background:#07131f !important;border-right:1px solid #1b324a !important;
  width:220px !important;min-width:200px !important;max-width:220px !important;
  visibility: visible !important;
  display: block !important;
  transform: none !important;
}
section[data-testid="stSidebar"] + div { margin-left: 0 !important; padding-left: 0 !important; }
.carrier-logo {
  width:112px;height:44px;border:1px solid #96b6ff;border-radius:50%;
  display:flex;align-items:center;justify-content:center;margin:22px auto 34px;
  background:radial-gradient(circle at 50% 45%,#2738a1 0%,#18216f 62%,#0d143d 100%);
  color:#fff;font:italic 25px Georgia,serif;box-shadow:0 0 0 2px #2d51ca inset,0 0 8px rgba(90,126,255,.7);
}
.sidebar-meta {padding:16px 20px 0;}
.sidebar-unit {width:200px;margin:18px auto 14px;display:block;filter:drop-shadow(0 10px 14px rgba(0,0,0,.45));}
.site-meta-label {font:700 12px 'DM Sans',sans-serif;color:white !important;margin:12px 0 3px !important;}
.site-meta-value {font:500 13px 'DM Sans',sans-serif;color:#5da1ff !important;margin:0 0 13px !important;}
.dashboard-shell {font-family:'DM Sans',sans-serif;color:var(--hvac-text);max-width:100%;margin:0 auto;}
.dashboard-shell * {box-sizing:border-box;}
.dashboard-shell h1,.dashboard-shell h2,.dashboard-shell h3,.dashboard-shell p {margin-top:0;}
.topbar {display:grid;grid-template-columns:1fr 500px;gap:22px;align-items:center;border-bottom:1px solid #183048;padding:0 0 15px;margin-bottom:14px;}
.title-main {font:800 28px/1.05 'Barlow',sans-serif !important;letter-spacing:.2px;margin:0 !important;color:white !important;}
.title-sub {font:600 16px/1.2 'DM Sans',sans-serif;margin:6px 0 0;color:#e8eef5;}
.top-actions {display:grid;grid-template-columns:142px 198px 150px;align-items:center;gap:16px;}
.status-block {border-right:1px solid #183048;padding-left:8px;}
.native-status {display:flex;align-items:center;gap:9px;justify-content:flex-end;padding-right:14px;min-height:50px;}
.native-title-main {font:800 28px/1.05 'Barlow',sans-serif !important;color:white !important;margin:0 !important;}
.native-title-sub {font:600 16px/1.2 'DM Sans',sans-serif !important;color:#e8eef5 !important;margin:6px 0 0 !important;}
.native-date {display:grid;grid-template-columns:30px 1fr;gap:10px;align-items:center;border-right:1px solid #183048;min-height:50px;color:white;}
.native-date strong {font:800 15px 'DM Sans',sans-serif;color:white;}
.native-date span {font:700 15px 'DM Sans',sans-serif;color:white;}
.date-block {display:grid;grid-template-columns:32px 1fr;gap:10px;align-items:center;color:white;border-right:1px solid #183048;}
.calendar-icon {font-size:24px;color:#cfd9e4;}
.date-line {font:600 15px 'DM Sans',sans-serif;}
.unit-select-fake {height:44px;border:1px solid #25415e;border-radius:9px;display:flex;align-items:center;justify-content:space-between;padding:0 16px;background:#0c1c2e;color:white;font:600 15px 'DM Sans',sans-serif;}
.rtu-control div[data-baseweb="select"] > div {background:#0c1c2e !important;border:1px solid #25415e !important;border-radius:9px !important;min-height:44px !important;}
.rtu-control div[data-baseweb="select"] span {color:white !important;font:700 15px 'DM Sans',sans-serif !important;}
.rtu-control label {display:none !important;}
.dashboard-link {color:#4d9cff !important;text-decoration:none !important;font:700 12px 'DM Sans',sans-serif;cursor:pointer;}
.dashboard-link:hover {color:#8fc1ff !important;text-decoration:underline !important;}
.native-topbar {max-width:100%;margin:0 auto 12px;display:block;}
/* KPI grid with responsive fallback */
.kpi-grid {display:grid;grid-template-columns:repeat(6,1fr);gap:9px;margin-bottom:12px;}
@media (max-width:1000px) { .kpi-grid {grid-template-columns:repeat(3,1fr);} }
.dash-card {background:linear-gradient(145deg,#102135,#0c1928);border:1px solid #20364d;border-radius:7px;box-shadow:0 0 0 1px rgba(255,255,255,.015) inset;}
.kpi-tile {height:126px;padding:15px 14px 9px;position:relative;overflow:hidden;}
.kpi-head {display:grid;grid-template-columns:54px 1fr;gap:11px;align-items:start;}
.kpi-icon {width:48px;height:48px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:25px;color:white;}
.kpi-name {font:800 13px/1.15 'Barlow',sans-serif;text-transform:uppercase;color:white;margin-top:3px;}
.kpi-number {font:800 31px/.95 'Barlow',sans-serif;color:white;letter-spacing:.2px;margin-top:9px;}
.kpi-unit2 {font:600 14px 'DM Sans',sans-serif;color:#dce6ef;margin-left:3px;}
.sparkline {position:absolute;left:14px;right:12px;bottom:13px;height:31px;}
.row-a {display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px;}
.panel {padding:14px 16px;}
.panel-title {font:800 16px/1.15 'Barlow',sans-serif !important;text-transform:uppercase;color:white !important;margin:0 0 11px !important;letter-spacing:.2px;}
.system-panel {min-height:314px;}
.risk-panel {min-height:314px;}
.metric-strip {display:grid;grid-template-columns:repeat(5,1fr);border:1px solid #1f354e;border-radius:7px;overflow:hidden;margin-top:7px;}
.metric-cell {min-height:58px;border-right:1px solid #1f354e;padding:10px 10px;background:#0b1827;}
.metric-cell:last-child {border-right:0;}
.metric-label {font:800 11px 'Barlow',sans-serif;text-transform:uppercase;color:#e6eff7;margin:0 0 5px;}
.metric-value {font:800 21px 'Barlow',sans-serif;color:white;margin:0;}
.risk-grid {display:grid;grid-template-columns:1fr 1.6fr;gap:14px;align-items:center;}
.risk-info {border-left:1px solid #1f354e;padding-left:18px;min-height:220px;overflow:hidden;}
.risk-label {font:800 13px 'Barlow',sans-serif;text-transform:uppercase;color:#d7e4ef;margin:0 0 8px;}
.risk-component-name {font:800 20px 'Barlow',sans-serif;text-transform:uppercase;color:var(--hvac-red);margin:0 0 20px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.risk-machine {float:right;font-size:54px;color:var(--hvac-red);opacity:.8;margin-top:-44px;}
.confidence-track {height:12px;border-radius:10px;background:#213446;overflow:hidden;margin:8px 0 8px;}
.confidence-fill {height:100%;background:linear-gradient(90deg,#44d25a,#5bd869);border-radius:10px;}
.confidence-row {display:flex;justify-content:space-between;align-items:center;color:white;font:700 14px 'DM Sans',sans-serif;}
.risk-separator {height:1px;background:#1f354e;margin:14px 0;}
.ttf {font:800 22px 'Barlow',sans-serif;color:#ffb31d;margin:0;}
/* Bug 5: Row-b ratio 4-2-2 for trend chart breathing room */
.row-b {display:grid;grid-template-columns:2fr 1fr 1fr;gap:10px;margin-bottom:12px;}
.trend-panel,.alerts-panel,.ai-panel {min-height:256px;overflow:hidden;}
.alerts-panel,.ai-panel {padding:14px;}
.alert-row {display:grid;grid-template-columns:31px 1fr 58px;gap:9px;padding:9px 0;border-top:1px solid #20364d;align-items:center;}
.alert-row:first-of-type {border-top:0;}
.alert-icon {font-size:27px;line-height:1;}
.alert-title2 {font:800 13px 'DM Sans',sans-serif;color:#ff6b5f;margin:0;}
.alert-msg2 {font:500 12px 'DM Sans',sans-serif;color:white;margin:2px 0 0;}
.alert-time2 {font:500 12px 'DM Sans',sans-serif;color:white;text-align:right;}
.view-link {font:600 12px 'DM Sans',sans-serif;color:#4d9cff;text-align:center;margin-top:5px;}
.ai-line {display:grid;grid-template-columns:18px 1fr;gap:10px;margin:16px 0;color:white;font:500 14px/1.45 'DM Sans',sans-serif;}
.ai-dot {width:12px;height:12px;border-radius:50%;display:block;margin-top:5px;}
.row-c {display:grid;grid-template-columns:1fr 1.75fr;gap:10px;}
.action-panel {min-height:148px;padding:13px 16px;}
.maintenance-panel {min-height:148px;padding:13px 16px;}
.action-line {display:flex;gap:9px;align-items:center;color:white;font:500 13px 'DM Sans',sans-serif;margin:7px 0;}
.check {width:18px;height:18px;border-radius:50%;background:#5bd869;color:white;display:inline-flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;}
.maint-grid {display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:7px;}
.maint-cell {min-height:82px;border:1px solid #20364d;border-radius:7px;background:#0d1b2b;display:grid;grid-template-columns:36px 1fr;align-items:center;padding:8px 8px;overflow:hidden;gap:8px;}
.maint-icon {font-size:26px;text-align:center;}
.maint-label {font:700 10px/1.2 'Barlow',sans-serif;color:white;text-transform:uppercase;margin:0;white-space:normal;word-wrap:break-word;}
.maint-value {font:800 15px/1.2 'Barlow',sans-serif;color:white;margin:2px 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.maint-sub {font:500 11px/1.2 'DM Sans',sans-serif;color:#a8bacb;margin:0;white-space:normal;word-wrap:break-word;}
.airflow-svg text {font-family:'Barlow',sans-serif;font-weight:800;}
@media (max-width:1200px){
  .kpi-grid,.row-a,.row-b,.row-c,.topbar {grid-template-columns:1fr;}
  .system-panel,.risk-panel,.trend-panel,.alerts-panel,.ai-panel,.action-panel,.maintenance-panel {height:auto;}
  .risk-grid {grid-template-columns:1fr;}
  .risk-info {border-left:0;border-top:1px solid #1f354e;padding-left:0;padding-top:14px;}
}
</style>""", unsafe_allow_html=True)


# ── Session State Init ──────────────────────────────────────────────────────
if "simulator" not in st.session_state: st.session_state.simulator = SensorSimulator(mode="auto")
if "alert_log" not in st.session_state: st.session_state.alert_log = collections.deque(maxlen=50)
if "session_start_time" not in st.session_state: st.session_state.session_start_time = datetime.datetime.now()
if "last_prediction" not in st.session_state: st.session_state.last_prediction = {"predicted_class": "Normal", "confidence": 0.0, "probabilities": {}}
if "active_page" not in st.session_state: st.session_state.active_page = "dashboard"
if "sim_interval" not in st.session_state: st.session_state.sim_interval = 2.0
if "streaming" not in st.session_state: st.session_state.streaming = False
if "selected_unit" not in st.session_state: st.session_state.selected_unit = "RTU-01"

try:
    page_param = st.query_params.get("page")
    if page_param in ["dashboard", "live_monitor", "predictions", "alerts", "training", "ai_insights", "history", "settings"]:
        st.session_state.active_page = page_param
except Exception:
    pass

def asset_data_uri(path, mime="image/png"):
    try:
        with open(path, "rb") as f:
            return f"data:{mime};base64,{base64.b64encode(f.read()).decode('ascii')}"
    except Exception:
        return ""

RTU_IMAGE_URI = asset_data_uri(os.path.join(ROOT, "static", "3dimage.png"))

# ── Active Nav CSS Injection ────────────────────────────────────────────────
nav_items = ["dashboard", "live_monitor", "predictions", "alerts", "history", "training", "ai_insights", "settings"]
active_idx = nav_items.index(st.session_state.active_page) + 1 if st.session_state.active_page in nav_items else 1
st.markdown(f"""
<style>
div[data-testid="stSidebar"] .stButton:nth-of-type({active_idx}) > button {{
    background: #174f99 !important;
    color: #dce8f5 !important;
    border-left: 3px solid rgba(59,158,255,0.6) !important;
    font-weight: 600 !important;
}}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="carrier-logo">Carrier</div>', unsafe_allow_html=True)

    def sidebar_nav(label, target):
        if st.button(label, use_container_width=True):
            st.session_state.active_page = target
            try:
                st.query_params["page"] = target
            except Exception:
                pass
            st.rerun()

    sidebar_nav("🏠 Dashboard", "dashboard")
    sidebar_nav("🕐 Live Monitor", "live_monitor")
    sidebar_nav("📊 Predictions", "predictions")
    sidebar_nav("🔔 Alerts", "alerts")
    sidebar_nav("📈 History", "history")
    sidebar_nav("📋 Reports", "training")
    sidebar_nav("🤖 AI Insights", "ai_insights")
    sidebar_nav("⚙️ Settings", "settings")

    st.markdown('<div style="height:30px"></div>', unsafe_allow_html=True)

    if RTU_IMAGE_URI:
        st.markdown(f'<img class="sidebar-unit" src="{RTU_IMAGE_URI}" alt="Rooftop unit">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-meta"><p class="site-meta-label">Site</p><p class="site-meta-value">Banquet Hall AC System</p><p class="site-meta-label">Location</p><p class="site-meta-value">Mumbai, India</p><p class="site-meta-label">Unit Type</p><p class="site-meta-value">Rooftop Unit (RTU)</p></div>', unsafe_allow_html=True)
# ── Header Banner ───────────────────────────────────────────────────────────
MODEL_PATH = os.path.join(ROOT, "model", "model.pkl")
model_exists = os.path.exists(MODEL_PATH)
status = ("online", "ONLINE") if model_exists else ("offline", "STANDBY")
now = datetime.datetime.now()
if st.session_state.active_page not in ["dashboard", "live_monitor"]:
    h1, h2, h3 = st.columns([4, 3, 2])
    with h1:
        st.markdown('<div><p class="header-title">ROOFTOP UNIT (RTU) DASHBOARD</p><p class="header-sub">AI Based Predictive Maintenance System</p></div>', unsafe_allow_html=True)
    with h2:
        badge_html = '<span class="online-badge"><span class="pulse-dot"></span>ONLINE</span>' if model_exists else '<span class="offline-badge">⚫ STANDBY</span>'
        st.markdown(f'<div style="display:flex;align-items:center;gap:12px;justify-content:flex-end;padding-top:6px">{badge_html}<span id="live-time-banner" style="color:#6b8299;font-family:DM Sans,sans-serif;font-size:0.85rem">{now.strftime("%d %b %Y")}&nbsp;&nbsp;{now.strftime("%I:%M:%S %p")}</span></div>', unsafe_allow_html=True)
    with h3:
        st.selectbox("Unit", ["RTU-01", "RTU-02", "RTU-03"], label_visibility="collapsed")
# ── KPI & SVG Helpers ────────────────────────────────────────────────────────
KPI_CONFIG = [
    ("Supply Air Temp", "supply_temp_C", "°C", COLORS["accent_cyan"], "🌡️"),
    ("Return Air Temp", "return_temp_C", "°C", COLORS["accent_green"], "🌡️"),
    ("Outdoor Temp", "outdoor_temp_C", "°C", COLORS["accent_yellow"], "☀️"),
    ("Filter Health", "filter_health", "%", COLORS["accent_green"], "🌀"),
    ("Fan Speed", "fan_speed_RPM", "RPM", COLORS["accent_blue"], "⚙️"),
    ("Power / Current", "compressor_current_A", "A", COLORS["accent_orange"], "⚡"),
]

def render_kpi_strip(reading, buffer_df):
    cols = st.columns(6)
    for i, (label, key, unit, color, icon) in enumerate(KPI_CONFIG):
        with cols[i]:
            val = reading.get(key, 0)
            if key == "filter_health":
                val_display = f"{val * 100:.0f}"
                c_color = COLORS["accent_red"] if val < 0.5 else color
            else:
                val_display = str(val)
                c_color = color
            st.markdown(f'<div class="kpi-card"><p class="kpi-label">{icon} {label}</p><p class="kpi-value" style="color:{c_color}">{val_display}<span class="kpi-unit"> {unit}</span></p></div>', unsafe_allow_html=True)
            hist = buffer_df[key].tolist()[-20:] if key in buffer_df.columns and len(buffer_df) > 0 else [0]
            if key == "filter_health": hist = [v*100 for v in hist]
            st.plotly_chart(plot_sparkline(hist, c_color), use_container_width=True, key=f"spark_{key}_{reading.get('tick')}")

def render_svg_diagram(predicted_class):
    fc = FAULT_COLORS.get(predicted_class, COLORS["accent_blue"])
    nb = COLORS["accent_blue"]
    filt_c = COLORS["accent_orange"] if predicted_class == "Filter_Clog" else nb
    coil_c = COLORS["accent_red"] if predicted_class in ("Compressor_Fault", "Refrigerant_Leak") else nb
    fan_c = COLORS["accent_red"] if predicted_class == "Fan_Fault" else nb
    wire_c = COLORS["accent_yellow"] if predicted_class == "Electrical_Issue" else nb
    damp_c = nb
    svg = f'''<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-height:200px">
    <defs><marker id="ah" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{wire_c}"/></marker></defs>
    <text x="30" y="20" fill="#6b8299" font-size="10" font-family="DM Sans">OUTDOOR AIR</text>
    <line x1="80" y1="80" x2="130" y2="80" stroke="{wire_c}" stroke-width="2" marker-end="url(#ah)"/>
    <rect x="130" y="55" width="90" height="55" rx="6" fill="#0f1623" stroke="{damp_c}" stroke-width="2"/>
    <text x="148" y="45" fill="#6b8299" font-size="9" font-family="DM Sans">MIXING DAMPER</text>
    <text x="155" y="87" fill="#dce8f5" font-size="11" font-family="Barlow">☰</text>
    <line x1="220" y1="80" x2="260" y2="80" stroke="{wire_c}" stroke-width="2" marker-end="url(#ah)"/>
    <rect x="260" y="55" width="80" height="55" rx="6" fill="#0f1623" stroke="{filt_c}" stroke-width="2"/>
    <text x="280" y="45" fill="#6b8299" font-size="9" font-family="DM Sans">FILTER</text>
    <text x="285" y="87" fill="#dce8f5" font-size="11" font-family="Barlow">▓▓▓</text>
    <line x1="340" y1="80" x2="380" y2="80" stroke="{wire_c}" stroke-width="2" marker-end="url(#ah)"/>
    <rect x="380" y="55" width="90" height="55" rx="6" fill="#0f1623" stroke="{coil_c}" stroke-width="2"/>
    <text x="390" y="45" fill="#6b8299" font-size="9" font-family="DM Sans">COOLING COIL</text>
    <text x="410" y="87" fill="#dce8f5" font-size="11" font-family="Barlow">❄️</text>
    <line x1="470" y1="80" x2="510" y2="80" stroke="{wire_c}" stroke-width="2" marker-end="url(#ah)"/>
    <rect x="510" y="55" width="90" height="55" rx="6" fill="#0f1623" stroke="{fan_c}" stroke-width="2"/>
    <text x="525" y="45" fill="#6b8299" font-size="9" font-family="DM Sans">SUPPLY FAN</text>
    <text x="542" y="87" fill="#dce8f5" font-size="11" font-family="Barlow">🌀</text>
    <line x1="600" y1="80" x2="670" y2="80" stroke="{wire_c}" stroke-width="2" marker-end="url(#ah)"/>
    <text x="630" y="70" fill="#6b8299" font-size="10" font-family="DM Sans">SUPPLY AIR</text>
    <text x="30" y="160" fill="#6b8299" font-size="10" font-family="DM Sans">RETURN AIR</text>
    <line x1="130" y1="150" x2="80" y2="150" stroke="{wire_c}" stroke-width="2" marker-end="url(#ah)"/>
    <line x1="130" y1="110" x2="130" y2="150" stroke="{wire_c}" stroke-width="1.5" stroke-dasharray="4"/>
    </svg>'''
    st.markdown(svg, unsafe_allow_html=True)

def _fmt(value, decimals=1):
    try:
        return f"{float(value):.{decimals}f}"
    except Exception:
        return "0.0"

def _clamp(value, low=0, high=100):
    return max(low, min(high, value))

def _sensor_risk_score(reading):
    checks = [
        (reading.get("compressor_current_A", 0), 14, 26, 1.0),
        (reading.get("supply_temp_C", 0), 14, 30, 0.9),
        (reading.get("discharge_pressure_psi", 0), 190, 330, 0.8),
        (reading.get("suction_pressure_psi", 55), 55, 25, 0.9),
        (reading.get("fan_speed_RPM", 1450), 1450, 750, 0.9),
        (reading.get("vibration_mm_s", 0), 0.25, 1.4, 0.85),
        (1 - float(reading.get("filter_health", 1)), 0.1, 0.7, 0.85),
        (5.0 - float(reading.get("airflow_rate", 5)), 0.0, 3.0, 0.7),
    ]
    scores = []
    for value, normal, severe, weight in checks:
        try:
            value = float(value)
            if severe >= normal:
                raw = (value - normal) / (severe - normal)
            else:
                raw = (normal - value) / (normal - severe)
            scores.append(_clamp(raw * 100, 0, 100) * weight)
        except Exception:
            continue
    return max(scores) if scores else 0

def _risk_state(reading, pred, alerts):
    predicted_class = pred.get("predicted_class", "Normal")
    probs = pred.get("probabilities", {}) or {}
    normal_prob = float(probs.get("Normal", 0.0) or 0.0)
    fault_prob = max([float(v or 0) for k, v in probs.items() if k != "Normal"] or [0.0])
    model_score = fault_prob * 100
    sensor_score = _sensor_risk_score(reading)
    alert_score = 0
    if alerts:
        severity_weights = {"critical": 80, "warning": 55, "info": 25}
        alert_score = max(severity_weights.get(a.get("severity"), 25) for a in alerts)
    if predicted_class == "Normal":
        risk_pct = int(round(max((1 - normal_prob) * 55, sensor_score, alert_score)))
    else:
        risk_pct = int(round(max(model_score * 0.72 + sensor_score * 0.28, sensor_score, alert_score)))
    risk_pct = int(_clamp(risk_pct, 0, 96 if predicted_class != "Normal" else 65))
    if risk_pct < 20:
        risk_label, risk_color = "NORMAL", "#54d764"
    elif risk_pct < 50:
        risk_label, risk_color = "LOW RISK", "#ffbc22"
    elif risk_pct < 75:
        risk_label, risk_color = "MEDIUM RISK", "#ffbc22"
    else:
        risk_label, risk_color = "HIGH RISK", "#ff4d4d"
    confidence_pct = int(round(_clamp(float(pred.get("confidence", 0.0) or 0) * 100, 0, 100)))
    return risk_pct, risk_label, risk_color, confidence_pct

def _render_native_topbar(title, subtitle, status_text="ONLINE"):
    st.markdown('<div class="native-topbar">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([5.8, 1.25, 1.65, 1.15], vertical_alignment="center")
    with c1:
        st.markdown(f'<h1 class="native-title-main">{title}</h1><p class="native-title-sub">{subtitle}</p>', unsafe_allow_html=True)
    with c2:
        badge = '<span class="online-badge"><span class="pulse-dot"></span>' + status_text + '</span>' if status_text == "ONLINE" else '<span class="offline-badge">⚫ ' + status_text + '</span>'
        st.markdown(f'<div class="native-status">{badge}</div>', unsafe_allow_html=True)
    with c3:
        current = datetime.datetime.now()
        st.markdown(f'<div class="native-date"><div class="calendar-icon">&#128197;</div><div id="live-time-native"><strong>{current.strftime("%d %b %Y")}</strong><br><span>{current.strftime("%I:%M:%S %p")}</span></div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="rtu-control">', unsafe_allow_html=True)
        st.selectbox("Unit", ["RTU-01", "RTU-02", "RTU-03"], key="selected_unit", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def _rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def _spark_svg(values, color, width=210, height=34):
    vals = [float(v) for v in values if v is not None] or [0]
    vals = vals[-36:]
    mn, mx = min(vals), max(vals)
    span = mx - mn if mx != mn else 1
    points = []
    for i, v in enumerate(vals):
        x = i * (width / max(1, len(vals) - 1))
        y = height - 3 - ((v - mn) / span) * (height - 8)
        points.append((x, y))
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    area = f"0,{height} {line} {width},{height}"
    r, g, b = _rgb(color)
    return f'<svg class="sparkline" viewBox="0 0 {width} {height}" preserveAspectRatio="none"><polygon points="{area}" fill="rgba({r},{g},{b},0.18)"/><polyline points="{line}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'

def _trend_svg(buffer_df, width=560, height=168, is_live=False):
    series = [
        ("supply_temp_C", "#2f8df5"),
        ("return_temp_C", "#54d764"),
        ("compressor_current_A", "#ff4d4d"),
        ("airflow_rate", "#ffae1a"),
    ]
    rows = []
    chart_left, chart_top, chart_w, chart_h = 42, 34, width - 58, height - 56
    for yv in [0, 25, 50, 75, 100]:
        y = chart_top + chart_h - (yv / 100) * chart_h
        rows.append(f'<line x1="{chart_left}" y1="{y:.1f}" x2="{chart_left+chart_w}" y2="{y:.1f}" stroke="#20364d" stroke-width="1"/><text x="8" y="{y+4:.1f}" fill="#dce8f5" font-size="11">{yv}</text>')
    if buffer_df.empty:
        vals_df = pd.DataFrame()
    else:
        vals_df = buffer_df.tail(52).copy()
    for col, color in series:
        if col not in vals_df:
            continue
        vals = vals_df[col].astype(float).tolist()
        mn, mx = min(vals), max(vals)
        span = mx - mn if mx != mn else 1
        pts = []
        for i, v in enumerate(vals):
            x = chart_left + i * (chart_w / max(1, len(vals) - 1))
            y = chart_top + chart_h - ((v - mn) / span) * chart_h
            pts.append(f"{x:.1f},{y:.1f}")
        rows.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"/>')
    legend = ''.join([
        '<line x1="10" y1="14" x2="24" y2="14" stroke="#2f8df5" stroke-width="3"/><text x="30" y="18" fill="white" font-size="11">Supply Air Temp (&deg;C)</text>',
        '<line x1="160" y1="14" x2="174" y2="14" stroke="#54d764" stroke-width="3"/><text x="180" y="18" fill="white" font-size="11">Return Air Temp (&deg;C)</text>',
        '<line x1="310" y1="14" x2="324" y2="14" stroke="#ff4d4d" stroke-width="3"/><text x="330" y="18" fill="white" font-size="11">Compressor Current (A)</text>',
        '<line x1="470" y1="14" x2="484" y2="14" stroke="#ffae1a" stroke-width="3"/><text x="490" y="18" fill="white" font-size="11">Airflow (CFM)</text>',
    ])
    # ── Real-time X-axis labels from actual data timestamps ──
    tick_labels = []
    tick_class = ""
    if is_live and not vals_df.empty and "timestamp_str" in vals_df.columns:
        ts_list = vals_df["timestamp_str"].tolist()
        n_ticks = 7
        step = max(1, (len(ts_list) - 1) // (n_ticks - 1))
        for i in range(n_ticks):
            idx = min(i * step, len(ts_list) - 1)
            raw = ts_list[idx]  # e.g. "09:15:32 AM"
            # Show HH:MM AM/PM only
            parts = raw.split(":")
            if len(parts) >= 2:
                short = parts[0] + ":" + parts[1] + " " + raw.split()[-1] if " " in raw else raw[:5]
            else:
                short = raw
            tick_labels.append(short)
    else:
        # Dashboard: generate 24h labels and tag for JS dynamic updating
        _now = datetime.datetime.now()
        tick_class = "trend-label-dash"
        for i in range(7):
            t = _now - datetime.timedelta(hours=24 - i * 4)
            tick_labels.append(t.strftime("%I:%M %p"))
    
    ticks = ''.join(f'<text x="{chart_left+i*(chart_w/6):.1f}" y="{height-5}" fill="#dce8f5" font-size="11" text-anchor="middle" class="{tick_class}">{label}</text>' for i, label in enumerate(tick_labels))
    return f'<svg viewBox="0 0 {width} {height}" style="width:100%;height:190px">{legend}{"".join(rows)}{ticks}</svg>'

def _gauge_svg(risk_pct, risk_label, risk_color):
    angle = math.radians(205 + (risk_pct / 100) * 130)
    nx = 135 + math.cos(angle) * 78
    ny = 150 + math.sin(angle) * 78
    return f'''
    <svg viewBox="0 0 270 215" style="width:100%;height:225px">
      <defs>
        <linearGradient id="riskGradient" x1="0%" x2="100%"><stop offset="0%" stop-color="#54d764"/><stop offset="50%" stop-color="#ffbc22"/><stop offset="100%" stop-color="#ff4d4d"/></linearGradient>
      </defs>
      <path d="M45 150 A92 92 0 0 1 225 150" fill="none" stroke="url(#riskGradient)" stroke-width="24" stroke-linecap="round"/>
      <line x1="135" y1="150" x2="{nx:.1f}" y2="{ny:.1f}" stroke="#9ab5d2" stroke-width="6" stroke-linecap="round"/>
      <circle cx="135" cy="150" r="7" fill="#9ab5d2"/>
      <text x="135" y="137" text-anchor="middle" fill="{risk_color}" font-family="Barlow" font-size="48" font-weight="800">{risk_pct}<tspan font-size="26">%</tspan></text>
      <text x="135" y="164" text-anchor="middle" fill="white" font-family="Barlow" font-size="16" font-weight="800">RISK LEVEL</text>
      <rect x="80" y="178" width="110" height="36" rx="18" fill="{risk_color}"/>
      <text x="135" y="202" text-anchor="middle" fill="white" font-family="Barlow" font-size="17" font-weight="800">{risk_label}</text>
    </svg>'''

def _airflow_svg(reading, predicted_class):
    fan_stroke = "#ff4d4d" if predicted_class == "Fan_Fault" else "#a6b6c7"
    filter_stroke = "#ff4d4d" if predicted_class == "Filter_Clog" else "#dce6ef"
    filter_fill = "#3e8f40" if predicted_class != "Filter_Clog" else "#f5a623"
    coil_stroke = "#2f8df5" if predicted_class not in ("Compressor_Fault", "Refrigerant_Leak") else "#ff4d4d"
    damper_stroke = "#ff4d4d" if predicted_class == "Control_Sensor_Fault" else "#d7dce2"
    wire_stroke = "#ff4d4d" if predicted_class == "Electrical_Issue" else "#8998a8"
    return f'''
    <svg class="airflow-svg" viewBox="0 0 650 164" style="width:100%;height:164px">
      <defs>
        <marker id="arr" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#2f8df5"/></marker>
        <linearGradient id="duct" x1="0" x2="1"><stop offset="0" stop-color="#304053" stop-opacity=".45"/><stop offset="1" stop-color="#60758a" stop-opacity=".28"/></linearGradient>
      </defs>
      <text x="18" y="42" fill="white" font-size="12">OUTDOOR</text><text x="30" y="57" fill="white" font-size="12">AIR</text>
      <text x="18" y="112" fill="white" font-size="12">RETURN</text><text x="36" y="127" fill="white" font-size="12">AIR</text>
      <text x="102" y="14" fill="white" font-size="12">MIXING DAMPER</text><text x="250" y="14" fill="white" font-size="12">FILTER</text>
      <text x="354" y="14" fill="white" font-size="12">COOLING COIL</text><text x="486" y="14" fill="white" font-size="12">SUPPLY FAN</text>
      <line x1="70" y1="62" x2="125" y2="62" stroke="#2f8df5" stroke-width="3" marker-end="url(#arr)"/>
      <line x1="70" y1="124" x2="125" y2="124" stroke="#2f8df5" stroke-width="3" marker-end="url(#arr)"/>
      <path d="M118 31 H560 V92 H118 Z" fill="url(#duct)" stroke="{wire_stroke}" stroke-width="2"/>
      <path d="M118 92 H162 V141 H118 Z" fill="rgba(255,255,255,.08)" stroke="{wire_stroke}" stroke-width="2"/>
      <rect x="136" y="31" width="22" height="61" fill="rgba(255,255,255,.2)" stroke="{damper_stroke}" stroke-width="3"/><path d="M145 34 l-8 54 M156 36 l-10 55" stroke="{damper_stroke}" stroke-width="2"/>
      <path d="M132 97 l24 37 M158 97 l-27 39" stroke="{damper_stroke}" stroke-width="4"/>
      <line x1="82" y1="62" x2="100" y2="62" stroke="#2f8df5" stroke-width="3" marker-end="url(#arr)"/>
      <line x1="185" y1="62" x2="225" y2="62" stroke="#2f8df5" stroke-width="3" marker-end="url(#arr)"/>
      <rect x="230" y="28" width="48" height="69" fill="#1b2835" stroke="{filter_stroke}" stroke-width="4"/>
      <rect x="238" y="35" width="32" height="55" fill="{filter_fill}" stroke="#97d977"/><path d="M240 38 l27 48 M245 36 l24 43 M238 48 l24 40" stroke="#1c4f25" stroke-width="2"/>
      <line x1="278" y1="62" x2="326" y2="62" stroke="#2f8df5" stroke-width="3" marker-end="url(#arr)"/>
      <rect x="330" y="28" width="68" height="74" fill="#1b2835" stroke="#dce6ef" stroke-width="3"/>
      <rect x="338" y="36" width="52" height="58" fill="#123b65" stroke="{coil_stroke}" stroke-width="2"/>
      <path d="M343 48 q10 -12 20 0 t20 0 M343 63 q10 -12 20 0 t20 0 M343 78 q10 -12 20 0 t20 0" fill="none" stroke="#44aaff" stroke-width="2"/>
      <line x1="364" y1="102" x2="364" y2="128" stroke="#2f8df5" stroke-width="3"/><text x="379" y="130" fill="white" font-size="16">{_fmt(reading.get("supply_temp_C", 7.6), 1)} &deg;C</text>
      <rect x="455" y="26" width="78" height="78" fill="#27313c" stroke="#dce6ef" stroke-width="2"/>
      <circle cx="494" cy="65" r="29" fill="#8e939a" stroke="{fan_stroke}" stroke-width="4"/><circle cx="494" cy="65" r="9" fill="#2a2f36"/>
      <path d="M494 38 q14 16 3 24 q-14 -2 -3 -24 M521 67 q-17 13 -25 0 q7 -13 25 0 M491 92 q-13 -17 1 -25 q13 7 -1 25" fill="#d4d7dc"/>
      <path d="M533 48 h50 l24 18 l-24 18 h-50 z" fill="#225383" opacity=".72"/>
      <line x1="608" y1="67" x2="644" y2="67" stroke="#2f8df5" stroke-width="3" marker-end="url(#arr)"/>
      <text x="598" y="42" fill="white" font-size="12">SUPPLY</text><text x="611" y="58" fill="white" font-size="12">AIR</text>
    </svg>'''

# ── Page Renders ────────────────────────────────────────────────────────────

def _kpi_strip_html(reading, buffer_df):
    filter_color = "#54d764" if float(reading.get("filter_health", 1)) >= 0.5 else "#ff4d4d"
    kpis = [
        ("SUPPLY AIR TEMP", "supply_temp_C", "&deg;C", "#0f4b7a", "#2f8df5", "&#127777;", _fmt(reading.get("supply_temp_C", 0), 1)),
        ("RETURN AIR TEMP", "return_temp_C", "&deg;C", "#185f2d", "#54d764", "&#127777;", _fmt(reading.get("return_temp_C", 0), 1)),
        ("OUTDOOR TEMP", "outdoor_temp_C", "&deg;C", "#7c5a00", "#ffbc22", "&#9728;", _fmt(reading.get("outdoor_temp_C", 0), 1)),
        ("FILTER HEALTH", "filter_health", "%", "#185f2d", filter_color, "&#128260;", f'{float(reading.get("filter_health", 1)) * 100:.0f}'),
        ("FAN SPEED", "fan_speed_RPM", "RPM", "#392178", "#a35cff", "&#10033;", str(int(float(reading.get("fan_speed_RPM", 0))))),
        ("POWER CONSUMPTION", "compressor_current_A", "kW", "#9a4307", "#ff7a18", "&#9889;", _fmt(float(reading.get("compressor_current_A", 10)) * 1.0, 1)),
    ]
    html = ""
    for label, key, unit, bg, color, icon, value in kpis:
        hist = buffer_df[key].tolist() if key in buffer_df.columns else [0]
        if key == "filter_health":
            hist = [float(v) * 100 for v in hist]
        html += f'''<div class="dash-card kpi-tile"><div class="kpi-head"><div class="kpi-icon" style="background:{bg}">{icon}</div><div><div class="kpi-name">{label}</div><div class="kpi-number">{value}<span class="kpi-unit2"> {unit}</span></div></div></div>{_spark_svg(hist, color)}</div>'''
    return html
def render_dashboard_content():
    sim = st.session_state.simulator
    reading = sim.next_reading()
    buffer_df = sim.get_buffer(120)

    if model_exists:
        try:
            feat = {k: v for k, v in reading.items() if k not in ("fault", "timestamp_str", "tick")}
            st.session_state.last_prediction = predict_fault(feat)
        except Exception:
            pass

    pred = st.session_state.last_prediction
    predicted_class = pred.get("predicted_class", "Normal")

    alerts = evaluate_alerts(reading)
    for a in alerts:
        st.session_state.alert_log.append(a)

    risk_pct, risk_label, risk_color, confidence_pct = _risk_state(reading, pred, alerts)
    ttf = "--" if risk_pct == 0 else "7 - 14 Days" if risk_pct < 50 else "3 - 7 Days" if risk_pct < 70 else "2 - 3 Days" if risk_pct < 85 else "1 - 2 Days"
    kpi_html = _kpi_strip_html(reading, buffer_df)

    mixed = (float(reading.get("outdoor_temp_C", 0)) + float(reading.get("return_temp_C", 0))) / 2
    coil_in = float(reading.get("return_temp_C", 0)) * 0.6 + float(reading.get("outdoor_temp_C", 0)) * 0.4
    supply = float(reading.get("supply_temp_C", 0))
    damper = float(reading.get("damper_position_%", 0))
    metrics_html = ''.join([
        f'<div class="metric-cell"><p class="metric-label">MIXED AIR TEMP</p><p class="metric-value">{mixed:.1f}<span class="kpi-unit2"> &deg;C</span></p></div>',
        f'<div class="metric-cell"><p class="metric-label">COIL INLET TEMP</p><p class="metric-value">{coil_in:.1f}<span class="kpi-unit2"> &deg;C</span></p></div>',
        f'<div class="metric-cell"><p class="metric-label">COIL OUTLET TEMP</p><p class="metric-value">{supply:.1f}<span class="kpi-unit2"> &deg;C</span></p></div>',
        '<div class="metric-cell"><p class="metric-label">HUMIDITY</p><p class="metric-value">48<span class="kpi-unit2"> %RH</span></p></div>',
        f'<div class="metric-cell"><p class="metric-label">DAMPER POSITION</p><p class="metric-value" style="color:#54d764">{damper:.0f}<span class="kpi-unit2"> %</span></p></div>',
    ])

    recent_alerts = list(st.session_state.alert_log)[-3:]
    if not recent_alerts:
        recent_alerts = [
            {"label":"High Compressor Current", "message":"Current is above normal range", "timestamp":"10:30 AM", "severity":"critical"},
            {"label":"High Discharge Temperature", "message":"Discharge temp is high", "timestamp":"10:28 AM", "severity":"warning"},
            {"label":"Airflow Dropping", "message":"Possible filter clogging", "timestamp":"10:25 AM", "severity":"warning"},
        ]
    alerts_html = ""
    for a in reversed(recent_alerts[:3]):
        icon = "&#9888;" if a.get("severity") != "critical" else "&#9940;"
        alerts_html += f'<div class="alert-row"><div class="alert-icon" style="color:#ff7a18">{icon}</div><div><p class="alert-title2">{a.get("label", "Alert")}</p><p class="alert-msg2">{a.get("message", "")}</p></div><div class="alert-time2">{a.get("timestamp", "")}</div></div>'

    explanations = AI_EXPLANATIONS.get(predicted_class, AI_EXPLANATIONS["Normal"])
    ai_html = ""
    for color, text in explanations[:3]:
        ai_html += f'<div class="ai-line"><span class="ai-dot" style="background:{color}"></span><span>{text}</span></div>'

    actions = RECOMMENDED_ACTIONS.get(predicted_class, RECOMMENDED_ACTIONS["Normal"])
    actions_html = ''.join(f'<div class="action-line"><span class="check">&#10003;</span><span>{act}</span></div>' for act in actions[:4])
    component = FAULT_COMPONENT.get(predicted_class, predicted_class.replace("_", " "))
    uptime_delta = datetime.datetime.now() - st.session_state.session_start_time
    uptime_pct = min(99.9, 98.6 + uptime_delta.total_seconds() / 360000)
    alert_count = len(st.session_state.alert_log)
    # ── Dynamic maintenance dates (14-day cycle) ──
    now_dt = datetime.datetime.now()
    _last_maint = now_dt - datetime.timedelta(days=7)
    _next_maint = now_dt + datetime.timedelta(days=7)
    last_maint_str = _last_maint.strftime("%d %b %Y")
    next_maint_str = _next_maint.strftime("%d %b %Y")
    last_maint_ago_str = "7 Days Ago"
    next_maint_in_str = "In 7 Days"
    trend = _trend_svg(buffer_df)
    airflow = _airflow_svg(reading, predicted_class)
    gauge = _gauge_svg(risk_pct, risk_label, risk_color)
    date_line = now.strftime("%d %b %Y") + "<br>" + now.strftime("%I:%M:%S %p")
    selected_unit = st.session_state.get("selected_unit", "RTU-01")
    view_alerts_href = "?page=alerts"
    view_report_href = "?page=history"
    _render_native_topbar("ROOFTOP UNIT (RTU) DASHBOARD", "AI Based Predictive Maintenance System")

    st.markdown(f'''
    <div class="dashboard-shell">
      <div class="kpi-grid">{kpi_html}</div>
      <div class="row-a">
        <div class="dash-card panel system-panel"><h2 class="panel-title">SYSTEM OVERVIEW</h2>{airflow}<div class="metric-strip">{metrics_html}</div></div>
        <div class="dash-card panel risk-panel"><h2 class="panel-title">FAILURE RISK</h2><div class="risk-grid"><div>{gauge}</div><div class="risk-info" style="overflow:hidden"><p class="risk-label">PREDICTED COMPONENT</p><div class="risk-machine">&#128308;</div><h3 class="risk-component-name" style="word-break:keep-all;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:clamp(0.9rem,1.5vw,1.3rem)">{component}</h3><p class="risk-label">PREDICTION CONFIDENCE</p><div class="confidence-row"><div class="confidence-track" style="flex:1"><div class="confidence-fill" style="width:{confidence_pct}%"></div></div><span style="margin-left:12px">{confidence_pct}%</span></div><div class="risk-separator"></div><p class="risk-label">TIME TO FAILURE (EST.)</p><p class="ttf">{ttf}</p></div></div></div>
      </div>
      <div class="row-b">
        <div class="dash-card panel trend-panel"><h2 class="panel-title">PARAMETER TRENDS <span style="font-weight:500;text-transform:none">(Last 24 Hours)</span></h2>{trend}</div>
        <div class="dash-card alerts-panel"><h2 class="panel-title">ACTIVE ALERTS</h2>{alerts_html}<div class="view-link"><a class="dashboard-link" href="{view_alerts_href}" target="_self">View All Alerts&nbsp; &#8594;</a></div></div>
        <div class="dash-card ai-panel"><h2 class="panel-title">AI EXPLANATION</h2>{ai_html}</div>
      </div>
      <div class="row-c">
        <div class="dash-card action-panel"><h2 class="panel-title">RECOMMENDED ACTION</h2>{actions_html}</div>
        <div class="dash-card maintenance-panel"><h2 class="panel-title">MAINTENANCE SUMMARY</h2><div class="maint-grid"><div class="maint-cell"><div class="maint-icon" style="color:#2f8df5">&#128197;</div><div><p class="maint-label">LAST MAINTENANCE</p><p class="maint-value">{last_maint_str}</p><p class="maint-sub">{last_maint_ago_str}</p></div></div><div class="maint-cell"><div class="maint-icon" style="color:#54d764">&#9716;</div><div><p class="maint-label">NEXT MAINTENANCE</p><p class="maint-value">{next_maint_str}</p><p class="maint-sub">{next_maint_in_str}</p></div></div><div class="maint-cell"><div class="maint-icon" style="color:#ff7a18">&#128295;</div><div><p class="maint-label">TOTAL ALERTS (30 DAYS)</p><p class="maint-value">{alert_count}</p><p class="maint-sub"><a class="dashboard-link" href="{view_report_href}" target="_self">View Report</a></p></div></div><div class="maint-cell"><div class="maint-icon" style="color:#9d65ff">&#128200;</div><div><p class="maint-label">SYSTEM UPTIME</p><p class="maint-value">{uptime_pct:.1f} %</p><p class="maint-sub" style="color:#54d764">Excellent</p></div></div></div></div>
      </div>
    </div>
    ''', unsafe_allow_html=True)
def render_live_monitor_content():
    sim = st.session_state.simulator
    reading = sim.next_reading()
    buffer_df = sim.get_buffer(140)

    rows_html = ""
    last_rows = sim.get_buffer(12)
    if not last_rows.empty:
        cols = ["timestamp_str", "fault", "supply_temp_C", "return_temp_C", "filter_health", "fan_speed_RPM", "compressor_current_A", "damper_position_%"]
        cols = [c for c in cols if c in last_rows.columns]
        for _, row in last_rows.tail(10).iloc[::-1].iterrows():
            fault = row.get("fault", "Normal")
            fc = FAULT_COLORS.get(fault, "#54d764")
            cells = ""
            for c in cols:
                val = row[c]
                if c == "filter_health":
                    try: val = f"{float(val) * 100:.0f}%"
                    except Exception: pass
                color = fc if c == "fault" else "#f3f7fb"
                cells += f'<td style="padding:9px 10px;color:{color};border-bottom:1px solid #20364d;font:600 12px DM Sans,sans-serif;white-space:nowrap">{val}</td>'
            rows_html += f"<tr>{cells}</tr>"
        headers = ''.join(f'<th style="padding:10px;color:#93a9bd;text-align:left;border-bottom:1px solid #20364d;font:800 11px Barlow,sans-serif;text-transform:uppercase">{c.replace("_", " ")}</th>' for c in cols)
        table_html = f'<table style="width:100%;border-collapse:collapse"><thead><tr>{headers}</tr></thead><tbody>{rows_html}</tbody></table>'
    else:
        table_html = '<div style="color:#93a9bd;font:600 14px DM Sans,sans-serif;padding:20px">Collecting live readings...</div>'

    trend = _trend_svg(buffer_df, width=760, height=210, is_live=True)
    filter_pct = float(reading.get("filter_health", 1)) * 100
    airflow = _airflow_svg(reading, reading.get("fault", "Normal"))
    _render_native_topbar("LIVE MONITOR", "Real-time RTU sensor stream and component health", "ONLINE" if st.session_state.streaming else "PAUSED")

    st.markdown(f'''
    <div class="dashboard-shell">
      <div class="kpi-grid">{_kpi_strip_html(reading, buffer_df)}</div>
      <div class="row-a">
        <div class="dash-card panel system-panel"><h2 class="panel-title">AIRFLOW AND COMPONENT STATUS</h2>{airflow}<div class="metric-strip"><div class="metric-cell"><p class="metric-label">FILTER HEALTH</p><p class="metric-value" style="color:{'#54d764' if filter_pct >= 50 else '#ff4d4d'}">{filter_pct:.0f}<span class="kpi-unit2"> %</span></p></div><div class="metric-cell"><p class="metric-label">AIRFLOW</p><p class="metric-value">{float(reading.get('airflow_rate', 0)) * 840:.0f}<span class="kpi-unit2"> CFM</span></p></div><div class="metric-cell"><p class="metric-label">FAN SPEED</p><p class="metric-value">{float(reading.get('fan_speed_RPM', 0)):.0f}<span class="kpi-unit2"> RPM</span></p></div><div class="metric-cell"><p class="metric-label">VIBRATION</p><p class="metric-value">{float(reading.get('vibration_mm_s', 0)):.2f}</p></div><div class="metric-cell"><p class="metric-label">DAMPER</p><p class="metric-value">{float(reading.get('damper_position_%', 0)):.0f}<span class="kpi-unit2"> %</span></p></div></div></div>
        <div class="dash-card panel system-panel"><h2 class="panel-title">LIVE PARAMETER TRENDS</h2>{trend}</div>
      </div>
      <div class="dash-card panel" style="min-height:260px;overflow:auto"><h2 class="panel-title">RECENT READINGS</h2>{table_html}</div>
    </div>
    ''', unsafe_allow_html=True)
def render_predictions():
    st.markdown("## 🔮 Predictions")
    if not model_exists:
        st.warning("⚠️ No trained model found. Please train the model first.")
        return

    st.markdown("#### 📡 Sensor Input Panel")
    feature_names = get_feature_names()
    input_data = {}
    cols = st.columns(3)
    for i, feat in enumerate(feature_names):
        with cols[i % 3]:
            lo, hi = FEATURE_RANGES.get(feat, (0.0, 100.0))
            default = round((lo + hi) / 2, 2)
            step = round((hi - lo) / 100, 4) if (hi - lo) > 0 else 0.1
            label = feat.replace("_", " ").title()
            input_data[feat] = st.number_input(label, min_value=float(lo), max_value=float(hi), value=float(default), step=float(step), key=f"pred_{feat}")

    is_valid, warnings = validate_input(input_data)
    for w in warnings:
        st.warning(f"⚠️ {w}")

    if st.button("⚡ Predict Fault", type="primary"):
        clear_model_cache()
        with st.spinner("Running prediction..."):
            result = predict_fault(input_data)
        pred_class = result["predicted_class"]
        confidence = result["confidence"]
        color = FAULT_COLORS.get(pred_class, COLORS["accent_blue"])
        st.markdown("---")
        pc1, pc2 = st.columns(2)
        with pc1:
            risk = "HIGH RISK" if pred_class != "Normal" else "LOW RISK"
            rc = COLORS["accent_red"] if pred_class != "Normal" else COLORS["accent_green"]
            st.markdown(f'<div class="card" style="text-align:center"><p class="kpi-label">PREDICTED FAULT</p><h2 style="color:{color};font-family:Barlow;font-size:2rem">{pred_class}</h2><p class="kpi-label">Confidence</p><h3 style="color:{color};font-family:Barlow">{confidence*100:.1f}%</h3><br><span style="display:inline-block;padding:4px 14px;border-radius:20px;font-size:0.85rem;font-weight:700;font-family:Barlow,sans-serif;letter-spacing:0.08em;background:rgba({",".join(str(int(rc[i:i+2],16)) for i in (1,3,5))},0.15);color:{rc};border:1px solid {rc}">{risk}</span></div>', unsafe_allow_html=True)
        with pc2:
            st.plotly_chart(plot_probability_chart(result["probabilities"]), use_container_width=True)
        log_prediction({"predicted_class": pred_class, "confidence": confidence, "input_features": input_data})

def render_alerts():
    st.markdown("## 🔔 Alerts")
    alert_log = list(st.session_state.alert_log)
    active = [a for a in alert_log if not a.get("resolved")]
    resolved = [a for a in alert_log if a.get("resolved")]

    st.markdown(f'<div class="card" style="display:flex;justify-content:space-between;align-items:center"><span style="color:#dce8f5;font-family:Barlow;font-weight:700;font-size:1.2rem">{len(active)} Active Alerts</span></div>', unsafe_allow_html=True)

    filt = st.radio("Filter", ["All", "Critical", "Warning", "Info"], horizontal=True, key="alert_filt")
    if filt != "All":
        active = [a for a in active if a["severity"] == filt.lower()]

    if not active:
        st.markdown('<div class="card" style="text-align:center;color:#22d46b">✅ No active alerts</div>', unsafe_allow_html=True)
    else:
        for i, a in enumerate(reversed(active)):
            icon = SEVERITY_ICONS.get(a["severity"], "⚠️")
            c1, c2, c3 = st.columns([6, 2, 1])
            with c1:
                st.markdown(f'{icon} **{a["label"]}** — {a["message"]}', unsafe_allow_html=False)
            with c2:
                st.caption(a.get("timestamp", ""))
            with c3:
                if st.button("Ack", key=f"ack_{i}_{a['id']}"):
                    for item in st.session_state.alert_log:
                        if item["id"] == a["id"] and item.get("timestamp") == a.get("timestamp"):
                            item["resolved"] = True
                    st.rerun()

    if resolved:
        st.markdown("---")
        st.markdown('<p class="section-title">RESOLVED ALERTS</p>', unsafe_allow_html=True)
        for a in reversed(resolved[-10:]):
            st.caption(f"✅ {a['label']} — {a['message']} ({a.get('timestamp','')})")

def render_training():
    st.markdown("## 🏋️ Model Training")
    DATA_PATH = os.path.join(ROOT, "data", "hvac_synthetic_dataset.csv")

    history = get_metrics_history()
    if not history.empty:
        last = history.iloc[-1]
        st.markdown(f'<div class="card"><p class="kpi-label">TRAINING STATUS</p><p style="color:#22d46b;font-family:Barlow;font-size:1.1rem;font-weight:600">Last trained: {last["timestamp"]} | Test Accuracy: {last["test_accuracy"]*100:.2f}%</p></div>', unsafe_allow_html=True)

    st.markdown("#### ⚙️ Hyperparameter Configuration")
    hc1, hc2, hc3, hc4 = st.columns(4)
    n_est = hc1.slider("n_estimators", 50, 300, DEFAULT_HYPERPARAMS["n_estimators"], key="hp_nest")
    lr = hc2.slider("learning_rate", 0.01, 0.3, DEFAULT_HYPERPARAMS["learning_rate"], step=0.01, key="hp_lr")
    md = hc3.slider("max_depth", 3, 10, DEFAULT_HYPERPARAMS["max_depth"], key="hp_md")
    with hc4:
        st.metric("Eval Metric", DEFAULT_HYPERPARAMS["eval_metric"])
        if st.button("Reset Defaults", key="hp_reset"):
            st.rerun()

    st.markdown("#### 📊 Data Split")
    s1, s2, s3 = st.columns(3)
    s1.markdown('<div class="card"><h3 style="color:#22d46b;margin:0;font-family:Barlow">80%</h3><p style="color:#6b8299;margin:0;font-family:DM Sans">Training Set</p></div>', unsafe_allow_html=True)
    s2.markdown('<div class="card"><h3 style="color:#3b9eff;margin:0;font-family:Barlow">10%</h3><p style="color:#6b8299;margin:0;font-family:DM Sans">Validation Set</p></div>', unsafe_allow_html=True)
    s3.markdown('<div class="card"><h3 style="color:#f5a623;margin:0;font-family:Barlow">10%</h3><p style="color:#6b8299;margin:0;font-family:DM Sans">Test Set</p></div>', unsafe_allow_html=True)

    if st.button("🚀 Train Model", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        def update_progress(pct, msg):
            progress_bar.progress(pct)
            status_text.info(f"⏳ {msg}")
        with st.spinner("Training in progress..."):
            custom_params = {"n_estimators": n_est, "learning_rate": lr, "max_depth": md, "eval_metric": DEFAULT_HYPERPARAMS["eval_metric"], "random_state": 42}
            metrics = train_model(DATA_PATH, progress_callback=update_progress, hyperparams=custom_params)
        status_text.success("✅ Training complete!")
        st.session_state["last_metrics"] = metrics

    if "last_metrics" in st.session_state:
        metrics = st.session_state["last_metrics"]
        st.markdown("#### 🎯 Results")
        a1, a2, a3, a4 = st.columns(4)
        a1.metric("Train Accuracy", f"{metrics['train_accuracy']*100:.2f}%")
        a2.metric("Val Accuracy", f"{metrics['val_accuracy']*100:.2f}%")
        a3.metric("Test Accuracy", f"{metrics['test_accuracy']*100:.2f}%")
        a4.metric("Duration", f"{metrics['duration_seconds']:.1f}s")
        st.plotly_chart(plot_accuracy_comparison(metrics['train_accuracy'], metrics['val_accuracy'], metrics['test_accuracy']), use_container_width=True)
        r1, r2 = st.columns(2)
        with r1:
            st.plotly_chart(plot_confusion_matrix(metrics["confusion_matrix"], metrics["class_names"]), use_container_width=True)
        with r2:
            st.markdown("#### 📋 Classification Report")
            report = metrics["classification_report"]
            rows = []
            for cls in metrics["class_names"]:
                if cls in report:
                    r = report[cls]
                    rows.append({"Class": cls, "Precision": f"{r['precision']:.3f}", "Recall": f"{r['recall']:.3f}", "F1": f"{r['f1-score']:.3f}", "Support": int(r['support'])})
            if "accuracy" in report:
                rows.append({"Class": "Accuracy", "Precision": "", "Recall": "", "F1": f"{report['accuracy']:.3f}", "Support": ""})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

def render_ai_insights():
    st.markdown("## 🔍 AI Insights")
    
    # ── Section 1: Charts ─────────────────────────────────
    col_fi, col_hm = st.columns(2)
    with col_fi:
        if model_exists:
            model = load_model()[0]
            importances = dict(zip(get_feature_names(), model.feature_importances_))
            st.plotly_chart(plot_feature_importance(importances), use_container_width=True)
        else:
            st.info("Train the model first to see feature importances.")
    
    with col_hm:
        buffer_df = st.session_state.simulator.get_buffer(200)
        if len(buffer_df) >= 10:
            st.plotly_chart(plot_correlation_heatmap(buffer_df), use_container_width=True)
        else:
            st.info("Collecting sensor data for correlation analysis...")
    
    # ── Section 2: Real-Time Grok Insight ─────────────────
    st.markdown("---")
    st.markdown("### 🤖 Real-Time AI Analysis")
    
    reading  = st.session_state.get("last_reading", {})
    if not reading: reading = st.session_state.simulator.next_reading()
    pred     = st.session_state.get("last_prediction", {"predicted_class": "Normal", "confidence": 0.0, "probabilities": {}})
    
    refresh_col, _ = st.columns([1, 4])
    with refresh_col:
        refresh_clicked = st.button("🔄 Refresh Analysis", key="refresh_insight")
    
    # Auto-generate on first load OR on refresh click
    from utils.grok_client import get_initial_insight, stream_chat_response, build_sensor_context
    if "grok_insight" not in st.session_state or refresh_clicked:
        if reading:
            with st.spinner("Analyzing sensor data with Grok AI..."):
                st.session_state.grok_insight = get_initial_insight(reading, pred)
                # Reset chat history when insight refreshes
                st.session_state.chat_history = []
        else:
            st.session_state.grok_insight = "Start the simulator to generate live sensor data for analysis."
    
    # Display insight in styled card
    st.markdown(f"""
    <div class="insight-card">
        <div class="insight-header">
            <span class="insight-icon">🔬</span>
            <span class="insight-title">Live Analysis — {pred.get('predicted_class','Normal')} 
            ({pred.get('confidence',0)*100:.0f}% confidence)</span>
        </div>
        <div class="insight-body">{st.session_state.get('grok_insight','').replace(chr(10),'<br>')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # ── Section 3: Chat Interface ──────────────────────────
    st.markdown("---")
    st.markdown("### 💬 Chat with AI Analyst")
    st.caption("Ask follow-up questions about the failure risk, sensor readings, or maintenance recommendations.")
    
    # Initialize chat history with the insight as the first assistant message
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Render chat history
    chat_container = st.container(height=380)
    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
                st.markdown(msg["content"])
    
    # Suggested quick questions (shown when chat is empty)
    if not st.session_state.chat_history:
        st.markdown("**Quick questions:**")
        q_col1, q_col2, q_col3 = st.columns(3)
        quick_qs = [
            ("🔧 What parts should I inspect first?", q_col1),
            ("📅 How urgent is this fault?", q_col2),
            ("💰 What's the repair cost estimate?", q_col3),
        ]
        for question, col in quick_qs:
            with col:
                if st.button(question, key=f"quick_{question[:20]}"):
                    st.session_state.pending_question = question
                    st.rerun()
    
    # Chat input
    user_input = st.chat_input("Ask the AI analyst anything about this fault...")
    
    # Handle pending quick question OR typed input
    if "pending_question" in st.session_state:
        user_input = st.session_state.pop("pending_question")
    
    if user_input:
        # Add context message if this is the first question
        if not st.session_state.chat_history:
            context_msg = {
                "role": "user",
                "content": f"Context: {build_sensor_context(reading, pred)}\n\nMy question: {user_input}"
            }
        else:
            context_msg = {"role": "user", "content": user_input}
        
        # Append user message to display history (without context prefix for display)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Build full message list for API (with context only on first message)
        api_messages = []
        for i, msg in enumerate(st.session_state.chat_history[:-1]):
            api_messages.append(msg)
        api_messages.append(context_msg)
        
        # Stream assistant response
        with chat_container:
            with st.chat_message("assistant", avatar="🤖"):
                response_placeholder = st.empty()
                full_response = ""
                for chunk in stream_chat_response(api_messages):
                    full_response += chunk
                    response_placeholder.markdown(full_response + "▌")
                response_placeholder.markdown(full_response)
        
        st.session_state.chat_history.append({"role": "assistant", "content": full_response})
        st.rerun()

def render_history():
    st.markdown("## 📈 History")
    history = get_metrics_history()

    st.markdown("### Training Run History")
    if history.empty:
        st.info("ℹ️ No training runs recorded yet.")
    else:
        st.markdown(f"**{len(history)} training run(s) recorded**")
        st.plotly_chart(plot_metrics_history(history), use_container_width=True)
        m1, m2, m3 = st.columns(3)
        best = history.loc[history["test_accuracy"].idxmax()]
        m1.metric("Best Test Accuracy", f"{best['test_accuracy']*100:.2f}%")
        m2.metric("Latest Run", history.iloc[-1]["timestamp"])
        m3.metric("Avg Duration", f"{history['duration_seconds'].mean():.1f}s")
        display_df = history[["id","timestamp","train_accuracy","val_accuracy","test_accuracy","duration_seconds"]].copy()
        display_df.columns = ["Run","Timestamp","Train Acc","Val Acc","Test Acc","Duration (s)"]
        for col in ["Train Acc","Val Acc","Test Acc"]:
            display_df[col] = (display_df[col]*100).round(2).astype(str) + "%"
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### Recent Predictions")
    pred_log_path = os.path.join(ROOT, "prediction_log.json")
    if os.path.exists(pred_log_path):
        try:
            with open(pred_log_path, "r") as f:
                preds = json.load(f)
            if isinstance(preds, list) and preds:
                rows = []
                for p in preds[-20:]:
                    rows.append({"Timestamp": p.get("timestamp",""), "Predicted": p.get("predicted_class",""), "Confidence": p.get("confidence",0)})
                pdf = pd.DataFrame(rows)
                html_rows = ""
                for _, row in pdf.iterrows():
                    fc = FAULT_COLORS.get(row["Predicted"], COLORS["accent_blue"])
                    conf = float(row["Confidence"]) if row["Confidence"] else 0
                    conf_pct = int(conf * 100)
                    html_rows += f'<tr style="border-bottom:1px solid #1c2e47"><td style="padding:6px 10px;color:#6b8299;font-size:0.8rem">{row["Timestamp"]}</td><td style="padding:6px 10px;color:{fc};font-weight:600;font-family:Barlow">{row["Predicted"]}</td><td style="padding:6px 10px"><div style="background:#131d2e;border-radius:4px;height:16px;width:100%"><div style="background:{fc};height:100%;width:{conf_pct}%;border-radius:4px;font-size:0.65rem;color:white;text-align:center;line-height:16px">{conf_pct}%</div></div></td></tr>'
                st.markdown(f'<div style="border:1px solid #1c2e47;border-radius:8px;background:#0f1623;overflow:hidden"><table style="width:100%;border-collapse:collapse"><thead><tr><th style="padding:6px 10px;color:#6b8299;font-size:0.7rem;text-transform:uppercase;text-align:left">Timestamp</th><th style="padding:6px 10px;color:#6b8299;font-size:0.7rem;text-transform:uppercase;text-align:left">Predicted Class</th><th style="padding:6px 10px;color:#6b8299;font-size:0.7rem;text-transform:uppercase;text-align:left">Confidence</th></tr></thead><tbody>{html_rows}</tbody></table></div>', unsafe_allow_html=True)
            else:
                st.info("No predictions logged yet.")
        except Exception:
            st.info("No predictions logged yet.")
    else:
        st.info("No prediction log file found.")

def render_settings():
    st.markdown("## ⚙️ Settings")
    st.markdown(
        '<div class="card"><p class="section-title">SIMULATOR CONTROLS</p>'
        '<p style="color:#dce8f5;font-family:DM Sans">Configure the data simulator mode, stream interval, and manual fault injection.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("### Simulator Settings")
    sim_mode = st.radio("Mode", ["Auto", "Normal", "Inject Fault"], horizontal=True, key="sim_mode")
    mode_map = {"Auto": "auto", "Normal": "normal", "Inject Fault": "manual"}
    st.session_state.simulator.mode = mode_map[sim_mode]

    if sim_mode == "Inject Fault":
        fault_submode = st.radio("Fault Selection", ["Random Faults", "Specific Fault"], key="fault_submode", horizontal=True)
        if fault_submode == "Specific Fault":
            fault_type = st.selectbox("Fault Type", ["Filter_Clog","Refrigerant_Leak","Compressor_Fault","Fan_Fault","Electrical_Issue","Control_Sensor_Fault"])
            st.session_state.simulator.fault_override = fault_type
        else:
            st.session_state.simulator.fault_override = "random"
    else:
        st.session_state.simulator.fault_override = None

    interval = st.slider("Refresh Interval (seconds)", min_value=0.5, max_value=10.0, value=st.session_state.sim_interval, step=0.5, key="sim_interval")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶ Start Stream" if not st.session_state.get("streaming") else "⏹ Stop Stream", use_container_width=True):
            st.session_state.streaming = not st.session_state.get("streaming", False)
            st.rerun()
        st.markdown(f'<div style="text-align:center;font-size:0.95rem;margin-top:10px;font-weight:600;font-family:DM Sans,sans-serif;color:{"#54d764" if st.session_state.streaming else "#a8bcd4"}">{"🟢 STREAMING ACTIVE" if st.session_state.streaming else "⚫ STREAMING PAUSED"}</div>', unsafe_allow_html=True)
    with col2:
        if st.button("🔄 Reset Simulator", use_container_width=True):
            st.session_state.simulator.reset()
            st.session_state.alert_log.clear()
            st.success("Simulator reset successfully!")
# ── Routing & Streamlit Fragments ──────────────────────────────────────────

# Dynamic fragments for dashboard and live monitor based on streaming status
run_interval = st.session_state.sim_interval if st.session_state.streaming else None

@st.fragment(run_every=run_interval)
def fragment_dashboard():
    render_dashboard_content()

@st.fragment(run_every=run_interval)
def fragment_live_monitor():
    render_live_monitor_content()

active_page = st.session_state.active_page

# Render inside a container
with st.container():
    st.markdown('<div class="page-content">', unsafe_allow_html=True)
    if active_page == "dashboard":
        fragment_dashboard()
    elif active_page == "live_monitor":
        fragment_live_monitor()
    elif active_page == "predictions":
        render_predictions()
    elif active_page == "alerts":
        render_alerts()
    elif active_page == "training":
        render_training()
    elif active_page == "ai_insights":
        render_ai_insights()
    elif active_page == "history":
        render_history()
    elif active_page == "settings":
        render_settings()
    st.markdown('</div>', unsafe_allow_html=True)

# ── Floating AI Chat Bubble ─────────────────────────────────────────────────
def render_floating_chat():
    """Render the floating AI assistant bubble available on every page."""
    from utils.grok_client import build_sensor_context, SYSTEM_PROMPT
    import streamlit.components.v1 as components

    pred    = st.session_state.get("last_prediction",
              {"predicted_class": "Normal", "confidence": 0.0, "probabilities": {}})
    reading = st.session_state.get("last_reading", {})
    if not reading:
        reading = st.session_state.simulator.next_reading()

    predicted_class = pred.get("predicted_class", "Normal")
    confidence      = int(pred.get("confidence", 0.0) * 100)
    sensor_ctx      = build_sensor_context(reading, pred).replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")

    # Get API credentials for direct browser-side calls
    api_key = os.getenv("GROK_API_KEY", "")
    api_url = os.getenv("GROK_BASE_URL", "https://api.x.ai/v1")
    api_model = os.getenv("GROK_MODEL", "grok-3")
    if not api_key:
        try:
            api_key = st.secrets.get("GROK_API_KEY", "")
            api_url = st.secrets.get("GROK_BASE_URL", api_url)
            api_model = st.secrets.get("GROK_MODEL", api_model)
        except Exception:
            pass
    sys_prompt = SYSTEM_PROMPT.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$").replace("\n", "\\n")

    # ── Inject CSS + HTML via st.markdown ───────────────
    st.markdown(f"""
    <style>
    @keyframes fab-bubble-pulse {{
      0%,100% {{ box-shadow: 0 4px 20px rgba(59,158,255,.4), 0 0 0 0 rgba(59,158,255,.35); }}
      50%      {{ box-shadow: 0 4px 20px rgba(59,158,255,.4), 0 0 0 9px rgba(59,158,255,0); }}
    }}
    #hvac-fab {{
      position:fixed; bottom:50px; right:50px; z-index:99999;
      width:56px; height:56px; border-radius:50%;
      background:linear-gradient(135deg,#1565c0,#3b9eff);
      border:2px solid #5ab0ff;
      display:flex; align-items:center; justify-content:center;
      cursor:pointer; animation:fab-bubble-pulse 2.5s ease-in-out infinite;
      font-size:24px; color:#fff; user-select:none; transition:transform .2s;
    }}
    #hvac-fab:hover {{ transform:scale(1.1); }}
    #hvac-panel {{
      position:fixed; bottom:94px; right:26px; z-index:99998;
      width:380px; max-height:500px;
      background:linear-gradient(145deg,#0d1b2b,#0f1623);
      border:1px solid #1c2e47; border-radius:16px;
      box-shadow:0 12px 48px rgba(0,0,0,.65);
      display:none; flex-direction:column; overflow:hidden;
    }}
    #hvac-panel-header {{
      display:flex; align-items:center; justify-content:space-between;
      padding:13px 16px; border-bottom:1px solid #1c2e47;
      background:linear-gradient(135deg,#0f1623,#131d2e);
    }}
    .hvac-panel-title {{ font:700 .95rem 'Barlow',sans-serif; color:#dce8f5; }}
    .hvac-panel-sub   {{ font:500 .75rem 'DM Sans',sans-serif; color:#6b8299; margin-top:2px; }}
    #hvac-panel-close {{
      background:none; border:none; color:#6b8299;
      font-size:1.1rem; cursor:pointer; padding:4px 8px;
      border-radius:6px; line-height:1; transition:all .2s;
    }}
    #hvac-panel-close:hover {{ background:rgba(255,255,255,.07); color:#dce8f5; }}
    #hvac-msgs {{
      flex:1; overflow-y:auto; padding:14px 14px 8px;
      max-height:310px; display:flex; flex-direction:column; gap:10px;
    }}
    #hvac-msgs::-webkit-scrollbar {{ width:4px; }}
    #hvac-msgs::-webkit-scrollbar-thumb {{ background:#1c2e47; border-radius:4px; }}
    .fab-msg {{
      max-width:88%; padding:9px 13px; border-radius:13px;
      font:500 .84rem/1.5 'DM Sans',sans-serif; color:#dce8f5;
      word-wrap:break-word; animation:msgFadeIn .25s ease-out;
    }}
    @keyframes msgFadeIn {{
      from {{ opacity:0; transform:translateY(6px); }}
      to   {{ opacity:1; transform:translateY(0); }}
    }}
    .user-msg {{ align-self:flex-end;
                 background:linear-gradient(135deg,#1565c0,#1976d2);
                 border-bottom-right-radius:3px; }}
    .bot-msg  {{ align-self:flex-start;
                 background:#131d2e; border:1px solid #1c2e47;
                 border-bottom-left-radius:3px; }}
    .fab-welcome {{ text-align:center; padding:30px 16px;
                    color:#dce8f5; font:500 .88rem 'DM Sans',sans-serif; }}
    .fab-typing {{ align-self:flex-start; padding:10px 16px;
                   display:flex; gap:5px; align-items:center; }}
    .fab-typing-dot {{ width:7px; height:7px; border-radius:50%;
                       background:#6b8299; animation:typingBounce 1.2s ease-in-out infinite; }}
    .fab-typing-dot:nth-child(2) {{ animation-delay:.2s; }}
    .fab-typing-dot:nth-child(3) {{ animation-delay:.4s; }}
    @keyframes typingBounce {{
      0%,60%,100% {{ transform:translateY(0); opacity:.4; }}
      30%          {{ transform:translateY(-6px); opacity:1; }}
    }}
    #hvac-input-row {{
      display:flex; gap:8px; padding:10px 12px;
      border-top:1px solid #1c2e47; background:#0b1520;
      border-radius:0 0 16px 16px;
    }}
    #hvac-input {{
      flex:1; background:#131d2e; border:1px solid #1c2e47;
      border-radius:9px; padding:9px 13px;
      color:#dce8f5; font:500 .84rem 'DM Sans',sans-serif; outline:none;
      transition:border-color .2s;
    }}
    #hvac-input:focus {{ border-color:#3b9eff; }}
    #hvac-input::placeholder {{ color:#6b8299; }}
    #hvac-send {{
      width:38px; height:38px; border-radius:9px; border:none;
      background:linear-gradient(135deg,#1565c0,#3b9eff);
      color:#fff; font-size:1rem; cursor:pointer;
      display:flex; align-items:center; justify-content:center;
      transition:transform .15s, box-shadow .2s; flex-shrink:0;
    }}
    #hvac-send:hover {{ transform:scale(1.06);
                        box-shadow:0 0 10px rgba(59,158,255,.45); }}
    @media(max-width:480px){{
      #hvac-panel {{ width:calc(100vw - 32px); right:16px; }}
    }}
    </style>

    <div id="hvac-fab" title="Ask AI Assistant">🤖</div>
    <div id="hvac-panel">
      <div id="hvac-panel-header">
        <div>
          <div class="hvac-panel-title">🤖 HVAC AI Assistant</div>
          <div class="hvac-panel-sub">
            {predicted_class} &nbsp;·&nbsp; {confidence}% confidence
          </div>
        </div>
        <button id="hvac-panel-close" title="Close">✕</button>
      </div>
      <div id="hvac-msgs">
        <div class="fab-welcome">
          <div style="font-size:2.2rem;margin-bottom:8px">🤖</div>
          <div>Hi! I'm your HVAC AI Assistant.</div>
          <div style="font-size:0.78rem;margin-top:4px;color:#6b8299">
            Ask me about fault predictions, sensor readings,<br>or maintenance recommendations.
          </div>
        </div>
      </div>
      <div id="hvac-input-row">
        <input id="hvac-input" type="text"
               placeholder="Ask about faults, sensors, maintenance..."/>
        <button id="hvac-send" title="Send">➤</button>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── JS — calls Groq API directly from browser (works on Cloud!) ──
    components.html(f"""
    <script>
    const D = window.parent.document;
    const SENSOR_CTX = `{sensor_ctx}`;
    const API_KEY = `{api_key}`;
    const API_URL = `{api_url}`;
    const API_MODEL = `{api_model}`;
    const SYS_PROMPT = `{sys_prompt}`;
    let chatHistory = [];
    let sending = false;

    function hvacInit() {{
      const fab   = D.getElementById('hvac-fab');
      const panel = D.getElementById('hvac-panel');
      const close = D.getElementById('hvac-panel-close');
      const inp   = D.getElementById('hvac-input');
      const send  = D.getElementById('hvac-send');

      if (!fab || !panel) return;

      if (!fab.dataset.hvacBound) {{
        fab.dataset.hvacBound = 'true';
        fab.addEventListener('click', () => {{
          const open = panel.style.display === 'flex';
          panel.style.display = open ? 'none' : 'flex';
          fab.textContent     = open ? '🤖'  : '✕';
          if (!open) scrollMsgs();
        }});
        if (close) close.addEventListener('click', () => {{
          panel.style.display = 'none';
          fab.textContent = '🤖';
        }});
      }}
      if (send && !send.dataset.hvacBound) {{
        send.dataset.hvacBound = 'true';
        send.addEventListener('click', doSend);
      }}
      if (inp && !inp.dataset.hvacBound) {{
        inp.dataset.hvacBound = 'true';
        inp.addEventListener('keydown', e => {{
          if (e.key === 'Enter') {{ e.preventDefault(); doSend(); }}
        }});
      }}
    }}

    function scrollMsgs() {{
      const m = D.getElementById('hvac-msgs');
      if (m) m.scrollTop = m.scrollHeight;
    }}

    function addBubble(cls, text) {{
      const m = D.getElementById('hvac-msgs');
      if (!m) return;
      const w = m.querySelector('.fab-welcome');
      if (w) w.remove();
      const d = D.createElement('div');
      d.className = 'fab-msg ' + cls;
      d.innerHTML = text.replace(/&/g,'&amp;').replace(/</g,'&lt;')
                        .replace(/>/g,'&gt;').replace(/\\n/g,'<br>');
      m.appendChild(d);
      scrollMsgs();
    }}

    async function doSend() {{
      if (sending) return;
      const inp = D.getElementById('hvac-input');
      if (!inp) return;
      const val = inp.value.trim();
      if (!val) return;
      inp.value = '';
      sending = true;

      addBubble('user-msg', val);
      chatHistory.push({{role:'user', content: val}});

      const m = D.getElementById('hvac-msgs');
      const typing = D.createElement('div');
      typing.className = 'fab-typing';
      typing.id = 'hvac-typing';
      typing.innerHTML = '<div class="fab-typing-dot"></div>'
        + '<div class="fab-typing-dot"></div>'
        + '<div class="fab-typing-dot"></div>';
      if (m) {{ m.appendChild(typing); scrollMsgs(); }}

      const apiMsgs = chatHistory.map((msg, i) => {{
        if (i === 0 && msg.role === 'user') {{
          return {{role:'user', content: 'Context: ' + SENSOR_CTX + '\\n\\nQuestion: ' + msg.content}};
        }}
        return msg;
      }});

      if (!API_KEY) {{
        const t = D.getElementById('hvac-typing');
        if (t) t.remove();
        addBubble('bot-msg', '⚠️ API key not configured. Add GROK_API_KEY to your .env or Streamlit secrets.');
        sending = false;
        return;
      }}

      try {{
        const resp = await fetch(API_URL + '/chat/completions', {{
          method: 'POST',
          headers: {{
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + API_KEY
          }},
          body: JSON.stringify({{
            model: API_MODEL,
            messages: [{{role:'system', content: SYS_PROMPT}}, ...apiMsgs],
            max_tokens: 600,
            temperature: 0.4
          }})
        }});
        const data = await resp.json();
        const t = D.getElementById('hvac-typing');
        if (t) t.remove();
        if (data.choices && data.choices[0]) {{
          const reply = data.choices[0].message.content;
          addBubble('bot-msg', reply);
          chatHistory.push({{role:'assistant', content: reply}});
        }} else if (data.error) {{
          addBubble('bot-msg', '⚠️ ' + (data.error.message || 'API error'));
        }} else {{
          addBubble('bot-msg', '⚠️ Unexpected response from API.');
        }}
      }} catch(e) {{
        const t = D.getElementById('hvac-typing');
        if (t) t.remove();
        addBubble('bot-msg', '⚠️ Connection error: ' + e.message);
      }}
      sending = false;
      if (inp) inp.focus();
    }}

    setInterval(hvacInit, 150);
    </script>
    """, height=0, width=0)


render_floating_chat()

