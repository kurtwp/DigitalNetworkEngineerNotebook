"""Theme constants and global styles for Net Notebook."""

from typing import Callable

from nicegui import ui

# ── Light color palette (matches ticket app style) ────────────────────────────
DARK_BG = "#f0f2f5"  # page background — light gray
PANEL_BG = "#ffffff"  # card / panel background — white
SIDEBAR_BG = "#ffffff"  # sidebar — white with border
BORDER = "#e0e3e8"  # subtle gray border
ACCENT = "#2e7d32"  # green — matches ticket app buttons
ACCENT_DIM = "#1b5e20"
ACCENT_BLUE = "#1565c0"  # blue accent for secondary actions
TEXT_PRI = "#1a1a2e"  # near-black for primary text
TEXT_SEC = "#4a5568"  # medium gray
TEXT_MUTED = "#9aa0ad"  # light gray for labels/meta
JUNIPER = "#2e7d32"  # Juniper green
CISCO = "#1565c0"  # Cisco blue

TAG_COLORS: dict[str, tuple[str, str]] = {
    "info": ("#e8eaf6", "#3949ab"),
    "pre-check": ("#e8f5e9", "#2e7d32"),
    "action": ("#f1f8e9", "#558b2f"),
    "issue": ("#ffebee", "#c62828"),
    "post-check": ("#e3f2fd", "#1565c0"),
}

STATUS_COLORS: dict[str, str] = {
    "active": "#2e7d32",
    "on-hold": "#e65100",
    "complete": "#9aa0ad",
    "scheduled": "#1565c0",
    "decom": "#c62828",
    "pending": "#e65100",
    "in-maintenance": "#e65100",
}

SECTION_ICONS: dict[str, tuple[str, str]] = {
    "overview": ("grid_view", "Overview"),
    "devices": ("dns", "Devices"),
    "circuits": ("cable", "Circuits"),
    "ip_plan": ("lan", "IP Plan"),
    "paths": ("route", "A-Z Paths"),
    "journal": ("history_edu", "Journal"),
}


def apply_global_styles() -> None:
    """Inject global CSS and font imports into the page head."""
    ui.add_head_html(
        f"""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Roboto:wght@300;400;500;600&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <style>
      * {{ box-sizing: border-box; margin: 0; padding: 0; }}

      body, .nicegui-content {{
        background: {DARK_BG} !important;
        font-family: 'Roboto', sans-serif !important;
        color: {TEXT_PRI} !important;
      }}

      /* Scrollbar */
      ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
      ::-webkit-scrollbar-track {{ background: {DARK_BG}; }}
      ::-webkit-scrollbar-thumb {{ background: #d0d4db; border-radius: 3px; }}
      ::-webkit-scrollbar-thumb:hover {{ background: {ACCENT}66; }}

      /* NiceGUI / Quasar overrides */
      .q-field__control {{ background: {PANEL_BG} !important; border-color: {BORDER} !important; }}
      .q-field__native, .q-field__input {{ color: {TEXT_PRI} !important; font-family: 'Roboto', sans-serif !important; }}

      /* Fix label/value overlap */
      .q-field__label {{
        color: {TEXT_SEC} !important;
        font-size: 11px !important;
        font-weight: 500 !important;
        top: 5px !important;
        transform: none !important;
        transition: none !important;
      }}
      .q-field__control-container {{ padding-top: 18px !important; }}
      .q-field__native, .q-field__input {{ margin-top: 0 !important; padding-top: 2px !important; font-size: 14px !important; }}
      .q-field--outlined .q-field__control {{ border: 1px solid #d0d4db !important; border-radius: 6px !important; }}
      .q-field--outlined.q-field--focused .q-field__control {{ border-color: {ACCENT} !important; box-shadow: 0 0 0 2px {ACCENT}18 !important; }}
      .q-item {{ color: {TEXT_PRI} !important; }}
      .q-menu {{ background: {PANEL_BG} !important; border: 1px solid {BORDER} !important; box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important; }}
      .q-dialog .q-card {{ background: {PANEL_BG} !important; border: 1px solid {BORDER} !important; box-shadow: 0 8px 24px rgba(0,0,0,0.12) !important; }}
      .q-table {{ background: {PANEL_BG} !important; }}
      .q-table th {{ color: {TEXT_SEC} !important; border-color: {BORDER} !important; font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; background: #f8f9fb !important; }}
      .q-table td {{ color: {TEXT_PRI} !important; border-color: {DARK_BG} !important; }}
      .q-table tbody tr:hover td {{ background: #f5f7fa !important; }}
      .q-separator {{ background: {BORDER} !important; }}
      .q-tab {{ color: {TEXT_SEC} !important; }}
      .q-tab--active {{ color: {ACCENT} !important; }}
      .q-tab__indicator {{ background: {ACCENT} !important; }}
      .q-expansion-item .q-item {{ background: #f8f9fb !important; border-radius: 6px; }}
      .q-expansion-item__content {{ background: {PANEL_BG}; }}
      .nicegui-markdown p, .nicegui-markdown li {{ color: {TEXT_PRI}; font-family: 'Roboto', sans-serif; }}
      .nicegui-markdown code {{ background: {DARK_BG}; color: {ACCENT}; padding: 2px 6px; border-radius: 3px; font-family: 'JetBrains Mono', monospace; font-size: 0.85em; border: 1px solid {BORDER}; }}
      .nicegui-markdown pre {{ background: #f8f9fb; border: 1px solid {BORDER}; border-radius: 6px; padding: 12px; overflow-x: auto; }}
      .nicegui-markdown pre code {{ background: none; color: {ACCENT_DIM}; border: none; }}

      /* Sidebar nav item */
      .nav-item {{
        display: flex; align-items: center; gap: 10px;
        padding: 9px 14px; border-radius: 6px;
        cursor: pointer; transition: all 0.15s ease;
        color: {TEXT_SEC}; font-size: 13.5px; font-weight: 500;
        letter-spacing: 0.01em; user-select: none;
      }}
      .nav-item:hover {{ background: {DARK_BG}; color: {TEXT_PRI}; }}
      .nav-item.active {{ background: #e8f5e9; color: {ACCENT}; border-left: 3px solid {ACCENT}; padding-left: 11px; font-weight: 600; }}
      .nav-item .material-icons {{ font-size: 18px; }}

      /* Vendor badges */
      .badge-juniper {{ background: #e8f5e9; color: {JUNIPER}; border: 1px solid #a5d6a7; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; letter-spacing: 0.05em; }}
      .badge-cisco   {{ background: #e3f2fd; color: {CISCO}; border: 1px solid #90caf9; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; letter-spacing: 0.05em; }}
      .badge-other   {{ background: #f5f5f5; color: #757575; border: 1px solid #e0e0e0; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; letter-spacing: 0.05em; }}

      /* Status dots */
      .status-dot {{ width: 7px; height: 7px; border-radius: 50%; display: inline-block; margin-right: 6px; }}

      /* Code textarea */
      .code-area textarea {{ font-family: 'JetBrains Mono', monospace !important; font-size: 12.5px !important; line-height: 1.6 !important; color: {ACCENT_DIM} !important; background: #f8f9fb !important; }}

      /* Allow manual textarea resize */
      .q-field__native[style*="resize"] {{ resize: both !important; overflow: auto !important; }}

      /* Card */
      .nb-card {{ background: {PANEL_BG}; border: 1px solid {BORDER}; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }}
      .nb-card:hover {{ border-color: #c8cdd5; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}

      /* Section header */
      .section-header {{ font-size: 10px; text-transform: uppercase; letter-spacing: 0.1em; color: {TEXT_MUTED}; font-weight: 600; padding: 12px 16px 4px; }}

      /* Mono text */
      .mono {{ font-family: 'JetBrains Mono', monospace; font-size: 12.5px; }}

      /* Tag pill */
      .tag-pill {{ padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; letter-spacing: 0.04em; }}

      /* Hop chain */
      .hop-card {{ background: #f8f9fb; border: 1px solid {BORDER}; border-radius: 6px; padding: 12px 16px; }}
      .hop-card.carrier {{ border-color: #c5cae9; background: #f3f4ff; }}

      /* Animate in */
      @keyframes fadeUp {{ from {{ opacity:0; transform: translateY(6px); }} to {{ opacity:1; transform: translateY(0); }} }}
      .fade-up {{ animation: fadeUp 0.18s ease forwards; }}

      /* Input focus ring */
      .q-field--focused .q-field__control {{ border-color: {ACCENT} !important; box-shadow: 0 0 0 2px {ACCENT}20 !important; }}

      /* Button base reset */
      button {{ cursor: pointer; }}
    </style>
    """
    )


def sidebar_nav(
    project_id: int, active_section: str, on_navigate: Callable[[str], None]
) -> None:
    """Render the left sidebar with project context and nav links."""
    from netbook.database import get_project

    project = get_project(project_id)

    with ui.column().classes(
        "w-[230px] min-w-[230px] h-screen overflow-y-auto shrink-0 p-0"
    ).style(
        f"background:{SIDEBAR_BG}; border-right:1px solid {BORDER};"
        f"box-shadow: 2px 0 8px rgba(0,0,0,0.04);"
    ):
        # App title bar
        with ui.element("div").classes("px-4 pt-[18px] pb-[14px]").style(
            f"border-bottom:1px solid {BORDER}; background:#f8f9fb;"
        ):
            ui.label("NET NOTEBOOK").classes(
                "font-bold text-xs tracking-[0.15em]"
            ).style(f"font-family:'JetBrains Mono',monospace; color:{ACCENT};")
            ui.label("Work Notes").classes("text-xs mt-0.5").style(
                f"color:{TEXT_MUTED};"
            )

        # Project context card
        with ui.element("div").classes("px-4 py-3.5").style(
            f"border-bottom:1px solid {BORDER};"
        ):
            if project:
                ticket = project["ticket_num"] or "—"
                ui.label(ticket).classes("text-[13px] font-bold").style(
                    f"font-family:'JetBrains Mono',monospace; color:{ACCENT};"
                )
                ui.label(project["name"]).classes(
                    "text-[12.5px] mt-1 leading-snug font-medium"
                ).style(f"color:{TEXT_PRI};")
                if project["type_of_work"]:
                    ui.label(project["type_of_work"]).classes(
                        "text-[11.5px] mt-[3px]"
                    ).style(f"color:{TEXT_SEC};")
                if project["scheduled_date"]:
                    with ui.row().classes("items-center mt-1.5 gap-1"):
                        ui.icon("event").classes("text-[13px]").style(
                            f"color:{TEXT_MUTED};"
                        )
                        ui.label(project["scheduled_date"]).classes("text-xs").style(
                            f"color:{TEXT_MUTED}; font-family:'JetBrains Mono',monospace;"
                        )
                status = project["status"] or "active"
                sc = STATUS_COLORS.get(status.lower(), TEXT_MUTED)
                with ui.row().classes("items-center mt-2 gap-1.5"):
                    ui.element("span").classes(
                        "w-[7px] h-[7px] rounded-full inline-block"
                    ).style(f"background:{sc};")
                    ui.label(status.capitalize()).classes("text-xs font-medium").style(
                        f"color:{sc};"
                    )

        # Navigation section label
        ui.element("div").classes("section-header")

        # Nav items
        with ui.element("div").classes("px-2 py-1"):
            for key, (icon, label) in SECTION_ICONS.items():
                is_active = (key == active_section) or (
                    key == "journal" and active_section.startswith("journal")
                )

                if key == "journal":
                    from netbook.database import get_journal

                    journal_entries = get_journal(project_id)

                item = ui.element("div").classes(
                    f"nav-item {'active' if is_active else ''}"
                )
                with item:
                    ui.icon(icon).classes("text-[17px]").style(
                        f"color:{'inherit' if not is_active else ACCENT};"
                    )
                    ui.label(label).classes("text-[13.5px] flex-1")
                    # Show chevron for Journal when it has entries
                    if key == "journal" and journal_entries:
                        ui.icon(
                            "expand_more" if is_active else "chevron_right"
                        ).classes("text-[14px]").style(f"color:{TEXT_MUTED};")
                item.on("click", lambda k=key: on_navigate(k))

                # Journal sub-items: only visible when Journal is active
                if key == "journal" and is_active and journal_entries:
                    with ui.element("div").classes("pl-7 pb-1"):
                        for entry in journal_entries:
                            entry_title = (
                                entry["title"]
                                if "title" in entry.keys() and entry["title"]
                                else None
                            )
                            display_text = entry_title or (
                                entry["entry"][:25] + "..."
                                if len(entry["entry"]) > 25
                                else entry["entry"]
                            )
                            is_entry_active = active_section == f"journal:{entry['id']}"
                            sub_item = (
                                ui.label(display_text)
                                .classes(
                                    "text-xs px-2 py-1 cursor-pointer rounded"
                                    " whitespace-nowrap overflow-hidden"
                                    " text-ellipsis max-w-[170px]"
                                )
                                .style(
                                    f"color:{ACCENT if is_entry_active else TEXT_MUTED};"
                                    f"font-weight:{'600' if is_entry_active else '400'};"
                                    f"background:{'#e8f5e9' if is_entry_active else 'transparent'};"
                                )
                            )
                            sub_item.on(
                                "click",
                                lambda eid=entry["id"]: on_navigate(f"journal:{eid}"),
                            )

        # Back to projects
        with ui.element("div").classes("px-2 py-3 mt-auto").style(
            f"border-top:1px solid {BORDER};"
        ):
            back = ui.element("div").classes("nav-item").style(f"color:{TEXT_MUTED};")
            with back:
                ui.icon("arrow_back").classes("text-[16px]")
                ui.label("All Projects").classes("text-[13px]")
            back.on("click", lambda: ui.navigate.to("/"))
