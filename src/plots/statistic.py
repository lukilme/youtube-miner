import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

PALETTE = {
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

plt.rcParams.update({
    "figure.facecolor": PALETTE["bg"],
    "axes.facecolor":   PALETTE["panel"],
    "axes.edgecolor":   PALETTE["muted"],
    "axes.labelcolor":  PALETTE["text"],
    "text.color":       PALETTE["text"],
    "xtick.color":      PALETTE["muted"],
    "ytick.color":      PALETTE["muted"],
    "grid.color":       PALETTE["muted"],
    "grid.alpha":       0.3,
})


def plot_log_log_regression(
    df,
    x_col,
    y_col,
    title=None,
    xlabel=None,
    ylabel=None,
    figsize=(10, 7),
    zero_replacement=1,
    palette=None,
    return_stats=False,
):
    """
    Gera um gráfico de dispersão log-log com reta de regressão linear.

    Parâmetros
    ----------
    df : pd.DataFrame
        DataFrame contendo os dados.
    x_col : str
        Nome da coluna a ser usada no eixo X.
    y_col : str
        Nome da coluna a ser usada no eixo Y.
    title : str, opcional
        Título do gráfico.
    xlabel : str, opcional
        Rótulo do eixo X. Se não informado, usa o nome da coluna.
    ylabel : str, opcional
        Rótulo do eixo Y. Se não informado, usa o nome da coluna.
    figsize : tuple, default (10, 7)
        Tamanho da figura.
    zero_replacement : float, default 1
        Valor usado para substituir zeros na coluna Y (evita log(0)).
    palette : dict, opcional
        Dicionário com as cores do tema. Se None, usa PALETTE global.
    return_stats : bool, default False
        Se True, retorna (fig, ax, stats_dict) onde stats_dict contém
        'slope', 'intercept', 'r_value', 'p_value', 'r_squared'.

    Retorna
    matplotlib.figure.Figure, matplotlib.axes.Axes (e opcionalmente dict)
    """
    if palette is None:
        palette = PALETTE

    data = df[[x_col, y_col]].dropna().copy()
    
    # Remove entradas com x <= 0 (log indefinido)
    data = data[data[x_col] > 0]

    # Substitui zeros em y, se existirem, só por garantia
    if (data[y_col] == 0).any():
        data[y_col] = data[y_col].replace(0, zero_replacement)
    # Só por garantia...
    data = data[data[y_col] > 0]

    #  regressão no espaço log10
    log_x = np.log10(data[x_col])
    log_y = np.log10(data[y_col])

    slope, intercept, r_value, p_value, std_err = stats.linregress(log_x, log_y)
    r_squared = r_value ** 2

    x_fit = np.linspace(log_x.min(), log_x.max(), 100)
    y_fit = slope * x_fit + intercept

    rc_params = {
        "figure.facecolor": palette["bg"],
        "axes.facecolor": palette["panel"],
        "axes.edgecolor": palette["muted"],
        "axes.labelcolor": palette["text"],
        "text.color": palette["text"],
        "xtick.color": palette["muted"],
        "ytick.color": palette["muted"],
        "grid.color": palette["muted"],
        "grid.alpha": 0.3,
    }

    with plt.rc_context(rc_params):
        fig, ax = plt.subplots(figsize=figsize)
        ax.set_facecolor(palette["panel"])

        # Dispersão
        ax.scatter(
            data[x_col],
            data[y_col],
            alpha=0.8,
            color=palette["accent1"],
            edgecolor=palette["muted"],
            linewidth=0.3,
            s=10,
            label="Dados",
        )

        ax.plot(
            10 ** x_fit,
            10 ** y_fit,
            color=palette["accent2"],
            linewidth=1,
            label=f"Regressão log-log (R² = {r_squared:.2f})",
        )

        ax.set_xscale("log")
        ax.set_yscale("log")

        # Rótulos
        ax.set_xlabel(xlabel if xlabel else x_col)
        ax.set_ylabel(ylabel if ylabel else y_col)
        ax.set_title(
            title if title else f"Relação entre {x_col} e {y_col}\n(escalas logarítmicas)",
            fontsize=14,
            pad=15,
        )

        # Legenda
        legend = ax.legend(
            frameon=True,
            facecolor=palette["panel"],
            edgecolor=palette["muted"],
            labelcolor=palette["text"],
            fontsize=9,
        )
        legend.get_frame().set_alpha(0.9)

        # Anotação estatística
        annotation_text = (
            f"r de Pearson (log): {r_value:.3f}\n"
            f"p-valor: {p_value:.2e}\n"
            f"Inclinação: {slope:.3f}"
        )
        ax.text(
            0.95,
            0.05,
            annotation_text,
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            bbox=dict(
                boxstyle="round,pad=0.5",
                facecolor=palette["bg"],
                edgecolor=palette["muted"],
                alpha=0.8,
            ),
            color=palette["text"],
            fontsize=9,
        )

        ax.grid(True, which="both", linestyle="--", alpha=0.4)
        plt.tight_layout()

    if return_stats:
        stats_dict = {
            "slope": slope,
            "intercept": intercept,
            "r_value": r_value,
            "p_value": p_value,
            "r_squared": r_squared,
        }
        return fig, ax, stats_dict
    return fig, ax