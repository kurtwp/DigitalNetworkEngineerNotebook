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

    with ui.element("div").classes("min-h-screen px-16 py-14").style(
        f"background:{DARK_BG};"
    ):
        # Header
        with ui.row().classes("items-center justify-between mb-12 max-w-[900px]"):
            with ui.column().classes("gap-1"):
                ui.label("NET NOTEBOOK").classes(
                    "text-[11px] font-bold tracking-[0.18em]"
                ).style(f"font-family:'JetBrains Mono',monospace; color:{ACCENT};")
                ui.label("Projects").classes(
                    "text-[28px] font-semibold leading-tight"
                ).style(f"color:{TEXT_PRI};")

            new_btn = ui.button("+ New Project").style(
                f"background:{ACCENT} !important; color:#ffffff !important; font-weight:600 !important;"
                f"font-size:13px !important; padding:10px 24px !important;"
                f"border-radius:6px !important; border:none !important;"
                f"box-shadow: 0 2px 6px rgba(46,125,50,0.3) !important;"
                f"text-transform: none !important;"
            )

        # Project cards
        cards_col = ui.column().classes("gap-3 w-full max-w-[900px]")

        def refresh_projects() -> None:
            cards_col.clear()
            projects = get_all_projects()
            with cards_col:
                if not projects:
                    with ui.element("div").classes(
                        "rounded-[10px] px-[60px] py-[60px] text-center"
                    ).style(f"background:{PANEL_BG}; border:2px dashed {BORDER};"):
                        ui.icon("folder_open").classes("text-[44px]").style(
                            f"color:{TEXT_MUTED};"
                        )
                        ui.label("No projects yet").classes(
                            "text-[15px] mt-[14px]"
                        ).style(f"color:{TEXT_MUTED};")
                        ui.label("Click '+ New Project' to get started").classes(
                            "text-[13px] mt-1"
                        ).style(f"color:{TEXT_MUTED};")
                else:
                    for p in projects:
                        _project_card(p, refresh_projects)

        refresh_projects()

        # ── New project dialog ────────────────────────────────────────────────
        with ui.dialog() as new_dialog, ui.card().classes(
            "rounded-[10px] px-8 py-7 min-w-[500px] gap-0"
        ).style(
            f"background:{PANEL_BG}; border:1px solid {BORDER};"
            f"box-shadow: 0 8px 32px rgba(0,0,0,0.12);"
        ):
            ui.label("New Project").classes("text-[19px] font-semibold mb-5").style(
                f"color:{TEXT_PRI};"
            )
            name_in = ui.input("Project Name *").props("outlined").classes("w-full")
            ticket_in = ui.input("Ticket Number (optional)").classes("w-full mt-3")
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
                .classes("w-full mt-3")
            )
            date_in = ui.input("Scheduled Date (MM-DD-YYYY)").classes("w-full mt-3")
            status_in = (
                ui.select(
                    ["active", "on-hold", "complete", "scheduled"],
                    label="Status",
                    value="active",
                )
                .props("outlined")
                .classes("w-full mt-3")
            )

            with ui.row().classes("mt-[26px] gap-[10px] justify-end"):
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

    with ui.element("div").classes(
        "rounded-lg px-6 py-4 flex items-center gap-5 w-full"
    ).style(
        f"background:{PANEL_BG}; border:1px solid {BORDER};"
        f"transition: box-shadow 0.15s, border-color 0.15s;"
        f"box-shadow: 0 1px 4px rgba(0,0,0,0.05);"
    ):
        # Status dot
        ui.element("span").classes(
            "w-[10px] h-[10px] rounded-full shrink-0 inline-block"
        ).style(f"background:{sc};")

        # Text block
        with ui.column().classes("gap-1 flex-1 min-w-0 overflow-hidden"):
            with ui.row().classes("items-baseline gap-3 flex-nowrap min-w-0"):
                if ticket:
                    ui.label(ticket).classes(
                        "text-[15px] font-bold whitespace-nowrap shrink-0"
                    ).style(
                        f"font-family:'JetBrains Mono',monospace; color:{TEXT_PRI};"
                    )
                if name and name != ticket:
                    ui.label(name).classes(
                        "text-[14px] whitespace-nowrap overflow-hidden text-ellipsis"
                    ).style(f"color:{TEXT_SEC};")

            with ui.row().classes("items-center gap-4 mt-0.5"):
                if tow:
                    ui.label(tow).classes("text-[13px]").style(f"color:{TEXT_SEC};")
                if date:
                    with ui.row().classes("items-center gap-1"):
                        ui.icon("event").classes("text-[13px]").style(
                            f"color:{TEXT_MUTED};"
                        )
                        ui.label(date).classes("text-xs").style(
                            f"color:{TEXT_MUTED};"
                            f"font-family:'JetBrains Mono',monospace;"
                        )

        # Action buttons
        with ui.row().classes("gap-3 items-center shrink-0"):
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
                with ui.dialog() as d, ui.card().classes(
                    "rounded-[10px] p-[26px] min-w-[380px]"
                ).style(
                    f"background:{PANEL_BG}; border:1px solid {BORDER};"
                    f"box-shadow:0 8px 32px rgba(0,0,0,0.12);"
                ):
                    ui.label(f'Delete "{pname}"?').classes(
                        "text-base font-semibold mb-2"
                    ).style(f"color:{TEXT_PRI};")
                    ui.label(
                        "All associated data will be permanently removed."
                    ).classes("text-[13px] mb-[22px]").style(f"color:{TEXT_SEC};")
                    with ui.row().classes("gap-[10px] justify-end"):
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
