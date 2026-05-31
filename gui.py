import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import logging
import os
from pathlib import Path

# Importe as classes necessárias do seu módulo (ajuste o caminho conforme sua estrutura)
# Supondo que o código fornecido esteja em "youtube_client.py"
try:
    from api_getter import YouTubeClient, RateLimitConfig, LimitsConfig, YouTubeAuthError, YouTubeQuotaError
except ImportError:
    # Caso você tenha renomeado o arquivo ou queira incorporar diretamente, ajuste:
    # Aqui assumimos que o código original está em um arquivo separado.
    raise ImportError("Certifique-se de que o arquivo 'youtube_client.py' está no mesmo diretório e contém as classes necessárias.")


class QueueHandler(logging.Handler):
    """Handler personalizado para redirecionar logs para o widget ScrolledText."""
    def __init__(self, log_widget):
        super().__init__()
        self.log_widget = log_widget

    def emit(self, record):
        msg = self.format(record)
        # Usa after para atualizar a UI de forma thread-safe
        self.log_widget.after(0, self.write_log, msg)

    def write_log(self, msg):
        self.log_widget.configure(state='normal')
        self.log_widget.insert(tk.END, msg + '\n')
        self.log_widget.see(tk.END)
        self.log_widget.configure(state='disabled')


class YouTubeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Data Extractor")
        self.geometry("800x700")
        self.resizable(True, True)

        # Variáveis de configuração
        self.api_key_var = tk.StringVar(value=os.getenv("YOUTUBE_API_KEY", ""))
        self.region_var = tk.StringVar(value="BR")
        self.total_videos_var = tk.IntVar(value=50)
        self.category_var = tk.StringVar(value="")          # opcional, ex: "tecnologia"
        self.comments_pages_var = tk.IntVar(value=1)
        self.include_channels_var = tk.BooleanVar(value=False)
        self.output_dir_var = tk.StringVar(value="output")
        self.format_var = tk.StringVar(value="csv")

        self.rate_limit_var = tk.DoubleVar(value=3.0)
        self.burst_var = tk.IntVar(value=2)
        self.max_videos_limit_var = tk.IntVar(value=120)
        self.max_comments_limit_var = tk.IntVar(value=100)

        # Widget de log
        self.log_text = scrolledtext.ScrolledText(self, state='disabled', wrap=tk.WORD,
                                                  font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Configura logging
        self._setup_logging()

        # Painel de controle
        control_frame = ttk.Frame(self)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        # Notebook para organizar as abas
        notebook = ttk.Notebook(control_frame)
        notebook.pack(fill=tk.X, expand=True)

        # Aba principal
        main_tab = ttk.Frame(notebook)
        notebook.add(main_tab, text="Pipeline")

        # Aba avançada (limites)
        adv_tab = ttk.Frame(notebook)
        notebook.add(adv_tab, text="Avançado")

        # ---- Preenchimento da aba principal ----
        row = 0
        ttk.Label(main_tab, text="API Key:").grid(row=row, column=0, sticky='e', padx=2, pady=2)
        ttk.Entry(main_tab, textvariable=self.api_key_var, width=40).grid(row=row, column=1, sticky='w', padx=2, pady=2)

        row += 1
        ttk.Label(main_tab, text="Região:").grid(row=row, column=0, sticky='e', padx=2, pady=2)
        ttk.Entry(main_tab, textvariable=self.region_var, width=8).grid(row=row, column=1, sticky='w', padx=2, pady=2)

        row += 1
        ttk.Label(main_tab, text="Total de vídeos:").grid(row=row, column=0, sticky='e', padx=2, pady=2)
        ttk.Spinbox(main_tab, from_=1, to=500, textvariable=self.total_videos_var, width=5).grid(row=row, column=1, sticky='w', padx=2, pady=2)

        row += 1
        ttk.Label(main_tab, text="Categoria (opcional):").grid(row=row, column=0, sticky='e', padx=2, pady=2)
        ttk.Entry(main_tab, textvariable=self.category_var, width=20).grid(row=row, column=1, sticky='w', padx=2, pady=2)

        row += 1
        ttk.Label(main_tab, text="Páginas de comentários:").grid(row=row, column=0, sticky='e', padx=2, pady=2)
        ttk.Spinbox(main_tab, from_=1, to=10, textvariable=self.comments_pages_var, width=5).grid(row=row, column=1, sticky='w', padx=2, pady=2)

        row += 1
        ttk.Checkbutton(main_tab, text="Incluir detalhes dos canais", variable=self.include_channels_var).grid(row=row, column=1, sticky='w', padx=2, pady=2)

        row += 1
        ttk.Label(main_tab, text="Diretório de saída:").grid(row=row, column=0, sticky='e', padx=2, pady=2)
        dir_frame = ttk.Frame(main_tab)
        dir_frame.grid(row=row, column=1, sticky='w', padx=2, pady=2)
        ttk.Entry(dir_frame, textvariable=self.output_dir_var, width=20).pack(side=tk.LEFT, padx=(0,2))
        ttk.Button(dir_frame, text="...", width=3, command=self.browse_output_dir).pack(side=tk.LEFT)

        row += 1
        ttk.Label(main_tab, text="Formato:").grid(row=row, column=0, sticky='e', padx=2, pady=2)
        fmt_combo = ttk.Combobox(main_tab, textvariable=self.format_var, values=["csv", "json"], state='readonly', width=5)
        fmt_combo.grid(row=row, column=1, sticky='w', padx=2, pady=2)

        # Botão de execução
        row += 1
        self.run_button = ttk.Button(main_tab, text="Executar Pipeline", command=self.start_pipeline)
        self.run_button.grid(row=row, column=1, sticky='w', pady=5)

        # ---- Aba avançada (limites) ----
        row_adv = 0
        ttk.Label(adv_tab, text="Requisições por segundo:").grid(row=row_adv, column=0, sticky='e', padx=2, pady=2)
        ttk.Entry(adv_tab, textvariable=self.rate_limit_var, width=8).grid(row=row_adv, column=1, sticky='w', padx=2, pady=2)

        row_adv += 1
        ttk.Label(adv_tab, text="Burst:").grid(row=row_adv, column=0, sticky='e', padx=2, pady=2)
        ttk.Entry(adv_tab, textvariable=self.burst_var, width=8).grid(row=row_adv, column=1, sticky='w', padx=2, pady=2)

        row_adv += 1
        ttk.Label(adv_tab, text="Máx. vídeos (limite):").grid(row=row_adv, column=0, sticky='e', padx=2, pady=2)
        ttk.Entry(adv_tab, textvariable=self.max_videos_limit_var, width=8).grid(row=row_adv, column=1, sticky='w', padx=2, pady=2)

        row_adv += 1
        ttk.Label(adv_tab, text="Máx. comentários/vídeo:").grid(row=row_adv, column=0, sticky='e', padx=2, pady=2)
        ttk.Entry(adv_tab, textvariable=self.max_comments_limit_var, width=8).grid(row=row_adv, column=1, sticky='w', padx=2, pady=2)

    def _setup_logging(self):
        """Configura o logger para ser capturado pelo widget de log."""
        logger = logging.getLogger(__name__.split('.')[0])  # nome raiz do logger do cliente
        # Remove handlers existentes para evitar duplicação
        logger.handlers.clear()
        # Adiciona nosso handler
        handler = QueueHandler(self.log_text)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Captura também logs de outros módulos (ex: requests)
        logging.getLogger('requests').addHandler(handler)
        logging.getLogger('youtube_transcript_api').addHandler(handler)
        logging.getLogger('api_data_class').addHandler(handler)

    def browse_output_dir(self):
        directory = filedialog.askdirectory(initialdir=self.output_dir_var.get() or '.')
        if directory:
            self.output_dir_var.set(directory)

    def start_pipeline(self):
        """Inicia a execução do pipeline em uma thread separada."""
        # Validações básicas
        if not self.api_key_var.get().strip():
            messagebox.showerror("Erro", "API Key não informada.")
            return

        self.run_button.configure(state='disabled')
        # Cria thread
        thread = threading.Thread(target=self._run_pipeline_thread, daemon=True)
        thread.start()

    def _run_pipeline_thread(self):
        """Executa o pipeline e trata exceções."""
        try:
            client = YouTubeClient(
                api_key=self.api_key_var.get().strip() or None,
                rate_limit=RateLimitConfig(
                    requests_per_second=self.rate_limit_var.get(),
                    burst=self.burst_var.get()
                ),
                limits=LimitsConfig(
                    max_videos=self.max_videos_limit_var.get(),
                    max_comments_per_video=self.max_comments_limit_var.get()
                )
            )

            total = self.total_videos_var.get()
            region = self.region_var.get().upper()
            category = self.category_var.get().strip()
            comments_pages = self.comments_pages_var.get()
            include_channels = self.include_channels_var.get()
            output_dir = self.output_dir_var.get()
            fmt = self.format_var.get()

            # Se categoria foi informada, use fetch_videos_by_category; senão use run_pipeline
            if category:
                # fetch_videos_by_category usa páginas internamente; passamos max_items = total
                videos = client.fetch_videos_by_category(
                    category=category,
                    region_code=region,
                    max_items=total,
                    pages=(total // 50) + 1
                )
                # A partir daqui, executamos manualmente o resto do pipeline (comentários, canais)
                all_comments = []
                for idx, video in enumerate(videos, start=1):
                    logging.info("Comentários %d/%d – %s", idx, len(videos), video.video_id)
                    comments = client.fetch_comments(
                        video_id=video.video_id,
                        max_pages=comments_pages,
                    )
                    for c in comments:
                        c.video_title = video.title
                        c.channel_title = video.channel_title
                        c.video_view_count = video.view_count
                        c.video_like_count = video.like_count
                        c.video_comment_count = video.comment_count
                    all_comments.extend(comments)

                channels = []
                if include_channels:
                    unique_ids = list({v.channel_id for v in videos if v.channel_id})
                    logging.info("Buscando detalhes de %d canais únicos.", len(unique_ids))
                    channels = client.fetch_channels_by_ids(unique_ids)

                # Salva
                save = client.save_csv if fmt == "csv" else client.save_json
                region_lower = region.lower()
                os.makedirs(output_dir, exist_ok=True)
                save(
                    [v.to_dict() for v in videos],
                    os.path.join(output_dir, f"youtube_videos_{region_lower}.{fmt}")
                )
                save(
                    [c.to_dict() for c in all_comments],
                    os.path.join(output_dir, f"youtube_comments_{region_lower}.{fmt}")
                )
                if channels:
                    save(
                        [ch.to_dict() for ch in channels],
                        os.path.join(output_dir, f"youtube_channels_{region_lower}.{fmt}")
                    )
                logging.info("Pipeline finalizado. Arquivos salvos em '%s'.", output_dir)
            else:
                # Usa o pipeline padrão da classe
                client.run_pipeline(
                    total_videos=total,
                    region=region,
                    comments_pages=comments_pages,
                    include_channels=include_channels,
                    output_dir=output_dir,
                    fmt=fmt,
                )

            self.after(0, lambda: messagebox.showinfo("Sucesso", f"Pipeline concluído. Resultados em '{output_dir}'."))

        except YouTubeAuthError as e:
            self.after(0, lambda: messagebox.showerror("Erro de autenticação", str(e)))
        except YouTubeQuotaError as e:
            self.after(0, lambda: messagebox.showerror("Erro de cota", str(e)))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro", f"Ocorreu um erro:\n{str(e)}"))
        finally:
            self.after(0, lambda: self.run_button.configure(state='normal'))


if __name__ == "__main__":
    app = YouTubeApp()
    app.mainloop()