"""
AI Resume Screening and Job Matching System - Modern SaaS Design System & CSS.
Curated palette: Deep Navy (#0A0F1D, #0D1527), Electric Blue (#2563EB, #3B82F6),
Violet (#7C3AED, #8B5CF6), Cyan (#06B6D4, #22D3EE), White (#FFFFFF, #F8FAFC).
Includes responsive layouts, glassmorphism, dark/light themes, badges,
cards, metrics, split-screen auth, visual matching graphic, and micro-animations.
"""

import itertools
from typing import Optional

__all__ = ["get_css", "get_logo_svg"]

_logo_counter = itertools.count(1)


def get_logo_svg(size: int = 40, show_glow: bool = True, prefix: Optional[str] = None) -> str:
    """
    Returns an inline SVG of the professional brand logo combining:
    - A resume document sheet with folded corner & content lines
    - An AI neural intelligence spark in electric blue & violet
    - A verified matching checkmark badge in vibrant cyan/emerald
    Supports a custom or auto-generated unique ID prefix so multiple logos on the
    same page do not experience gradient or filter ID collisions.
    """
    uid = prefix if prefix is not None else f"inst_{next(_logo_counter)}"
    doc_grad_id = f"docGrad_{uid}"
    ai_grad_id = f"aiGrad_{uid}"
    check_grad_id = f"checkGrad_{uid}"
    glow_filter_id = f"logoGlow_{uid}"

    glow_filter = (
        f'<filter id="{glow_filter_id}" x="-20%" y="-20%" width="140%" height="140%">'
        f'<feGaussianBlur stdDeviation="3" result="blur" />'
        f'<feComposite in="SourceGraphic" in2="blur" operator="over" />'
        f'</filter>'
    ) if show_glow else ""
    filter_attr = f'filter="url(#{glow_filter_id})"' if show_glow else ""

    svg = (
        f'<svg width="{size}" height="{size}" viewBox="0 0 64 64" fill="none" '
        f'xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle; display: inline-block;">'
        f'<defs>'
        f'<linearGradient id="{doc_grad_id}" x1="8" y1="4" x2="56" y2="60" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0%" stop-color="#1E3A8A" />'
        f'<stop offset="50%" stop-color="#2563EB" />'
        f'<stop offset="100%" stop-color="#7C3AED" />'
        f'</linearGradient>'
        f'<linearGradient id="{ai_grad_id}" x1="20" y1="20" x2="48" y2="48" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0%" stop-color="#06B6D4" />'
        f'<stop offset="50%" stop-color="#38BDF8" />'
        f'<stop offset="100%" stop-color="#A855F7" />'
        f'</linearGradient>'
        f'<linearGradient id="{check_grad_id}" x1="38" y1="38" x2="60" y2="60" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0%" stop-color="#10B981" />'
        f'<stop offset="100%" stop-color="#06B6D4" />'
        f'</linearGradient>'
        f'{glow_filter}'
        f'</defs>'
        f'<rect x="10" y="6" width="38" height="48" rx="7" fill="url(#{doc_grad_id})" stroke="rgba(255,255,255,0.25)" stroke-width="1.5" />'
        f'<path d="M38 6 L48 16 L38 16 Z" fill="#60A5FA" opacity="0.6" />'
        f'<rect x="16" y="14" width="16" height="2.5" rx="1.25" fill="#E0E7FF" opacity="0.9" />'
        f'<rect x="16" y="20" width="24" height="2.5" rx="1.25" fill="#93C5FD" opacity="0.75" />'
        f'<rect x="16" y="26" width="20" height="2.5" rx="1.25" fill="#93C5FD" opacity="0.75" />'
        f'<rect x="16" y="32" width="14" height="2.5" rx="1.25" fill="#93C5FD" opacity="0.6" />'
        f'<g {filter_attr}>'
        f'<circle cx="28" cy="40" r="4.5" fill="url(#{ai_grad_id})" stroke="#FFFFFF" stroke-width="1.5" />'
        f'<circle cx="19" cy="38" r="2.2" fill="#38BDF8" />'
        f'<circle cx="34" cy="46" r="2.2" fill="#A855F7" />'
        f'<line x1="28" y1="40" x2="19" y2="38" stroke="#38BDF8" stroke-width="1.2" stroke-linecap="round" opacity="0.8" />'
        f'<line x1="28" y1="40" x2="34" y2="46" stroke="#A855F7" stroke-width="1.2" stroke-linecap="round" opacity="0.8" />'
        f'<path d="M28 35.5 L29.5 38.5 L32.5 40 L29.5 41.5 L28 44.5 L26.5 41.5 L23.5 40 L26.5 38.5 Z" fill="#FFFFFF" />'
        f'</g>'
        f'<g>'
        f'<circle cx="46" cy="46" r="13" fill="#0A0F1D" stroke="rgba(255,255,255,0.15)" stroke-width="2" />'
        f'<circle cx="46" cy="46" r="11" fill="url(#{check_grad_id})" />'
        f'<path d="M41.5 46.5 L44.5 49.5 L51 42.5" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />'
        f'</g>'
        f'</svg>'
    )
    return svg


def get_css(theme: str = "dark") -> str:
    """
    Returns full CSS stylesheet adapted for the specified theme ('dark' or 'light').
    Built on a tailored palette of Navy, Electric Blue, Violet, Cyan, and White.
    """
    if theme == "light":
        bg_main = "#F8FAFC"
        bg_card = "#FFFFFF"
        bg_card_secondary = "#F1F5F9"
        bg_card_hover = "#F8FAFC"
        text_primary = "#0F172A"
        text_secondary = "#475569"
        text_muted = "#64748B"
        border_color = "rgba(148, 163, 184, 0.35)"
        border_glow = "rgba(37, 99, 235, 0.4)"
        hero_gradient = "linear-gradient(135deg, #1E3A8A 0%, #2563EB 50%, #7C3AED 100%)"
        card_shadow = "0 8px 24px -4px rgba(15, 23, 42, 0.08), 0 2px 6px -1px rgba(15, 23, 42, 0.04)"
        glass_bg = "rgba(255, 255, 255, 0.85)"
        pill_bg_neutral = "#E2E8F0"
        pill_text_neutral = "#334155"
        code_bg = "#F1F5F9"
        stat_card_bg = "linear-gradient(145deg, #FFFFFF, #F8FAFC)"
    else:  # Dark mode (default & recommended)
        bg_main = "#0A0F1D"
        bg_card = "#111827"
        bg_card_secondary = "#1A2234"
        bg_card_hover = "#1F293D"
        text_primary = "#F8FAFC"
        text_secondary = "#94A3B8"
        text_muted = "#64748B"
        border_color = "rgba(255, 255, 255, 0.09)"
        border_glow = "rgba(59, 130, 246, 0.35)"
        hero_gradient = "linear-gradient(135deg, #38BDF8 0%, #818CF8 50%, #C084FC 100%)"
        card_shadow = "0 10px 30px -5px rgba(0, 0, 0, 0.45), 0 4px 12px -2px rgba(0, 0, 0, 0.3)"
        glass_bg = "rgba(17, 24, 39, 0.8)"
        pill_bg_neutral = "#1E293B"
        pill_text_neutral = "#CBD5E1"
        code_bg = "rgba(15, 23, 42, 0.75)"
        stat_card_bg = "linear-gradient(145deg, #131C2E, #111827)"

    css = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    :root {{
        --bg-main: {bg_main};
        --bg-card: {bg_card};
        --bg-card-secondary: {bg_card_secondary};
        --bg-card-hover: {bg_card_hover};
        --text-primary: {text_primary};
        --text-secondary: {text_secondary};
        --text-muted: {text_muted};
        --border-color: {border_color};
        --border-glow: {border_glow};
        --color-blue: #3B82F6;
        --color-blue-dark: #2563EB;
        --color-cyan: #06B6D4;
        --color-cyan-light: #38BDF8;
        --color-violet: #8B5CF6;
        --color-purple: #7C3AED;
        --color-emerald: #10B981;
        --color-emerald-light: #34D399;
        --color-amber: #F59E0B;
        --color-rose: #F43F5E;
        --color-navy: #0A0F1D;
        --card-shadow: {card_shadow};
    }}

    /* Global Typography & Background */
    html, body, [class*="css"], .stApp {{
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: var(--bg-main) !important;
        color: var(--text-primary) !important;
        letter-spacing: -0.15px;
    }}

    /* Clean Streamlit Header & Chrome */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header [data-testid="stHeader"] {{
        background: transparent !important;
    }}
    .block-container {{
        padding-top: 1.8rem !important;
        padding-bottom: 3.5rem !important;
        max-width: 1280px !important;
    }}

    /* Top Navigation Bar Glassmorphism */
    .saas-navbar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 14px 28px;
        background: {glass_bg};
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border: 1px solid var(--border-color);
        border-radius: 18px;
        margin-bottom: 28px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    }}
    .saas-brand-wrap {{
        display: flex;
        align-items: center;
        gap: 14px;
        text-decoration: none;
    }}
    .saas-brand-title {{
        font-size: 19px;
        font-weight: 800;
        letter-spacing: -0.6px;
        color: var(--text-primary);
        line-height: 1.2;
    }}
    .saas-brand-sub {{
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #38BDF8;
    }}
    .brand-gradient-text {{
        background: {hero_gradient};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }}

    /* Hero Section */
    .hero-container {{
        text-align: center;
        padding: 56px 28px 44px 28px;
        border-radius: 28px;
        background: radial-gradient(circle at 50% 15%, rgba(37, 99, 235, 0.22) 0%, rgba(124, 58, 237, 0.12) 45%, transparent 75%), var(--bg-card);
        border: 1px solid var(--border-color);
        margin-bottom: 36px;
        position: relative;
        overflow: hidden;
        box-shadow: var(--card-shadow);
    }}
    .hero-container::before {{
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, #06B6D4, #3B82F6, #8B5CF6, #06B6D4);
        background-size: 300% 100%;
        animation: gradientShift 6s ease infinite;
    }}
    @keyframes gradientShift {{
        0% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%; }}
    }}
    .hero-badge {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(59, 130, 246, 0.12);
        border: 1px solid rgba(59, 130, 246, 0.35);
        padding: 7px 18px;
        border-radius: 30px;
        font-size: 13px;
        font-weight: 700;
        color: #38BDF8;
        margin-bottom: 20px;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.2);
    }}
    .hero-title {{
        font-size: 48px;
        font-weight: 800;
        line-height: 1.15;
        letter-spacing: -1.4px;
        margin-bottom: 18px;
        color: var(--text-primary);
    }}
    .hero-subtitle {{
        font-size: 18px;
        color: var(--text-secondary);
        max-width: 740px;
        margin: 0 auto 32px auto;
        line-height: 1.65;
        font-weight: 400;
    }}

    /* Visual Matching Graphic / Showcase on Landing Page */
    .match-showcase-container {{
        background: {code_bg};
        border: 1px solid var(--border-color);
        border-radius: 24px;
        padding: 32px 24px;
        margin: 36px 0;
        position: relative;
        overflow: hidden;
    }}
    .match-showcase-header {{
        text-align: center;
        margin-bottom: 0;
    }}
    .match-showcase-title {{
        font-size: 22px;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: var(--text-primary);
    }}
    .match-showcase-desc {{
        font-size: 14px;
        color: var(--text-secondary);
        margin-top: 4px;
    }}

    /* Stat Cards */
    .stat-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 18px;
        margin-bottom: 32px;
    }}
    .stat-card {{
        background: {stat_card_bg};
        border: 1px solid var(--border-color);
        border-radius: 18px;
        padding: 22px 20px;
        text-align: left;
        box-shadow: var(--card-shadow);
        transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        position: relative;
        overflow: hidden;
    }}
    .stat-card:hover {{
        transform: translateY(-3px);
        border-color: var(--border-glow);
        box-shadow: 0 12px 36px -4px rgba(37, 99, 235, 0.2);
    }}
    .stat-card-top {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
    }}
    .stat-icon-wrap {{
        width: 42px;
        height: 42px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        background: rgba(59, 130, 246, 0.12);
        color: #38BDF8;
        border: 1px solid rgba(59, 130, 246, 0.25);
    }}
    .stat-num {{
        font-size: 34px;
        font-weight: 800;
        letter-spacing: -1px;
        color: var(--text-primary);
        line-height: 1.1;
        margin-bottom: 6px;
    }}
    .stat-lbl {{
        font-size: 13px;
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 0.6px;
        color: var(--text-secondary);
    }}
    .stat-delta {{
        font-size: 12px;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 8px;
        display: inline-block;
    }}
    .stat-delta-positive {{
        background: rgba(16, 185, 129, 0.15);
        color: #34D399;
    }}

    /* Glass Cards */
    .glass-card {{
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 20px;
        padding: 26px;
        margin-bottom: 22px;
        box-shadow: var(--card-shadow);
        transition: border-color 0.2s ease;
    }}
    .glass-card:hover {{
        border-color: var(--border-glow);
    }}

    /* Feature Cards */
    .feature-card {{
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 20px;
        padding: 26px;
        height: 100%;
        display: flex;
        flex-direction: column;
        transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
        box-shadow: var(--card-shadow);
    }}
    .feature-card:hover {{
        border-color: #38BDF8;
        transform: translateY(-4px);
        box-shadow: 0 14px 40px -6px rgba(56, 189, 248, 0.18);
    }}
    .feature-icon {{
        width: 48px;
        height: 48px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        margin-bottom: 18px;
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.15), rgba(124, 58, 237, 0.15));
        border: 1px solid rgba(59, 130, 246, 0.3);
    }}

    /* Workflow Cards */
    .step-card {{
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 18px;
        padding: 24px;
        height: 100%;
        box-shadow: var(--card-shadow);
        position: relative;
        overflow: hidden;
        transition: transform 0.2s ease;
    }}
    .step-card:hover {{
        transform: translateY(-3px);
        border-color: #818CF8;
    }}
    .step-num-badge {{
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 1px;
        text-transform: uppercase;
        padding: 4px 10px;
        border-radius: 8px;
        display: inline-block;
        margin-bottom: 12px;
    }}

    /* Badges & Pills */
    .badge-pill {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 13px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin: 3px 4px;
        letter-spacing: 0.2px;
        line-height: 1.3;
        transition: transform 0.15s ease;
    }}
    .badge-pill:hover {{
        transform: scale(1.04);
    }}
    .badge-matched {{
        background: rgba(16, 185, 129, 0.14);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.45);
    }}
    .badge-missing {{
        background: rgba(244, 63, 94, 0.14);
        color: #FB7185;
        border: 1px solid rgba(244, 63, 94, 0.45);
    }}
    .badge-bonus {{
        background: rgba(6, 182, 212, 0.14);
        color: #22D3EE;
        border: 1px solid rgba(6, 182, 212, 0.45);
    }}
    .badge-neutral {{
        background: {pill_bg_neutral};
        color: {pill_text_neutral};
        border: 1px solid var(--border-color);
    }}

    /* Candidate Header & Podium */
    .cand-header-box {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 18px;
        border-bottom: 1px solid var(--border-color);
        margin-bottom: 18px;
    }}
    .cand-name {{
        font-size: 24px;
        font-weight: 800;
        margin: 0;
        color: var(--text-primary);
        letter-spacing: -0.5px;
    }}
    .cand-rank {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        border-radius: 10px;
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.25), rgba(124, 58, 237, 0.25));
        border: 1px solid rgba(59, 130, 246, 0.4);
        color: #60A5FA;
        font-weight: 800;
        font-size: 15px;
        margin-right: 12px;
    }}
    .cand-rank-gold {{
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.3), rgba(217, 119, 6, 0.3));
        border-color: #F59E0B;
        color: #FBBF24;
        box-shadow: 0 0 14px rgba(245, 158, 11, 0.3);
    }}
    .cand-rank-silver {{
        background: linear-gradient(135deg, rgba(148, 163, 184, 0.25), rgba(100, 116, 139, 0.25));
        border-color: #94A3B8;
        color: #E2E8F0;
    }}
    .cand-rank-bronze {{
        background: linear-gradient(135deg, rgba(180, 83, 9, 0.25), rgba(146, 64, 14, 0.25));
        border-color: #B45309;
        color: #FDBA74;
    }}

    /* Mathematical Formula Card */
    .math-formula-box {{
        background: {code_bg};
        border-left: 4px solid #3B82F6;
        border-radius: 12px;
        padding: 18px 22px;
        margin: 18px 0;
        font-family: 'JetBrains Mono', monospace;
        font-size: 13.5px;
        color: #E2E8F0;
        line-height: 1.6;
        box-shadow: inset 0 2px 6px rgba(0,0,0,0.25);
    }}

    /* Split-Screen Auth Layout */
    .auth-split-wrapper {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 28px;
        align-items: stretch;
        margin: 20px 0;
    }}
    @media (max-width: 850px) {{
        .auth-split-wrapper {{
            grid-template-columns: 1fr;
        }}
    }}
    .auth-banner-side {{
        background: linear-gradient(145deg, #0D1527 0%, #151D33 50%, #1A213D 100%);
        border: 1px solid var(--border-color);
        border-radius: 24px;
        padding: 36px 30px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: var(--card-shadow);
        position: relative;
        overflow: hidden;
    }}
    .auth-banner-side::after {{
        content: '';
        position: absolute;
        top: -60px; right: -60px;
        width: 180px; height: 180px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(59, 130, 246, 0.25) 0%, transparent 70%);
        pointer-events: none;
    }}
    .auth-form-side {{
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 24px;
        padding: 34px 30px;
        box-shadow: var(--card-shadow);
    }}

    /* Admin & User Portal Custom Styles */
    .admin-portal-header {{
        background: linear-gradient(135deg, rgba(76, 29, 149, 0.4), rgba(124, 58, 237, 0.25));
        border: 1px solid rgba(168, 85, 247, 0.4);
        border-radius: 20px;
        padding: 24px 28px;
        margin-bottom: 24px;
        box-shadow: 0 10px 30px rgba(124, 58, 237, 0.15);
    }}
    .admin-badge {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(168, 85, 247, 0.18);
        border: 1px solid rgba(168, 85, 247, 0.45);
        color: #C084FC;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.6px;
        text-transform: uppercase;
    }}
    .admin-card {{
        background: linear-gradient(135deg, rgba(30, 27, 75, 0.7), rgba(46, 16, 101, 0.4));
        border: 1px solid rgba(168, 85, 247, 0.3);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
    }}
    .user-portal-badge {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(14, 165, 233, 0.15);
        border: 1px solid rgba(14, 165, 233, 0.4);
        color: #38BDF8;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.6px;
        text-transform: uppercase;
    }}

    /* Fact vs Inference Tagging */
    .fact-tag {{
        display: inline-block;
        font-size: 10px;
        text-transform: uppercase;
        font-weight: 800;
        padding: 3px 9px;
        border-radius: 5px;
        letter-spacing: 0.6px;
    }}
    .tag-grounded-fact {{
        background: #064E3B;
        color: #6EE7B7;
        border: 1px solid rgba(110, 231, 183, 0.3);
    }}
    .tag-model-inference {{
        background: #312E81;
        color: #C7D2FE;
        border: 1px solid rgba(199, 210, 254, 0.3);
    }}

    /* Roadmap Step Cards */
    .roadmap-step {{
        background: var(--bg-card-secondary);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 20px 22px;
        margin-bottom: 16px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }}
    .roadmap-step:hover {{
        transform: translateX(5px);
        border-color: #38BDF8;
    }}

    /* Ethics / AI Banner */
    .ethics-card {{
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.25) 0%, rgba(88, 28, 135, 0.25) 100%);
        border: 1px solid rgba(99, 102, 241, 0.35);
        border-radius: 18px;
        padding: 20px 24px;
        margin: 28px 0;
        display: flex;
        align-items: flex-start;
        gap: 16px;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.1);
    }}

    /* Activity Stream Timeline */
    .activity-stream {{
        border-left: 2px solid rgba(59, 130, 246, 0.3);
        margin-left: 12px;
        padding-left: 18px;
    }}
    .activity-item {{
        position: relative;
        padding-bottom: 16px;
    }}
    .activity-item::before {{
        content: '';
        position: absolute;
        left: -24px;
        top: 4px;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #38BDF8;
        box-shadow: 0 0 8px #38BDF8;
    }}

    /* Streamlit Interactive Component Overrides */
    .stButton > button {{
        border-radius: 12px !important;
        font-weight: 700 !important;
        letter-spacing: 0.2px !important;
        padding: 9px 20px !important;
        transition: all 0.22s ease !important;
    }}
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #2563EB 0%, #7C3AED 100%) !important;
        border: none !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 18px rgba(37, 99, 235, 0.45) !important;
    }}
    .stButton > button[kind="primary"]:hover {{
        box-shadow: 0 8px 26px rgba(124, 58, 237, 0.65) !important;
        transform: translateY(-2px) !important;
        background: linear-gradient(135deg, #1D4ED8 0%, #6D28D9 100%) !important;
    }}
    .stButton > button[kind="secondary"] {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
    }}
    .stButton > button[kind="secondary"]:hover {{
        border-color: #38BDF8 !important;
        color: #38BDF8 !important;
        transform: translateY(-1px) !important;
    }}

    /* File Uploader Custom Styling */
    [data-testid="stFileUploader"] {{
        background: {glass_bg};
        border-radius: 16px;
        padding: 12px;
    }}
    [data-testid="stFileUploadDropzone"] {{
        border: 2px dashed rgba(59, 130, 246, 0.4) !important;
        border-radius: 14px !important;
        background: rgba(37, 99, 235, 0.04) !important;
        transition: all 0.2s ease !important;
    }}
    [data-testid="stFileUploadDropzone"]:hover {{
        border-color: #38BDF8 !important;
        background: rgba(56, 189, 248, 0.08) !important;
    }}

    /* Inputs, Textareas, Selectboxes */
    .stTextInput > div > div > input, 
    .stTextArea > div > div > textarea {{
        border-radius: 12px !important;
        border: 1px solid var(--border-color) !important;
        background-color: var(--bg-card-secondary) !important;
        color: var(--text-primary) !important;
        font-family: inherit !important;
    }}
    .stTextInput > div > div > input:focus, 
    .stTextArea > div > div > textarea:focus {{
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.25) !important;
    }}

    /* Progress Bars */
    .stProgress > div > div > div > div {{
        background: linear-gradient(90deg, #06B6D4 0%, #3B82F6 50%, #8B5CF6 100%) !important;
        border-radius: 10px !important;
    }}

    /* Footer */
    .saas-footer {{
        border-top: 1px solid var(--border-color);
        padding: 28px 0 16px 0;
        margin-top: 48px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 16px;
        color: var(--text-muted);
        font-size: 13px;
    }}
    .footer-links {{
        display: flex;
        gap: 20px;
    }}
    .footer-links a {{
        color: var(--text-secondary);
        text-decoration: none;
        transition: color 0.2s ease;
    }}
    .footer-links a:hover {{
        color: #38BDF8;
    }}
</style>
"""
    return css
