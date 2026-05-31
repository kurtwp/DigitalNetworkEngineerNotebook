import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "worknotes.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS projects (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_num  TEXT,
                name        TEXT NOT NULL,
                type_of_work TEXT,
                status      TEXT DEFAULT 'active',
                scheduled_date TEXT,
                notes       TEXT,
                created_at  TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS devices (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                hostname    TEXT NOT NULL,
                vendor      TEXT CHECK(vendor IN ('Juniper','Cisco','Other')),
                model       TEXT,
                role        TEXT,
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
                created_at  TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS journal_entries (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                tag         TEXT DEFAULT 'info',
                entry       TEXT NOT NULL,
                created_at  TEXT DEFAULT (datetime('now'))
            );
        """)


# ── Project helpers ──────────────────────────────────────────────────────────

def get_all_projects():
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM projects ORDER BY created_at DESC"
        ).fetchall()


def get_project(project_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM projects WHERE id=?", (project_id,)
        ).fetchone()


def create_project(name, ticket_num="", type_of_work="", status="active", scheduled_date=""):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO projects (name, ticket_num, type_of_work, status, scheduled_date) VALUES (?,?,?,?,?)",
            (name, ticket_num, type_of_work, status, scheduled_date)
        )
        return cur.lastrowid


def update_project(project_id, **kwargs):
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [project_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE projects SET {fields} WHERE id=?", values)


def delete_project(project_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM projects WHERE id=?", (project_id,))


# ── Device helpers ───────────────────────────────────────────────────────────

def get_devices(project_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM devices WHERE project_id=? ORDER BY hostname", (project_id,)
        ).fetchall()


def get_device(device_id):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM devices WHERE id=?", (device_id,)).fetchone()


def create_device(project_id, hostname, vendor="Cisco", model="", role="", mgmt_ip="", site="", notes=""):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO devices (project_id,hostname,vendor,model,role,mgmt_ip,site,notes) VALUES (?,?,?,?,?,?,?,?)",
            (project_id, hostname, vendor, model, role, mgmt_ip, site, notes)
        )
        return cur.lastrowid


def update_device(device_id, **kwargs):
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [device_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE devices SET {fields} WHERE id=?", values)


def delete_device(device_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM devices WHERE id=?", (device_id,))


# ── Interface helpers ────────────────────────────────────────────────────────

def get_interfaces(device_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM interfaces WHERE device_id=?", (device_id,)
        ).fetchall()


def create_interface(device_id, name, ip_address="", description="", role="", circuit_id=None):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO interfaces (device_id,name,ip_address,description,role,circuit_id) VALUES (?,?,?,?,?,?)",
            (device_id, name, ip_address, description, role, circuit_id)
        )
        return cur.lastrowid


def delete_interface(interface_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM interfaces WHERE id=?", (interface_id,))


# ── Circuit helpers ──────────────────────────────────────────────────────────

def get_circuits(project_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM circuits WHERE project_id=? ORDER BY cid", (project_id,)
        ).fetchall()


def create_circuit(project_id, cid, carrier="", circuit_type="", bandwidth="", status="active", notes=""):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO circuits (project_id,cid,carrier,circuit_type,bandwidth,status,notes) VALUES (?,?,?,?,?,?,?)",
            (project_id, cid, carrier, circuit_type, bandwidth, status, notes)
        )
        return cur.lastrowid


def update_circuit(circuit_id, **kwargs):
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [circuit_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE circuits SET {fields} WHERE id=?", values)


def delete_circuit(circuit_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM circuits WHERE id=?", (circuit_id,))


# ── IP Plan helpers ──────────────────────────────────────────────────────────

def get_ip_plan(project_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM ip_plan WHERE project_id=?", (project_id,)
        ).fetchall()


def create_ip_entry(project_id, subnet, purpose="", assigned_to="", vlan_id="", notes=""):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO ip_plan (project_id,subnet,purpose,assigned_to,vlan_id,notes) VALUES (?,?,?,?,?,?)",
            (project_id, subnet, purpose, assigned_to, vlan_id, notes)
        )
        return cur.lastrowid


def delete_ip_entry(entry_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM ip_plan WHERE id=?", (entry_id,))


# ── Path helpers ─────────────────────────────────────────────────────────────

def get_paths(project_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM paths WHERE project_id=?", (project_id,)
        ).fetchall()


def get_path(path_id):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM paths WHERE id=?", (path_id,)).fetchone()


def create_path(project_id, name, customer="", a_side="", z_side="", status="active", notes=""):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO paths (project_id,name,customer,a_side,z_side,status,notes) VALUES (?,?,?,?,?,?,?)",
            (project_id, name, customer, a_side, z_side, status, notes)
        )
        return cur.lastrowid


def delete_path(path_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM paths WHERE id=?", (path_id,))


def get_path_hops(path_id):
    with get_conn() as conn:
        return conn.execute(
            """SELECT ph.*, d.hostname, d.vendor, c.cid
               FROM path_hops ph
               LEFT JOIN devices d ON ph.device_id = d.id
               LEFT JOIN circuits c ON ph.circuit_id = c.id
               WHERE ph.path_id=? ORDER BY ph.hop_order""",
            (path_id,)
        ).fetchall()


def add_path_hop(path_id, hop_order, hop_type, device_id=None,
                 ingress_iface="", egress_iface="", carrier_label="", circuit_id=None, notes=""):
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO path_hops
               (path_id,hop_order,hop_type,device_id,ingress_iface,egress_iface,carrier_label,circuit_id,notes)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (path_id, hop_order, hop_type, device_id,
             ingress_iface, egress_iface, carrier_label, circuit_id, notes)
        )
        return cur.lastrowid


def delete_path_hop(hop_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM path_hops WHERE id=?", (hop_id,))


# ── Config snippet helpers ───────────────────────────────────────────────────

def get_snippets(device_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM config_snippets WHERE device_id=? ORDER BY created_at DESC", (device_id,)
        ).fetchall()


def create_snippet(device_id, label, vendor="", version="v1", content=""):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO config_snippets (device_id,label,vendor,version,content) VALUES (?,?,?,?,?)",
            (device_id, label, vendor, version, content)
        )
        return cur.lastrowid


def delete_snippet(snippet_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM config_snippets WHERE id=?", (snippet_id,))


# ── Journal helpers ──────────────────────────────────────────────────────────

def get_journal(project_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM journal_entries WHERE project_id=? ORDER BY created_at DESC",
            (project_id,)
        ).fetchall()


def add_journal_entry(project_id, entry, tag="info"):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO journal_entries (project_id, entry, tag) VALUES (?,?,?)",
            (project_id, entry, tag)
        )
        return cur.lastrowid


def delete_journal_entry(entry_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM journal_entries WHERE id=?", (entry_id,))
