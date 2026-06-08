import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import warnings
import os

from IPython.display import display, Markdown
PALETTE = {
    "bg":      "#0D0F1A",
    "panel":   "#141726",
    "accent1": "#FF4D6D",
    "accent2": "#4CC9F0",
    "accent3": "#F4A261",
    "accent4": "#2EC4B6",
    "text":    "#E8EAF0",
    "muted":   "#6C7293",
}


def plot_logn1_example(val1=-0.99, val2: int=10):
    x = np.linspace(val1, val2, 100)
    y = np.log(x + 1)

    fig, ax = plt.subplots(figsize=(9, 5.5), facecolor=PALETTE["bg"])
    ax.set_facecolor(PALETTE["panel"])

    ax.plot(
        x, y, label="y = ln(x + 1)", color=PALETTE["accent2"], linewidth=2.5
    )
    ax.axvline(
        -1,
        color=PALETTE["accent1"],
        linewidth=1.5,
        linestyle="--",
        label="Assíntota (x = -1)",
    )

    ax.axhline(0, color=PALETTE["muted"], linewidth=0.8, linestyle="-", alpha=0.5)
    ax.axvline(0, color=PALETTE["muted"], linewidth=0.8, linestyle="-", alpha=0.5)

    ax.set_title(
        "Gráfico da Função y = ln(x + 1)", color=PALETTE["text"], fontsize=14, pad=15
    )
    ax.set_xlabel("Eixo X", color=PALETTE["text"], fontsize=11)
    ax.set_ylabel("Eixo Y", color=PALETTE["text"], fontsize=11)

    ax.tick_params(colors=PALETTE["text"], which="both")
    for spine in ax.spines.values():
        spine.set_color(PALETTE["muted"])

    ax.grid(True, which="both", linestyle=":", color=PALETTE["muted"], alpha=0.3)

    legend = ax.legend(
        facecolor=PALETTE["bg"], edgecolor=PALETTE["muted"], loc="lower right"
    )
    for text in legend.get_texts():
        text.set_color(PALETTE["text"])

    plt.show()
    
def plot_engagement_rate_example(df, LIKE_WEIGHT=2,COMMENT_WEIGHT=5):

    np.random.seed(42)

    from sympy import symbols

    L, C, V = symbols("L C V", positive=True)

    engagement_rate = (LIKE_WEIGHT*L + COMMENT_WEIGHT*C) / V
    
    display(Markdown(
                    "Se definirmos:\n- L = número de likes\n- C = número de comentários\n- V = número de visualizações"
                    ))
    
    display(engagement_rate)
    
    df["engagement_rate"] = np.where(
        df["view_count"].gt(0),
        (
            df["like_count"].fillna(0) * LIKE_WEIGHT +
            df["comment_count"].fillna(0) * COMMENT_WEIGHT
        ) / df["view_count"],
        np.nan
    )

    fig, ax = plt.subplots(figsize=(9, 5.5), facecolor=PALETTE["bg"])
    ax.set_facecolor(PALETTE["panel"])

    scatter = ax.scatter(
        df["view_count"], 
        df["engagement_rate"], 
        color=PALETTE["accent2"], 
        alpha=0.7, 
        edgecolors=PALETTE["panel"], 
        linewidths=0.5,
        s=50,
        label="Posts / Conteúdos"
    )

    mean_engagement = df["engagement_rate"].mean()
    ax.axhline(
        mean_engagement, 
        color=PALETTE["accent1"], 
        linestyle="--", 
        linewidth=1.5, 
        label=f"Média Geral ({mean_engagement:.2f})"
    )

    ax.set_title("Distribuição da Taxa de Engajamento Ponderada vs Visualizações", color=PALETTE["text"], fontsize=14, pad=15)
    ax.set_xlabel("Visualizações (view_count)", color=PALETTE["text"], fontsize=11)
    ax.set_ylabel("Taxa de Engajamento (engagement_rate)", color=PALETTE["text"], fontsize=11)

    ax.tick_params(colors=PALETTE["text"], which="both")
    for spine in ax.spines.values():
        spine.set_color(PALETTE["muted"])

    ax.grid(True, which="both", linestyle=":", color=PALETTE["muted"], alpha=0.3)

    legend = ax.legend(facecolor=PALETTE["bg"], edgecolor=PALETTE["muted"], loc="upper right")
    for text in legend.get_texts():
        text.set_color(PALETTE["text"])

    plt.tight_layout()
    # plt.savefig("engagement_rate_plot.png", facecolor=PALETTE["bg"])
