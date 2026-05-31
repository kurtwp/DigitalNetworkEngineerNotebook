"""Database layer for Net Notebook — SQLite3 with typed helpers."""

import logging
import sqlite3
from pathlib import Path

log = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "worknotes.db"

# ── Allowed fields for dynamic UPDATE queries (whitelist for safety) ─────────
_PROJECT_FIELDS = frozenset(
    {"name", "ticket_num", "type_of_work", "status", "scheduled_date", "notes"}
)
_DEVICE_FIELDS = frozenset({"hostname", "vendor", "model", "mgmt_ip", "site", "notes"})
_CIRCUIT_FIELDS = frozenset(
    {"cid", "carrier", "circuit_type", "bandwidth", "status", "notes"}
)


def get_conn() -> sqlite3.Connection:
    """Open a connection to the worknotes database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create all tables if they don't exist."""
    try:
        with get_conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_num  TEXT,
                    name        TEXT NOT NULL,
                    type_of_work TEXT,
                    status      TEXT DEFAULT 'active',
                    scheduled_date TEXT,
                    notes       TEXT,
                    created_at  TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
                );

                CREATE TABLE IF NOT EXISTS circuits (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    cid         TEXT NOT NULL,
                    carrier     TEXT,
                    circuit_type TEXT,
                    bandwidth   TEXT,
                    status      TEXT DEFAULT 'active',
                    notes       TEXT
                );

                CREATE TABLE IF NOT EXISTS devices (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    hostname    TEXT NOT NULL,
                    vendor      TEXT CHECK(vendor IN ('Juniper','Cisco','Other')),
                    model       TEXT,
                    mgmt_ip     TEXT,
                    site        TEXT,
                    notes       TEXT
                );

                CREATE TABLE IF NOT EXISTS interfaces (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id   INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
                    name        TEXT NOT NULL,
                    ip_address  TEXT,
                    description TEXT,
                    role        TEXT,
                    circuit_id  INTEGER REFERENCES circuits(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS ip_plan (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    subnet      TEXT NOT NULL,
                    purpose     TEXT,
                    assigned_to TEXT,
                    vlan_id     TEXT,
                    notes       TEXT
                );

                CREATE TABLE IF NOT EXISTS paths (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    name        TEXT NOT NULL,
                    customer    TEXT,
                    a_side      TEXT,
                    z_side      TEXT,
                    status      TEXT DEFAULT 'active',
                    notes       TEXT
                );

                CREATE TABLE IF NOT EXISTS path_hops (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    path_id     INTEGER NOT NULL REFERENCES paths(id) ON DELETE CASCADE,
                    hop_order   INTEGER NOT NULL,
                    hop_type    TEXT CHECK(hop_type IN ('device','carrier')),
                    device_id   INTEGER REFERENCES devices(id) ON DELETE SET NULL,
                    ingress_iface TEXT,
                    egress_iface  TEXT,
                    carrier_label TEXT,
                    circuit_id  INTEGER REFERENCES circuits(id) ON DELETE SET NULL,
                    notes       TEXT
                );

                CREATE TABLE IF NOT EXISTS config_snippets (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id   INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
                    label       TEXT NOT NULL,
                    vendor      TEXT,
                    version     TEXT,
                    content     TEXT,
                    created_at  TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
                );

                CREATE TABLE IF NOT EXISTS journal_entries (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    tag         TEXT DEFAULT 'info',
                    entry       TEXT NOT NULL,
                    created_at  TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
                );
            """
            )
        log.info("Database initialized at %s", DB_PATH)
    except sqlite3.Error as exc:
        log.error("Failed to initialize database: %s", exc, exc_info=True)
        raise


# ── Project helpers ──────────────────────────────────────────────────────────


def get_all_projects() -> list[sqlite3.Row]:
    """Return all projects ordered by creation date (newest first)."""
    try:
        with get_conn() as conn:
            return conn.execute(
                "SELECT * FROM projects ORDER BY created_at DESC"
            ).fetchall()
    except sqlite3.Error as exc:
        log.error("Failed to fetch projects: %s", exc)
        return []


def get_project(project_id: int) -> sqlite3.Row | None:
    """Return a single project by ID, or None if not found."""
    try:
        with get_conn() as conn:
            return conn.execute(
                "SELECT * FROM projects WHERE id=?", (project_id,)
            ).fetchone()
    except sqlite3.Error as exc:
        log.error("Failed to fetch project %s: %s", project_id, exc)
        return None


def create_project(
    name: str,
    ticket_num: str = "",
    type_of_work: str = "",
    status: str = "active",
    scheduled_date: str = "",
) -> int | None:
    """Create a new project and return its ID."""
    try:
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO projects (name, ticket_num, type_of_work, status, scheduled_date) VALUES (?,?,?,?,?)",
                (name, ticket_num, type_of_work, status, scheduled_date),
            )
            return cur.lastrowid
    except sqlite3.Error as exc:
        log.error("Failed to create project '%s': %s", name, exc)
        return None


def update_project(project_id: int, **kwargs: str) -> None:
    """Update project fields. Only whitelisted column names are accepted."""
    invalid = set(kwargs) - _PROJECT_FIELDS
    if invalid:
        raise ValueError(f"Invalid project fields: {invalid}")
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [project_id]
    try:
        with get_conn() as conn:
            conn.execute(f"UPDATE projects SET {fields} WHERE id=?", values)
    except sqlite3.Error as exc:
        log.error("Failed to update project %s: %s", project_id, exc)


def delete_project(project_id: int) -> None:
    """Delete a project and all associated data (cascading)."""
    try:
        with get_conn() as conn:
            conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
    except sqlite3.Error as exc:
        log.error("Failed to delete project %s: %s", project_id, exc)


# ── Device helpers ───────────────────────────────────────────────────────────


def get_devices(project_id: int) -> list[sqlite3.Row]:
    """Return all devices for a project, ordered by hostname."""
    try:
        with get_conn() as conn:
            return conn.execute(
                "SELECT * FROM devices WHERE project_id=? ORDER BY hostname",
                (project_id,),
            ).fetchall()
    except sqlite3.Error as exc:
        log.error("Failed to fetch devices for project %s: %s", project_id, exc)
        return []


def get_device(device_id: int) -> sqlite3.Row | None:
    """Return a single device by ID."""
    try:
        with get_conn() as conn:
            return conn.execute(
                "SELECT * FROM devices WHERE id=?", (device_id,)
            ).fetchone()
    except sqlite3.Error as exc:
        log.error("Failed to fetch device %s: %s", device_id, exc)
        return None


def create_device(
    project_id: int,
    hostname: str,
    vendor: str = "Cisco",
    model: str = "",
    mgmt_ip: str = "",
    site: str = "",
    notes: str = "",
) -> int | None:
    """Create a new device and return its ID."""
    try:
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO devices (project_id,hostname,vendor,model,mgmt_ip,site,notes) VALUES (?,?,?,?,?,?,?)",
                (project_id, hostname, vendor, model, mgmt_ip, site, notes),
            )
            return cur.lastrowid
    except sqlite3.Error as exc:
        log.error("Failed to create device '%s': %s", hostname, exc)
        return None


def update_device(device_id: int, **kwargs: str) -> None:
    """Update device fields. Only whitelisted column names are accepted."""
    invalid = set(kwargs) - _DEVICE_FIELDS
    if invalid:
        raise ValueError(f"Invalid device fields: {invalid}")
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [device_id]
    try:
        with get_conn() as conn:
            conn.execute(f"UPDATE devices SET {fields} WHERE id=?", values)
    except sqlite3.Error as exc:
        log.error("Failed to update device %s: %s", device_id, exc)


def delete_device(device_id: int) -> None:
    """Delete a device and its interfaces/snippets (cascading)."""
    try:
        with get_conn() as conn:
            conn.execute("DELETE FROM devices WHERE id=?", (device_id,))
    except sqlite3.Error as exc:
        log.error("Failed to delete device %s: %s", device_id, exc)


# ── Interface helpers ────────────────────────────────────────────────────────


def get_interfaces(device_id: int) -> list[sqlite3.Row]:
    """Return all interfaces for a device."""
    try:
        with get_conn() as conn:
            return conn.execute(
                "SELECT * FROM interfaces WHERE device_id=?", (device_id,)
            ).fetchall()
    except sqlite3.Error as exc:
        log.error("Failed to fetch interfaces for device %s: %s", device_id, exc)
        return []


def create_interface(
    device_id: int,
    name: str,
    ip_address: str = "",
    description: str = "",
    role: str = "",
    circuit_id: int | None = None,
) -> int | None:
    """Create a new interface and return its ID."""
    try:
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO interfaces (device_id,name,ip_address,description,role,circuit_id) VALUES (?,?,?,?,?,?)",
                (device_id, name, ip_address, description, role, circuit_id),
            )
            return cur.lastrowid
    except sqlite3.Error as exc:
        log.error("Failed to create interface '%s': %s", name, exc)
        return None


def delete_interface(interface_id: int) -> None:
    """Delete an interface."""
    try:
        with get_conn() as conn:
            conn.execute("DELETE FROM interfaces WHERE id=?", (interface_id,))
    except sqlite3.Error as exc:
        log.error("Failed to delete interface %s: %s", interface_id, exc)


# ── Circuit helpers ──────────────────────────────────────────────────────────


def get_circuits(project_id: int) -> list[sqlite3.Row]:
    """Return all circuits for a project, ordered by CID."""
    try:
        with get_conn() as conn:
            return conn.execute(
                "SELECT * FROM circuits WHERE project_id=? ORDER BY cid", (project_id,)
            ).fetchall()
    except sqlite3.Error as exc:
        log.error("Failed to fetch circuits for project %s: %s", project_id, exc)
        return []


def create_circuit(
    project_id: int,
    cid: str,
    carrier: str = "",
    circuit_type: str = "",
    bandwidth: str = "",
    status: str = "active",
    notes: str = "",
) -> int | None:
    """Create a new circuit and return its ID."""
    try:
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO circuits (project_id,cid,carrier,circuit_type,bandwidth,status,notes) VALUES (?,?,?,?,?,?,?)",
                (project_id, cid, carrier, circuit_type, bandwidth, status, notes),
            )
            return cur.lastrowid
    except sqlite3.Error as exc:
        log.error("Failed to create circuit '%s': %s", cid, exc)
        return None


def update_circuit(circuit_id: int, **kwargs: str) -> None:
    """Update circuit fields. Only whitelisted column names are accepted."""
    invalid = set(kwargs) - _CIRCUIT_FIELDS
    if invalid:
        raise ValueError(f"Invalid circuit fields: {invalid}")
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [circuit_id]
    try:
        with get_conn() as conn:
            conn.execute(f"UPDATE circuits SET {fields} WHERE id=?", values)
    except sqlite3.Error as exc:
        log.error("Failed to update circuit %s: %s", circuit_id, exc)


def delete_circuit(circuit_id: int) -> None:
    """Delete a circuit."""
    try:
        with get_conn() as conn:
            conn.execute("DELETE FROM circuits WHERE id=?", (circuit_id,))
    except sqlite3.Error as exc:
        log.error("Failed to delete circuit %s: %s", circuit_id, exc)


# ── IP Plan helpers ──────────────────────────────────────────────────────────


def get_ip_plan(project_id: int) -> list[sqlite3.Row]:
    """Return all IP plan entries for a project."""
    try:
        with get_conn() as conn:
            return conn.execute(
                "SELECT * FROM ip_plan WHERE project_id=?", (project_id,)
            ).fetchall()
    except sqlite3.Error as exc:
        log.error("Failed to fetch IP plan for project %s: %s", project_id, exc)
        return []


def create_ip_entry(
    project_id: int,
    subnet: str,
    purpose: str = "",
    assigned_to: str = "",
    vlan_id: str = "",
    notes: str = "",
) -> int | None:
    """Create a new IP plan entry and return its ID."""
    try:
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO ip_plan (project_id,subnet,purpose,assigned_to,vlan_id,notes) VALUES (?,?,?,?,?,?)",
                (project_id, subnet, purpose, assigned_to, vlan_id, notes),
            )
            return cur.lastrowid
    except sqlite3.Error as exc:
        log.error("Failed to create IP entry '%s': %s", subnet, exc)
        return None


def delete_ip_entry(entry_id: int) -> None:
    """Delete an IP plan entry."""
    try:
        with get_conn() as conn:
            conn.execute("DELETE FROM ip_plan WHERE id=?", (entry_id,))
    except sqlite3.Error as exc:
        log.error("Failed to delete IP entry %s: %s", entry_id, exc)


# ── Path helpers ─────────────────────────────────────────────────────────────


def get_paths(project_id: int) -> list[sqlite3.Row]:
    """Return all paths for a project."""
    try:
        with get_conn() as conn:
            return conn.execute(
                "SELECT * FROM paths WHERE project_id=?", (project_id,)
            ).fetchall()
    except sqlite3.Error as exc:
        log.error("Failed to fetch paths for project %s: %s", project_id, exc)
        return []


def get_path(path_id: int) -> sqlite3.Row | None:
    """Return a single path by ID."""
    try:
        with get_conn() as conn:
            return conn.execute("SELECT * FROM paths WHERE id=?", (path_id,)).fetchone()
    except sqlite3.Error as exc:
        log.error("Failed to fetch path %s: %s", path_id, exc)
        return None


def create_path(
    project_id: int,
    name: str,
    customer: str = "",
    a_side: str = "",
    z_side: str = "",
    status: str = "active",
    notes: str = "",
) -> int | None:
    """Create a new path and return its ID."""
    try:
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO paths (project_id,name,customer,a_side,z_side,status,notes) VALUES (?,?,?,?,?,?,?)",
                (project_id, name, customer, a_side, z_side, status, notes),
            )
            return cur.lastrowid
    except sqlite3.Error as exc:
        log.error("Failed to create path '%s': %s", name, exc)
        return None


def delete_path(path_id: int) -> None:
    """Delete a path and its hops (cascading)."""
    try:
        with get_conn() as conn:
            conn.execute("DELETE FROM paths WHERE id=?", (path_id,))
    except sqlite3.Error as exc:
        log.error("Failed to delete path %s: %s", path_id, exc)


def get_path_hops(path_id: int) -> list[sqlite3.Row]:
    """Return all hops for a path with joined device/circuit info."""
    try:
        with get_conn() as conn:
            return conn.execute(
                """SELECT ph.*, d.hostname, d.vendor, c.cid
                   FROM path_hops ph
                   LEFT JOIN devices d ON ph.device_id = d.id
                   LEFT JOIN circuits c ON ph.circuit_id = c.id
                   WHERE ph.path_id=? ORDER BY ph.hop_order""",
                (path_id,),
            ).fetchall()
    except sqlite3.Error as exc:
        log.error("Failed to fetch hops for path %s: %s", path_id, exc)
        return []


def add_path_hop(
    path_id: int,
    hop_order: int,
    hop_type: str,
    device_id: int | None = None,
    ingress_iface: str = "",
    egress_iface: str = "",
    carrier_label: str = "",
    circuit_id: int | None = None,
    notes: str = "",
) -> int | None:
    """Add a hop to a path and return its ID."""
    try:
        with get_conn() as conn:
            cur = conn.execute(
                """INSERT INTO path_hops
                   (path_id,hop_order,hop_type,device_id,ingress_iface,egress_iface,carrier_label,circuit_id,notes)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    path_id,
                    hop_order,
                    hop_type,
                    device_id,
                    ingress_iface,
                    egress_iface,
                    carrier_label,
                    circuit_id,
                    notes,
                ),
            )
            return cur.lastrowid
    except sqlite3.Error as exc:
        log.error("Failed to add hop to path %s: %s", path_id, exc)
        return None


def delete_path_hop(hop_id: int) -> None:
    """Delete a path hop."""
    try:
        with get_conn() as conn:
            conn.execute("DELETE FROM path_hops WHERE id=?", (hop_id,))
    except sqlite3.Error as exc:
        log.error("Failed to delete hop %s: %s", hop_id, exc)


# ── Config snippet helpers ───────────────────────────────────────────────────


def get_snippets(device_id: int) -> list[sqlite3.Row]:
    """Return all config snippets for a device."""
    try:
        with get_conn() as conn:
            return conn.execute(
                "SELECT * FROM config_snippets WHERE device_id=? ORDER BY created_at DESC",
                (device_id,),
            ).fetchall()
    except sqlite3.Error as exc:
        log.error("Failed to fetch snippets for device %s: %s", device_id, exc)
        return []


def create_snippet(
    device_id: int,
    label: str,
    vendor: str = "",
    version: str = "v1",
    content: str = "",
) -> int | None:
    """Create a config snippet and return its ID."""
    try:
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO config_snippets (device_id,label,vendor,version,content) VALUES (?,?,?,?,?)",
                (device_id, label, vendor, version, content),
            )
            return cur.lastrowid
    except sqlite3.Error as exc:
        log.error("Failed to create snippet '%s': %s", label, exc)
        return None


def delete_snippet(snippet_id: int) -> None:
    """Delete a config snippet."""
    try:
        with get_conn() as conn:
            conn.execute("DELETE FROM config_snippets WHERE id=?", (snippet_id,))
    except sqlite3.Error as exc:
        log.error("Failed to delete snippet %s: %s", snippet_id, exc)


# ── Journal helpers ──────────────────────────────────────────────────────────


def get_journal(project_id: int) -> list[sqlite3.Row]:
    """Return all journal entries for a project (newest first)."""
    try:
        with get_conn() as conn:
            return conn.execute(
                "SELECT * FROM journal_entries WHERE project_id=? ORDER BY created_at DESC",
                (project_id,),
            ).fetchall()
    except sqlite3.Error as exc:
        log.error("Failed to fetch journal for project %s: %s", project_id, exc)
        return []


def add_journal_entry(project_id: int, entry: str, tag: str = "info") -> int | None:
    """Add a journal entry and return its ID."""
    try:
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO journal_entries (project_id, entry, tag) VALUES (?,?,?)",
                (project_id, entry, tag),
            )
            return cur.lastrowid
    except sqlite3.Error as exc:
        log.error("Failed to add journal entry for project %s: %s", project_id, exc)
        return None


def delete_journal_entry(entry_id: int) -> None:
    """Delete a journal entry."""
    try:
        with get_conn() as conn:
            conn.execute("DELETE FROM journal_entries WHERE id=?", (entry_id,))
    except sqlite3.Error as exc:
        log.error("Failed to delete journal entry %s: %s", entry_id, exc)
