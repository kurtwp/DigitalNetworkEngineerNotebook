# Network Engineer Notebook — Feature Specification

A local desktop application for solo network engineers to document and manage projects involving Juniper and Cisco equipment, circuits, IP plans, and end-to-end customer paths.

The notebook operates independently but integrates with an existing Python/NiceGUI/SQLite3 ticket management application. It is accessed via a dedicated **Work Notes** tab that opens in a new browser tab from a ticket record.

---

## Core Concept

Everything is organized around **Projects**. A project represents a discrete body of work — a branch refresh, a new customer circuit, a lab build, a migration. All devices, circuits, IPs, and paths belong to a project.

---

## Projects

Each project contains:

- Project name and description
- Status (active, on-hold, complete)
- Start date / target completion date
- Free-form notes / journal area
- Links to: Devices, Circuits, IP Plan, Customer Paths

---

## Devices

Each device is a structured record within a project.

**Fields:**
- Hostname
- Vendor (Juniper / Cisco)
- Model
- Role (core, edge, PE, CPE, firewall, access, etc.)
- Management IP
- Site / location label

**Interfaces** are tracked per device:
- Interface name (e.g. `ge-0/0/1`, `GigabitEthernet0/0`)
- IP address assigned
- Description (free text — typically includes CID for carrier-facing interfaces)
- Linked Circuit ID (if applicable)
- Role (uplink, customer-facing, management, interconnect)

**Config Snippets** are attached per device:
- Label describing what the snippet does (e.g. "BGP neighbor to ISP", "OSPF area 0", "Interface uplink config")
- Vendor-appropriate syntax highlighting (IOS vs JunOS)
- Version label (e.g. v1, v2, post-change)
- One-click copy to clipboard

---

## Circuits (CIDs)

Circuit IDs are first-class objects, not just text fields.

**Fields:**
- Circuit ID (e.g. `ATT-MPLS-123456`, `TATA-DIA-789`)
- Carrier / provider name
- Circuit type (MPLS, DIA, P2P Ethernet, Broadband, etc.)
- Bandwidth
- Status (active, pending, in-maintenance, decom)
- Linked interface (device + interface name where it terminates)
- Notes

The CID is surfaced in the interface description of the device it terminates on, keeping config and circuit records in sync.

---

## IP Plan

Per-project IP address tracking.

**Fields per entry:**
- Subnet / CIDR
- Purpose / description
- Assigned device(s)
- VLAN ID (if applicable)
- Notes

Provides a quick at-a-glance view of what is allocated within a project.

---

## Customer Paths (A-to-Z)

A Customer Path represents the end-to-end route traffic takes from a customer A-side to a Z-side destination. Paths are built as an ordered chain of hops.

**Path record:**
- Path name (e.g. "Customer X — Site A to Data Center")
- Customer / service name
- A-side label (customer site, building, etc.)
- Z-side label (data center, hub, internet handoff, etc.)
- Status (active, in-build, decom)
- Notes

**Each hop in the chain is one of two types:**

**1. Managed Equipment Hop** (your gear)
- Device — selected from project device inventory
- Ingress interface
- Egress interface
- Notes for that hop

**2. Carrier Segment Hop** (provider cloud / black box)
- Label (e.g. "ATT MPLS Cloud")
- Linked Circuit ID
- Notes

**Example path chain:**

```
[A-side] Customer CPE (Cisco ISR)
  Interface: GigabitEthernet0/1  →  CID: ATT-12345
    ↓
[Carrier] ATT MPLS  (CID: ATT-12345)
    ↓
[Hop] PE Router (Juniper MX480)
  Ingress: et-0/0/2  |  Egress: et-0/0/5
    ↓
[Hop] Core Router (Cisco ASR)
  Ingress: Gi0/0  |  Egress: Gi0/1
    ↓
[Z-side] Data Center Firewall (Juniper SRX)
  Interface: xe-0/0/0
```

The path view is the primary troubleshooting and documentation reference — it answers "what does this customer's traffic touch, end to end?"

---

## Summary of Data Model

```
Project
├── Devices
│   ├── Device record (hostname, vendor, model, role, mgmt IP)
│   │   ├── Interfaces (name, IP, description, linked CID)
│   │   └── Config Snippets (label, vendor syntax, version)
├── Circuits (CIDs)
│   └── CID record (carrier, type, bandwidth, linked interface)
├── IP Plan
│   └── Subnet entries (CIDR, purpose, assigned devices)
└── Customer Paths
    └── Path record (A-to-Z chain of managed hops + carrier segments)
```

---

## Integration with Ticket Application

The notebook is **independent** of the ticket system but is launched from it. The ticket application (Python / NiceGUI / SQLite3) already supports linking a local filesystem directory to each ticket. The Work Notes notebook uses this linked directory as its data home.

### Work Notes Button

The existing Notes markdown textarea is **removed** from the ticket form. In its place, a **WORK NOTES** button is added to the ticket form toolbar.

```python
ui.button('Work Notes', on_click=lambda: 
    ui.navigate.to(f'/worknotes/{ticket_number}', new_tab=True))
```

Clicking the button opens the notebook in a **new browser tab**, keeping the ticket form fully accessible for reference.

### Launch Logic

```
User clicks WORK NOTES
  ├── Linked directory exists?
  │     YES → open /worknotes/{ticket_number} in new tab
  │     NO  → prompt: "Set a ticket directory first"
  │             └── after directory set → open notebook
  └── Notebook data stored as worknotes.db 
```
```

The `worknotes.db` file is fully self-contained. It can exist with or without a Jira ticket — the notebook can also be used for standalone projects that have no associated ticket.

---

## Work Notes Page — Layout

The Work Notes page opens as a full NiceGUI page at the route `/worknotes/{ticket_number}`.

```
┌─────────────────────┬────────────────────────────────────┐
│  Ticket Context     │                                    │
│  ─────────────────  │   Main Content Area                │
│  SEEIMP-110171      │                                    │
│  Decommission       │   (changes based on selected       │
│  05/02/2026         │    section in sidebar)             │
│  Scheduled          │                                    │
│  ─────────────────  │                                    │
│  📋 Overview        │                                    │
│  🖥  Devices        │                                    │
│  🔌 Circuits        │                                    │
│  🌐 IP Plan         │                                    │
│  🛤  A-Z Path       │                                    │
│  📓 Journal         │                                    │
└─────────────────────┴────────────────────────────────────┘
```

**Sidebar** — always visible, shows ticket metadata pulled from the existing SQLite ticket record (read-only), plus navigation to each notebook section.

**Main content area** — renders the selected section.

---

## Journal (Notes & Commands)

The Journal is a fast, frictionless scratchpad for capturing notes, one-off commands, and observations during a project. It replaces the old tagged change-log approach with a simpler model optimized for real-time use during change windows, troubleshooting, and documentation.

### Core Concept

- Simple timestamped text entries — no tags, no categories.
- Think of it as a notepad you scribble on during a call or change window.
- Entries can be short (a one-liner) or multi-line (pasted CLI output, config snippets).
- Optional linking to a specific device or circuit in the project.

### Entry Fields

Each journal entry contains:
- **Timestamp** — auto-stamped on creation
- **Entry text** — free-form text, supports multi-line content
- **Linked context** (optional) — associate the note with a device hostname or circuit ID from the project

### Input

- Always-visible text input at the top of the journal section. Type, click Add (or press Enter), done.
- Multi-line support for pasting commands or output.
- Optional device/circuit selector with autocomplete from the project's existing inventory.
- When a note is linked to a device or circuit, it appears both in the journal timeline AND on that device/circuit's detail view.

### Display

- Chronological list (newest first).
- Each entry shows: timestamp, text content, and linked device/circuit (if any).
- Long entries (pasted output) auto-collapse with a "show more" toggle.
- Monospace rendering for entries that look like commands or config.
- Copy button on each entry for quick paste into a terminal.

### Features

- Search/filter by keyword across all entries.
- Export all notes as plain text or markdown (for post-change reports or handoff).
- Delete individual entries.
- Entries linked to a device/circuit surface on that item's detail view.

### Example

```
┌─────────────────────────────────────────────────────┐
│  [text input ........................] [+ Add]      │
│  [optional: link to device/circuit ▼]               │
├─────────────────────────────────────────────────────┤
│  2026-05-31 14:22                                   │
│  show bgp summary | match 10.0.0.1                  │
│  ↳ linked to: PE1-CHI                          [⋮]  │
│─────────────────────────────────────────────────────│
│  2026-05-31 14:18                                   │
│  Customer confirmed cutover window 02:00-04:00 UTC  │
│                                                [⋮]  │
│─────────────────────────────────────────────────────│
│  2026-05-31 13:55                                   │
│  set interfaces xe-0/0/2 disable                    │
│  ↳ linked to: PE2-DAL                          [⋮]  │
└─────────────────────────────────────────────────────┘
```

### Data Model Change

```sql
journal_entries (
    id          INTEGER PRIMARY KEY,
    project_id  INTEGER NOT NULL REFERENCES projects(id),
    entry       TEXT NOT NULL,
    device_id   INTEGER REFERENCES devices(id) ON DELETE SET NULL,
    circuit_id  INTEGER REFERENCES circuits(id) ON DELETE SET NULL,
    created_at  TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
)
```

The `tag` column is removed. `device_id` and `circuit_id` are added for optional linking.

---

## Platform

- Local desktop application (PC)
- Built with Python / NiceGUI / SQLite3 (consistent with existing ticket app)
- Offline-first — no internet connection required
- Notebook data stored in linked ticket directory as `worknotes.db`
- Independent of Jira — can be used for projects without a ticket

---

## Out of Scope (for now)

- Real-time collaboration / multi-user
- SNMP / API auto-discovery
- Full topology diagramming
- Monitoring / alerting integration
- Export to PDF or Word
