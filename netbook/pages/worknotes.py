"""Work notes page — project detail view with sidebar navigation."""

import csv
import io
import json
import logging
import sqlite3
from typing import Callable

from nicegui import ui

from netbook.theme import (
    apply_global_styles,
    sidebar_nav,
    DARK_BG,
    PANEL_BG,
    SIDEBAR_BG,
    BORDER,
    ACCENT,
    ACCENT_DIM,
    TEXT_PRI,
    TEXT_SEC,
    TEXT_MUTED,
    JUNIPER,
    CISCO,
    STATUS_COLORS,
)
import netbook.database as db

log = logging.getLogger(__name__)


def worknotes_page(project_id: int) -> None:
    """Render the work notes page for a given project."""
    apply_global_styles()

    try:
        project_id = int(project_id)
    except (ValueError, TypeError):
        ui.label("Invalid project ID").classes("p-10").style(f"color:{TEXT_PRI};")
        return

    project = db.get_project(project_id)
    if not project:
        ui.label("Project not found").classes("p-10").style(f"color:{TEXT_PRI};")
        return

    # Reactive state
    active_section: dict[str, str] = {"key": "overview"}
    journal_expanded: dict[str, bool] = {"value": False}

    def navigate(section_key: str) -> None:
        # Toggle journal sub-menu when clicking Journal while already on it
        if section_key == "journal" and active_section["key"].startswith("journal"):
            journal_expanded["value"] = not journal_expanded["value"]
        elif section_key == "journal":
            journal_expanded["value"] = True
        elif not section_key.startswith("journal:"):
            journal_expanded["value"] = False

        active_section["key"] = section_key
        render_content()

    # ── Page shell ────────────────────────────────────────────────────────────
    with ui.element("div").classes("flex flex-row h-screen overflow-hidden"):
        # Sidebar (rebuilt on navigate to update active state)
        sidebar_slot = ui.element("div").classes("shrink-0")

        def render_sidebar() -> None:
            sidebar_slot.clear()
            with sidebar_slot:
                sidebar_nav(
                    project_id,
                    active_section["key"],
                    navigate,
                    journal_expanded["value"],
                )

        # Main content
        main = (
            ui.element("div")
            .classes("flex-1 overflow-y-auto")
            .style(f"background:{DARK_BG}; padding:32px 36px;")
        )

        def render_content() -> None:
            render_sidebar()
            main.clear()
            with main:
                section = active_section["key"]
                if section == "overview":
                    _section_overview(project_id, project)
                elif section == "devices":
                    _section_devices(project_id)
                elif section == "circuits":
                    _section_circuits(project_id)
                elif section == "ip_plan":
                    _section_ip_plan(project_id)
                elif section == "paths":
                    _section_paths(project_id)
                elif section == "journal":
                    _section_journal(project_id)
                elif section.startswith("journal:"):
                    entry_id = int(section.split(":")[1])
                    _section_journal_entry(project_id, entry_id, navigate)

        render_content()


# ─────────────────────────────────────────────────────────────────────────────
# OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────


def _section_overview(project_id: int, project: sqlite3.Row) -> None:
    _page_header("grid_view", "Overview")

    devices = db.get_devices(project_id)
    circuits = db.get_circuits(project_id)
    ips = db.get_ip_plan(project_id)
    paths = db.get_paths(project_id)
    journal = db.get_journal(project_id)

    # Stats row
    with ui.row().classes("gap-3 mb-7 flex-wrap"):
        for label, val, icon in [
            ("Devices", len(devices), "dns"),
            ("Circuits", len(circuits), "cable"),
            ("Subnets", len(ips), "lan"),
            ("Paths", len(paths), "route"),
            ("Journal", len(journal), "history_edu"),
        ]:
            _stat_card(label, val, icon)

    # Project details card
    with ui.element("div").classes("rounded-lg p-[22px] max-w-[700px]").style(
        f"background:{PANEL_BG}; border:1px solid {BORDER};"
    ):
        _label_row(
            "Ticket Number", project["ticket_num"] or "—", mono=True, accent=True
        )
        _label_row("Project Name", project["name"])
        _label_row("Type of Work", project["type_of_work"] or "—")
        _label_row("Status", project["status"] or "—")
        _label_row("Scheduled", project["scheduled_date"] or "—", mono=True)
        _label_row(
            "Created",
            project["created_at"][:10] if project["created_at"] else "—",
            mono=True,
        )

    # Recent journal entries
    if journal:
        ui.label("Recent Journal").classes(
            "text-[13px] font-semibold uppercase tracking-wider mt-7 mb-3"
        ).style(f"color:{TEXT_SEC};")
        for entry in journal[:5]:
            _journal_entry_card(entry)


# ─────────────────────────────────────────────────────────────────────────────
# DEVICES
# ─────────────────────────────────────────────────────────────────────────────


def _section_devices(project_id: int) -> None:
    _page_header("dns", "Devices")

    content_col = ui.column().classes("gap-4 w-full")

    def refresh() -> None:
        content_col.clear()
        devices = db.get_devices(project_id)
        with content_col:
            if not devices:
                _empty_state("No devices added yet", "dns")
                return

            # Download CSV button
            def download_devices_csv() -> None:
                rows = db.get_devices(project_id)
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(
                    ["Hostname", "Vendor", "Model", "Mgmt IP", "Site", "Notes"]
                )
                for d in rows:
                    writer.writerow(
                        [
                            d["hostname"],
                            d["vendor"] or "",
                            d["model"] or "",
                            d["mgmt_ip"] or "",
                            d["site"] or "",
                            d["notes"] or "",
                        ]
                    )
                ui.download(output.getvalue().encode("utf-8"), "devices.csv")

            with ui.row().classes("gap-2.5 items-center mb-2"):
                ui.button(
                    "Download CSV", icon="download", on_click=download_devices_csv
                ).classes("text-[12px] rounded-[5px] cursor-pointer").style(
                    f"background:{ACCENT}15; color:{ACCENT}; border:1px solid {ACCENT}33;"
                    f"padding:6px 14px;"
                )
                ui.label(
                    f"{len(devices)} device{'s' if len(devices) != 1 else ''}"
                ).classes("text-[12px]").style(f"color:{TEXT_MUTED};")

            # Spreadsheet-style table
            columns = [
                {
                    "name": "hostname",
                    "label": "Hostname",
                    "field": "hostname",
                    "align": "left",
                    "sortable": True,
                },
                {
                    "name": "vendor",
                    "label": "Vendor",
                    "field": "vendor",
                    "align": "left",
                    "sortable": True,
                },
                {"name": "model", "label": "Model", "field": "model", "align": "left"},
                {
                    "name": "mgmt_ip",
                    "label": "Mgmt IP",
                    "field": "mgmt_ip",
                    "align": "left",
                },
                {"name": "site", "label": "Site", "field": "site", "align": "left"},
                {"name": "actions", "label": "", "field": "actions", "align": "center"},
            ]
            rows_data = []
            for d in devices:
                rows_data.append(
                    {
                        "id": d["id"],
                        "hostname": d["hostname"] or "",
                        "vendor": d["vendor"] or "",
                        "model": d["model"] or "",
                        "mgmt_ip": d["mgmt_ip"] or "",
                        "site": d["site"] or "",
                    }
                )

            table = (
                ui.table(
                    columns=columns,
                    rows=rows_data,
                    row_key="id",
                )
                .classes("w-full rounded-lg")
                .style(f"background:{PANEL_BG}; border:1px solid {BORDER};")
                .props("flat bordered dense")
            )

            # Add delete button per row via slot
            table.add_slot(
                "body-cell-actions",
                """
                <q-td :props="props">
                    <q-btn flat dense icon="delete_outline" size="sm" color="grey"
                           @click="$parent.$emit('delete', props.row)" />
                </q-td>
            """,
            )
            table.on(
                "delete",
                lambda e: _confirm_delete(
                    f"Delete {e.args['hostname']}?",
                    lambda did=e.args["id"]: (db.delete_device(did), refresh()),
                ),
            )

    # Add device dialog
    with ui.dialog() as add_dlg, ui.card().classes(
        "rounded-[10px] p-[26px] min-w-[500px]"
    ).style(f"background:{PANEL_BG}; border:1px solid {BORDER};"):
        ui.label("Add Device").classes("text-[17px] font-semibold mb-[18px]").style(
            f"color:{TEXT_PRI};"
        )
        hostname_in = ui.input("Hostname *").props("outlined").classes("w-full")
        vendor_in = (
            ui.select(["Cisco", "Juniper", "Other"], label="Vendor", value="Cisco")
            .props("outlined")
            .classes("w-full mt-2.5")
        )
        model_in = ui.input("Model").props("outlined").classes("w-full mt-2.5")
        mgmt_in = ui.input("Management IP").props("outlined").classes("w-full mt-2.5")
        site_in = ui.input("Site / Location").props("outlined").classes("w-full mt-2.5")
        notes_in = ui.textarea("Notes").props("outlined").classes("w-full mt-2.5")

        with ui.row().classes("mt-[22px] gap-2.5 justify-end"):
            ui.button("Cancel", on_click=add_dlg.close).style(_cancel_style())

            def do_add() -> None:
                if not hostname_in.value.strip():
                    ui.notify("Hostname required", color="negative")
                    return
                db.create_device(
                    project_id,
                    hostname_in.value.strip(),
                    vendor=vendor_in.value,
                    model=model_in.value,
                    mgmt_ip=mgmt_in.value,
                    site=site_in.value,
                    notes=notes_in.value,
                )
                add_dlg.close()
                refresh()
                ui.notify("Device added", color="positive")

            ui.button("Add Device", on_click=do_add).style(_primary_btn_style())

    def open_add_device() -> None:
        hostname_in.value = ""
        vendor_in.value = "Cisco"
        model_in.value = ""
        mgmt_in.value = ""
        site_in.value = ""
        notes_in.value = ""
        add_dlg.open()

    _add_button("Add Device", open_add_device)
    refresh()


def _device_card(
    dev: sqlite3.Row, project_id: int, refresh_cb: Callable[[], None]
) -> None:
    """Render a single device card with interfaces and config snippets."""
    vendor = dev["vendor"] or "Other"
    badge_class = f"badge-{vendor.lower()}"

    with ui.element("div").classes("rounded-lg p-[18px]").style(
        f"background:{PANEL_BG}; border:1px solid {BORDER};"
    ):
        with ui.row().classes("items-start justify-between"):
            with ui.column().classes("gap-1"):
                with ui.row().classes("items-center gap-2.5"):
                    ui.label(dev["hostname"]).classes(
                        "font-mono text-[15px] font-semibold"
                    ).style(f"color:{TEXT_PRI};")
                    ui.element("span").classes(badge_class).style("").set_content(
                        vendor
                    )
                with ui.row().classes("gap-5 mt-1"):
                    if dev["model"]:
                        _meta_chip("memory", dev["model"])
                    if dev["mgmt_ip"]:
                        _meta_chip("router", dev["mgmt_ip"], mono=True)
                    if dev["site"]:
                        _meta_chip("place", dev["site"])

            with ui.row().classes("gap-1.5"):
                del_btn = (
                    ui.button("", icon="delete_outline")
                    .classes("cursor-pointer")
                    .style(f"background:transparent; color:{TEXT_MUTED}; border:none;")
                )
                del_btn.on(
                    "click",
                    lambda did=dev["id"]: _confirm_delete(
                        f"Delete {dev['hostname']}?",
                        lambda: (db.delete_device(did), refresh_cb()),
                    ),
                )

        # Interfaces sub-section (always show expansion)
        with ui.expansion("Interfaces", icon="cable").classes(
            "mt-3.5 rounded-md"
        ).style(f"background:#f8f9fb; border:1px solid {BORDER};"):
            iface_col = ui.column().classes("gap-1.5 py-2.5")

            def refresh_ifaces(device_id: int = dev["id"]) -> None:
                iface_col.clear()
                ifaces = db.get_interfaces(device_id)
                with iface_col:
                    if not ifaces:
                        ui.label("No interfaces").classes("text-[12px] py-1").style(
                            f"color:{TEXT_MUTED};"
                        )
                    for iface in ifaces:
                        with ui.row().classes("items-center gap-3 rounded-[5px]").style(
                            f"padding:6px 8px; background:#f0f2f5;"
                        ):
                            ui.label(iface["name"]).classes(
                                "font-mono text-[12.5px] min-w-[140px]"
                            ).style(f"color:{ACCENT};")
                            if iface["ip_address"]:
                                ui.label(iface["ip_address"]).classes(
                                    "font-mono text-[12px]"
                                ).style(f"color:{TEXT_SEC};")
                            if iface["description"]:
                                ui.label(iface["description"]).classes(
                                    "text-[12px] flex-1"
                                ).style(f"color:{TEXT_MUTED};")
                            del_i = (
                                ui.icon("close")
                                .classes("text-[14px] cursor-pointer ml-auto")
                                .style(f"color:{TEXT_MUTED};")
                            )
                            del_i.on(
                                "click",
                                lambda iid=iface["id"]: (
                                    db.delete_interface(iid),
                                    refresh_ifaces(),
                                ),
                            )

                    # Add interface inline
                    with ui.row().classes("mt-2 gap-2 items-end"):
                        ni = (
                            ui.input("Interface name")
                            .props("outlined")
                            .classes("flex-1")
                        )
                        nip = ui.input("IP").props("outlined").classes("w-[140px]")
                        nd = (
                            ui.input("Description / CID")
                            .props("outlined")
                            .classes("flex-[2]")
                        )

                        def add_iface(device_id: int = dev["id"]) -> None:
                            if not ni.value.strip():
                                return
                            db.create_interface(
                                device_id,
                                ni.value.strip(),
                                ip_address=nip.value.strip(),
                                description=nd.value.strip(),
                            )
                            ni.value = ""
                            nip.value = ""
                            nd.value = ""
                            refresh_ifaces()

                        ui.button("+", on_click=add_iface).classes(
                            "rounded-[5px] font-bold cursor-pointer"
                        ).style(
                            f"background:{ACCENT}22; color:{ACCENT}; border:1px solid {ACCENT}44;"
                            f"padding:6px 12px;"
                        )

            refresh_ifaces()

        # Config snippets sub-section
        with ui.expansion("Config Snippets", icon="code").classes(
            "mt-2 rounded-md"
        ).style(f"background:#f8f9fb; border:1px solid {BORDER};"):
            snip_col = ui.column().classes("gap-2 py-2.5")

            def refresh_snippets(device_id: int = dev["id"]) -> None:
                snip_col.clear()
                snips = db.get_snippets(device_id)
                with snip_col:
                    if not snips:
                        ui.label("No config snippets").classes("text-[12px]").style(
                            f"color:{TEXT_MUTED};"
                        )
                    for s in snips:
                        with ui.element("div").classes("rounded-md p-3").style(
                            f"background:#f8f9fb; border:1px solid {BORDER};"
                        ):
                            with ui.row().classes("items-center justify-between mb-2"):
                                ui.label(s["label"]).classes(
                                    "text-[13px] font-semibold"
                                ).style(f"color:{TEXT_PRI};")
                                with ui.row().classes("gap-2 items-center"):
                                    if s["version"]:
                                        ui.label(s["version"]).classes(
                                            "text-[10px] font-mono rounded-[3px]"
                                        ).style(
                                            f"color:{TEXT_MUTED};"
                                            f"background:#f5f7fa; padding:2px 6px;"
                                        )
                                    ui.button(
                                        "Copy",
                                        on_click=lambda c=s[
                                            "content"
                                        ]: ui.run_javascript(
                                            f"navigator.clipboard.writeText({json.dumps(c or '')})"
                                        ),
                                    ).classes(
                                        "text-[11px] rounded cursor-pointer"
                                    ).style(
                                        f"background:{ACCENT}15; color:{ACCENT}; border:1px solid {ACCENT}33;"
                                        f"padding:3px 10px;"
                                    )
                                    ui.icon("delete_outline").classes(
                                        "text-[15px] cursor-pointer"
                                    ).style(f"color:{TEXT_MUTED};").on(
                                        "click",
                                        lambda sid=s["id"]: (
                                            db.delete_snippet(sid),
                                            refresh_snippets(),
                                        ),
                                    )
                            ui.code(s["content"] or "").classes(
                                "font-mono text-[12px] whitespace-pre overflow-x-auto block"
                            ).style(f"color:#1b5e20; background:#f8f9fb;")

                    # Add snippet
                    ui.separator().style(f"background:{BORDER}; margin:8px 0;")
                    sl = ui.input("Label").props("outlined").classes("w-full")
                    sv = (
                        ui.input("Version", value="v1")
                        .props("outlined")
                        .classes("w-[120px] mt-2")
                    )
                    sc_text = ui.textarea("Config").classes(
                        "code-area w-full mt-2 font-mono"
                    )

                    def add_snip(device_id: int = dev["id"]) -> None:
                        if not sl.value.strip():
                            return
                        db.create_snippet(
                            device_id,
                            sl.value.strip(),
                            vendor=dev["vendor"],
                            version=sv.value.strip(),
                            content=sc_text.value,
                        )
                        sl.value = ""
                        sv.value = "v1"
                        sc_text.value = ""
                        refresh_snippets()

                    ui.button("Add Snippet", on_click=add_snip).classes(
                        "text-[12px] rounded-[5px] mt-2 cursor-pointer"
                    ).style(
                        f"background:{ACCENT}18; color:{ACCENT}; border:1px solid {ACCENT}33;"
                        f"padding:6px 14px;"
                    )

            refresh_snippets()


# ─────────────────────────────────────────────────────────────────────────────
# CIRCUITS
# ─────────────────────────────────────────────────────────────────────────────


def _section_circuits(project_id: int) -> None:
    _page_header("cable", "Circuits")

    content_col = ui.column().classes("gap-4 w-full")

    def refresh() -> None:
        content_col.clear()
        circuits = db.get_circuits(project_id)
        with content_col:
            if not circuits:
                _empty_state("No circuits added yet", "cable")
                return

            # Download CSV button
            def download_circuits_csv() -> None:
                rows = db.get_circuits(project_id)
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(
                    ["Circuit ID", "Carrier", "Type", "Bandwidth", "Status", "Notes"]
                )
                for c in rows:
                    writer.writerow(
                        [
                            c["cid"],
                            c["carrier"] or "",
                            c["circuit_type"] or "",
                            c["bandwidth"] or "",
                            c["status"] or "",
                            c["notes"] or "",
                        ]
                    )
                ui.download(output.getvalue().encode("utf-8"), "circuits.csv")

            with ui.row().classes("gap-2.5 items-center mb-2"):
                ui.button(
                    "Download CSV", icon="download", on_click=download_circuits_csv
                ).classes("text-[12px] rounded-[5px] cursor-pointer").style(
                    f"background:{ACCENT}15; color:{ACCENT}; border:1px solid {ACCENT}33;"
                    f"padding:6px 14px;"
                )
                ui.label(
                    f"{len(circuits)} circuit{'s' if len(circuits) != 1 else ''}"
                ).classes("text-[12px]").style(f"color:{TEXT_MUTED};")

            # Spreadsheet-style table
            columns = [
                {
                    "name": "cid",
                    "label": "Circuit ID",
                    "field": "cid",
                    "align": "left",
                    "sortable": True,
                },
                {
                    "name": "carrier",
                    "label": "Carrier",
                    "field": "carrier",
                    "align": "left",
                    "sortable": True,
                },
                {
                    "name": "circuit_type",
                    "label": "Type",
                    "field": "circuit_type",
                    "align": "left",
                    "sortable": True,
                },
                {
                    "name": "bandwidth",
                    "label": "Bandwidth",
                    "field": "bandwidth",
                    "align": "left",
                },
                {
                    "name": "status",
                    "label": "Status",
                    "field": "status",
                    "align": "left",
                    "sortable": True,
                },
                {"name": "notes", "label": "Notes", "field": "notes", "align": "left"},
                {"name": "actions", "label": "", "field": "actions", "align": "center"},
            ]
            rows_data = []
            for c in circuits:
                rows_data.append(
                    {
                        "id": c["id"],
                        "cid": c["cid"] or "",
                        "carrier": c["carrier"] or "",
                        "circuit_type": c["circuit_type"] or "",
                        "bandwidth": c["bandwidth"] or "",
                        "status": c["status"] or "",
                        "notes": c["notes"] or "",
                    }
                )

            table = (
                ui.table(
                    columns=columns,
                    rows=rows_data,
                    row_key="id",
                )
                .classes("w-full rounded-lg")
                .style(f"background:{PANEL_BG}; border:1px solid {BORDER};")
                .props("flat bordered dense")
            )

            # Add delete button per row via slot
            table.add_slot(
                "body-cell-actions",
                """
                <q-td :props="props">
                    <q-btn flat dense icon="delete_outline" size="sm" color="grey"
                           @click="$parent.$emit('delete', props.row)" />
                </q-td>
            """,
            )
            table.on(
                "delete",
                lambda e: _confirm_delete(
                    f"Delete circuit {e.args['cid']}?",
                    lambda cid=e.args["id"]: (db.delete_circuit(cid), refresh()),
                ),
            )

    # Add circuit dialog
    with ui.dialog() as add_dlg, ui.card().classes(
        "rounded-[10px] p-[26px] min-w-[480px]"
    ).style(f"background:{PANEL_BG}; border:1px solid {BORDER};"):
        ui.label("Add Circuit").classes("text-[17px] font-semibold mb-[18px]").style(
            f"color:{TEXT_PRI};"
        )
        cid_in = ui.input("Circuit ID *").props("outlined").classes("w-full")
        carr_in = (
            ui.input("Carrier / Provider").props("outlined").classes("w-full mt-2.5")
        )
        type_in = (
            ui.select(
                [
                    "",
                    "MPLS",
                    "DIA",
                    "P2P Ethernet",
                    "Broadband",
                    "VPLS",
                    "SD-WAN",
                    "Other",
                ],
                label="Circuit Type",
                value="",
            )
            .props("outlined")
            .classes("w-full mt-2.5")
        )
        bw_in = ui.input("Bandwidth (e.g. 1Gbps)").classes("w-full mt-2.5")
        stat_in = (
            ui.select(
                ["active", "pending", "in-maintenance", "decom"],
                label="Status",
                value="active",
            )
            .props("outlined")
            .classes("w-full mt-2.5")
        )
        notes_in = ui.textarea("Notes").props("outlined").classes("w-full mt-2.5")

        with ui.row().classes("mt-[22px] gap-2.5 justify-end"):
            ui.button("Cancel", on_click=add_dlg.close).style(_cancel_style())

            def do_add() -> None:
                if not cid_in.value.strip():
                    ui.notify("Circuit ID required", color="negative")
                    return
                db.create_circuit(
                    project_id,
                    cid_in.value.strip(),
                    carrier=carr_in.value,
                    circuit_type=type_in.value,
                    bandwidth=bw_in.value,
                    status=stat_in.value,
                    notes=notes_in.value,
                )
                add_dlg.close()
                refresh()
                ui.notify("Circuit added", color="positive")

            ui.button("Add Circuit", on_click=do_add).style(_primary_btn_style())

    def open_add_circuit() -> None:
        cid_in.value = ""
        carr_in.value = ""
        type_in.value = ""
        bw_in.value = ""
        stat_in.value = "active"
        notes_in.value = ""
        add_dlg.open()

    _add_button("Add Circuit", open_add_circuit)
    refresh()


# ─────────────────────────────────────────────────────────────────────────────
# IP PLAN
# ─────────────────────────────────────────────────────────────────────────────


def _section_ip_plan(project_id: int) -> None:
    _page_header("lan", "IP Plan")
    ip_col = ui.column().classes("gap-2 w-full")

    def refresh() -> None:
        ip_col.clear()
        entries = db.get_ip_plan(project_id)
        with ip_col:
            if not entries:
                _empty_state("No subnets added yet", "lan")
                return
            with ui.element("div").classes(
                "text-[10px] uppercase tracking-wider font-semibold"
            ).style(
                f"display:grid; grid-template-columns: 1.5fr 2fr 1.5fr 0.8fr auto;"
                f"padding:8px 14px; color:{TEXT_MUTED};"
            ):
                for h in ["Subnet / CIDR", "Purpose", "Assigned To", "VLAN", ""]:
                    ui.label(h)
            for e in entries:
                _ip_row(e, refresh)

    with ui.dialog() as add_dlg, ui.card().classes(
        "rounded-[10px] p-[26px] min-w-[460px]"
    ).style(f"background:{PANEL_BG}; border:1px solid {BORDER};"):
        ui.label("Add IP Entry").classes("text-[17px] font-semibold mb-[18px]").style(
            f"color:{TEXT_PRI};"
        )
        sub_in = ui.input("Subnet / CIDR *  (e.g. 10.0.0.0/24)").classes("w-full")
        pur_in = ui.input("Purpose").props("outlined").classes("w-full mt-2.5")
        asgn_in = ui.input("Assigned Device(s)").classes("w-full mt-2.5")
        vlan_in = ui.input("VLAN ID").props("outlined").classes("w-full mt-2.5")
        note_in = ui.input("Notes").props("outlined").classes("w-full mt-2.5")

        with ui.row().classes("mt-[22px] gap-2.5 justify-end"):
            ui.button("Cancel", on_click=add_dlg.close).style(_cancel_style())

            def do_add() -> None:
                if not sub_in.value.strip():
                    ui.notify("Subnet required", color="negative")
                    return
                db.create_ip_entry(
                    project_id,
                    sub_in.value.strip(),
                    purpose=pur_in.value,
                    assigned_to=asgn_in.value,
                    vlan_id=vlan_in.value,
                    notes=note_in.value,
                )
                add_dlg.close()
                refresh()
                ui.notify("IP entry added", color="positive")

            ui.button("Add Entry", on_click=do_add).style(_primary_btn_style())

    def open_add_ip() -> None:
        sub_in.value = ""
        pur_in.value = ""
        asgn_in.value = ""
        vlan_in.value = ""
        note_in.value = ""
        add_dlg.open()

    _add_button("Add Subnet", open_add_ip)
    refresh()


def _ip_row(e: sqlite3.Row, refresh_cb: Callable[[], None]) -> None:
    with ui.element("div").classes("rounded-md items-center").style(
        f"display:grid; grid-template-columns: 1.5fr 2fr 1.5fr 0.8fr auto;"
        f"padding:11px 14px; background:{PANEL_BG}; border:1px solid {BORDER};"
    ):
        ui.label(e["subnet"]).classes("font-mono text-[13px] font-semibold").style(
            f"color:{ACCENT};"
        )
        ui.label(e["purpose"] or "—").classes("text-[13px]").style(f"color:{TEXT_SEC};")
        ui.label(e["assigned_to"] or "—").classes("font-mono text-[12px]").style(
            f"color:{TEXT_MUTED};"
        )
        ui.label(e["vlan_id"] or "—").classes("font-mono text-[12px]").style(
            f"color:{TEXT_MUTED};"
        )
        ui.icon("delete_outline").classes("text-[16px] cursor-pointer").style(
            f"color:{TEXT_MUTED};"
        ).on(
            "click",
            lambda eid=e["id"]: _confirm_delete(
                f"Delete {e['subnet']}?",
                lambda: (db.delete_ip_entry(eid), refresh_cb()),
            ),
        )


# ─────────────────────────────────────────────────────────────────────────────
# A-Z PATHS
# ─────────────────────────────────────────────────────────────────────────────


def _section_paths(project_id: int) -> None:
    _page_header("route", "A-Z Paths")
    paths_col = ui.column().classes("gap-3.5 w-full")

    def refresh() -> None:
        paths_col.clear()
        paths = db.get_paths(project_id)
        with paths_col:
            if not paths:
                _empty_state("No paths defined yet", "route")
                return
            for p in paths:
                _path_card(p, project_id, refresh)

    with ui.dialog() as add_dlg, ui.card().classes(
        "rounded-[10px] p-[26px] min-w-[500px]"
    ).style(f"background:{PANEL_BG}; border:1px solid {BORDER};"):
        ui.label("New A-Z Path").classes("text-[17px] font-semibold mb-[18px]").style(
            f"color:{TEXT_PRI};"
        )
        name_in = ui.input("Path Name *").props("outlined").classes("w-full")
        cust_in = (
            ui.input("Customer / Service").props("outlined").classes("w-full mt-2.5")
        )
        a_in = ui.input("A-Side (e.g. Customer Site A)").classes("w-full mt-2.5")
        z_in = ui.input("Z-Side (e.g. Data Center)").classes("w-full mt-2.5")
        stat_in = (
            ui.select(["active", "in-build", "decom"], label="Status", value="active")
            .props("outlined")
            .classes("w-full mt-2.5")
        )

        with ui.row().classes("mt-[22px] gap-2.5 justify-end"):
            ui.button("Cancel", on_click=add_dlg.close).style(_cancel_style())

            def do_add() -> None:
                if not name_in.value.strip():
                    ui.notify("Path name required", color="negative")
                    return
                db.create_path(
                    project_id,
                    name_in.value.strip(),
                    customer=cust_in.value,
                    a_side=a_in.value,
                    z_side=z_in.value,
                    status=stat_in.value,
                )
                add_dlg.close()
                refresh()
                ui.notify("Path created", color="positive")

            ui.button("Create Path", on_click=do_add).style(_primary_btn_style())

    def open_add_path() -> None:
        name_in.value = ""
        cust_in.value = ""
        a_in.value = ""
        z_in.value = ""
        stat_in.value = "active"
        add_dlg.open()

    _add_button("New Path", open_add_path)
    refresh()


def _path_card(
    path: sqlite3.Row, project_id: int, refresh_cb: Callable[[], None]
) -> None:
    """Render a path card with hop chain and add-hop controls."""
    hops = db.get_path_hops(path["id"])
    sc = STATUS_COLORS.get((path["status"] or "active").lower(), TEXT_MUTED)

    with ui.element("div").classes("rounded-lg p-5").style(
        f"background:{PANEL_BG}; border:1px solid {BORDER};"
    ):
        with ui.row().classes("items-start justify-between mb-4"):
            with ui.column().classes("gap-1"):
                ui.label(path["name"]).classes("text-[15px] font-semibold").style(
                    f"color:{TEXT_PRI};"
                )
                if path["customer"]:
                    ui.label(path["customer"]).classes("text-[12px]").style(
                        f"color:{TEXT_MUTED};"
                    )
            with ui.row().classes("items-center gap-1.5"):
                ui.element("span").style(
                    f"width:7px;height:7px;border-radius:50%;background:{sc};display:inline-block;"
                )
                ui.label(path["status"] or "active").classes("text-[12px]").style(
                    f"color:{sc};"
                )
                ui.icon("delete_outline").classes(
                    "text-[16px] cursor-pointer ml-2"
                ).style(f"color:{TEXT_MUTED};").on(
                    "click",
                    lambda pid=path["id"]: _confirm_delete(
                        f"Delete path '{path['name']}'?",
                        lambda: (db.delete_path(pid), refresh_cb()),
                    ),
                )

        # A-side / Z-side labels
        with ui.row().classes("gap-2 items-center mb-3.5"):
            if path["a_side"]:
                ui.label(f"A: {path['a_side']}").classes("text-[12px] rounded").style(
                    f"color:{ACCENT}; background:{ACCENT}12;"
                    f"padding:3px 10px; border:1px solid {ACCENT}33;"
                )
            ui.icon("arrow_forward").classes("text-[14px]").style(
                f"color:{TEXT_MUTED};"
            )
            if path["z_side"]:
                ui.label(f"Z: {path['z_side']}").classes("text-[12px] rounded").style(
                    f"color:#52a0c9; background:#52a0c912;"
                    f"padding:3px 10px; border:1px solid #52a0c933;"
                )

        # Hop chain
        hop_col = ui.column().classes("gap-0")
        with hop_col:
            _render_hops(hops, hop_col)

        # Add hop controls
        with ui.expansion("Add Hop", icon="add_circle_outline").classes(
            "mt-2.5 rounded-md"
        ).style(f"background:#f8f9fb; border:1px solid {BORDER};"):
            hop_type_sel = (
                ui.select(["device", "carrier"], label="Hop Type", value="device")
                .props("outlined")
                .classes("w-full")
            )
            devices = db.get_devices(project_id)
            device_names = {d["hostname"]: d["id"] for d in devices}
            dev_sel = ui.select(
                list(device_names.keys()) or ["(no devices)"], label="Device"
            ).classes("w-full mt-2.5")
            ing_in = (
                ui.input("Ingress Interface").props("outlined").classes("w-full mt-2.5")
            )
            egr_in = (
                ui.input("Egress Interface").props("outlined").classes("w-full mt-2.5")
            )
            carr_lbl_in = (
                ui.input("Carrier Label").props("outlined").classes("w-full mt-2.5")
            )
            circuits = db.get_circuits(project_id)
            ckt_names = {"(none)": None} | {c["cid"]: c["id"] for c in circuits}
            ckt_sel = ui.select(
                list(ckt_names.keys()), label="Circuit ID (optional)", value="(none)"
            ).classes("w-full mt-2.5")
            hop_notes = ui.input("Notes").props("outlined").classes("w-full mt-2.5")

            def do_add_hop(path_id: int = path["id"]) -> None:
                next_order = len(db.get_path_hops(path_id)) + 1
                ht = hop_type_sel.value
                did = device_names.get(dev_sel.value) if ht == "device" else None
                cid = ckt_names.get(ckt_sel.value)
                db.add_path_hop(
                    path_id,
                    next_order,
                    ht,
                    device_id=did,
                    ingress_iface=ing_in.value,
                    egress_iface=egr_in.value,
                    carrier_label=carr_lbl_in.value,
                    circuit_id=cid,
                    notes=hop_notes.value,
                )
                hop_col.clear()
                with hop_col:
                    _render_hops(db.get_path_hops(path_id), hop_col)
                ui.notify("Hop added", color="positive")

            ui.button("Add Hop", on_click=do_add_hop).classes(
                "text-[12px] rounded-[5px] mt-3 cursor-pointer"
            ).style(
                f"background:{ACCENT}18; color:{ACCENT}; border:1px solid {ACCENT}33;"
                f"padding:6px 14px;"
            )


def _render_hops(hops: list[sqlite3.Row], hop_col) -> None:
    """Render the hop chain visualization. Hop deletion now refreshes the UI."""
    if not hops:
        ui.label("No hops yet — add hops below").classes("text-[12px] py-1").style(
            f"color:{TEXT_MUTED};"
        )
        return

    def _delete_and_refresh(hop_id: int, path_id: int) -> None:
        db.delete_path_hop(hop_id)
        hop_col.clear()
        with hop_col:
            _render_hops(db.get_path_hops(path_id), hop_col)

    for i, hop in enumerate(hops):
        is_carrier = hop["hop_type"] == "carrier"
        bg = "#f3f4ff" if is_carrier else "#f8f9fb"
        border = "#c5cae9" if is_carrier else BORDER

        with ui.element("div").classes("rounded-md relative").style(
            f"background:{bg}; border:1px solid {border}; padding:10px 14px;"
        ):
            with ui.row().classes("items-center gap-2.5"):
                if is_carrier:
                    ui.icon("cloud").classes("text-[16px]").style("color:#7e57c2;")
                    label = hop["carrier_label"] or "Carrier"
                    ui.label(label).classes("text-[13px] font-semibold").style(
                        "color:#5c35a0;"
                    )
                    if hop["cid"]:
                        ui.label(f"CID: {hop['cid']}").classes(
                            "font-mono text-[11px] rounded-[3px]"
                        ).style(
                            f"color:{ACCENT}; background:{ACCENT}12; padding:2px 8px;"
                        )
                else:
                    ui.icon("dns").classes("text-[16px]").style(f"color:{ACCENT};")
                    ui.label(hop["hostname"] or "—").classes(
                        "font-mono text-[13px] font-semibold"
                    ).style(f"color:{TEXT_PRI};")
                    if hop["vendor"]:
                        vendor_color = JUNIPER if hop["vendor"] == "Juniper" else CISCO
                        ui.label(hop["vendor"]).classes(
                            "text-[11px] rounded-[3px]"
                        ).style(
                            f"color:{vendor_color}; background:{vendor_color}18;"
                            f"padding:1px 7px;"
                        )
                    if hop["ingress_iface"]:
                        ui.label(f"in: {hop['ingress_iface']}").classes(
                            "font-mono text-[11px]"
                        ).style(f"color:{TEXT_MUTED};")
                    if hop["egress_iface"]:
                        ui.label(f"out: {hop['egress_iface']}").classes(
                            "font-mono text-[11px]"
                        ).style(f"color:{TEXT_MUTED};")
                ui.icon("delete_outline").classes(
                    "text-[14px] cursor-pointer ml-auto"
                ).style(f"color:{TEXT_MUTED};").on(
                    "click",
                    lambda hid=hop["id"], pid=hop["path_id"]: _delete_and_refresh(
                        hid, pid
                    ),
                )

        if i < len(hops) - 1:
            ui.element("div").style(
                f"width:2px; height:18px; background:linear-gradient({BORDER},{BORDER});"
                f"margin:0 20px;"
            )


# ─────────────────────────────────────────────────────────────────────────────
# JOURNAL
# ─────────────────────────────────────────────────────────────────────────────


def _section_journal(project_id: int) -> None:
    # Build device/circuit options for the combo field
    devices = db.get_devices(project_id)
    circuits = db.get_circuits(project_id)
    # Map display text -> (device_id, circuit_id)
    link_lookup: dict[str, tuple[int | None, int | None]] = {}
    combo_options: list[str] = []
    for d in devices:
        label = f"🖥 {d['hostname']}"
        combo_options.append(label)
        link_lookup[label] = (d["id"], None)
    for c in circuits:
        label = f"🔌 {c['cid']}"
        combo_options.append(label)
        link_lookup[label] = (None, c["id"])

    # ── Export function ───────────────────────────────────────────────────────
    def export_journal() -> None:
        entries = db.get_journal(project_id)
        lines: list[str] = []
        for e in entries:
            ts = e["created_at"][:16].replace("T", " ") if e["created_at"] else "—"
            link = ""
            if e["hostname"]:
                link = f"  [device: {e['hostname']}]"
            elif e["cid"]:
                link = f"  [circuit: {e['cid']}]"
            title_str = (
                f"  **{e['title']}**\n" if ("title" in e.keys() and e["title"]) else ""
            )
            lines.append(f"[{ts}]{link}\n{title_str}{e['entry']}\n")
        content = "\n".join(lines)
        ui.download(content.encode("utf-8"), "journal.md")

    # ── Container for input references (avoids Python closure scoping issue) ──
    inputs: dict = {}

    # ── Sticky header row: title left, controls right ─────────────────────────
    with ui.element("div").classes("sticky top-0 z-10 w-full pb-3").style(
        f"background:{DARK_BG};"
    ):
        with ui.row().classes("items-center justify-between w-full"):
            # Left: page title
            with ui.row().classes("items-center gap-3"):
                ui.icon("history_edu").classes("text-[22px]").style(f"color:{ACCENT};")
                ui.label("Journal").classes("text-[22px] font-semibold").style(
                    f"color:{TEXT_PRI};"
                )

            # Right: Add + Export buttons
            with ui.row().classes("items-center gap-2.5"):

                def do_add() -> None:
                    title_val = (
                        inputs["title"].value.strip() if inputs["title"].value else ""
                    )
                    if not title_val:
                        ui.notify("Title / subject is required", color="negative")
                        return
                    if not inputs["entry"].value.strip():
                        ui.notify("Note cannot be empty", color="negative")
                        return
                    device_id, circuit_id = link_lookup.get(title_val, (None, None))
                    db.add_journal_entry(
                        project_id,
                        inputs["entry"].value.strip(),
                        title=title_val,
                        device_id=device_id,
                        circuit_id=circuit_id,
                    )
                    inputs["title"].value = ""
                    inputs["entry"].value = ""
                    ui.notify("Note added — see sidebar", color="positive")

                ui.button("+ ADD", on_click=do_add).classes(
                    "font-semibold rounded-md cursor-pointer"
                ).style(
                    f"background:{ACCENT}; color:#ffffff;"
                    f"padding:8px 20px; border:none;"
                )
                ui.button(
                    "EXPORT NOTES", icon="download", on_click=export_journal
                ).classes("font-semibold rounded-md cursor-pointer").style(
                    f"background:{ACCENT}; color:#ffffff;"
                    f"padding:8px 20px; border:none;"
                )

    # ── Title: type a custom title OR select a device/circuit ────────────────
    with ui.row().classes("w-full mb-3 items-center gap-4"):
        inputs["title"] = (
            ui.input(label="Type a title").props("outlined dense").classes("flex-1")
        )
        ui.label("or").classes("text-sm font-medium").style(f"color:{TEXT_MUTED};")
        if combo_options:

            def on_pick(e):
                if e.value:
                    inputs["title"].value = e.value

            inputs["picker"] = (
                ui.select(
                    options=combo_options,
                    label="Select device / circuit",
                    value=None,
                    on_change=on_pick,
                )
                .props("outlined dense")
                .classes("flex-1")
            )

            # Clear picker when user types in title manually
            def on_title_change():
                if inputs["title"].value and inputs.get("picker"):
                    inputs["picker"].value = None

            inputs["title"].on("update:model-value", on_title_change)

    # ── Notes input (full width, scales with window) ──────────────────────────
    inputs["entry"] = (
        ui.textarea("Type a note, command, or observation...")
        .props("outlined")
        .classes("font-mono text-[13px]")
        .style("width:100%; height:calc(100vh - 280px); overflow:auto; resize:both;")
    )


def _journal_entry_card(
    entry: sqlite3.Row,
    on_delete: Callable[[], None] | None = None,
) -> None:
    """Render a single journal entry as a clean note card."""
    ts = entry["created_at"][:16].replace("T", " ") if entry["created_at"] else "—"
    linked_device = entry["hostname"] if "hostname" in entry.keys() else None
    linked_circuit = entry["cid"] if "cid" in entry.keys() else None
    title = entry["title"] if "title" in entry.keys() else None
    text = entry["entry"] or ""

    # Detect if entry looks like a command (single line, starts with common CLI patterns)
    is_command = (
        "\n" not in text.strip()
        and len(text) < 200
        and any(
            text.strip().startswith(p)
            for p in [
                "show ",
                "set ",
                "delete ",
                "ping ",
                "traceroute ",
                "no ",
                "interface ",
                "router ",
                "ip ",
                "configure",
                "commit",
                "rollback",
                "request ",
            ]
        )
    )

    with ui.element("div").classes("rounded-md").style(
        f"background:{PANEL_BG}; border:1px solid {BORDER}; border-left:3px solid {ACCENT};"
        f"padding:12px 16px;"
    ):
        # Header row: timestamp + linked context + actions
        with ui.row().classes("items-center gap-2.5 mb-1.5"):
            ui.label(ts).classes("font-mono text-[11px]").style(f"color:{TEXT_MUTED};")
            if linked_device:
                ui.label(f"🖥 {linked_device}").classes("text-[11px] rounded").style(
                    f"color:{ACCENT}; background:{ACCENT}12;"
                    f"padding:2px 8px; border:1px solid {ACCENT}33;"
                )
            elif linked_circuit:
                ui.label(f"🔌 {linked_circuit}").classes("text-[11px] rounded").style(
                    f"color:{CISCO}; background:{CISCO}12;"
                    f"padding:2px 8px; border:1px solid {CISCO}33;"
                )
            # Spacer + actions
            with ui.row().classes("ml-auto gap-1.5 items-center"):
                ui.button(
                    "",
                    icon="content_copy",
                    on_click=lambda t=text: ui.run_javascript(
                        f"navigator.clipboard.writeText({json.dumps(t)})"
                    ),
                ).props("flat dense size=sm").style(f"color:{TEXT_MUTED};")
                if on_delete:
                    ui.button("", icon="delete_outline", on_click=on_delete).props(
                        "flat dense size=sm"
                    ).style(f"color:{TEXT_MUTED};")

        # Title (if present)
        if title:
            ui.label(title).classes("text-[14px] font-semibold mb-1").style(
                f"color:{TEXT_PRI};"
            )

        # Entry text
        if is_command:
            ui.label(text).classes(
                "font-mono text-[12.5px] whitespace-pre-wrap leading-relaxed rounded"
            ).style(
                f"color:{TEXT_PRI}; background:#f8f9fb; padding:8px 12px;"
                f"border:1px solid {BORDER};"
            )
        else:
            ui.label(text).classes(
                "text-[13.5px] whitespace-pre-wrap leading-relaxed"
            ).style(f"color:{TEXT_PRI};")


# ─────────────────────────────────────────────────────────────────────────────
# JOURNAL ENTRY DETAIL
# ─────────────────────────────────────────────────────────────────────────────


def _section_journal_entry(
    project_id: int, entry_id: int, navigate: Callable[[str], None]
) -> None:
    """Show a single journal entry detail view with edit and delete."""
    entries = db.get_journal(project_id)
    entry = None
    for e in entries:
        if e["id"] == entry_id:
            entry = e
            break

    if not entry:
        ui.label("Entry not found").classes("p-10").style(f"color:{TEXT_PRI};")
        return

    ts = entry["created_at"][:16].replace("T", " ") if entry["created_at"] else "—"
    title = entry["title"] if "title" in entry.keys() and entry["title"] else None
    linked_device = entry["hostname"] if "hostname" in entry.keys() else None
    linked_circuit = entry["cid"] if "cid" in entry.keys() else None
    text = entry["entry"] or ""

    # Back link
    back = (
        ui.element("div")
        .classes("flex items-center gap-1.5 text-[13px] cursor-pointer mb-5")
        .style(f"color:{TEXT_MUTED};")
    )
    with back:
        ui.icon("arrow_back").classes("text-[16px]")
        ui.label("Back to Journal").classes("text-[13px]")
    back.on("click", lambda: navigate("journal"))

    # Header row with title + action buttons
    with ui.row().classes("items-center justify-between w-full mb-4"):
        with ui.row().classes("items-center gap-3"):
            ui.icon("history_edu").classes("text-[22px]").style(f"color:{ACCENT};")
            ui.label(title or "Journal Entry").classes(
                "text-[22px] font-semibold"
            ).style(f"color:{TEXT_PRI};")

        # Action buttons
        with ui.row().classes("items-center gap-2"):

            def do_delete() -> None:
                db.delete_journal_entry(entry_id)
                ui.notify("Entry deleted", color="negative")
                navigate("journal")

            def open_edit() -> None:
                edit_dlg.open()

            ui.button("EDIT", icon="edit", on_click=open_edit).classes(
                "font-semibold rounded-md cursor-pointer"
            ).style(
                f"background:{ACCENT}; color:#ffffff;" f"padding:8px 18px; border:none;"
            )
            ui.button(
                "DELETE",
                icon="delete",
                on_click=lambda: _confirm_delete(
                    f"Delete this journal entry?", do_delete
                ),
            ).classes("font-semibold rounded-md cursor-pointer").style(
                "background:#c62828; color:#ffffff;" "padding:8px 18px; border:none;"
            )

    # Metadata row
    with ui.row().classes("items-center gap-3 mb-4"):
        ui.label(ts).classes("font-mono text-[12px]").style(f"color:{TEXT_MUTED};")
        if linked_device:
            ui.label(f"🖥 {linked_device}").classes("text-[12px] rounded").style(
                f"color:{ACCENT}; background:{ACCENT}12;"
                f"padding:3px 10px; border:1px solid {ACCENT}33;"
            )
        elif linked_circuit:
            ui.label(f"🔌 {linked_circuit}").classes("text-[12px] rounded").style(
                f"color:{CISCO}; background:{CISCO}12;"
                f"padding:3px 10px; border:1px solid {CISCO}33;"
            )

    # Entry content
    with ui.element("div").classes("rounded-lg p-5 w-full").style(
        f"background:{PANEL_BG}; border:1px solid {BORDER};"
        f"max-height:calc(100vh - 300px); overflow:auto;"
    ):
        ui.label(text).classes(
            "font-mono text-[13px] whitespace-pre-wrap leading-[1.7]"
        ).style(f"color:{TEXT_PRI};")

    # Copy button
    with ui.row().classes("mt-3"):
        ui.button(
            "Copy to clipboard",
            icon="content_copy",
            on_click=lambda: ui.run_javascript(
                f"navigator.clipboard.writeText({json.dumps(text)})"
            ),
        ).classes("text-[12px] rounded-[5px] cursor-pointer").style(
            f"background:{ACCENT}15; color:{ACCENT}; border:1px solid {ACCENT}33;"
            f"padding:6px 14px;"
        )

    # ── Edit dialog ───────────────────────────────────────────────────────────
    with ui.dialog() as edit_dlg, ui.card().classes("rounded-[10px] p-[26px]").style(
        f"background:{PANEL_BG}; border:1px solid {BORDER};"
        f"min-width:600px; min-height:400px; resize:both; overflow:auto;"
    ):
        ui.label("Edit Journal Entry").classes(
            "text-[17px] font-semibold mb-[18px]"
        ).style(f"color:{TEXT_PRI};")
        edit_title = (
            ui.input("Title", value=title or "").props("outlined").classes("w-full")
        )
        edit_text = (
            ui.textarea("Entry", value=text)
            .props("outlined")
            .classes(
                "w-full mt-2.5 font-mono text-[13px] min-h-[250px] resize overflow-auto"
            )
        )
        with ui.row().classes("mt-5 gap-2.5 justify-end"):
            ui.button("Cancel", on_click=edit_dlg.close).style(_cancel_style())

            def do_save() -> None:
                if not edit_title.value.strip():
                    ui.notify("Title is required", color="negative")
                    return
                if not edit_text.value.strip():
                    ui.notify("Entry cannot be empty", color="negative")
                    return
                db.update_journal_entry(
                    entry_id, edit_title.value.strip(), edit_text.value.strip()
                )
                edit_dlg.close()
                ui.notify("Entry updated", color="positive")
                navigate(f"journal:{entry_id}")

            ui.button("Save", on_click=do_save).classes(
                "font-semibold rounded-md cursor-pointer"
            ).style(
                f"background:{ACCENT}; color:#ffffff;" f"padding:8px 22px; border:none;"
            )


# ─────────────────────────────────────────────────────────────────────────────
# SHARED HELPERS
# ─────────────────────────────────────────────────────────────────────────────


def _page_header(icon: str, title: str) -> None:
    with ui.row().classes("items-center gap-3 mb-6"):
        ui.icon(icon).classes("text-[22px]").style(f"color:{ACCENT};")
        ui.label(title).classes("text-[22px] font-semibold").style(f"color:{TEXT_PRI};")


def _add_button(label: str, on_click: Callable[[], None]) -> None:
    ui.button(f"+ {label}", on_click=on_click).classes(
        "text-[13px] font-semibold rounded-md cursor-pointer mb-4"
    ).style(
        f"background:{ACCENT}18; color:{ACCENT}; border:1px solid {ACCENT}44;"
        f"padding:8px 18px;"
    )


def _empty_state(msg: str, icon: str) -> None:
    with ui.element("div").classes("rounded-lg text-center w-full").style(
        f"background:{PANEL_BG}; border:1px dashed {BORDER}; padding:50px;"
    ):
        ui.icon(icon).classes("text-[36px]").style(f"color:{TEXT_MUTED};")
        ui.label(msg).classes("text-[14px] mt-2.5").style(f"color:{TEXT_MUTED};")


def _stat_card(label: str, value: int, icon: str) -> None:
    with ui.element("div").classes("rounded-lg min-w-[130px]").style(
        f"background:{PANEL_BG}; border:1px solid {BORDER}; padding:16px 20px;"
    ):
        ui.icon(icon).classes("text-[18px] mb-2").style(f"color:{ACCENT};")
        ui.label(str(value)).classes("text-[26px] font-bold").style(
            f"color:{TEXT_PRI};"
        )
        ui.label(label).classes("text-[11px] uppercase tracking-wider").style(
            f"color:{TEXT_MUTED};"
        )


def _label_row(
    label: str, value: str, mono: bool = False, accent: bool = False
) -> None:
    color = ACCENT if accent else TEXT_PRI
    with ui.row().classes("items-baseline py-2 gap-0").style(
        f"border-bottom:1px solid {BORDER};"
    ):
        ui.label(label).classes("text-[12px] w-[160px] shrink-0").style(
            f"color:{TEXT_MUTED};"
        )
        if mono:
            ui.label(value).classes("font-mono text-[13px] font-medium").style(
                f"color:{color};"
            )
        else:
            ui.label(value).classes("text-[14px] font-medium").style(f"color:{color};")


def _meta_chip(icon: str, text: str, mono: bool = False) -> None:
    with ui.row().classes("items-center gap-1"):
        ui.icon(icon).classes("text-[13px]").style(f"color:{TEXT_MUTED};")
        if mono:
            ui.label(text).classes("font-mono text-[11.5px]").style(
                f"color:{TEXT_SEC};"
            )
        else:
            ui.label(text).classes("text-[12px]").style(f"color:{TEXT_SEC};")


def _primary_btn_style() -> str:
    return (
        f"background:{ACCENT}; color:#f0f2f5; font-weight:600;"
        f"padding:8px 22px; border-radius:6px; border:none; cursor:pointer;"
    )


def _cancel_style() -> str:
    return (
        f"background:transparent; color:{TEXT_SEC}; border:1px solid {BORDER};"
        f"padding:8px 18px; border-radius:6px;"
    )


def _confirm_delete(message: str, on_confirm: Callable[[], None]) -> None:
    with ui.dialog() as d, ui.card().classes("rounded-[10px] p-6").style(
        f"background:{PANEL_BG}; border:1px solid {BORDER};"
    ):
        ui.label(message).classes("text-[15px] font-semibold mb-4").style(
            f"color:{TEXT_PRI};"
        )
        with ui.row().classes("gap-2.5 justify-end"):
            ui.button("Cancel", on_click=d.close).style(_cancel_style())

            def do() -> None:
                on_confirm()
                d.close()

            ui.button("Delete", on_click=do).classes("font-semibold rounded-md").style(
                "background:#c62828; color:white; padding:8px 18px; border:none;"
            )
    d.open()
