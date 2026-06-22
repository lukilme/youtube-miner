import streamlit as st
from streamlit_option_menu import option_menu
import src.core.setting as config

config.conf_browser_setting(st)
config.conf_global_style(st)

st.set_page_config(layout="wide")


def render():

    with st.sidebar:
        selected = option_menu(
            menu_title="Menu",
            options=[page.name for page in config.PAGES],
            icons=[page.icon for page in config.PAGES],
            menu_icon="grid-fill",
            default_index=0,
            orientation="vertical",
            styles={
                "container": {
                    "background-color": "#0f1117",
                    "border-radius": "14px",
                    "border": "1px solid #1f2937",
                },
                "icon": {
                    "color": "#3b82f6",
                    "font-size": "18px",
                },
                "nav-link": {
                    "font-size": "16px",
                    "font-weight": "500",
                    "text-align": "center",
                    "margin": "6px",
                    "padding": "10px 10px",
                    "border-radius": "10px",
                    "color": "#d1d5db",
                    "background-color": "#111827",
                    "--hover-color": "#1e293b",
                    "min-width": "110px",
                },
                "nav-link-selected": {
                    "background-color": "white",
                    "color": "#2563eb",
                },
            },
        )

    selected_page = next(page for page in config.PAGES if page.name == selected)

    selected_page.render(st)


render()
