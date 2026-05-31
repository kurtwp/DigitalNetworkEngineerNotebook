from nicegui import ui
from netbook.database import init_db
from netbook.pages.projects import projects_page
from netbook.pages.worknotes import worknotes_page

# Initialize database on startup
init_db()


@ui.page("/")
def index():
    projects_page()


@ui.page("/worknotes/{project_id}")
def worknotes(project_id: int):
    worknotes_page(project_id)


ui.run(
    title="Net Notebook",
    dark=False,
    port=8080,
    reload=False,
    favicon="🖧",
)
