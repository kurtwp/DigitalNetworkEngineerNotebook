"""Net Notebook — NiceGUI network engineering project tracker."""

import logging
import sys

from nicegui import ui

from netbook.database import init_db
from netbook.pages.projects import projects_page
from netbook.pages.worknotes import worknotes_page

# ── Logging setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stderr),
    ],
)
log = logging.getLogger(__name__)

# Initialize database on startup
init_db()


@ui.page("/")
def index() -> None:
    """Render the projects listing page."""
    projects_page()


@ui.page("/worknotes/{project_id}")
def worknotes(project_id: int) -> None:
    """Render the work notes page for a specific project."""
    worknotes_page(project_id)


log.info("Starting Net Notebook on port 8080")
ui.run(
    title="Net Notebook",
    dark=False,
    port=8080,
    reload=False,
    favicon="🖧",
)
