"""
AI Resume Screening and Job Matching System - Reusable UI Components.
Generates polished, accessible HTML/CSS components for landing page, dashboard,
match visualization, badges, and headers.
"""

from typing import List, Dict, Any, Optional
from src.styles import get_logo_svg


def render_brand_badge(size: int = 36, show_title: bool = True, subtitle: str = "Intelligence Platform") -> str:
    """Renders the professional SVG logo with typography."""
    logo_svg = get_logo_svg(size=size, prefix="brand")
    if not show_title:
        return f"<div style='display:inline-block;'>{logo_svg}</div>"
    
    return (
        f"<div style='display: flex; align-items: center; gap: 12px;'>"
        f"<div style='display: flex; align-items: center; justify-content: center;'>{logo_svg}</div>"
        f"<div>"
        f"<div style='font-size: 18px; font-weight: 800; letter-spacing: -0.5px; line-height: 1.2;'>"
        f"AI Resume Screening <span style='background: linear-gradient(135deg, #38BDF8, #818CF8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>& Job Matching</span>"
        f"</div>"
        f"<div style='font-size: 11px; color: #38BDF8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px;'>{subtitle}</div>"
        f"</div>"
        f"</div>"
    )


def render_navbar_html(user: Optional[Dict[str, Any]] = None) -> str:
    """Renders top SaaS navigation bar with brand logo and user status."""
    logo_svg = get_logo_svg(size=36, prefix="navbar")
    
    if user and user.get("is_authenticated"):
        if user.get("role") == "admin":
            user_badge = (
                f"<div style='display: flex; align-items: center; gap: 10px; background: rgba(168, 85, 247, 0.15); border: 1px solid rgba(168, 85, 247, 0.4); padding: 6px 14px; border-radius: 24px;'>"
                f"<div style='width: 26px; height: 26px; border-radius: 50%; background: linear-gradient(135deg, #A855F7, #EC4899); display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 800; color: #fff;'>🛡️</div>"
                f"<div style='text-align: left;'>"
                f"<div style='font-size: 12px; font-weight: 700; color: #F8FAFC;'>{user.get('full_name')}</div>"
                f"<div style='font-size: 10px; color: #C084FC; font-weight: 700; text-transform: uppercase;'>System Administrator</div>"
                f"</div>"
                f"</div>"
            )
        else:
            user_badge = (
                f"<div style='display: flex; align-items: center; gap: 10px; background: rgba(59, 130, 246, 0.12); border: 1px solid rgba(59, 130, 246, 0.3); padding: 6px 14px; border-radius: 24px;'>"
                f"<div style='width: 26px; height: 26px; border-radius: 50%; background: linear-gradient(135deg, #06B6D4, #7C3AED); display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 800; color: #fff;'>"
                f"{user.get('full_name', 'U')[0]}"
                f"</div>"
                f"<div style='text-align: left;'>"
                f"<div style='font-size: 12px; font-weight: 700; color: #F8FAFC;'>{user.get('full_name')}</div>"
                f"<div style='font-size: 10px; color: #38BDF8; font-weight: 600;'>{user.get('role')}</div>"
                f"</div>"
                f"</div>"
            )
    else:
        user_badge = (
            f"<div style='background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.3); padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 700; color: #FBBF24;'>"
            f"⚡ Demo Guest Mode"
            f"</div>"
        )

    return (
        f"<div class='saas-navbar'>"
        f"<div class='saas-brand-wrap'>"
        f"{logo_svg}"
        f"<div>"
        f"<div class='saas-brand-title'>"
        f"AI Resume Screening <span class='brand-gradient-text'>& Job Matching</span>"
        f"</div>"
        f"<div class='saas-brand-sub'>Autonomous Contextual Talent Intelligence</div>"
        f"</div>"
        f"</div>"
        f"<div>{user_badge}</div>"
        f"</div>"
    )


def render_visual_matching_showcase() -> str:
    """
    Renders an interactive visual matching graphic on the landing page
    demonstrating resumes matched against target job requirements in real-time.
    """
    return """
    <div class='match-showcase-container'>
        <div class='match-showcase-header'>
            <div class='hero-badge' style='margin-bottom: 10px;'>🎯 Live Semantic Inference Simulation</div>
            <div class='match-showcase-title'>Intelligent Neural Matching in Action</div>
            <div class='match-showcase-desc'>
                Sentence embeddings project resumes and job criteria into a shared 384-dimensional vector space to evaluate conceptual relevance.
            </div>
        </div>
    </div>
    """


def render_stat_card_html(num: Any, label: str, icon: str = "📊", delta: str = "", delta_type: str = "positive") -> str:
    """Renders a styled metric card."""
    delta_html = ""
    if delta:
        delta_cls = "stat-delta-positive" if delta_type == "positive" else "stat-delta-neutral"
        delta_html = f"<span class='stat-delta {delta_cls}'>{delta}</span>"

    return f"""
    <div class='stat-card'>
        <div class='stat-card-top'>
            <div class='stat-icon-wrap'>{icon}</div>
            {delta_html}
        </div>
        <div class='stat-num'>{num}</div>
        <div class='stat-lbl'>{label}</div>
    </div>
    """


def render_footer_html() -> str:
    """Renders the startup-grade footer."""
    return """
    <div class='saas-footer'>
        <div>
            <strong style='color: #F8FAFC;'>AI Resume Screening & Job Matching System</strong> &middot; Next-Gen Talent Intelligence
            <div style='font-size: 11px; color: #64748B; margin-top: 4px;'>
                Built with Streamlit, Sentence-Transformers & PyMuPDF &middot; Zero GPU / 100% Private Local Inference
            </div>
        </div>
        <div class='footer-links'>
            <a href='#'>Fair Hiring Charter</a>
            <a href='#'>Explainability Spec</a>
            <a href='#'>Security & Privacy</a>
            <a href='#'>Hackathon Showcase 2026</a>
        </div>
    </div>
    """
