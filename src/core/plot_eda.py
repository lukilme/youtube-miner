import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import warnings
import os

warnings.filterwarnings("ignore")


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