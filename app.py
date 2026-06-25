import streamlit as st
from streamlit_option_menu import option_menu
import src.core.setting as config

st.set_page_config(layout="wide")

config.conf_browser_setting(st)
config.conf_global_style(st)


def toggle_theme():
    st.session_state.theme = "light" if st.session_state._theme_toggle else "dark"


THEMES = {
    "dark": {
        # Página
        "app_bg":        "#0e1117",
        "app_text":      "#f9fafb",
        # Sidebar
        "sidebar_bg":    "#0f1117",
        "sidebar_text":  "#d1d5db",
        "sidebar_border":"#1f2937",
        # Menu
        "menu_bg":       "#1a1f2e",
        "menu_border":   "0px solid #1f2937",
        "link_bg":       "#1a1f2e",
        "link_hover":    "#1e293b",
        "text_color":    "#d1d5db",
        "selected_bg":   "#628ae2",
        "selected_text": "#ffffff",
        "icon_color":    "#324e8b",
        "menu_title":    "#9ca3af",
        # Misc
        "divider":       "#1f2937",
        "heading_color": "#9ca3af",
        "toggle_label":  "#d1d5db",
    },
    "light": {
        # Página
        "app_bg":        "#f9fafb",
        "app_text":      "#111827",
        # Sidebar
        "sidebar_bg":    "#f3f4f6",
        "sidebar_text":  "#1f2937",
        "sidebar_border":"#e5e7eb",
        # Menu
        "menu_bg":       "#ffffff",
        "menu_border":   "0px solid #e5e7eb",
        "link_bg":       "#ffffff",
        "link_hover":    "#e0e7ff",
        "text_color":    "#1f2937",
        "selected_bg":   "#628ae2",
        "selected_text": "#ffffff",
        "icon_color":    "#324e8b",
        "menu_title":    "#6b7280",
        # Misc
        "divider":       "#e5e7eb",
        "heading_color": "#6b7280",
        "toggle_label":  "#374151",
    },
}


def apply_theme(c: dict):
    """Injeta todo o CSS de tema em um único bloco, evitando conflitos."""
    st.markdown(
        f"""
        <style>
            /* ── Página ── */
            .stApp {{
                background-color: {c["app_bg"]} !important;
                color: {c["app_text"]} !important;
            }}
            .stApp h1, .stApp h2, .stApp h3,
            .stApp p, .stApp span, .stApp label {{
                color: {c["app_text"]} !important;
            }}

            /* ── Sidebar — fundo real (seletores internos do Streamlit) ── */
            [data-testid="stSidebarContent"] {{
                background-color: {c["sidebar_bg"]} !important;
            }}
            [data-testid="stSidebarUserContent"] {{
                background-color: {c["sidebar_bg"]} !important;
            }}

            .stAppHeader{{
                background-color: {c["sidebar_bg"]} !important;

            }}
            
            [data-testid="stAppToolbar"] {{
                background-color: {c["sidebar_bg"]} !important;
            }}

            /* ── Sidebar — borda lateral ── */
            section[data-testid="stSidebar"] {{
                border-right: 1px solid {c["sidebar_border"]} !important;
            }}

            /* ── Sidebar — posição sticky ── */
            section[data-testid="stSidebar"] > div:first-child {{
                position: sticky;
                top: 0;
                height: 100vh;
                overflow-y: auto;
            }}

            /* ── Sidebar — textos genéricos ── */
            section[data-testid="stSidebar"] * {{
                color: {c["sidebar_text"]} !important;
            }}

            /* ── Sidebar — cabeçalho (h3) ── */
            [data-testid="stSidebar"] h3 {{
                color: {c["heading_color"]} !important;
                font-family: 'Inter', sans-serif;
                font-size: 14px;
                font-weight: 500;
                letter-spacing: 0.04em;
                text-transform: uppercase;
                margin-bottom: 12px;
            }}

            /* ── Sidebar — toggle label ── */
            [data-testid="stSidebar"] .stToggle p {{
                color: {c["toggle_label"]} !important;
                font-size: 14px;
                font-weight: 400;
            }}

            /* ── Sidebar — divider ── */
            [data-testid="stSidebar"] hr {{
                border-color: {c["divider"]} !important;
                margin: 16px 0;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render():
    if "theme" not in st.session_state:
        st.session_state.theme = "dark"

    c = THEMES[st.session_state.theme]
    apply_theme(c)

    with st.sidebar:
        st.write("### Configurações")

        st.toggle(
            "Modo Claro",
            value=(st.session_state.theme == "light"),
            key="_theme_toggle",
            on_change=toggle_theme,
        )

        st.divider()

        selected = option_menu(
            menu_title="Menu",
            options=[page.name for page in config.PAGES],
            icons=[page.icon for page in config.PAGES],
            menu_icon="grid-fill",
            default_index=0,
            orientation="vertical",
            key=f"nav_menu_{st.session_state.theme}",
            styles={
                "container": {
                    "background-color": c["menu_bg"],
                    "border-radius": "0px",
                    "border": c["menu_border"],
                    "padding": "8px",
                },
                "menu-title": {
                    "font-size": "11px",
                    "font-weight": "500",
                    "color": c["menu_title"],
                    "text-transform": "uppercase",
                    "letter-spacing": "0.08em",
                    "padding": "4px 8px 8px",
                },
                "icon": {
                    "color": c["icon_color"],
                    "font-size": "18px",
                },
                "nav-link": {
                    "font-size": "14px",
                    "font-weight": "400",
                    "text-align": "left",
                    "margin": "2px 0",
                    "padding": "9px 12px",
                    "color": c["text_color"],
                    "background-color": c["link_bg"],
                    "--hover-color": c["link_hover"],
                },
                "nav-link-selected": {
                    "background-color": c["selected_bg"],
                    "color": c["selected_text"],
                    "font-weight": "500",
                },
            },
        )

    selected_page = next(page for page in config.PAGES if page.name == selected)
    selected_page.render(st)


render()