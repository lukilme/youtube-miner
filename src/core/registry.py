from src.core.page import Page

import src.steps.intro.page as intro_module
import src.steps.youtube_scrapper.page as youtube_module
import src.steps.general_analysis.page as general_analysis_module
import src.steps.cleaning.page as cleaning_module
import src.steps.pos_cleaning.page as pos_cleaning_module

PAGES: list[Page] = [
    Page(name="Introdução", icon="house-fill", render=intro_module.render),
    Page(name="YouTube Scrapper", icon="youtube", render=youtube_module.render),
    Page(
        name="Análise Geral",
        icon="bar-chart-fill",
        render=general_analysis_module.render,
    ),
    Page(name="Limpeza", icon="trash-fill", render=cleaning_module.render),
    Page(
        name="Análise Pós-Limpeza",
        icon="graph-up-arrow",
        render=pos_cleaning_module.render,
    ),
]
