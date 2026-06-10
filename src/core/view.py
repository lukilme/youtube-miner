from IPython.display import Markdown, display, HTML
import pandas as pd

PALETTE: dict[str, str] = {
    "bg": "#0D0F1A",
    "panel": "#141726",
    "accent1": "#FF4D6D",
    "accent2": "#4CC9F0",
    "accent3": "#F4A261",
    "accent4": "#2EC4B6",
    "accent5": "#9B5DE5",
    "accent6": "#FDD167",
    "accent7": "#06D6A0",
    "accent8": "#EF476F",
    "accent9": "#118AB2",
    "accent10": "#FF9F1C",
    "accent11": "#7B2CBF",
    "accent12": "#80ED99",
    "text": "#E8EAF0",
    "muted": "#6C7293",
}


def printf(text_format):
    display(Markdown(text_format))


def box(text: str, color: str = "#4CC9F0", background: str = "#141726"):
    display(
        HTML(
            f"""
            <div style="
                border: 3px solid {PALETTE["accent1"]};
                background: {PALETTE["bg"]};
                padding: 12px;
                margin: 10px 0;
                border-radius: 6px;
                color: white;
            ">
                {text}
            </div>
            """
        )
    )


def md(
    text: str,
    level: int | None = None,
) -> None:
    if level is not None:
        text = f'{"#" * level} {text}'

    display(Markdown(text))


def show_dataframe(
    df: pd.DataFrame,
    title: str = "",
    color: str = "#4CC9F0",
    background: str = "#141726",
    max_rows: int = 15,
) -> None:
    """
    Exibe um DataFrame truncado (primeiros 5, meio 5, últimos 5)
    dentro de uma caixa estilizada, com título Markdown opcional.
    """
    if title:
        md(title)

    n: int = len(df)
    if n <= max_rows:
        html_table: str = _styled_table(df, color)
        display(
            HTML(
                f"""
            <div style="
                border-left: 6px solid {color};
                background: {background};
                padding: 4px;
                border-radius: 8px;
                color: white;
                font-family: 'Segoe UI', sans-serif;
            ">
                {html_table}
            </div>
        """
            )
        )
        return

    head: pd.DataFrame = df.head(5)
    tail: pd.DataFrame = df.tail(5)

    middle_start: int = n // 2 - 2
    middle_start = max(5, middle_start)
    middle_end: int = middle_start + 5
    if middle_end > n - 5:
        middle_end = n - 5
        middle_start = middle_end - 5
    middle = df.iloc[middle_start:middle_end]

    head_html: str = _styled_table(head, color)
    # middle_html = _styled_table(middle, color)
    # tail_html = _styled_table(tail, color)

    # separator = """
    #     <div style="text-align:center; color:#888; padding:6px 0; font-style:italic;">
    #         • • •
    #     </div>
    # """

    # full_content = f"""
    # {head_html}
    # {separator}
    # {middle_html}
    # {separator}
    # {tail_html}
    # <div style="font-size:12px; color:#aaa; margin-top:6px;">
    #     Mostrando 15 de {n} linhas
    # </div>
    # """
    # separator = """
    #     <div style="text-align:center; color:#888; padding:6px 0; font-style:italic;">
    #         • • •
    #     </div>
    # """

    full_content = f"""
    {head_html}
    <div style="font-size:12px; color:#aaa; margin-top:6px;">
        Mostrando 15 de {n} linhas
    </div>
     """
    display(
        HTML(
            f"""
        <div style="
            background: {background};
            padding: 16px;
            border-radius: 8px;
            color: white;
            font-family: 'Segoe UI', sans-serif;
        ">
            {full_content}
        </div>
    """
        )
    )


def _styled_table(df: pd.DataFrame, color: str) -> str:
    """Retorna o HTML de uma tabela pandas com estilo noturno."""
    html = df.to_html(border=0, classes="dataframe-table", index=True)
    return f"""
    <style>
        .dataframe-table {{
            width: 100%;
            border-collapse: collapse;
            color: #e0e0e0;
            font-size: 14px;
            margin: 4px 0;
        }}
        .dataframe-table th {{
            color: #0b0d17;
            padding: 8px 10px;
            text-align: left;
            font-weight: 600;
        }}
        .dataframe-table td {{
            padding: 6px 10px;
            border-bottom: 1px solid #2a2e3f;
        }}
        .dataframe-table tr:hover {{
            background-color: #1e2132;
        }}
    </style>
    {html}
    """


def show_dataframe_with_box(df, title="", **kwargs):
    html_table = df.to_html(border=0, classes="dataframe-table")
    styled = f"<style>... (mesmo CSS anterior) ...</style>{html_table}"
    if title:
        md(title)
    box(styled, **kwargs)
