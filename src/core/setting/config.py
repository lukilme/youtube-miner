from PIL import Image
import streamlit as st
from dotenv import load_dotenv
import logging
from src.core.setting.logger import setup_logger
logger: logging.Logger = setup_logger("config")

load_dotenv()

def conf_browser_setting(st):
    try:
        logo = Image.open("static/ifpb.png")

        st.set_page_config(
            page_title="Tópicos Especiais",
            page_icon=logo,
        )
    except Exception:
        logger.error("arquivo de icone nao foi achado")

        # repeticao desnecessária...
        st.set_page_config(page_title="Tópicos Especiais")


def conf_global_style(st):
    st.markdown(
        """
        <style>

        /* Fundo principal */
        .stApp {
            background-color: #0b0f19;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #0f1117 !important;
            border-right: 1px solid #1f2937;
        }

        /* Conteúdo interno da sidebar */
        section[data-testid="stSidebar"] > div {
            background-color: #0f1117;
        }

        /* Remove cinza padrão */
        div[data-testid="stSidebarContent"] {
            background-color: #0f1117;
        }

        /* Texto da sidebar */
        section[data-testid="stSidebar"] * {
            color: #f3f4f6;
        }
        
        </style>
        """,
        unsafe_allow_html=True,
    )
