
# Digital Network Engineer Notebook — Feature Specification

A local desktop application for solo network engineers to document and manage projects involving Juniper and Cisco equipment, circuits, IP plans, and end-to-end customer paths.

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

## Platform

- Local desktop application (PC)
- Offline-first — no internet connection required
- Data stored locally on disk

---

## Out of Scope (for now)

- Real-time collaboration / multi-user
- SNMP / API auto-discovery
- Full topology diagramming
- Monitoring / alerting integration
