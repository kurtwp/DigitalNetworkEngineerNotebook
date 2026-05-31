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
        ui.label("Invalid project ID").style(f"color:{TEXT_PRI}; padding:40px;")
        return

    project = db.get_project(project_id)
    if not project:
        ui.label("Project not found").style(f"color:{TEXT_PRI}; padding:40px;")
        return

    # Reactive state
    active_section: dict[str, str] = {"key": "overview"}

    def navigate(section_key: str) -> None:
        active_section["key"] = section_key
        render_content()

    # ── Page shell ────────────────────────────────────────────────────────────
    with ui.element("div").style(
        "display:flex; flex-direction:row; height:100vh; overflow:hidden;"
    ):
        # Sidebar (rebuilt on navigate to update active state)
        sidebar_slot = ui.element("div").style("flex-shrink:0;")

        def render_sidebar() -> None:
            sidebar_slot.clear()
            with sidebar_slot:
                sidebar_nav(project_id, active_section["key"], navigate)

        # Main content
        main = ui.element("div").style(
            f"flex:1; overflow-y:auto; background:{DARK_BG}; padding:32px 36px;"
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
    with ui.row().style("gap:12px; margin-bottom:28px; flex-wrap:wrap;"):
        for label, val, icon in [
            ("Devices", len(devices), "dns"),
            ("Circuits", len(circuits), "cable"),
            ("Subnets", len(ips), "lan"),
            ("Paths", len(paths), "route"),
            ("Journal", len(journal), "history_edu"),
        ]:
            _stat_card(label, val, icon)

    # Project details card
    with ui.element("div").style(
        f"background:{PANEL_BG}; border:1px solid {BORDER}; border-radius:8px; padding:22px; max-width:700px;"
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
        ui.label("Recent Journal").style(
            f"font-size:13px; font-weight:600; color:{TEXT_SEC};"
            f"text-transform:uppercase; letter-spacing:0.08em; margin-top:28px; margin-bottom:12px;"
        )
        for entry in journal[:5]:
            _journal_entry_card(entry)


# ─────────────────────────────────────────────────────────────────────────────
# DEVICES
# ─────────────────────────────────────────────────────────────────────────────


def _section_devices(project_id: int) -> None:
    _page_header("dns", "Devices")

    content_col = ui.column().style("gap:16px; width:100%;")

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

            with ui.row().style("gap:10px; align-items:center; margin-bottom:8px;"):
                ui.button(
                    "Download CSV", icon="download", on_click=download_devices_csv
                ).style(
                    f"background:{ACCENT}15; color:{ACCENT}; border:1px solid {ACCENT}33;"
                    f"font-size:12px; padding:6px 14px; border-radius:5px; cursor:pointer;"
                )
                ui.label(
                    f"{len(devices)} device{'s' if len(devices) != 1 else ''}"
                ).style(f"font-size:12px; color:{TEXT_MUTED};")

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
                .style(
                    f"width:100%; background:{PANEL_BG}; border:1px solid {BORDER}; border-radius:8px;"
                )
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
    with ui.dialog() as add_dlg, ui.card().style(
        f"background:{PANEL_BG}; border:1px solid {BORDER}; border-radius:10px; padding:26px; min-width:500px;"
    ):
        ui.label("Add Device").style(
            f"font-size:17px; font-weight:600; color:{TEXT_PRI}; margin-bottom:18px;"
        )
        hostname_in = ui.input("Hostname *").props("outlined").style("width:100%;")
        vendor_in = (
            ui.select(["Cisco", "Juniper", "Other"], label="Vendor", value="Cisco")
            .props("outlined")
            .style("width:100%; margin-top:10px;")
        )
        model_in = (
            ui.input("Model").props("outlined").style("width:100%; margin-top:10px;")
        )
        mgmt_in = (
            ui.input("Management IP")
            .props("outlined")
            .style("width:100%; margin-top:10px;")
        )
        site_in = (
            ui.input("Site / Location")
            .props("outlined")
            .style("width:100%; margin-top:10px;")
        )
        notes_in = (
            ui.textarea("Notes").props("outlined").style("width:100%; margin-top:10px;")
        )

        with ui.row().style("margin-top:22px; gap:10px; justify-content:flex-end;"):
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

    with ui.element("div").style(
        f"background:{PANEL_BG}; border:1px solid {BORDER}; border-radius:8px; padding:18px;"
    ):
        with ui.row().style("align-items:flex-start; justify-content:space-between;"):
            with ui.column().style("gap:4px;"):
                with ui.row().style("align-items:center; gap:10px;"):
                    ui.label(dev["hostname"]).style(
                        f"font-family:'JetBrains Mono',monospace; font-size:15px; font-weight:600; color:{TEXT_PRI};"
                    )
                    ui.element("span").classes(badge_class).style("").set_content(
                        vendor
                    )
                with ui.row().style(f"gap:20px; margin-top:4px;"):
                    if dev["model"]:
                        _meta_chip("memory", dev["model"])
                    if dev["mgmt_ip"]:
                        _meta_chip("router", dev["mgmt_ip"], mono=True)
                    if dev["site"]:
                        _meta_chip("place", dev["site"])

            with ui.row().style("gap:6px;"):
                del_btn = ui.button("", icon="delete_outline").style(
                    f"background:transparent; color:{TEXT_MUTED}; border:none; cursor:pointer;"
                )
                del_btn.on(
                    "click",
                    lambda did=dev["id"]: _confirm_delete(
                        f"Delete {dev['hostname']}?",
                        lambda: (db.delete_device(did), refresh_cb()),
                    ),
                )

        # Interfaces sub-section (always show expansion)
        with ui.expansion("Interfaces", icon="cable").style(
            f"margin-top:14px; background:#f8f9fb; border-radius:6px;"
            f"border:1px solid {BORDER};"
        ):
            iface_col = ui.column().style("gap:6px; padding:10px 0;")

            def refresh_ifaces(device_id: int = dev["id"]) -> None:
                iface_col.clear()
                ifaces = db.get_interfaces(device_id)
                with iface_col:
                    if not ifaces:
                        ui.label("No interfaces").style(
                            f"color:{TEXT_MUTED}; font-size:12px; padding:4px 0;"
                        )
                    for iface in ifaces:
                        with ui.row().style(
                            f"align-items:center; gap:12px; padding:6px 8px;"
                            f"background:#f0f2f5; border-radius:5px;"
                        ):
                            ui.label(iface["name"]).style(
                                f"font-family:'JetBrains Mono',monospace; font-size:12.5px; color:{ACCENT}; min-width:140px;"
                            )
                            if iface["ip_address"]:
                                ui.label(iface["ip_address"]).style(
                                    f"font-family:'JetBrains Mono',monospace; font-size:12px; color:{TEXT_SEC};"
                                )
                            if iface["description"]:
                                ui.label(iface["description"]).style(
                                    f"font-size:12px; color:{TEXT_MUTED}; flex:1;"
                                )
                            del_i = ui.icon("close").style(
                                f"font-size:14px; color:{TEXT_MUTED}; cursor:pointer; margin-left:auto;"
                            )
                            del_i.on(
                                "click",
                                lambda iid=iface["id"]: (
                                    db.delete_interface(iid),
                                    refresh_ifaces(),
                                ),
                            )

                    # Add interface inline
                    with ui.row().style(
                        "margin-top:8px; gap:8px; align-items:flex-end;"
                    ):
                        ni = (
                            ui.input("Interface name")
                            .props("outlined")
                            .style("flex:1;")
                        )
                        nip = ui.input("IP").props("outlined").style("width:140px;")
                        nd = (
                            ui.input("Description / CID")
                            .props("outlined")
                            .style("flex:2;")
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

                        ui.button("+", on_click=add_iface).style(
                            f"background:{ACCENT}22; color:{ACCENT}; border:1px solid {ACCENT}44;"
                            f"padding:6px 12px; border-radius:5px; font-weight:700; cursor:pointer;"
                        )

            refresh_ifaces()

        # Config snippets sub-section
        with ui.expansion("Config Snippets", icon="code").style(
            f"margin-top:8px; background:#f8f9fb; border-radius:6px; border:1px solid {BORDER};"
        ):
            snip_col = ui.column().style("gap:8px; padding:10px 0;")

            def refresh_snippets(device_id: int = dev["id"]) -> None:
                snip_col.clear()
                snips = db.get_snippets(device_id)
                with snip_col:
                    if not snips:
                        ui.label("No config snippets").style(
                            f"color:{TEXT_MUTED}; font-size:12px;"
                        )
                    for s in snips:
                        with ui.element("div").style(
                            f"background:#f8f9fb; border:1px solid {BORDER}; border-radius:6px; padding:12px;"
                        ):
                            with ui.row().style(
                                "align-items:center; justify-content:space-between; margin-bottom:8px;"
                            ):
                                ui.label(s["label"]).style(
                                    f"font-size:13px; font-weight:600; color:{TEXT_PRI};"
                                )
                                with ui.row().style("gap:8px; align-items:center;"):
                                    if s["version"]:
                                        ui.label(s["version"]).style(
                                            f"font-size:10px; color:{TEXT_MUTED}; font-family:'JetBrains Mono',monospace;"
                                            f"background:#f5f7fa; padding:2px 6px; border-radius:3px;"
                                        )
                                    ui.button(
                                        "Copy",
                                        on_click=lambda c=s[
                                            "content"
                                        ]: ui.run_javascript(
                                            f"navigator.clipboard.writeText({json.dumps(c or '')})"
                                        ),
                                    ).style(
                                        f"background:{ACCENT}15; color:{ACCENT}; border:1px solid {ACCENT}33;"
                                        f"font-size:11px; padding:3px 10px; border-radius:4px; cursor:pointer;"
                                    )
                                    ui.icon("delete_outline").style(
                                        f"font-size:15px; color:{TEXT_MUTED}; cursor:pointer;"
                                    ).on(
                                        "click",
                                        lambda sid=s["id"]: (
                                            db.delete_snippet(sid),
                                            refresh_snippets(),
                                        ),
                                    )
                            ui.code(s["content"] or "").style(
                                f"font-family:'JetBrains Mono',monospace; font-size:12px; color:#1b5e20;"
                                f"background:#f8f9fb; white-space:pre; overflow-x:auto; display:block;"
                            )

                    # Add snippet
                    ui.separator().style(f"background:{BORDER}; margin:8px 0;")
                    sl = ui.input("Label").props("outlined").style("width:100%;")
                    sv = (
                        ui.input("Version", value="v1")
                        .props("outlined")
                        .style("width:120px; margin-top:8px;")
                    )
                    sc_text = (
                        ui.textarea("Config")
                        .classes("code-area")
                        .style(
                            "width:100%; margin-top:8px; font-family:'JetBrains Mono',monospace;"
                        )
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

                    ui.button("Add Snippet", on_click=add_snip).style(
                        f"background:{ACCENT}18; color:{ACCENT}; border:1px solid {ACCENT}33;"
                        f"font-size:12px; padding:6px 14px; border-radius:5px; margin-top:8px; cursor:pointer;"
                    )

            refresh_snippets()


# ─────────────────────────────────────────────────────────────────────────────
# CIRCUITS
# ─────────────────────────────────────────────────────────────────────────────


def _section_circuits(project_id: int) -> None:
    _page_header("cable", "Circuits")

    content_col = ui.column().style("gap:16px; width:100%;")

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

            with ui.row().style("gap:10px; align-items:center; margin-bottom:8px;"):
                ui.button(
                    "Download CSV", icon="download", on_click=download_circuits_csv
                ).style(
                    f"background:{ACCENT}15; color:{ACCENT}; border:1px solid {ACCENT}33;"
                    f"font-size:12px; padding:6px 14px; border-radius:5px; cursor:pointer;"
                )
                ui.label(
                    f"{len(circuits)} circuit{'s' if len(circuits) != 1 else ''}"
                ).style(f"font-size:12px; color:{TEXT_MUTED};")

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
                .style(
                    f"width:100%; background:{PANEL_BG}; border:1px solid {BORDER}; border-radius:8px;"
                )
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
    with ui.dialog() as add_dlg, ui.card().style(
        f"background:{PANEL_BG}; border:1px solid {BORDER}; border-radius:10px; padding:26px; min-width:480px;"
    ):
        ui.label("Add Circuit").style(
            f"font-size:17px; font-weight:600; color:{TEXT_PRI}; margin-bottom:18px;"
        )
        cid_in = ui.input("Circuit ID *").props("outlined").style("width:100%;")
        carr_in = (
            ui.input("Carrier / Provider")
            .props("outlined")
            .style("width:100%; margin-top:10px;")
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
            .style("width:100%; margin-top:10px;")
        )
        bw_in = ui.input("Bandwidth (e.g. 1Gbps)").style("width:100%; margin-top:10px;")
        stat_in = (
            ui.select(
                ["active", "pending", "in-maintenance", "decom"],
                label="Status",
                value="active",
            )
            .props("outlined")
            .style("width:100%; margin-top:10px;")
        )
        notes_in = (
            ui.textarea("Notes").props("outlined").style("width:100%; margin-top:10px;")
        )

        with ui.row().style("margin-top:22px; gap:10px; justify-content:flex-end;"):
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
    ip_col = ui.column().style("gap:8px; width:100%;")

    def refresh() -> None:
        ip_col.clear()
        entries = db.get_ip_plan(project_id)
        with ip_col:
            if not entries:
                _empty_state("No subnets added yet", "lan")
                return
            with ui.element("div").style(
                f"display:grid; grid-template-columns: 1.5fr 2fr 1.5fr 0.8fr auto;"
                f"padding:8px 14px; font-size:10px; text-transform:uppercase;"
                f"letter-spacing:0.08em; color:{TEXT_MUTED}; font-weight:600; gap:0;"
            ):
                for h in ["Subnet / CIDR", "Purpose", "Assigned To", "VLAN", ""]:
                    ui.label(h)
            for e in entries:
                _ip_row(e, refresh)

    with ui.dialog() as add_dlg, ui.card().style(
        f"background:{PANEL_BG}; border:1px solid {BORDER}; border-radius:10px; padding:26px; min-width:460px;"
    ):
        ui.label("Add IP Entry").style(
            f"font-size:17px; font-weight:600; color:{TEXT_PRI}; margin-bottom:18px;"
        )
        sub_in = ui.input("Subnet / CIDR *  (e.g. 10.0.0.0/24)").style("width:100%;")
        pur_in = (
            ui.input("Purpose").props("outlined").style("width:100%; margin-top:10px;")
        )
        asgn_in = ui.input("Assigned Device(s)").style("width:100%; margin-top:10px;")
        vlan_in = (
            ui.input("VLAN ID").props("outlined").style("width:100%; margin-top:10px;")
        )
        note_in = (
            ui.input("Notes").props("outlined").style("width:100%; margin-top:10px;")
        )

        with ui.row().style("margin-top:22px; gap:10px; justify-content:flex-end;"):
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
    with ui.element("div").style(
        f"display:grid; grid-template-columns: 1.5fr 2fr 1.5fr 0.8fr auto;"
        f"padding:11px 14px; background:{PANEL_BG}; border:1px solid {BORDER};"
        f"border-radius:6px; align-items:center; gap:0;"
    ):
        ui.label(e["subnet"]).style(
            f"font-family:'JetBrains Mono',monospace; font-size:13px; color:{ACCENT}; font-weight:600;"
        )
        ui.label(e["purpose"] or "—").style(f"font-size:13px; color:{TEXT_SEC};")
        ui.label(e["assigned_to"] or "—").style(
            f"font-family:'JetBrains Mono',monospace; font-size:12px; color:{TEXT_MUTED};"
        )
        ui.label(e["vlan_id"] or "—").style(
            f"font-family:'JetBrains Mono',monospace; font-size:12px; color:{TEXT_MUTED};"
        )
        ui.icon("delete_outline").style(
            f"font-size:16px; color:{TEXT_MUTED}; cursor:pointer;"
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
    paths_col = ui.column().style("gap:14px; width:100%;")

    def refresh() -> None:
        paths_col.clear()
        paths = db.get_paths(project_id)
        with paths_col:
            if not paths:
                _empty_state("No paths defined yet", "route")
                return
            for p in paths:
                _path_card(p, project_id, refresh)

    with ui.dialog() as add_dlg, ui.card().style(
        f"background:{PANEL_BG}; border:1px solid {BORDER}; border-radius:10px; padding:26px; min-width:500px;"
    ):
        ui.label("New A-Z Path").style(
            f"font-size:17px; font-weight:600; color:{TEXT_PRI}; margin-bottom:18px;"
        )
        name_in = ui.input("Path Name *").props("outlined").style("width:100%;")
        cust_in = (
            ui.input("Customer / Service")
            .props("outlined")
            .style("width:100%; margin-top:10px;")
        )
        a_in = ui.input("A-Side (e.g. Customer Site A)").style(
            "width:100%; margin-top:10px;"
        )
        z_in = ui.input("Z-Side (e.g. Data Center)").style(
            "width:100%; margin-top:10px;"
        )
        stat_in = (
            ui.select(["active", "in-build", "decom"], label="Status", value="active")
            .props("outlined")
            .style("width:100%; margin-top:10px;")
        )

        with ui.row().style("margin-top:22px; gap:10px; justify-content:flex-end;"):
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

    with ui.element("div").style(
        f"background:{PANEL_BG}; border:1px solid {BORDER}; border-radius:8px; padding:20px;"
    ):
        with ui.row().style(
            "align-items:flex-start; justify-content:space-between; margin-bottom:16px;"
        ):
            with ui.column().style("gap:4px;"):
                ui.label(path["name"]).style(
                    f"font-size:15px; font-weight:600; color:{TEXT_PRI};"
                )
                if path["customer"]:
                    ui.label(path["customer"]).style(
                        f"font-size:12px; color:{TEXT_MUTED};"
                    )
            with ui.row().style("align-items:center; gap:6px;"):
                ui.element("span").style(
                    f"width:7px;height:7px;border-radius:50%;background:{sc};display:inline-block;"
                )
                ui.label(path["status"] or "active").style(
                    f"font-size:12px; color:{sc};"
                )
                ui.icon("delete_outline").style(
                    f"font-size:16px; color:{TEXT_MUTED}; cursor:pointer; margin-left:8px;"
                ).on(
                    "click",
                    lambda pid=path["id"]: _confirm_delete(
                        f"Delete path '{path['name']}'?",
                        lambda: (db.delete_path(pid), refresh_cb()),
                    ),
                )

        # A-side / Z-side labels
        with ui.row().style("gap:8px; align-items:center; margin-bottom:14px;"):
            if path["a_side"]:
                ui.label(f"A: {path['a_side']}").style(
                    f"font-size:12px; color:{ACCENT}; background:{ACCENT}12;"
                    f"padding:3px 10px; border-radius:4px; border:1px solid {ACCENT}33;"
                )
            ui.icon("arrow_forward").style(f"font-size:14px; color:{TEXT_MUTED};")
            if path["z_side"]:
                ui.label(f"Z: {path['z_side']}").style(
                    f"font-size:12px; color:#52a0c9; background:#52a0c912;"
                    f"padding:3px 10px; border-radius:4px; border:1px solid #52a0c933;"
                )

        # Hop chain
        hop_col = ui.column().style("gap:0;")
        with hop_col:
            _render_hops(hops, hop_col)

        # Add hop controls
        with ui.expansion("Add Hop", icon="add_circle_outline").style(
            f"margin-top:10px; background:#f8f9fb; border-radius:6px; border:1px solid {BORDER};"
        ):
            hop_type_sel = (
                ui.select(["device", "carrier"], label="Hop Type", value="device")
                .props("outlined")
                .style("width:100%;")
            )
            devices = db.get_devices(project_id)
            device_names = {d["hostname"]: d["id"] for d in devices}
            dev_sel = ui.select(
                list(device_names.keys()) or ["(no devices)"], label="Device"
            ).style("width:100%; margin-top:10px;")
            ing_in = (
                ui.input("Ingress Interface")
                .props("outlined")
                .style("width:100%; margin-top:10px;")
            )
            egr_in = (
                ui.input("Egress Interface")
                .props("outlined")
                .style("width:100%; margin-top:10px;")
            )
            carr_lbl_in = (
                ui.input("Carrier Label")
                .props("outlined")
                .style("width:100%; margin-top:10px;")
            )
            circuits = db.get_circuits(project_id)
            ckt_names = {"(none)": None} | {c["cid"]: c["id"] for c in circuits}
            ckt_sel = ui.select(
                list(ckt_names.keys()), label="Circuit ID (optional)", value="(none)"
            ).style("width:100%; margin-top:10px;")
            hop_notes = (
                ui.input("Notes")
                .props("outlined")
                .style("width:100%; margin-top:10px;")
            )

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

            ui.button("Add Hop", on_click=do_add_hop).style(
                f"background:{ACCENT}18; color:{ACCENT}; border:1px solid {ACCENT}33;"
                f"font-size:12px; padding:6px 14px; border-radius:5px; margin-top:12px; cursor:pointer;"
            )


def _render_hops(hops: list[sqlite3.Row], hop_col) -> None:
    """Render the hop chain visualization. Hop deletion now refreshes the UI."""
    if not hops:
        ui.label("No hops yet — add hops below").style(
            f"color:{TEXT_MUTED}; font-size:12px; padding:4px 0;"
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

        with ui.element("div").style(
            f"background:{bg}; border:1px solid {border}; border-radius:6px;"
            f"padding:10px 14px; position:relative;"
        ):
            with ui.row().style("align-items:center; gap:10px;"):
                if is_carrier:
                    ui.icon("cloud").style(f"font-size:16px; color:#7e57c2;")
                    label = hop["carrier_label"] or "Carrier"
                    ui.label(label).style(
                        f"font-size:13px; color:#5c35a0; font-weight:600;"
                    )
                    if hop["cid"]:
                        ui.label(f"CID: {hop['cid']}").style(
                            f"font-family:'JetBrains Mono',monospace; font-size:11px;"
                            f"color:{ACCENT}; background:{ACCENT}12; padding:2px 8px; border-radius:3px;"
                        )
                else:
                    ui.icon("dns").style(f"font-size:16px; color:{ACCENT};")
                    ui.label(hop["hostname"] or "—").style(
                        f"font-family:'JetBrains Mono',monospace; font-size:13px; color:{TEXT_PRI}; font-weight:600;"
                    )
                    if hop["vendor"]:
                        vendor_color = JUNIPER if hop["vendor"] == "Juniper" else CISCO
                        ui.label(hop["vendor"]).style(
                            f"font-size:11px; color:{vendor_color}; background:{vendor_color}18;"
                            f"padding:1px 7px; border-radius:3px;"
                        )
                    if hop["ingress_iface"]:
                        ui.label(f"in: {hop['ingress_iface']}").style(
                            f"font-family:'JetBrains Mono',monospace; font-size:11px; color:{TEXT_MUTED};"
                        )
                    if hop["egress_iface"]:
                        ui.label(f"out: {hop['egress_iface']}").style(
                            f"font-family:'JetBrains Mono',monospace; font-size:11px; color:{TEXT_MUTED};"
                        )
                ui.icon("delete_outline").style(
                    f"font-size:14px; color:{TEXT_MUTED}; cursor:pointer; margin-left:auto;"
                ).on(
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
    # Build device/circuit options for linking
    devices = db.get_devices(project_id)
    circuits = db.get_circuits(project_id)
    link_options: dict[str, tuple[int | None, int | None]] = {"(none)": (None, None)}
    for d in devices:
        link_options[f"🖥 {d['hostname']}"] = (d["id"], None)
    for c in circuits:
        link_options[f"🔌 {c['cid']}"] = (None, c["id"])

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
            title_str = f"  **{e['title']}**\n" if e.get("title") else ""
            lines.append(f"[{ts}]{link}\n{title_str}{e['entry']}\n")
        content = "\n".join(lines)
        ui.download(content.encode("utf-8"), "journal.md")

    # ── Sticky header row: title left, controls right ─────────────────────────
    with ui.element("div").style(
        f"position:sticky; top:0; z-index:10; background:{DARK_BG};"
        f"padding-bottom:12px; width:100%;"
    ):
        with ui.row().style(
            "align-items:center; justify-content:space-between; width:100%;"
        ):
            # Left: page title
            with ui.row().style("align-items:center; gap:12px;"):
                ui.icon("history_edu").style(f"font-size:22px; color:{ACCENT};")
                ui.label("Journal").style(
                    f"font-size:22px; font-weight:600; color:{TEXT_PRI};"
                )

            # Right: link selector + Add + Export
            with ui.row().style("align-items:center; gap:10px;"):
                link_sel = (
                    ui.select(
                        list(link_options.keys()),
                        value="(none)",
                        label="Link to device/circuit (optional)",
                    )
                    .props("outlined dense")
                    .style("min-width:250px;")
                )

                def do_add() -> None:
                    if not entry_in.value.strip():
                        ui.notify("Note cannot be empty", color="negative")
                        return
                    device_id, circuit_id = link_options.get(
                        link_sel.value, (None, None)
                    )
                    db.add_journal_entry(
                        project_id,
                        entry_in.value.strip(),
                        title=title_in.value.strip(),
                        device_id=device_id,
                        circuit_id=circuit_id,
                    )
                    title_in.value = ""
                    entry_in.value = ""
                    link_sel.value = "(none)"
                    ui.notify("Note added — see sidebar", color="positive")

                ui.button("+ ADD", on_click=do_add).style(
                    f"background:{ACCENT}; color:#ffffff; font-weight:600;"
                    f"padding:8px 20px; border-radius:6px; border:none; cursor:pointer;"
                )
                ui.button(
                    "EXPORT NOTES", icon="download", on_click=export_journal
                ).style(
                    f"background:{ACCENT}; color:#ffffff; font-weight:600;"
                    f"padding:8px 20px; border-radius:6px; border:none; cursor:pointer;"
                )

    # ── Title + Notes input (full width, scales with window) ──────────────────
    title_in = (
        ui.input("Title (optional)")
        .props("outlined dense")
        .style("width:100%; margin-bottom:8px;")
    )
    entry_in = (
        ui.textarea("Type a note, command, or observation...")
        .props("outlined autogrow")
        .style(
            "width:100%; font-family:'JetBrains Mono',monospace; font-size:13px;"
            "min-height:200px;"
        )
    )

    # Hint text
    ui.label("Notes appear in the sidebar under Journal. Click one to view it.").style(
        f"font-size:12px; color:{TEXT_MUTED}; margin-top:16px;"
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

    with ui.element("div").style(
        f"background:{PANEL_BG}; border:1px solid {BORDER}; border-left:3px solid {ACCENT};"
        f"border-radius:6px; padding:12px 16px;"
    ):
        # Header row: timestamp + linked context + actions
        with ui.row().style("align-items:center; gap:10px; margin-bottom:6px;"):
            ui.label(ts).style(
                f"font-family:'JetBrains Mono',monospace; font-size:11px; color:{TEXT_MUTED};"
            )
            if linked_device:
                ui.label(f"🖥 {linked_device}").style(
                    f"font-size:11px; color:{ACCENT}; background:{ACCENT}12;"
                    f"padding:2px 8px; border-radius:4px; border:1px solid {ACCENT}33;"
                )
            elif linked_circuit:
                ui.label(f"🔌 {linked_circuit}").style(
                    f"font-size:11px; color:{CISCO}; background:{CISCO}12;"
                    f"padding:2px 8px; border-radius:4px; border:1px solid {CISCO}33;"
                )
            # Spacer + actions
            with ui.row().style("margin-left:auto; gap:6px; align-items:center;"):
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
            ui.label(title).style(
                f"font-size:14px; font-weight:600; color:{TEXT_PRI}; margin-bottom:4px;"
            )

        # Entry text
        font = (
            "font-family:'JetBrains Mono',monospace; font-size:12.5px;"
            if is_command
            else "font-size:13.5px;"
        )
        bg_style = (
            f"background:#f8f9fb; padding:8px 12px; border-radius:4px; border:1px solid {BORDER};"
            if is_command
            else ""
        )
        ui.label(text).style(
            f"{font} color:{TEXT_PRI}; line-height:1.6; white-space:pre-wrap; {bg_style}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# JOURNAL ENTRY DETAIL
# ─────────────────────────────────────────────────────────────────────────────


def _section_journal_entry(
    project_id: int, entry_id: int, navigate: Callable[[str], None]
) -> None:
    """Show a single journal entry detail view."""
    entries = db.get_journal(project_id)
    entry = None
    for e in entries:
        if e["id"] == entry_id:
            entry = e
            break

    if not entry:
        ui.label("Entry not found").style(f"color:{TEXT_PRI}; padding:40px;")
        return

    # Back link
    with ui.row().style(
        "align-items:center; gap:8px; margin-bottom:20px; cursor:pointer;"
    ):
        back = ui.element("div").style(
            f"display:flex; align-items:center; gap:6px; color:{TEXT_MUTED};"
            f"font-size:13px; cursor:pointer;"
        )
        with back:
            ui.icon("arrow_back").style("font-size:16px;")
            ui.label("Back to Journal").style("font-size:13px;")
        back.on("click", lambda: navigate("journal"))

    ts = entry["created_at"][:16].replace("T", " ") if entry["created_at"] else "—"
    title = entry["title"] if "title" in entry.keys() and entry["title"] else None
    linked_device = entry["hostname"] if "hostname" in entry.keys() else None
    linked_circuit = entry["cid"] if "cid" in entry.keys() else None
    text = entry["entry"] or ""

    # Header
    with ui.row().style("align-items:center; gap:12px; margin-bottom:16px;"):
        ui.icon("history_edu").style(f"font-size:22px; color:{ACCENT};")
        if title:
            ui.label(title).style(f"font-size:22px; font-weight:600; color:{TEXT_PRI};")
        else:
            ui.label("Journal Entry").style(
                f"font-size:22px; font-weight:600; color:{TEXT_PRI};"
            )

    # Metadata row
    with ui.row().style("align-items:center; gap:12px; margin-bottom:16px;"):
        ui.label(ts).style(
            f"font-family:'JetBrains Mono',monospace; font-size:12px; color:{TEXT_MUTED};"
        )
        if linked_device:
            ui.label(f"🖥 {linked_device}").style(
                f"font-size:12px; color:{ACCENT}; background:{ACCENT}12;"
                f"padding:3px 10px; border-radius:4px; border:1px solid {ACCENT}33;"
            )
        elif linked_circuit:
            ui.label(f"🔌 {linked_circuit}").style(
                f"font-size:12px; color:{CISCO}; background:{CISCO}12;"
                f"padding:3px 10px; border-radius:4px; border:1px solid {CISCO}33;"
            )

    # Entry content
    with ui.element("div").style(
        f"background:{PANEL_BG}; border:1px solid {BORDER}; border-radius:8px;"
        f"padding:20px; width:100%;"
    ):
        ui.label(text).style(
            f"font-family:'JetBrains Mono',monospace; font-size:13px;"
            f"color:{TEXT_PRI}; line-height:1.7; white-space:pre-wrap;"
        )

    # Copy button
    with ui.row().style("margin-top:12px;"):
        ui.button(
            "Copy to clipboard",
            icon="content_copy",
            on_click=lambda: ui.run_javascript(
                f"navigator.clipboard.writeText({json.dumps(text)})"
            ),
        ).style(
            f"background:{ACCENT}15; color:{ACCENT}; border:1px solid {ACCENT}33;"
            f"font-size:12px; padding:6px 14px; border-radius:5px; cursor:pointer;"
        )


# ─────────────────────────────────────────────────────────────────────────────
# SHARED HELPERS
# ─────────────────────────────────────────────────────────────────────────────


def _page_header(icon: str, title: str) -> None:
    with ui.row().style("align-items:center; gap:12px; margin-bottom:24px;"):
        ui.icon(icon).style(f"font-size:22px; color:{ACCENT};")
        ui.label(title).style(f"font-size:22px; font-weight:600; color:{TEXT_PRI};")


def _add_button(label: str, on_click: Callable[[], None]) -> None:
    ui.button(f"+ {label}", on_click=on_click).style(
        f"background:{ACCENT}18; color:{ACCENT}; border:1px solid {ACCENT}44;"
        f"font-size:13px; font-weight:600; padding:8px 18px; border-radius:6px;"
        f"cursor:pointer; margin-bottom:16px;"
    )


def _empty_state(msg: str, icon: str) -> None:
    with ui.element("div").style(
        f"background:{PANEL_BG}; border:1px dashed {BORDER}; border-radius:8px;"
        f"padding:50px; text-align:center; width:100%;"
    ):
        ui.icon(icon).style(f"font-size:36px; color:{TEXT_MUTED};")
        ui.label(msg).style(f"color:{TEXT_MUTED}; font-size:14px; margin-top:10px;")


def _stat_card(label: str, value: int, icon: str) -> None:
    with ui.element("div").style(
        f"background:{PANEL_BG}; border:1px solid {BORDER}; border-radius:8px;"
        f"padding:16px 20px; min-width:130px;"
    ):
        ui.icon(icon).style(f"font-size:18px; color:{ACCENT}; margin-bottom:8px;")
        ui.label(str(value)).style(
            f"font-size:26px; font-weight:700; color:{TEXT_PRI};"
        )
        ui.label(label).style(
            f"font-size:11px; color:{TEXT_MUTED}; text-transform:uppercase; letter-spacing:0.08em;"
        )


def _label_row(
    label: str, value: str, mono: bool = False, accent: bool = False
) -> None:
    color = ACCENT if accent else TEXT_PRI
    font = (
        f"font-family:'JetBrains Mono',monospace; font-size:13px;"
        if mono
        else f"font-size:14px;"
    )
    with ui.row().style(
        f"align-items:baseline; padding:8px 0; border-bottom:1px solid {BORDER}; gap:0;"
    ):
        ui.label(label).style(
            f"font-size:12px; color:{TEXT_MUTED}; width:160px; flex-shrink:0;"
        )
        ui.label(value).style(f"{font} color:{color}; font-weight:500;")


def _meta_chip(icon: str, text: str, mono: bool = False) -> None:
    font = (
        "font-family:'JetBrains Mono',monospace; font-size:11.5px;"
        if mono
        else "font-size:12px;"
    )
    with ui.row().style(f"align-items:center; gap:4px;"):
        ui.icon(icon).style(f"font-size:13px; color:{TEXT_MUTED};")
        ui.label(text).style(f"{font} color:{TEXT_SEC};")


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
    with ui.dialog() as d, ui.card().style(
        f"background:{PANEL_BG}; border:1px solid {BORDER}; border-radius:10px; padding:24px;"
    ):
        ui.label(message).style(
            f"font-size:15px; font-weight:600; color:{TEXT_PRI}; margin-bottom:16px;"
        )
        with ui.row().style("gap:10px; justify-content:flex-end;"):
            ui.button("Cancel", on_click=d.close).style(_cancel_style())

            def do() -> None:
                on_confirm()
                d.close()

            ui.button("Delete", on_click=do).style(
                "background:#c62828; color:white; font-weight:600; padding:8px 18px; border-radius:6px; border:none;"
            )
    d.open()
