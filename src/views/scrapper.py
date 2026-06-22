import streamlit as st
import inspect
from typing import get_type_hints, Any
from pathlib import Path
import sys

ROOT: Path = Path.cwd().parent
sys.path.append(str(ROOT))
from src.core.interface import IYouTubeClient


def _format_type(t: Any) -> str:
    """Formata um tipo para exibição amigável."""
    if hasattr(t, "__name__"):
        return t.__name__
    return str(t).replace("typing.", "")


def _render_method(method_name: str, method):
    """Renderiza um método da classe com seus detalhes."""
    with st.expander(f"🔹 {method_name}", expanded=False):
        sig = inspect.signature(method)
        params = list(sig.parameters.values())

        try:
            hints = get_type_hints(method)
        except Exception:
            hints = {}

        if params:
            st.markdown("**Parâmetros:**")
            for p in params:
                if p.name == "self":
                    continue
                tipo = hints.get(p.name, "Any")
                tipo_str = _format_type(tipo)
                default = (
                    "" if p.default is inspect.Parameter.empty else f" = {p.default}"
                )
                st.markdown(f"- `{p.name}`: `{tipo_str}`{default}")
        else:
            st.markdown("**Parâmetros:** Nenhum")

        return_annotation = hints.get("return", "None")
        st.markdown(f"**Retorno:** `{_format_type(return_annotation)}`")

        doc = inspect.getdoc(method)
        if doc:
            st.markdown("**Descrição:**")
            st.markdown(doc.strip())
        else:
            st.markdown("*(sem descrição)*")


def render(st):
    """Página de documentação da interface IYouTubeClient."""
    st.markdown(
        """
        <h1 style='text-align: center; color: #3b82f6;'>
            Documentação da API — YouTube Client
        </h1>
        <p style='text-align: center; font-size: 1.2rem; color: #9ca3af;'>
            Interface abstrata que define todos os métodos disponíveis para interagir com a YouTube Data API v3.
        </p>
        <hr>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Ver definição da classe (código)", expanded=False):
        try:
            source = inspect.getsource(IYouTubeClient)
            st.code(source, language="python")
        except Exception:
            st.warning("Não foi possível obter o código-fonte.")

    st.markdown("## Métodos da Interface")

    methods = inspect.getmembers(IYouTubeClient, predicate=inspect.isfunction)
    methods = [(name, method) for name, method in methods if not name.startswith("_")]

    if not methods:
        st.info("Nenhum método público encontrado.")
        return

    methods.sort(key=lambda x: x[0])

    for name, method in methods:
        _render_method(name, method)

    st.markdown("---")
    st.caption(
        "Esta documentação é gerada automaticamente a partir do código-fonte "
        "usando `inspect` e `typing.get_type_hints`."
    )
