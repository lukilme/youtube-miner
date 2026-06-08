import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import matplotlib.ticker as mticker
from matplotlib.gridspec import GridSpec
import seaborn as sns
import warnings
import os

warnings.filterwarnings("ignore")

_CATEGORY_MAP = {
            "filme": "1",
            "filmes": "1",
            "animacao": "1",
            "automovel": "2",
            "automoveis": "2",
            "veiculo": "2",
            "musica": "10",
            "animal": "15",
            "animais": "15",
            "pet": "15",
            "esporte": "17",
            "esportes": "17",
            "viagem": "19",
            "viagens": "19",
            "gaming": "20",
            "jogos": "20",
            "jogo": "20",
            "game": "20",
            "vlog": "22",
            "pessoas": "22",
            "comedia": "23",
            "humor": "23",
            "entretenimento": "24",
            "noticias": "25",
            "politica": "25",
            "tutorial": "26",
            "estilo": "26",
            "beleza": "26",
            "educacao": "27",
            "Educação": "27",
            "ciencia": "28",
            "tecnologia": "28",
            "tech": "28",
            "ong": "29",
        }

CATEGORY_NAMES = {
    "1": "Filmes e Animação",
    "2": "Automóveis e Veículos",
    "10": "Música",
    "15": "Animais e Pets",
    "17": "Esportes",
    "19": "Viagens e Eventos",
    "20": "Games",
    "22": "Pessoas e Blogs",
    "23": "Comédia",
    "24": "Entretenimento",
    "25": "Notícias e Política",
    "26": "Como Fazer e Estilo",
    "27": "Educação",
    "28": "Ciência e Tecnologia",
    "29": "ONGs e Ativismo",
}

class YouTubeDashboard:
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

    def __init__(self, df: pd.DataFrame, output_path: str = "eda_youtube_videos.png"):
        self.df = df.copy()
        self.output_path = output_path

        self.logger = logging.getLogger(self.__class__.__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        plt.rcParams.update({
            "figure.facecolor":  self.PALETTE["bg"],
            "axes.facecolor":    self.PALETTE["panel"],
            "axes.edgecolor":    self.PALETTE["muted"],
            "axes.labelcolor":   self.PALETTE["text"],
            "xtick.color":       self.PALETTE["muted"],
            "ytick.color":       self.PALETTE["muted"],
            "text.color":        self.PALETTE["text"],
            "grid.color":        "#1E2135",
            "grid.linewidth":    0.6,
            "font.family":       "DejaVu Sans",
            "font.size":         10,
        })

        self._prepare_data()

    def _save_and_log(self, fig, filepath):
        fig.savefig(filepath, dpi=155, bbox_inches="tight", facecolor=self.PALETTE["bg"])
        plt.close(fig)
        self.logger.info(f"Plot salvo: {filepath}")

    def _prepare_data(self):
        df = self.df

        null_abs = df.isnull().sum()
        null_pct = df.isnull().mean()
        self.null_df = pd.DataFrame({
            "nulos": null_abs,
            "pct_%": (null_pct * 100).round(1)
        }).sort_values("pct_%", ascending=False)
        self.null_plot_data = self.null_df[self.null_df["nulos"] > 0].sort_values("pct_%")

        if "country" in df.columns:
            self.country_counts = df["country"].value_counts().head(8)
        else:
            self.country_counts = pd.Series(dtype=int)

        if "macro_category" in df.columns:
            self.macro_counts = df["macro_category"].value_counts()
        else:
            self.macro_counts = pd.Series(dtype=int)

        if "source_label" in df.columns and "engagement_rate" in df.columns:
            self.eng_by_source = df.groupby("source_label")["engagement_rate"].median().sort_values()
        else:
            self.eng_by_source = pd.Series(dtype=float)
        print(self.eng_by_source)

        if "year" in df.columns and "month" in df.columns:
            monthly = df.groupby(["year", "month"]).size().reset_index(name="count")
            monthly["period"] = monthly["year"].astype(str) + "-" + monthly["month"].astype(str).str.zfill(2)
            monthly = monthly.sort_values(["year", "month"])
            self.monthly = monthly
        else:
            self.monthly = pd.DataFrame(columns=["period", "count"])

        if "category_id" in df.columns:
            self.top_cats = df["category_id"].value_counts().head(5).index.tolist()
        else:
            self.top_cats = []

        metrics = ["view_count", "like_count", "comment_count", "engagement_rate"]
        available = [m for m in metrics if m in df.columns]
        self.corr = df[available].corr() if len(available) > 1 else pd.DataFrame()
        print(self.corr)
        scatter_cols = ["view_count", "like_count", "source_label"]
        if all(c in df.columns for c in scatter_cols):
            self.scatter_sample = df[scatter_cols].dropna().sample(min(800, len(df)))
        else:
            self.scatter_sample = pd.DataFrame()

    @staticmethod
    def _style_ax(ax, title, palette = PALETTE):
        ax.set_title(title, color=palette["text"], fontsize=11, pad=8, fontweight="bold")
        ax.grid(axis="y", alpha=0.3)
        for spine in ax.spines.values():
            spine.set_edgecolor(palette["muted"])
            spine.set_linewidth(0.6)
    def _plot_mapa_nulidade(self):
        fig, ax = plt.subplots(figsize=(18, 6), facecolor=self.PALETTE["bg"])
        if not self.null_plot_data.empty:
            colors_bar = [
                self.PALETTE["accent1"] if v > 50 else self.PALETTE["accent3"] if v > 10 else self.PALETTE["accent2"]
                for v in self.null_plot_data["pct_%"]
            ]
            bars = ax.barh(self.null_plot_data.index, self.null_plot_data["pct_%"], color=colors_bar, height=0.6)
            ax.set_xlabel("% de Valores Nulos")
            for bar, pct in zip(bars, self.null_plot_data["pct_%"]):
                ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                        f"{pct:.1f}%", va="center", color=self.PALETTE["text"], fontsize=9)
            patches = [
                mpatches.Patch(color=self.PALETTE["accent1"], label=">50% nulo"),
                mpatches.Patch(color=self.PALETTE["accent3"], label="10-50% nulo"),
                mpatches.Patch(color=self.PALETTE["accent2"], label="<10% nulo"),
            ]
            ax.legend(handles=patches, loc="lower right", framealpha=0.2, fontsize=9)
        ax.set_title("Mapa de Nulidade por Coluna", color=self.PALETTE["text"], fontsize=12, pad=10, fontweight="bold")
        ax.set_facecolor(self.PALETTE["panel"])
        for spine in ax.spines.values():
            spine.set_edgecolor(self.PALETTE["muted"])
        fig.tight_layout()
        return fig

    def _plot_distribuicao_views(self):
        fig, ax = plt.subplots(figsize=(10, 6), facecolor=self.PALETTE["bg"])
        if "view_count" in self.df.columns:
            v = self.df["view_count"].dropna()
            if len(v) > 0:
                ax.hist(np.log10(v + 1), bins=40, color=self.PALETTE["accent2"], alpha=0.85, edgecolor="none")
                ax.axvline(np.log10(v.median()), color=self.PALETTE["accent1"], lw=2, linestyle="--",
                           label=f"Mediana: {v.median()/1e3:.0f}K")
                ax.legend(fontsize=8, framealpha=0.2)
        ax.set_xlabel("log₁₀(view_count)")
        self._style_ax = lambda ax, title: YouTubeDashboard._style_ax(ax, title)
        self._style_ax(ax, "Distribuição de Visualizações (log)")
        fig.tight_layout()
        return fig

    def _plot_top_paises(self):
        fig, ax = plt.subplots(figsize=(10, 6), facecolor=self.PALETTE["bg"])
        print(self.country_counts)
        if not self.country_counts.empty:
            colors_c = [self.PALETTE["accent1"], self.PALETTE["accent2"], self.PALETTE["accent4"], self.PALETTE["accent3"]] * 2
            cnt = self.country_counts
            ax.barh(cnt.index[::-1], cnt.values[::-1], color=colors_c[:len(cnt)], height=0.6)
            for i, (val, idx) in enumerate(zip(cnt.values[::-1], cnt.index[::-1])):
                ax.text(val + 5, i, str(val), va="center", fontsize=8, color=self.PALETTE["text"])
        self._style_ax(ax, "Vídeos por País")
        fig.tight_layout()
        return fig

    def _plot_macro_categoria(self):
        fig, ax = plt.subplots(figsize=(8, 8), facecolor=self.PALETTE["bg"])
        if not self.macro_counts.empty:
            mc = self.macro_counts
            wedge_colors = [self.PALETTE["accent1"], self.PALETTE["accent2"], self.PALETTE["accent4"],
                            self.PALETTE["accent3"], self.PALETTE["muted"]]
            wedges, texts, autotexts = ax.pie(
                mc.values, labels=mc.index, autopct="%1.1f%%",
                colors=wedge_colors[:len(mc)], startangle=140, pctdistance=0.75,
                textprops={"color": self.PALETTE["text"], "fontsize": 8},
                wedgeprops={"edgecolor": self.PALETTE["bg"], "linewidth": 1.5}
            )
            for at in autotexts:
                at.set_fontsize(7.5)
        ax.set_title("Macro-categoria", color=self.PALETTE["text"], fontsize=11, pad=8, fontweight="bold")
        fig.tight_layout()
        return fig

    def _plot_engajamento_por_fonte(self):
        fig, ax = plt.subplots(figsize=(10, 6), facecolor=self.PALETTE["bg"])
        if not self.eng_by_source.empty:
            ax.barh(self.eng_by_source.index, self.eng_by_source.values * 100, color=self.PALETTE["accent1"], height=0.5)
            ax.set_xlabel("Engagement Rate Mediano (%)")
            for i, val in enumerate(self.eng_by_source.values):
                ax.text(val*100 + 0.002, i, f"{val*100:.2f}%", va="center", fontsize=8, color=self.PALETTE["text"])
        else:
            print("Catástrofe")
        self._style_ax(ax, "Engajamento por Fonte")
        fig.tight_layout()
        return fig

    def _plot_publicacoes_mes(self):
        fig, ax = plt.subplots(figsize=(10, 6), facecolor=self.PALETTE["bg"])
        
        if not self.monthly.empty:
            monthly = self.monthly
            ax.fill_between(range(len(monthly)), monthly["count"], alpha=0.35, color=self.PALETTE["accent1"])
            ax.plot(range(len(monthly)), monthly["count"], color=self.PALETTE["accent1"], lw=2)
            step = max(1, len(monthly)//6)
            ax.set_xticks(range(0, len(monthly), step))
            ax.set_xticklabels(monthly["period"].iloc[::step], rotation=40, ha="right", fontsize=7)
            ax.set_ylabel("Nº de Vídeos")
        self._style_ax(ax, "Publicações por Mês")
        fig.tight_layout()
        return fig
    
    def _plot_boxplot_views_categoria(self):
        
        _ID_TO_NAME = {}
        for nome, id_str in _CATEGORY_MAP.items():
            if id_str not in _ID_TO_NAME:
                _ID_TO_NAME[id_str] = nome
        
        fig, ax = plt.subplots(figsize=(10, 6), facecolor=self.PALETTE["bg"])
        if self.top_cats and "view_count" in self.df.columns:
            groups = []
            for c in self.top_cats:
                vals = self.df[self.df["category_id"] == c]["view_count"].dropna()
                groups.append(np.log10(vals + 1) if len(vals) > 0 else [])
            if any(len(g) > 0 for g in groups):
                bp = ax.boxplot(groups, patch_artist=True,
                                medianprops={"color": self.PALETTE["accent1"], "lw": 2},
                                whiskerprops={"color": self.PALETTE["muted"]},
                                capprops={"color": self.PALETTE["muted"]},
                                flierprops={"marker": "o", "color": self.PALETTE["accent3"], "alpha": 0.3, "markersize": 3})
                box_colors = [self.PALETTE["accent2"], self.PALETTE["accent4"],
                            self.PALETTE["accent3"], self.PALETTE["accent1"], self.PALETTE["muted"]]
                for patch, col in zip(bp["boxes"], box_colors):
                    patch.set_facecolor(col)
                    patch.set_alpha(0.7)
                
                labels = []
                for c in self.top_cats:
                    cat_id = str(int(c))
                    nome = _ID_TO_NAME.get(cat_id, f"cat {cat_id}")
                    labels.append(nome)
                
                ax.set_xticklabels(labels, fontsize=8)
                ax.set_ylabel("log₁₀(view_count)")
        self._style_ax(ax, "Views por Categoria (Top 5)")
        fig.tight_layout()
        return fig

    def _plot_correlacao(self):
        fig, ax = plt.subplots(figsize=(8, 6), facecolor=self.PALETTE["bg"])
        if not self.corr.empty:
            metrics = self.corr.columns.tolist()
            im = ax.imshow(self.corr.values, cmap="RdYlGn", vmin=-1, vmax=1, aspect="auto")
            ax.set_xticks(range(len(metrics)))
            ax.set_yticks(range(len(metrics)))
            ax.set_xticklabels(metrics, fontsize=8, rotation=30)
            ax.set_yticklabels(metrics, fontsize=8)
            for i in range(len(metrics)):
                for j in range(len(metrics)):
                    ax.text(j, i, f"{self.corr.values[i,j]:.2f}", ha="center", va="center",
                            color="black", fontsize=9, fontweight="bold")
            plt.colorbar(im, ax=ax, fraction=0.046)
        ax.set_title("Correlação entre Métricas", color=self.PALETTE["text"], fontsize=11, pad=8, fontweight="bold")
        fig.tight_layout()
        return fig

    def _plot_scatter_views_likes(self):
        fig, ax = plt.subplots(figsize=(10, 6), facecolor=self.PALETTE["bg"])
        if not self.scatter_sample.empty:
            src_labels = self.scatter_sample["source_label"].unique()
            src_colors = dict(zip(src_labels, [self.PALETTE["accent1"], self.PALETTE["accent2"],
                                               self.PALETTE["accent3"]][:len(src_labels)]))
            print((src_labels))
            for src in src_labels:
                s = self.scatter_sample[self.scatter_sample["source_label"] == src]
                ax.scatter(np.log10(s["view_count"]+1), np.log10(s["like_count"]+1),
                           c=src_colors[src], alpha=0.4, s=12, label=src)
            ax.legend(fontsize=7, framealpha=0.2, markerscale=1.5)
        ax.set_xlabel("log₁₀(views)")
        ax.set_ylabel("log₁₀(likes)")
        print()
        self._style_ax(ax, "Views x Likes por Fonte")
        fig.tight_layout()
        return fig

    def _plot_sumario_limpeza(self):
        fig, ax = plt.subplots(figsize=(10, 6), facecolor=self.PALETTE["bg"])
        ax.axis("off")
        df = self.df
        summary = [
            ("Shape atual",           f"{df.shape[0]:,} × {df.shape[1]}"),
            ("Nulos view_count",      f"{df['view_count'].isnull().sum():,}" if "view_count" in df.columns else "N/A"),
            ("Nulos like_count",      f"{df['like_count'].isnull().sum():,}" if "like_count" in df.columns else "N/A"),
            ("Países únicos",         f"{df['country'].nunique()}" if "country" in df.columns else "N/A"),
            ("Fontes únicas",         f"{df['source_label'].nunique()}" if "source_label" in df.columns else "N/A"),
            ("Categorias",            f"{df['category_id'].nunique()}" if "category_id" in df.columns else "N/A"),
            ("Macro-cats",            f"{df['macro_category'].nunique()}" if "macro_category" in df.columns else "N/A"),
            ("Eng. mediano",          f"{df['engagement_rate'].median():.4f}" if "engagement_rate" in df.columns else "N/A"),
            ("Período",               f"{int(df['year'].min())}-{int(df['year'].max())}" if "year" in df.columns else "N/A"),
        ]
        for i, (label, val) in enumerate(summary):
            y = 0.95 - i * 0.09
            ax.text(0.02, y, label + ":", color=self.PALETTE["muted"], fontsize=9, transform=ax.transAxes)
            ax.text(0.62, y, val, color=self.PALETTE["accent2"], fontsize=9, fontweight="bold", transform=ax.transAxes)
        ax.set_title("Sumário da Limpeza", color=self.PALETTE["text"], fontsize=11, pad=8, fontweight="bold")
        ax.set_facecolor(self.PALETTE["panel"])
        fig.tight_layout()
        return fig

    def generate_separate_plots(self, output_dir="plots"):
        os.makedirs(output_dir, exist_ok=True)
        plots = [
            ("01_mapa_nulidade.png", self._plot_mapa_nulidade),
            ("02_distribuicao_views.png", self._plot_distribuicao_views),
            ("03_top_paises.png", self._plot_top_paises),
            ("04_macro_categoria.png", self._plot_macro_categoria),
            ("05_engajamento_por_fonte.png", self._plot_engajamento_por_fonte),
            ("06_publicacoes_mes.png", self._plot_publicacoes_mes),
            ("07_boxplot_views_categoria.png", self._plot_boxplot_views_categoria),
            ("08_correlacao.png", self._plot_correlacao),
            ("09_scatter_views_likes.png", self._plot_scatter_views_likes),
            ("10_sumario_limpeza.png", self._plot_sumario_limpeza),
        ]
        figures = []
        for filename, plot_func in plots:
            filepath = os.path.join(output_dir, filename)
            fig = plot_func()
            self._save_and_log(fig, filepath)
            figures.append(fig)
        return figures

    def generate_dashboard(self) -> plt.Figure:
        palette = self.PALETTE
        df = self.df
        fig = plt.figure(figsize=(22, 28), facecolor=palette["bg"])
        fig.suptitle("EDA & Limpeza — Vídeos YouTube", fontsize=22, fontweight="bold",
                     color=palette["text"], y=0.995)

        gs = gridspec.GridSpec(4, 3, figure=fig, hspace=0.52, wspace=0.38)

        self._style_ax = lambda ax, title: YouTubeDashboard._style_ax(ax, title, palette)

        ax0 = fig.add_subplot(gs[0, :])
        if not self.null_plot_data.empty:
            colors_bar = [
                palette["accent1"] if v > 50 else
                palette["accent3"] if v > 10 else
                palette["accent2"]
                for v in self.null_plot_data["pct_%"]
            ]
            bars = ax0.barh(self.null_plot_data.index, self.null_plot_data["pct_%"],
                            color=colors_bar, height=0.6)
            ax0.set_xlabel("% de Valores Nulos", color=palette["text"])
            for bar, pct in zip(bars, self.null_plot_data["pct_%"]):
                ax0.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                         f"{pct:.1f}%", va="center", color=palette["text"], fontsize=9)
            patches = [
                mpatches.Patch(color=palette["accent1"], label=">50% nulo"),
                mpatches.Patch(color=palette["accent3"], label="10-50% nulo"),
                mpatches.Patch(color=palette["accent2"], label="<10% nulo"),
            ]
            ax0.legend(handles=patches, loc="lower right", framealpha=0.2, fontsize=9)
        ax0.set_title("Mapa de Nulidade por Coluna", color=palette["text"],
                      fontsize=12, pad=10, fontweight="bold")
        ax0.set_facecolor(palette["panel"])
        for spine in ax0.spines.values():
            spine.set_edgecolor(palette["muted"])

        ax1 = fig.add_subplot(gs[1, 0])
        if "view_count" in df.columns:
            v = df["view_count"].dropna()
            if len(v) > 0:
                ax1.hist(np.log10(v + 1), bins=40, color=palette["accent2"],
                         alpha=0.85, edgecolor="none")
                ax1.axvline(np.log10(v.median()), color=palette["accent1"],
                            lw=2, linestyle="--", label=f"Mediana: {v.median()/1e3:.0f}K")
                ax1.legend(fontsize=8, framealpha=0.2)
        ax1.set_xlabel("log₁₀(view_count)")
        self._style_ax(ax1, "Distribuição de Visualizações (log)")

        ax2 = fig.add_subplot(gs[1, 1])
        if not self.country_counts.empty:
            colors_c = [palette["accent1"], palette["accent2"],
                        palette["accent4"], palette["accent3"]] * 2
            cnt = self.country_counts
            ax2.barh(cnt.index[::-1], cnt.values[::-1],
                     color=colors_c[:len(cnt)], height=0.6)
            for i, (val, idx) in enumerate(zip(cnt.values[::-1], cnt.index[::-1])):
                ax2.text(val + 5, i, str(val), va="center", fontsize=8, color=palette["text"])
        self._style_ax(ax2, "Vídeos por País")

        ax3 = fig.add_subplot(gs[1, 2])
        if not self.macro_counts.empty:
            mc = self.macro_counts
            wedge_colors = [palette["accent1"], palette["accent2"],
                            palette["accent4"], palette["accent3"], palette["muted"]]
            wedges, texts, autotexts = ax3.pie(
                mc.values, labels=mc.index, autopct="%1.1f%%",
                colors=wedge_colors[:len(mc)], startangle=140,
                pctdistance=0.75,
                textprops={"color": palette["text"], "fontsize": 8},
                wedgeprops={"edgecolor": palette["bg"], "linewidth": 1.5}
            )
            for at in autotexts:
                at.set_fontsize(7.5)
        ax3.set_title("Macro-categoria", color=palette["text"], fontsize=11, pad=8, fontweight="bold")

        ax4 = fig.add_subplot(gs[2, 0])
        if not self.eng_by_source.empty:
            ax4.barh(self.eng_by_source.index, self.eng_by_source.values * 100,
                     color=palette["accent4"], height=0.5)
            ax4.set_xlabel("Engagement Rate Mediano (%)")
            for i, val in enumerate(self.eng_by_source.values):
                ax4.text(val*100 + 0.002, i, f"{val*100:.2f}%", va="center",
                         fontsize=8, color=palette["text"])
        self._style_ax(ax4, "Engajamento por Fonte")

        ax5 = fig.add_subplot(gs[2, 1])
        if not self.monthly.empty:
            monthly = self.monthly
            ax5.fill_between(range(len(monthly)), monthly["count"],
                             alpha=0.35, color=palette["accent1"])
            ax5.plot(range(len(monthly)), monthly["count"], color=palette["accent1"], lw=2)
            step = max(1, len(monthly)//6)
            ax5.set_xticks(range(0, len(monthly), step))
            ax5.set_xticklabels(monthly["period"].iloc[::step], rotation=40, ha="right", fontsize=7)
            ax5.set_ylabel("Nº de Vídeos")
        self._style_ax(ax5, "Publicações por Mês")

        ax6 = fig.add_subplot(gs[2, 2])
        if self.top_cats and "view_count" in df.columns:
            groups = []
            for c in self.top_cats:
                vals = df[df["category_id"] == c]["view_count"].dropna()
                if len(vals) > 0:
                    groups.append(np.log10(vals + 1))
                else:
                    groups.append([])
            if any(len(g) > 0 for g in groups):
                bp = ax6.boxplot(groups, patch_artist=True,
                                 medianprops={"color": palette["accent1"], "lw": 2},
                                 whiskerprops={"color": palette["muted"]},
                                 capprops={"color": palette["muted"]},
                                 flierprops={"marker": "o", "color": palette["accent3"],
                                             "alpha": 0.3, "markersize": 3})
                box_colors = [palette["accent2"], palette["accent4"],
                              palette["accent3"], palette["accent1"], palette["muted"]]
                for patch, col in zip(bp["boxes"], box_colors):
                    patch.set_facecolor(col)
                    patch.set_alpha(0.7)
                ax6.set_xticklabels([f"cat {int(c)}" for c in self.top_cats], fontsize=8)
                ax6.set_ylabel("log₁₀(view_count)")
        self._style_ax(ax6, "Views por Categoria (Top 5)")

        ax7 = fig.add_subplot(gs[3, 0])
        if not self.corr.empty:
            metrics = self.corr.columns.tolist()
            im = ax7.imshow(self.corr.values, cmap="RdYlGn", vmin=-1, vmax=1, aspect="auto")
            ax7.set_xticks(range(len(metrics)))
            ax7.set_yticks(range(len(metrics)))
            ax7.set_xticklabels(metrics, fontsize=8, rotation=30)
            ax7.set_yticklabels(metrics, fontsize=8)
            for i in range(len(metrics)):
                for j in range(len(metrics)):
                    ax7.text(j, i, f"{self.corr.values[i,j]:.2f}", ha="center", va="center",
                             color="black", fontsize=9, fontweight="bold")
            plt.colorbar(im, ax=ax7, fraction=0.046)
        ax7.set_title("Correlação entre Métricas", color=palette["text"],
                      fontsize=11, pad=8, fontweight="bold")

        ax8 = fig.add_subplot(gs[3, 1])
        if not self.scatter_sample.empty:
            src_labels = self.scatter_sample["source_label"].unique()
            src_colors = dict(zip(src_labels, [palette["accent1"], palette["accent3"],
                                               palette["accent4"]][:len(src_labels)]))
            for src in src_labels:
                s = self.scatter_sample[self.scatter_sample["source_label"] == src]
                ax8.scatter(np.log10(s["view_count"]+1), np.log10(s["like_count"]+1),
                            c=src_colors[src], alpha=0.4, s=12, label=src)
            ax8.legend(fontsize=7, framealpha=0.2, markerscale=1.5)
        ax8.set_xlabel("log₁₀(views)")
        ax8.set_ylabel("log₁₀(likes)")
        self._style_ax(ax8, "Views x Likes por Fonte")

        ax9 = fig.add_subplot(gs[3, 2])
        ax9.axis("off")
        summary = [
            ("Shape atual",           f"{df.shape[0]:,} × {df.shape[1]}"),
            ("Nulos view_count",      f"{df['view_count'].isnull().sum():,}" if "view_count" in df.columns else "N/A"),
            ("Nulos like_count",      f"{df['like_count'].isnull().sum():,}" if "like_count" in df.columns else "N/A"),
            ("Países únicos",         f"{df['country'].nunique()}" if "country" in df.columns else "N/A"),
            ("Fontes únicas",         f"{df['source_label'].nunique()}" if "source_label" in df.columns else "N/A"),
            ("Categorias",            f"{df['category_id'].nunique()}" if "category_id" in df.columns else "N/A"),
            ("Macro-cats",            f"{df['macro_category'].nunique()}" if "macro_category" in df.columns else "N/A"),
            ("Eng. mediano",          f"{df['engagement_rate'].median():.4f}" if "engagement_rate" in df.columns else "N/A"),
            ("Período",               f"{int(df['year'].min())}-{int(df['year'].max())}" if "year" in df.columns else "N/A"),
        ]
        for i, (label, val) in enumerate(summary):
            y = 0.95 - i * 0.09
            ax9.text(0.02, y, label + ":", color=palette["muted"],  fontsize=9,
                     transform=ax9.transAxes)
            ax9.text(0.62, y, val,         color=palette["accent2"], fontsize=9,
                     fontweight="bold", transform=ax9.transAxes)
        ax9.set_title("Sumário da Limpeza", color=palette["text"], fontsize=11,
                      pad=8, fontweight="bold")
        ax9.set_facecolor(palette["panel"])

        plt.savefig(self.output_path, dpi=155, bbox_inches="tight", facecolor=palette["bg"])
        self.logger.info(f"Dashboard salvo em: {self.output_path}")
        return fig
    
    


warnings.filterwarnings("ignore")

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

ACCENT_LIST = [
    PALETTE["accent2"],
    PALETTE["accent1"],
    PALETTE["accent3"],
    PALETTE["accent4"],
]


def _apply_base_style(fig, axes=None):
    """Aplica estilo escuro padrão a uma figura e lista de Axes."""
    fig.patch.set_facecolor(PALETTE["bg"])
    if axes is None:
        return
    for ax in (axes if hasattr(axes, "__iter__") else [axes]):
        ax.set_facecolor(PALETTE["panel"])
        ax.tick_params(colors=PALETTE["muted"], labelsize=9)
        ax.xaxis.label.set_color(PALETTE["text"])
        ax.yaxis.label.set_color(PALETTE["text"])
        ax.title.set_color(PALETTE["text"])
        for spine in ax.spines.values():
            spine.set_edgecolor(PALETTE["muted"])
            spine.set_linewidth(0.5)


def _fmt_millions(x, _):
    if x >= 1_000_000:
        return f"{x/1_000_000:.1f}M"
    if x >= 1_000:
        return f"{x/1_000:.0f}K"
    return f"{x:.0f}"


def _save_or_show(fig, filename=None, show=True):
    plt.tight_layout()
    if filename:
        fig.savefig(filename, dpi=150, bbox_inches="tight",
                    facecolor=PALETTE["bg"])
        print(f"Salvo em: {filename}")
    if show:
        plt.show()
        
    plt.close(fig)


def plot_boxplots(df: pd.DataFrame, filename: str = None):
    """
    Boxplots lado a lado das métricas numéricas principais.
    Usa escala logarítmica para view_count, like_count e comment_count.
    """
    cols = {
        "view_count":      ("Visualizações", True),
        "like_count":      ("Likes", True),
        "comment_count":   ("Comentários", True),
        "engagement_rate": ("Eng. Rate", False),
        "duration_seconds":("Duração (s)", True),
        "tags_n":          ("# Tags", False),
        "title_len":       ("Len. Título", False),
    }

    fig, axes = plt.subplots(1, len(cols), figsize=(18, 6))
    _apply_base_style(fig, axes)

    for ax, ((col, (label, log_scale)), color) in zip(
        axes, zip(cols.items(), ACCENT_LIST * 4)
    ):
        data = df[col].dropna()
        bp = ax.boxplot(
            data,
            vert=True,
            patch_artist=True,
            widths=0.5,
            medianprops=dict(color=PALETTE["accent1"], linewidth=2.5),
            whiskerprops=dict(color=PALETTE["muted"], linewidth=1.2),
            capprops=dict(color=PALETTE["muted"], linewidth=1.2),
            flierprops=dict(
                marker="o", color=color, alpha=0.4,
                markersize=3, linestyle="none"
            ),
        )
        bp["boxes"][0].set_facecolor(color)
        bp["boxes"][0].set_alpha(0.75)

        ax.set_title(label, fontsize=10, fontweight="bold", pad=8)
        ax.set_xticks([])
        if log_scale:
            ax.set_yscale("log")
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(_fmt_millions))

    fig.suptitle("Boxplots – Métricas do Dataset YouTube",
                 color=PALETTE["text"], fontsize=14, fontweight="bold", y=1.02)
    _save_or_show(fig, filename)
_CATEGORY_MAP = {
            "filme": "1",
            "filmes": "1",
            "animacao": "1",
            "automovel": "2",
            "automoveis": "2",
            "veiculo": "2",
            "musica": "10",
            "animal": "15",
            "animais": "15",
            "pet": "15",
            "esporte": "17",
            "esportes": "17",
            "viagem": "19",
            "viagens": "19",
            "gaming": "20",
            "jogos": "20",
            "jogo": "20",
            "game": "20",
            "vlog": "22",
            "pessoas": "22",
            "comedia": "23",
            "humor": "23",
            "entretenimento": "24",
            "noticias": "25",
            "politica": "25",
            "tutorial": "26",
            "estilo": "26",
            "beleza": "26",
            "educacao": "27",
            "Educação": "27",
            "ciencia": "28",
            "tecnologia": "28",
            "tech": "28",
            "ong": "29",
        }

def plot_histograms(df: pd.DataFrame, filename: str = None):
    """
    Grade 3x3 de histogramas para as principais variáveis numéricas.
    """
    cols = [
        ("log_view_count",       "log(Visualizações)"),
        ("log_like_count",       "log(Likes)"),
        ("log_comment_count",    "log(Comentários)"),
        ("engagement_rate",      "Engagement Rate"),
        ("likes_per_view",       "Likes / View"),
        ("comments_per_view",    "Comentários / View"),
        ("duration_seconds",     "Duração (s)"),
        ("tags_n",               "# Tags"),
        ("title_len",            "Len. Título (chars)"),
    ]

    fig, axes = plt.subplots(3, 3, figsize=(14, 12))
    _apply_base_style(fig, axes.flat)

    for ax, (col, label), color in zip(axes.flat, cols, ACCENT_LIST * 3):
        data = df[col].dropna()
        ax.hist(data, bins=35, color=color, alpha=0.80, edgecolor="none")
        ax.axvline(data.median(), color=PALETTE["accent1"],
                   linewidth=1.8, linestyle="--", label="Mediana")
        ax.set_title(label, fontsize=9, fontweight="bold")
        ax.set_ylabel("Freq.", fontsize=8)
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f"{int(x)}"))

    fig.suptitle("Histogramas – Distribuição das Variáveis",
                 color=PALETTE["text"], fontsize=14, fontweight="bold", y=1.01)
    _save_or_show(fig, filename)

def plot_category_pie(df: pd.DataFrame, filename: str = None):
    """
    Gráfico de pizza (donut) com a distribuição de vídeos por categoria.
    Categorias com menos de 10% são agrupadas em 'Outros'.
    """
    counts = df["category_id"].astype(str).value_counts()

    total = counts.sum()
    percentages = counts / total * 100

    major = counts[percentages >= 10]
    minor = counts[percentages < 10]

    if not minor.empty:
        major["Outros"] = minor.sum()

    labels = [
        CATEGORY_NAMES.get(cat, f"Categoria {cat}")
        if cat != "Outros"
        else "Outros"
        for cat in major.index
    ]

    sizes = major.values

    colors = [
        ACCENT_LIST[i % len(ACCENT_LIST)]
        if i < 4
        else PALETTE["muted"]
        for i in range(len(sizes))
    ]

    fig, ax = plt.subplots(figsize=(9, 9))
    _apply_base_style(fig, ax)
    ax.set_facecolor(PALETTE["bg"])

    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=None,
        autopct=lambda p: f"{p:.1f}%" if p > 3 else "",
        startangle=140,
        colors=colors,
        pctdistance=0.78,
        wedgeprops=dict(
            width=0.55,
            edgecolor=PALETTE["bg"],
            linewidth=2,
        ),
    )

    for at in autotexts:
        at.set_color(PALETTE["bg"])
        at.set_fontsize(9)
        at.set_fontweight("bold")

    ax.legend(
        wedges,
        labels,
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        fontsize=9,
        frameon=False,
        labelcolor=PALETTE["text"],
    )

    centre = plt.Circle((0, 0), 0.45, color=PALETTE["bg"])
    ax.add_patch(centre)

    ax.text(
        0,
        0,
        f"{len(df)}\nvídeos",
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
        color=PALETTE["text"],
    )

    ax.set_title(
        "Distribuição por Categoria",
        color=PALETTE["text"],
        fontsize=14,
        fontweight="bold",
        pad=20,
    )

    _save_or_show(fig, filename)
    
def plot_views_by_category(df: pd.DataFrame, filename: str = None):
    """
    Barras horizontais com view_count médio e mediano por categoria.
    """
    grouped = (
        df.groupby("category_id")["view_count"]
        .agg(["mean", "median"])
        .sort_values("mean", ascending=True)
    )

    fig, ax = plt.subplots(figsize=(12, 7))
    _apply_base_style(fig, ax)

    y = np.arange(len(grouped))
    h = 0.38

    mean_bars = ax.barh(
        y + h / 2,
        grouped["mean"],
        height=h,
        color=PALETTE["accent2"],
        alpha=0.85,
        label="Média",
    )

    median_bars = ax.barh(
        y - h / 2,
        grouped["median"],
        height=h,
        color=PALETTE["accent3"],
        alpha=0.85,
        label="Mediana",
    )

    labels = [
        CATEGORY_NAMES.get(str(cat), f"Categoria {cat}")
        for cat in grouped.index
    ]

    ax.set_yticks(y)
    ax.set_yticklabels(
        labels,
        color=PALETTE["text"],
        fontsize=9,
    )

    ax.xaxis.set_major_formatter(
        mticker.FuncFormatter(_fmt_millions)
    )

    ax.set_xlabel("Visualizações")
    ax.set_title(
        "Views Médias e Medianas por Categoria",
        fontsize=13,
        fontweight="bold",
    )

    ax.legend(
        frameon=False,
        labelcolor=PALETTE["text"],
        fontsize=9,
    )

    ax.grid(
        axis="x",
        color=PALETTE["muted"],
        alpha=0.2,
        linewidth=0.6,
    )

    max_val = grouped[["mean", "median"]].to_numpy().max()
    offset = max_val * 0.01

    for bar in mean_bars:
        value = bar.get_width()
        ax.text(
            value + offset,
            bar.get_y() + bar.get_height() / 2,
            _fmt_millions(value, None),
            va="center",
            ha="left",
            color="white",
            fontsize=8,
            fontweight="bold",
        )

    for bar in median_bars:
        value = bar.get_width()
        ax.text(
            value + offset,
            bar.get_y() + bar.get_height() / 2,
            _fmt_millions(value, None),
            va="center",
            ha="left",
            color="white",
            fontsize=8,
            fontweight="bold",
        )

    _save_or_show(fig, filename)

def plot_scatter_views_likes(df: pd.DataFrame, filename: str = None):
    """
    Scatter plot log(views) vs log(likes) colorido por engagement_rate.
    """
    data = df.dropna(subset=["log_view_count", "log_like_count",
                              "engagement_rate"])

    fig, ax = plt.subplots(figsize=(10, 7))
    _apply_base_style(fig, ax)

    sc = ax.scatter(
        data["log_view_count"], data["log_like_count"],
        c=data["engagement_rate"],
        cmap="plasma", alpha=0.65, s=20, linewidths=0,
    )

    cbar = fig.colorbar(sc, ax=ax, pad=0.02)
    cbar.set_label("Engagement Rate", color=PALETTE["text"], fontsize=9)
    cbar.ax.yaxis.set_tick_params(color=PALETTE["muted"])
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color=PALETTE["muted"])

    m, b = np.polyfit(data["log_view_count"], data["log_like_count"], 1)
    x_line = np.linspace(data["log_view_count"].min(),
                         data["log_view_count"].max(), 200)
    ax.plot(x_line, m * x_line + b,
            color=PALETTE["accent1"], linewidth=2, linestyle="--",
            label=f"Tendência (r²={np.corrcoef(data['log_view_count'], data['log_like_count'])[0,1]**2:.2f})")

    ax.set_xlabel("log(Visualizações)")
    ax.set_ylabel("log(Likes)")
    ax.set_title("Views x Likes — Escala Logarítmica",
                 fontsize=13, fontweight="bold")
    ax.legend(frameon=False, labelcolor=PALETTE["text"], fontsize=9)
    ax.grid(color=PALETTE["muted"], alpha=0.15, linewidth=0.5)

    _save_or_show(fig, filename)


def plot_correlation_heatmap(df: pd.DataFrame, filename: str = None):
    """
    Heatmap de correlação de Pearson entre variáveis numéricas.
    """
    num_cols = [
        "log_view_count", "log_like_count", "log_comment_count",
        "engagement_rate", "likes_per_view", "comments_per_view",
        "log_duration_seconds", "tags_n", "title_len", "published_hour",
    ]
    corr = df[num_cols].corr()

    fig, ax = plt.subplots(figsize=(12, 10))
    _apply_base_style(fig, ax)

    cmap = sns.diverging_palette(340, 190, s=90, l=40, as_cmap=True)
    sns.heatmap(
        corr, ax=ax, cmap=cmap, center=0,
        annot=True, fmt=".2f", annot_kws={"size": 8, "color": "black"},
        linewidths=0.5, linecolor=PALETTE["bg"],
        cbar_kws={"shrink": 0.8},
    )
    ax.set_xticklabels(ax.get_xticklabels(), rotation=40,
                       ha="right", color=PALETTE["text"], fontsize=8)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0,
                       color=PALETTE["text"], fontsize=8)
    ax.set_title("Mapa de Correlação – Variáveis Numéricas",
                 fontsize=13, fontweight="bold", pad=14)

    cbar = ax.collections[0].colorbar
    cbar.ax.yaxis.set_tick_params(color=PALETTE["muted"])
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color=PALETTE["muted"])

    _save_or_show(fig, filename)

def plot_publish_hour(df: pd.DataFrame, filename: str = None):
    """
    Barras verticais mostrando a distribuição de vídeos por hora de publicação.
    """
    hour_counts = df["published_hour"].value_counts().sort_index()
    hours = hour_counts.index
    counts = hour_counts.values

    fig, ax = plt.subplots(figsize=(13, 5))
    _apply_base_style(fig, ax)

    bars = ax.bar(hours, counts, color=PALETTE["accent2"],
                  alpha=0.80, width=0.75, edgecolor="none")

    peak_h = hour_counts.idxmax()
    bars[peak_h].set_color(PALETTE["accent1"])
    bars[peak_h].set_alpha(1.0)

    ax.set_xlabel("Hora de Publicação (UTC)")
    ax.set_ylabel("Quantidade de Vídeos")
    ax.set_title("Distribuição de Publicações por Hora do Dia",
                 fontsize=13, fontweight="bold")
    ax.set_xticks(range(0, 24))
    ax.grid(axis="y", color=PALETTE["muted"], alpha=0.2, linewidth=0.6)

    peak_patch = mpatches.Patch(color=PALETTE["accent1"],
                                label=f"Pico: {peak_h}h ({hour_counts[peak_h]} vídeos)")
    ax.legend(handles=[peak_patch], frameon=False,
              labelcolor=PALETTE["text"], fontsize=9)

    _save_or_show(fig, filename)

def plot_engagement_violin(df: pd.DataFrame, filename: str = None):
    """
    Violin plots do engagement_rate por category_id.
    """
    cats = sorted(df["category_id"].dropna().unique())
    data_by_cat = [df.loc[df["category_id"] == c, "engagement_rate"].dropna()
                   for c in cats]

    fig, ax = plt.subplots(figsize=(12, 6))
    _apply_base_style(fig, ax)

    parts = ax.violinplot(data_by_cat, positions=range(len(cats)),
                          showmedians=True, showextrema=False)
    labels = [
        CATEGORY_NAMES.get(str(cat), f"Categoria {cat}")
        for cat in cats
    ]
    for i, (pc, color) in enumerate(
        zip(parts["bodies"], ACCENT_LIST * (len(cats) // 4 + 1))
    ):
        pc.set_facecolor(color)
        pc.set_alpha(0.65)
        pc.set_edgecolor(PALETTE["bg"])

    parts["cmedians"].set_edgecolor(PALETTE["accent1"])
    parts["cmedians"].set_linewidth(2)

    ax.set_xticks(range(len(cats)))
    ax.set_xticklabels(
        labels,
        rotation=20,
        ha="right",
        color=PALETTE["text"],
        fontsize=9,
    )
    ax.set_facecolor("#eceff2") 
    ax.set_ylabel("Engagement Rate")
    ax.set_title("Engagement Rate por Categoria",
                 fontsize=13, fontweight="bold")
    ax.grid(axis="y", color=PALETTE["muted"], alpha=0.2, linewidth=0.6)

    _save_or_show(fig, filename)

def plot_dashboard(df: pd.DataFrame, filename: str = None):
    """
    Dashboard compacto com 6 gráficos em um único painel.
    """
    fig = plt.figure(figsize=(18, 12))
    fig.patch.set_facecolor(PALETTE["bg"])
    gs = GridSpec(3, 3, figure=fig, hspace=0.5, wspace=0.4)

    axes = [
        fig.add_subplot(gs[0, 0]),
        fig.add_subplot(gs[0, 1]),
        fig.add_subplot(gs[0, 2]),
        fig.add_subplot(gs[1, :2]),
        fig.add_subplot(gs[1, 2]),
        fig.add_subplot(gs[2, :]),
    ]
    _apply_base_style(fig, axes)

    ax = axes[0]
    data = df["log_view_count"].dropna()
    ax.hist(data, bins=30, color=PALETTE["accent2"], alpha=0.8, edgecolor="none")
    ax.axvline(data.median(), color=PALETTE["accent1"],
               linewidth=1.8, linestyle="--")
    ax.set_title("Dist. log(Views)", fontsize=10, fontweight="bold")

    ax = axes[1]
    data = df["engagement_rate"].dropna()
    ax.hist(data, bins=30, color=PALETTE["accent3"], alpha=0.8, edgecolor="none")
    ax.axvline(data.median(), color=PALETTE["accent1"],
               linewidth=1.8, linestyle="--")
    ax.set_title("Dist. Engagement Rate", fontsize=10, fontweight="bold")

    ax = axes[2]
    data = df["duration_seconds"].dropna()
    ax.hist(np.log1p(data), bins=30, color=PALETTE["accent4"],
            alpha=0.8, edgecolor="none")
    ax.axvline(np.log1p(data.median()), color=PALETTE["accent1"],
               linewidth=1.8, linestyle="--")
    ax.set_title("Dist. log(Duração)", fontsize=10, fontweight="bold")

    ax = axes[3]
    d = df.dropna(subset=["log_view_count", "log_like_count", "engagement_rate"])
    sc = ax.scatter(d["log_view_count"], d["log_like_count"],
                    c=d["engagement_rate"], cmap="plasma",
                    alpha=0.55, s=12, linewidths=0)
    m, b = np.polyfit(d["log_view_count"], d["log_like_count"], 1)
    x_ = np.linspace(d["log_view_count"].min(), d["log_view_count"].max(), 100)
    ax.plot(x_, m * x_ + b, color=PALETTE["accent1"],
            linewidth=1.8, linestyle="--")
    ax.set_xlabel("log(Views)")
    ax.set_ylabel("log(Likes)")
    ax.set_title("Views x Likes", fontsize=10, fontweight="bold")
    ax.grid(color=PALETTE["muted"], alpha=0.12, linewidth=0.4)

    ax = axes[4]
    ax.set_facecolor(PALETTE["bg"])
    counts = df["category_id"].value_counts()
    wedges, _, _ = ax.pie(
        counts.values,
        autopct=lambda p: f"{p:.0f}%" if p > 5 else "",
        startangle=90,
        colors=ACCENT_LIST * (len(counts) // 4 + 1),
        wedgeprops=dict(width=0.55, edgecolor=PALETTE["bg"], linewidth=1.5),
        pctdistance=0.75,
    )
    ax.set_title("Categorias", fontsize=10, fontweight="bold")

    ax = axes[5]
    hc = df["published_hour"].value_counts().sort_index()
    bar_colors = [PALETTE["accent1"] if h == hc.idxmax()
                  else PALETTE["accent2"] for h in hc.index]
    ax.bar(hc.index, hc.values, color=bar_colors, alpha=0.82, width=0.75)
    ax.set_xlabel("Hora (UTC)")
    ax.set_ylabel("Qtd. Vídeos")
    ax.set_title("Publicações por Hora", fontsize=10, fontweight="bold")
    ax.set_xticks(range(0, 24))
    ax.grid(axis="y", color=PALETTE["muted"], alpha=0.15, linewidth=0.5)

    fig.suptitle("YouTube Dataset — Dashboard de Análise",
                 color=PALETTE["text"], fontsize=16,
                 fontweight="bold", y=1.01)

    _save_or_show(fig, filename)