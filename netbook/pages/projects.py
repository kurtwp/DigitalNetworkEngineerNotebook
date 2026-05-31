"""Projects listing page for Net Notebook."""

import sqlite3
from typing import Callable

from nicegui import ui

from netbook.database import (
    get_all_projects,
    create_project,
    delete_project,
    update_project,
)
from netbook.theme import (
    apply_global_styles,
    DARK_BG,
    PANEL_BG,
    BORDER,
    ACCENT,
    ACCENT_DIM,
    TEXT_PRI,
    TEXT_SEC,
    TEXT_MUTED,
    STATUS_COLORS,
)


def projects_page() -> None:
    """Render the main projects listing page."""
    apply_global_styles()

    with ui.element("div").style(
        f"min-height:100vh; background:{DARK_BG}; padding:40px 48px;"
    ):
        # Header
        with ui.row().style(
            "align-items:center; justify-content:space-between; margin-bottom:32px; max-width:860px;"
        ):
            with ui.column().style("gap:2px;"):
                ui.label("NET NOTEBOOK").style(
                    f"font-family:'JetBrains Mono',monospace; font-size:11px;"
                    f"letter-spacing:0.18em; color:{ACCENT}; font-weight:700;"
                )
                ui.label("Projects").style(
                    f"font-size:26px; font-weight:600; color:{TEXT_PRI}; line-height:1.2;"
                )

            new_btn = ui.button("+ New Project").style(
                f"background:{ACCENT} !important; color:#ffffff !important; font-weight:600 !important;"
                f"font-size:13px !important; padding:9px 22px !important;"
                f"border-radius:6px !important; border:none !important;"
                f"box-shadow: 0 2px 6px rgba(46,125,50,0.3) !important;"
                f"text-transform: none !important;"
            )

        # Project cards
        cards_col = ui.column().style("gap:10px; width:100%; max-width:860px;")

        def refresh_projects() -> None:
            cards_col.clear()
            projects = get_all_projects()
            with cards_col:
                if not projects:
                    with ui.element("div").style(
                        f"background:{PANEL_BG}; border:2px dashed {BORDER};"
                        f"border-radius:10px; padding:60px; text-align:center;"
                    ):
                        ui.icon("folder_open").style(
                            f"font-size:44px; color:{TEXT_MUTED};"
                        )
                        ui.label("No projects yet").style(
                            f"color:{TEXT_MUTED}; font-size:15px; margin-top:14px;"
                        )
                        ui.label("Click '+ New Project' to get started").style(
                            f"color:{TEXT_MUTED}; font-size:13px; margin-top:4px;"
                        )
                else:
                    for p in projects:
                        _project_card(p, refresh_projects)

        refresh_projects()

        # ── New project dialog ────────────────────────────────────────────────
        with ui.dialog() as new_dialog, ui.card().style(
            f"background:{PANEL_BG}; border:1px solid {BORDER}; border-radius:10px;"
            f"padding:28px 32px; min-width:500px; gap:0;"
            f"box-shadow: 0 8px 32px rgba(0,0,0,0.12);"
        ):
            ui.label("New Project").style(
                f"font-size:19px; font-weight:600; color:{TEXT_PRI}; margin-bottom:20px;"
            )
            name_in = ui.input("Project Name *").props("outlined").style("width:100%;")
            ticket_in = ui.input("Ticket Number (optional)").style(
                "width:100%; margin-top:12px;"
            )
            type_in = (
                ui.select(
                    [
                        "",
                        "Decommission",
                        "New Install",
                        "Migration",
                        "Upgrade",
                        "Troubleshoot",
                        "Lab",
                        "Other",
                    ],
                    label="Type of Work",
                    value="",
                )
                .props("outlined")
                .style("width:100%; margin-top:12px;")
            )
            date_in = ui.input("Scheduled Date (MM-DD-YYYY)").style(
                "width:100%; margin-top:12px;"
            )
            status_in = (
                ui.select(
                    ["active", "on-hold", "complete", "scheduled"],
                    label="Status",
                    value="active",
                )
                .props("outlined")
                .style("width:100%; margin-top:12px;")
            )

            with ui.row().style("margin-top:26px; gap:10px; justify-content:flex-end;"):
                ui.button("Cancel", on_click=new_dialog.close).style(
                    f"background:transparent !important; color:{TEXT_SEC} !important;"
                    f"border:1px solid {BORDER} !important; padding:8px 18px !important;"
                    f"border-radius:6px !important; text-transform:none !important;"
                )

                def do_create() -> None:
                    if not name_in.value.strip():
                        ui.notify("Project name is required", color="negative")
                        return
                    create_project(
                        name=name_in.value.strip(),
                        ticket_num=ticket_in.value.strip(),
                        type_of_work=type_in.value,
                        status=status_in.value,
                        scheduled_date=date_in.value.strip(),
                    )
                    new_dialog.close()
                    refresh_projects()
                    ui.notify("Project created", color="positive")

                ui.button("Create", on_click=do_create).style(
                    f"background:{ACCENT} !important; color:#ffffff !important; font-weight:600 !important;"
                    f"padding:8px 24px !important; border-radius:6px !important;"
                    f"border:none !important; text-transform:none !important;"
                )

        def open_new_dialog() -> None:
            """Clear inputs and open the new project dialog."""
            name_in.value = ""
            ticket_in.value = ""
            type_in.value = ""
            date_in.value = ""
            status_in.value = "active"
            new_dialog.open()

        new_btn.on("click", open_new_dialog)


def _project_card(project: sqlite3.Row, refresh_cb: Callable[[], None]) -> None:
    """Render a single project card."""
    status = (project["status"] or "active").lower()
    sc = STATUS_COLORS.get(status, TEXT_MUTED)
    ticket = project["ticket_num"] or ""
    name = project["name"] or ""
    tow = project["type_of_work"] or ""
    date = project["scheduled_date"] or ""

    with ui.element("div").style(
        f"background:{PANEL_BG}; border:1px solid {BORDER}; border-radius:8px;"
        f"padding:14px 18px; transition: box-shadow 0.15s, border-color 0.15s;"
        f"box-shadow: 0 1px 4px rgba(0,0,0,0.05);"
        f"display:flex; align-items:center; gap:14px; width:100%;"
    ):
        # Status dot
        ui.element("span").style(
            f"width:9px; height:9px; border-radius:50%; background:{sc};"
            f"flex-shrink:0; display:inline-block;"
        )

        # Text block
        with ui.column().style("gap:2px; flex:1; min-width:0; overflow:hidden;"):
            with ui.row().style(
                "align-items:baseline; gap:10px; flex-wrap:nowrap; min-width:0;"
            ):
                if ticket:
                    ui.label(ticket).style(
                        f"font-family:'JetBrains Mono',monospace; font-size:14px;"
                        f"font-weight:700; color:{TEXT_PRI}; white-space:nowrap; flex-shrink:0;"
                    )
                if name and name != ticket:
                    ui.label(name).style(
                        f"font-size:13px; color:{TEXT_SEC}; white-space:nowrap;"
                        f"overflow:hidden; text-overflow:ellipsis;"
                    )

            with ui.row().style("align-items:center; gap:14px;"):
                if tow:
                    ui.label(tow).style(f"font-size:12px; color:{TEXT_SEC};")
                if date:
                    with ui.row().style("align-items:center; gap:3px;"):
                        ui.icon("event").style(f"font-size:12px; color:{TEXT_MUTED};")
                        ui.label(date).style(
                            f"font-size:12px; color:{TEXT_MUTED};"
                            f"font-family:'JetBrains Mono',monospace;"
                        )

        # Action buttons
        with ui.row().style("gap:8px; align-items:center; flex-shrink:0;"):
            open_btn = ui.button("OPEN").style(
                f"background:{ACCENT} !important; color:#ffffff !important;"
                f"font-size:12px !important; font-weight:700 !important;"
                f"padding:6px 18px !important; border-radius:5px !important;"
                f"border:none !important; letter-spacing:0.05em !important;"
                f"text-transform:none !important; min-width:72px !important;"
                f"box-shadow: 0 1px 4px rgba(46,125,50,0.25) !important;"
            )
            open_btn.on(
                "click", lambda pid=project["id"]: ui.navigate.to(f"/worknotes/{pid}")
            )

            del_btn = ui.button("", icon="delete").style(
                f"background:#f5f5f5 !important; color:#757575 !important;"
                f"border:1px solid #e0e0e0 !important; border-radius:5px !important;"
                f"min-width:36px !important; width:36px !important; padding:6px !important;"
            )

            def confirm_delete(
                pid: int = project["id"], pname: str = project["name"]
            ) -> None:
                with ui.dialog() as d, ui.card().style(
                    f"background:{PANEL_BG}; border:1px solid {BORDER}; border-radius:10px;"
                    f"padding:26px; min-width:380px; box-shadow:0 8px 32px rgba(0,0,0,0.12);"
                ):
                    ui.label(f'Delete "{pname}"?').style(
                        f"font-size:16px; font-weight:600; color:{TEXT_PRI}; margin-bottom:8px;"
                    )
                    ui.label("All associated data will be permanently removed.").style(
                        f"font-size:13px; color:{TEXT_SEC}; margin-bottom:22px;"
                    )
                    with ui.row().style("gap:10px; justify-content:flex-end;"):
                        ui.button("Cancel", on_click=d.close).style(
                            f"background:transparent !important; color:{TEXT_SEC} !important;"
                            f"border:1px solid {BORDER} !important; padding:7px 16px !important;"
                            f"border-radius:6px !important; text-transform:none !important;"
                        )

                        def do_del(dialog: ui.dialog = d) -> None:
                            delete_project(pid)
                            dialog.close()
                            refresh_cb()
                            ui.notify("Project deleted", color="negative")

                        ui.button("Delete", on_click=do_del).style(
                            "background:#c62828 !important; color:white !important;"
                            "font-weight:600 !important; padding:7px 18px !important;"
                            "border-radius:6px !important; border:none !important;"
                            "text-transform:none !important;"
                        )
                d.open()

            del_btn.on("click", confirm_delete)
