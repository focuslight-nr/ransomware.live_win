#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ransomware.live GUI Manager
Cross-platform management UI for ransomware group/victim data.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import json
import os
import sys
import subprocess
import threading
from pathlib import Path
from datetime import datetime
from collections import Counter

# Setup paths
script_dir = Path(__file__).resolve().parent
home = script_dir.parent

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=home / ".env")
except ImportError:
    pass

db_dir = home / os.getenv("DB_DIR", "db").strip("/")
GROUPS_FILE = db_dir / "groups.json"
VICTIMS_FILE = db_dir / "victims.json"
BIN_DIR = home / "bin"

# Platform font
if sys.platform == "win32":
    FONT = "Segoe UI"
    MONO = "Courier New"
else:
    FONT = "SF Pro Display"
    MONO = "Monaco"


# ── Colors (Catppuccin Mocha) ──────────────────────────────────────────────
BG      = "#1e1e2e"
SURFACE = "#181825"
OVERLAY = "#313244"
BTN_BG  = "#45475a"
BTN_HOV = "#585b70"
FG      = "#cdd6f4"
SUB_FG  = "#a6adc8"
ACCENT  = "#89b4fa"  # blue
GREEN   = "#a6e3a1"
RED     = "#f38ba8"
YELLOW  = "#f9e2af"
ORANGE  = "#fab387"


# ── Data helpers ───────────────────────────────────────────────────────────

def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def make_location_schema(url: str) -> dict:
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "http://" + url
    try:
        import tldextract
        p = tldextract.extract(url)
        fqdn = f"{p.subdomain}.{p.domain}.{p.suffix}" if p.subdomain else f"{p.domain}.{p.suffix}"
    except Exception:
        fqdn = url
    return {
        "fqdn": fqdn,
        "title": None,
        "slug": url,
        "available": False,
        "updated": None,
        "lastscrape": "2021-01-01 00:00:00.000000",
        "enabled": True,
        "type": "DLS",
    }


# ── Main Application ───────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ransomware.live Manager")
        self.geometry("1280x820")
        self.minsize(960, 640)
        self.configure(bg=BG)

        self._apply_theme()
        self._setup_tag_colors()

        self.groups: list = []
        self.victims: list = []
        self._reload_data()

        self._victim_sort_col = "discovered"
        self._victim_sort_rev = True
        self.current_group_idx = None
        self.filtered_groups: list = []

        self._build_ui()
        self._update_statusbar()

        # Keyboard shortcuts
        self.bind("<F5>", lambda _: self._refresh_all())
        self.bind("<Control-r>", lambda _: self._refresh_all())

    # ── Theme ──────────────────────────────────────────────────────────────

    def _apply_theme(self):
        s = ttk.Style(self)
        s.theme_use("clam")

        base = dict(background=BG, foreground=FG, fieldbackground=OVERLAY,
                    troughcolor=OVERLAY, bordercolor=OVERLAY,
                    darkcolor=BG, lightcolor=OVERLAY, relief="flat",
                    font=(FONT, 10))
        s.configure(".", **base)

        s.configure("TNotebook", background=BG, borderwidth=0, tabmargins=[0, 0, 0, 0])
        s.configure("TNotebook.Tab", background=BTN_BG, foreground=FG,
                    padding=[14, 6], borderwidth=0, font=(FONT, 10))
        s.map("TNotebook.Tab",
              background=[("selected", ACCENT)],
              foreground=[("selected", BG)])

        s.configure("Treeview", background=OVERLAY, foreground=FG,
                    fieldbackground=OVERLAY, borderwidth=0, rowheight=26,
                    font=(FONT, 10))
        s.configure("Treeview.Heading", background=BTN_BG, foreground=FG,
                    relief="flat", borderwidth=0, font=(FONT, 10, "bold"))
        s.map("Treeview",
              background=[("selected", ACCENT)],
              foreground=[("selected", BG)])

        s.configure("TButton", background=BTN_BG, foreground=FG,
                    borderwidth=0, padding=[10, 5], relief="flat", font=(FONT, 10))
        s.map("TButton",
              background=[("active", BTN_HOV), ("pressed", ACCENT)])

        s.configure("Accent.TButton", background=ACCENT, foreground=BG,
                    borderwidth=0, padding=[10, 5], font=(FONT, 10, "bold"))
        s.map("Accent.TButton", background=[("active", "#b4d0fb")])

        s.configure("Danger.TButton", background=RED, foreground=BG,
                    borderwidth=0, padding=[10, 5], font=(FONT, 10))
        s.map("Danger.TButton", background=[("active", "#f5a0b5")])

        s.configure("TEntry", fieldbackground=OVERLAY, foreground=FG,
                    insertcolor=FG, borderwidth=0, font=(FONT, 10))
        s.configure("TCombobox", fieldbackground=OVERLAY, background=BTN_BG,
                    foreground=FG, arrowcolor=FG, borderwidth=0, font=(FONT, 10))
        s.map("TCombobox", fieldbackground=[("readonly", OVERLAY)])

        s.configure("TLabel", background=BG, foreground=FG, font=(FONT, 10))
        s.configure("TFrame", background=BG)
        s.configure("TScrollbar", background=BTN_BG, troughcolor=OVERLAY,
                    borderwidth=0, arrowcolor=FG, arrowsize=12)
        s.configure("TCheckbutton", background=BG, foreground=FG, font=(FONT, 10))
        s.map("TCheckbutton", background=[("active", BG)])
        s.configure("TSeparator", background=OVERLAY)

        s.configure("Header.TLabel", background=BG, foreground=ACCENT,
                    font=(FONT, 13, "bold"))
        s.configure("Sub.TLabel", background=BG, foreground=SUB_FG,
                    font=(FONT, 9))
        s.configure("Card.TFrame", background=OVERLAY, relief="flat")

    def _setup_tag_colors(self):
        pass  # Applied per-widget after creation

    # ── Data ──────────────────────────────────────────────────────────────

    def _reload_data(self):
        try:
            self.groups = load_json(GROUPS_FILE)
        except Exception as e:
            self.groups = []
            print(f"Error loading groups.json: {e}")
        try:
            self.victims = load_json(VICTIMS_FILE)
        except Exception as e:
            self.victims = []
            print(f"Error loading victims.json: {e}")

    def _refresh_all(self):
        self._reload_data()
        self._refresh_dashboard()
        self._refresh_groups_list()
        self._refresh_victims_table()
        self._update_statusbar()
        self._log("[INFO] Data reloaded.")

    # ── UI Layout ─────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header bar
        hdr = tk.Frame(self, bg=SURFACE, pady=10)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="  Ransomware.live Manager", bg=SURFACE, fg=ACCENT,
                 font=(FONT, 14, "bold")).pack(side=tk.LEFT)
        ttk.Button(hdr, text="⟳  Reload  (F5)", command=self._refresh_all,
                   style="TButton").pack(side=tk.RIGHT, padx=12)

        # Notebook
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self._build_dashboard_tab()
        self._build_groups_tab()
        self._build_victims_tab()
        self._build_console_tab()

        # Status bar
        self.status_var = tk.StringVar()
        tk.Label(self, textvariable=self.status_var,
                 bg=BTN_BG, fg=SUB_FG, anchor=tk.W,
                 padx=12, pady=3, font=(FONT, 9)).pack(fill=tk.X, side=tk.BOTTOM)

    def _update_statusbar(self):
        active = sum(
            1 for g in self.groups
            if any(l.get("available") and l.get("enabled") for l in g.get("locations", []))
        )
        self.status_var.set(
            f"  Groups: {len(self.groups)}   Active: {active}   "
            f"Victims: {len(self.victims)}   DB: {db_dir}"
        )

    # ── Dashboard Tab ─────────────────────────────────────────────────────

    def _build_dashboard_tab(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="  Dashboard  ")
        self._dash_frame = f
        self._refresh_dashboard()

    def _refresh_dashboard(self):
        for w in self._dash_frame.winfo_children():
            w.destroy()

        groups, victims = self.groups, self.victims
        active = sum(
            1 for g in groups
            if any(l.get("available") and l.get("enabled") for l in g.get("locations", []))
        )
        enabled_locs = sum(
            len([l for l in g.get("locations", []) if l.get("enabled")])
            for g in groups
        )

        # Stat cards
        cards_row = tk.Frame(self._dash_frame, bg=BG)
        cards_row.pack(fill=tk.X, padx=16, pady=(12, 8))

        for col, (num, lbl, color) in enumerate([
            (len(groups),   "Total Groups",      ACCENT),
            (active,        "Active Groups",      GREEN),
            (len(victims),  "Total Victims",      ORANGE),
            (enabled_locs,  "Enabled Locations",  YELLOW),
        ]):
            cards_row.columnconfigure(col, weight=1)
            card = tk.Frame(cards_row, bg=OVERLAY, padx=16, pady=12)
            card.grid(row=0, column=col, padx=6, sticky="ew")
            tk.Label(card, text=str(num), bg=OVERLAY, fg=color,
                     font=(FONT, 28, "bold")).pack()
            tk.Label(card, text=lbl, bg=OVERLAY, fg=SUB_FG,
                     font=(FONT, 10)).pack()

        # Two-column body
        body = tk.Frame(self._dash_frame, bg=BG)
        body.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # Recent victims
        lf = tk.Frame(body, bg=BG)
        lf.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        lf.rowconfigure(1, weight=1)
        lf.columnconfigure(0, weight=1)
        tk.Label(lf, text="Recent Victims", bg=BG, fg=ACCENT,
                 font=(FONT, 12, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 4))

        rv = ttk.Treeview(lf, columns=("group", "victim", "date"),
                          show="headings", selectmode="browse")
        rv.heading("group", text="Group")
        rv.heading("victim", text="Victim")
        rv.heading("date", text="Discovered")
        rv.column("group", width=110, minwidth=80)
        rv.column("victim", width=180, minwidth=120)
        rv.column("date", width=130, minwidth=100)
        vsb = ttk.Scrollbar(lf, orient=tk.VERTICAL, command=rv.yview)
        rv.configure(yscrollcommand=vsb.set)
        rv.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")

        recent = sorted(victims, key=lambda x: x.get("discovered", ""), reverse=True)[:20]
        for v in recent:
            rv.insert("", tk.END, values=(
                v.get("group_name", ""),
                v.get("post_title", "")[:45],
                v.get("discovered", "")[:16],
            ))

        # Top groups
        rf = tk.Frame(body, bg=BG)
        rf.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        rf.rowconfigure(1, weight=1)
        rf.columnconfigure(0, weight=1)
        tk.Label(rf, text="Top Groups by Victim Count", bg=BG, fg=ACCENT,
                 font=(FONT, 12, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 4))

        tg = ttk.Treeview(rf, columns=("group", "count", "status"),
                          show="headings", selectmode="browse")
        tg.heading("group", text="Group")
        tg.heading("count", text="Victims")
        tg.heading("status", text="Status")
        tg.column("group", width=160, minwidth=100)
        tg.column("count", width=70, anchor=tk.CENTER)
        tg.column("status", width=80, anchor=tk.CENTER)
        vsb2 = ttk.Scrollbar(rf, orient=tk.VERTICAL, command=tg.yview)
        tg.configure(yscrollcommand=vsb2.set)
        tg.grid(row=1, column=0, sticky="nsew")
        vsb2.grid(row=1, column=1, sticky="ns")

        counts = Counter(v.get("group_name", "") for v in victims)
        status_map = {
            g["name"]: "Active" if any(l.get("available") and l.get("enabled")
                                       for l in g.get("locations", [])) else "Down"
            for g in groups
        }
        for gname, cnt in counts.most_common(20):
            tg.insert("", tk.END, values=(gname, cnt, status_map.get(gname, "Unknown")))

        tg.tag_configure("active", foreground=GREEN)
        tg.tag_configure("down",   foreground=RED)
        for iid in tg.get_children():
            row_vals = tg.item(iid, "values")
            if row_vals[2] == "Active":
                tg.item(iid, tags=("active",))
            else:
                tg.item(iid, tags=("down",))

    # ── Groups Tab ────────────────────────────────────────────────────────

    def _build_groups_tab(self):
        outer = ttk.Frame(self.nb)
        self.nb.add(outer, text="  Groups  ")
        outer.columnconfigure(1, weight=1)
        outer.rowconfigure(0, weight=1)

        # Left panel: group list
        left = tk.Frame(outer, bg=SURFACE, width=230)
        left.grid(row=0, column=0, sticky="nsew", padx=(6, 0), pady=6)
        left.pack_propagate(False)
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        # Search
        sf = tk.Frame(left, bg=SURFACE)
        sf.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        tk.Label(sf, text="Search:", bg=SURFACE, fg=FG, font=(FONT, 10)).pack(side=tk.LEFT)
        self._grp_search = tk.StringVar()
        self._grp_search.trace_add("write", lambda *_: self._refresh_groups_list())
        se = ttk.Entry(sf, textvariable=self._grp_search)
        se.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))

        # List + scrollbar
        lf2 = tk.Frame(left, bg=SURFACE)
        lf2.grid(row=1, column=0, sticky="nsew", padx=8)
        lf2.rowconfigure(0, weight=1)
        lf2.columnconfigure(0, weight=1)

        vsb = tk.Scrollbar(lf2, bg=SURFACE, troughcolor=OVERLAY,
                           relief="flat", borderwidth=0)
        self._grp_lb = tk.Listbox(
            lf2, bg=OVERLAY, fg=FG, selectbackground=ACCENT,
            selectforeground=BG, borderwidth=0, highlightthickness=0,
            activestyle="none", font=(FONT, 10),
            yscrollcommand=vsb.set,
        )
        vsb.config(command=self._grp_lb.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        self._grp_lb.grid(row=0, column=0, sticky="nsew")
        self._grp_lb.bind("<<ListboxSelect>>", self._on_group_select)
        self._grp_lb.bind("<Double-Button-1>", self._on_group_select)

        # New group button
        ttk.Button(left, text="＋  New Group",
                   command=self._new_group, style="Accent.TButton").grid(
            row=2, column=0, sticky="ew", padx=8, pady=8)

        # Right panel: detail editor
        right = tk.Frame(outer, bg=BG)
        right.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)
        right.columnconfigure(1, weight=1)
        right.rowconfigure(7, weight=1)

        tk.Label(right, text="Group Details", bg=BG, fg=ACCENT,
                 font=(FONT, 13, "bold")).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(4, 10))

        # Editable fields
        self._grp_vars = {}
        field_defs = [
            ("Name",        "name"),
            ("Date",        "date"),
            ("Description", "description"),
            ("Contact",     "contact"),
            ("Meta",        "meta"),
        ]
        for row, (label, key) in enumerate(field_defs, start=1):
            tk.Label(right, text=f"{label}:", bg=BG, fg=FG,
                     font=(FONT, 10)).grid(row=row, column=0, sticky=tk.W,
                                           padx=(0, 10), pady=3)
            var = tk.StringVar()
            self._grp_vars[key] = var
            ttk.Entry(right, textvariable=var).grid(row=row, column=1,
                                                    sticky=tk.EW, pady=3)

        # Victim count badge
        self._grp_victim_var = tk.StringVar(value="")
        tk.Label(right, textvariable=self._grp_victim_var, bg=BG, fg=YELLOW,
                 font=(FONT, 10)).grid(row=1, column=1, sticky=tk.E)

        # Locations label + add button
        loc_hdr = tk.Frame(right, bg=BG)
        loc_hdr.grid(row=6, column=0, columnspan=2, sticky=tk.EW, pady=(10, 2))
        tk.Label(loc_hdr, text="Locations", bg=BG, fg=ACCENT,
                 font=(FONT, 12, "bold")).pack(side=tk.LEFT)
        ttk.Button(loc_hdr, text="＋ Add URL",
                   command=self._add_location, style="Accent.TButton").pack(side=tk.RIGHT)

        # Location treeview
        loc_frame = tk.Frame(right, bg=BG)
        loc_frame.grid(row=7, column=0, columnspan=2, sticky="nsew", pady=2)
        loc_frame.rowconfigure(0, weight=1)
        loc_frame.columnconfigure(0, weight=1)

        self._loc_tree = ttk.Treeview(
            loc_frame,
            columns=("url", "type", "available", "enabled", "lastscrape"),
            show="headings", selectmode="browse",
        )
        for col, (hdg, w, anchor) in [
            ("url",       ("URL",         320, tk.W)),
            ("type",      ("Type",         60, tk.CENTER)),
            ("available", ("Available",    75, tk.CENTER)),
            ("enabled",   ("Enabled",      65, tk.CENTER)),
            ("lastscrape",("Last Scrape", 150, tk.W)),
        ]:
            self._loc_tree.heading(col, text=hdg)
            self._loc_tree.column(col, width=w, anchor=anchor)

        lvsb = ttk.Scrollbar(loc_frame, orient=tk.VERTICAL,
                             command=self._loc_tree.yview)
        self._loc_tree.configure(yscrollcommand=lvsb.set)
        self._loc_tree.grid(row=0, column=0, sticky="nsew")
        lvsb.grid(row=0, column=1, sticky="ns")
        self._loc_tree.bind("<Double-Button-1>", self._edit_location_url)

        # Location row color tags
        self._loc_tree.tag_configure("enabled",  foreground=GREEN)
        self._loc_tree.tag_configure("disabled", foreground=RED)

        # Location action buttons
        loc_acts = tk.Frame(right, bg=BG)
        loc_acts.grid(row=8, column=0, columnspan=2, sticky=tk.EW, pady=4)
        ttk.Button(loc_acts, text="Toggle Enable/Disable",
                   command=self._toggle_location).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(loc_acts, text="Edit URL",
                   command=self._edit_location_url).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(loc_acts, text="Remove URL",
                   command=self._remove_location, style="Danger.TButton").pack(side=tk.LEFT)

        # Action bar
        act_bar = tk.Frame(right, bg=BG)
        act_bar.grid(row=9, column=0, columnspan=2, sticky=tk.EW, pady=(8, 4))
        ttk.Button(act_bar, text="💾  Save Changes",
                   command=self._save_group, style="Accent.TButton").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(act_bar, text="▶  Scrape",
                   command=self._run_scrape).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(act_bar, text="▶  Parse",
                   command=self._run_parse).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(act_bar, text="▶  Scrape + Parse",
                   command=self._run_scrape_parse).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(act_bar, text="🗑  Delete Group",
                   command=self._delete_group, style="Danger.TButton").pack(side=tk.RIGHT)

        self._refresh_groups_list()

    def _refresh_groups_list(self):
        q = getattr(self, "_grp_search", None)
        query = q.get().lower() if q else ""
        self.filtered_groups = [g for g in self.groups if query in g["name"].lower()]

        lb = self._grp_lb
        lb.delete(0, tk.END)
        vc = Counter(v.get("group_name", "") for v in self.victims)
        for g in self.filtered_groups:
            active = any(l.get("available") and l.get("enabled")
                         for l in g.get("locations", []))
            count = vc.get(g["name"], 0)
            label = f"{'●' if active else '○'} {g['name']}  ({count})"
            lb.insert(tk.END, label)
            lb.itemconfig(tk.END, fg=GREEN if active else FG)

    def _on_group_select(self, _event=None):
        sel = self._grp_lb.curselection()
        if not sel or sel[0] >= len(self.filtered_groups):
            return
        g = self.filtered_groups[sel[0]]
        self.current_group_idx = next(
            (i for i, x in enumerate(self.groups) if x["name"] == g["name"]), None
        )
        if self.current_group_idx is not None:
            self._populate_group_detail(g)

    def _populate_group_detail(self, g: dict):
        self._grp_vars["name"].set(g.get("name", ""))
        self._grp_vars["date"].set(g.get("date", ""))
        self._grp_vars["description"].set(g.get("description") or "")
        self._grp_vars["contact"].set(g.get("contact") or "")
        self._grp_vars["meta"].set(str(g.get("meta") or ""))

        vc = Counter(v.get("group_name", "") for v in self.victims)
        cnt = vc.get(g["name"], 0)
        self._grp_victim_var.set(f"Victims: {cnt}")

        self._loc_tree.delete(*self._loc_tree.get_children())
        for loc in g.get("locations", []):
            enabled = loc.get("enabled", True)
            tag = "enabled" if enabled else "disabled"
            self._loc_tree.insert("", tk.END, tags=(tag,), values=(
                loc.get("slug", ""),
                loc.get("type", "DLS"),
                "✓" if loc.get("available") else "✗",
                "ON" if enabled else "OFF",
                (loc.get("lastscrape") or "")[:16],
            ))

    def _save_group(self):
        if self.current_group_idx is None:
            messagebox.showwarning("No Selection", "Please select a group first.")
            return
        g = self.groups[self.current_group_idx]
        g["name"]        = self._grp_vars["name"].get().strip().lower()
        g["date"]        = self._grp_vars["date"].get().strip()
        g["description"] = self._grp_vars["description"].get().strip() or None
        g["contact"]     = self._grp_vars["contact"].get().strip() or None
        meta = self._grp_vars["meta"].get().strip()
        g["meta"]        = meta or None
        save_json(GROUPS_FILE, self.groups)
        self._refresh_groups_list()
        self._update_statusbar()
        self._log(f"[INFO] Saved group: {g['name']}")

    def _add_location(self):
        if self.current_group_idx is None:
            messagebox.showwarning("No Selection", "Please select a group first.")
            return
        url = simpledialog.askstring("Add Location", "Enter URL (onion or clearnet):", parent=self)
        if not url:
            return
        url = url.strip()
        g = self.groups[self.current_group_idx]
        if any(l.get("slug") == url for l in g.get("locations", [])):
            messagebox.showwarning("Duplicate", f"URL already exists for this group.")
            return
        g.setdefault("locations", []).append(make_location_schema(url))
        save_json(GROUPS_FILE, self.groups)
        self._populate_group_detail(g)
        self._log(f"[INFO] Added location {url} → {g['name']}")

    def _edit_location_url(self, _event=None):
        sel = self._loc_tree.selection()
        if not sel or self.current_group_idx is None:
            return
        old_url = self._loc_tree.item(sel[0], "values")[0]
        new_url = simpledialog.askstring("Edit URL", "New URL:", initialvalue=old_url, parent=self)
        if not new_url or new_url.strip() == old_url:
            return
        new_url = new_url.strip()
        g = self.groups[self.current_group_idx]
        for loc in g.get("locations", []):
            if loc.get("slug") == old_url:
                loc.update(make_location_schema(new_url))
                break
        save_json(GROUPS_FILE, self.groups)
        self._populate_group_detail(g)
        self._log(f"[INFO] Updated URL: {old_url} → {new_url}")

    def _toggle_location(self):
        sel = self._loc_tree.selection()
        if not sel or self.current_group_idx is None:
            messagebox.showwarning("No Selection", "Please select a location.")
            return
        url = self._loc_tree.item(sel[0], "values")[0]
        g = self.groups[self.current_group_idx]
        for loc in g.get("locations", []):
            if loc.get("slug") == url:
                loc["enabled"] = not loc.get("enabled", True)
                break
        save_json(GROUPS_FILE, self.groups)
        self._populate_group_detail(g)

    def _remove_location(self):
        sel = self._loc_tree.selection()
        if not sel or self.current_group_idx is None:
            return
        url = self._loc_tree.item(sel[0], "values")[0]
        if not messagebox.askyesno("Confirm", f"Remove:\n{url}"):
            return
        g = self.groups[self.current_group_idx]
        g["locations"] = [l for l in g.get("locations", []) if l.get("slug") != url]
        save_json(GROUPS_FILE, self.groups)
        self._populate_group_detail(g)
        self._log(f"[INFO] Removed {url} from {g['name']}")

    def _new_group(self):
        name = simpledialog.askstring("New Group", "Group name (lowercase):", parent=self)
        if not name:
            return
        name = name.strip().lower()
        if any(g["name"] == name for g in self.groups):
            messagebox.showwarning("Exists", f"Group '{name}' already exists.")
            return
        url = simpledialog.askstring("New Group", f"Initial URL for '{name}':", parent=self)
        if not url:
            return
        self.groups.append({
            "name": name,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "meta": None,
            "description": None,
            "contact": None,
            "locations": [make_location_schema(url.strip())],
            "profile": [],
        })
        save_json(GROUPS_FILE, self.groups)
        self._refresh_groups_list()
        self._update_statusbar()
        self._log(f"[INFO] Created group: {name}")

    def _delete_group(self):
        if self.current_group_idx is None:
            messagebox.showwarning("No Selection", "Please select a group first.")
            return
        g = self.groups[self.current_group_idx]
        if not messagebox.askyesno("Confirm Delete",
                                   f"Delete group '{g['name']}'?\nThis cannot be undone."):
            return
        self.groups.pop(self.current_group_idx)
        save_json(GROUPS_FILE, self.groups)
        self.current_group_idx = None
        self._refresh_groups_list()
        self._update_statusbar()
        self._log(f"[INFO] Deleted group: {g['name']}")

    def _run_scrape(self):
        if self.current_group_idx is None:
            messagebox.showwarning("No Selection", "Please select a group first.")
            return
        g = self.groups[self.current_group_idx]
        self._run_command([sys.executable, str(BIN_DIR / "scrape.py"), "-G", g["name"]])
        self.nb.select(3)

    def _run_parse(self):
        if self.current_group_idx is None:
            messagebox.showwarning("No Selection", "Please select a group first.")
            return
        g = self.groups[self.current_group_idx]
        self._run_command([sys.executable, str(BIN_DIR / "parse.py"), "-G", g["name"]])
        self.nb.select(3)

    def _run_scrape_parse(self):
        if self.current_group_idx is None:
            messagebox.showwarning("No Selection", "Please select a group first.")
            return
        g = self.groups[self.current_group_idx]
        name = g["name"]
        def _seq():
            self._run_command([sys.executable, str(BIN_DIR / "scrape.py"), "-G", name],
                              on_done=lambda: self._run_command(
                                  [sys.executable, str(BIN_DIR / "parse.py"), "-G", name]))
        _seq()
        self.nb.select(3)

    # ── Victims Tab ───────────────────────────────────────────────────────

    def _build_victims_tab(self):
        outer = ttk.Frame(self.nb)
        self.nb.add(outer, text="  Victims  ")
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)

        # Filter bar
        fbar = tk.Frame(outer, bg=BG)
        fbar.grid(row=0, column=0, sticky=tk.EW, padx=8, pady=(8, 4))

        tk.Label(fbar, text="Group:", bg=BG, fg=FG, font=(FONT, 10)).pack(side=tk.LEFT)
        self._vic_grp = tk.StringVar(value="All")
        self._vic_grp_cb = ttk.Combobox(fbar, textvariable=self._vic_grp,
                                        width=18, state="readonly")
        self._vic_grp_cb.pack(side=tk.LEFT, padx=(4, 14))
        self._vic_grp_cb.bind("<<ComboboxSelected>>", lambda _: self._refresh_victims_table())

        tk.Label(fbar, text="Search:", bg=BG, fg=FG, font=(FONT, 10)).pack(side=tk.LEFT)
        self._vic_search = tk.StringVar()
        self._vic_search.trace_add("write", lambda *_: self._refresh_victims_table())
        ttk.Entry(fbar, textvariable=self._vic_search, width=32).pack(
            side=tk.LEFT, padx=(4, 14))

        ttk.Button(fbar, text="Export CSV", command=self._export_victims_csv).pack(side=tk.RIGHT)

        self._vic_count = tk.StringVar()
        tk.Label(fbar, textvariable=self._vic_count, bg=BG, fg=SUB_FG,
                 font=(FONT, 9)).pack(side=tk.RIGHT, padx=8)

        # Table
        tf = tk.Frame(outer, bg=BG)
        tf.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        tf.rowconfigure(0, weight=1)
        tf.columnconfigure(0, weight=1)

        cols = ("group", "victim", "website", "country", "activity", "discovered")
        self._vic_tree = ttk.Treeview(tf, columns=cols, show="headings", selectmode="browse")

        headings = {
            "group":     ("Group",      120),
            "victim":    ("Victim",     220),
            "website":   ("Website",    180),
            "country":   ("Country",     80),
            "activity":  ("Activity",   120),
            "discovered":("Discovered", 150),
        }
        for col, (hdg, w) in headings.items():
            self._vic_tree.heading(col, text=hdg,
                                   command=lambda c=col: self._sort_victims(c))
            self._vic_tree.column(col, width=w, minwidth=60)

        vsb = ttk.Scrollbar(tf, orient=tk.VERTICAL, command=self._vic_tree.yview)
        hsb = ttk.Scrollbar(tf, orient=tk.HORIZONTAL, command=self._vic_tree.xview)
        self._vic_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self._vic_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self._vic_tree.bind("<Double-Button-1>", self._show_victim_detail)

        self._refresh_victims_table()

    def _refresh_victims_table(self):
        all_groups = sorted(set(v.get("group_name", "") for v in self.victims))
        self._vic_grp_cb["values"] = ["All"] + all_groups

        grp_filter = self._vic_grp.get()
        query = self._vic_search.get().lower()

        data = self.victims
        if grp_filter and grp_filter != "All":
            data = [v for v in data if v.get("group_name") == grp_filter]
        if query:
            data = [v for v in data if
                    query in v.get("post_title", "").lower() or
                    query in v.get("website", "").lower() or
                    query in v.get("country", "").lower() or
                    query in v.get("description", "").lower() or
                    query in v.get("group_name", "").lower()]

        key_map = {
            "group": "group_name", "victim": "post_title", "website": "website",
            "country": "country", "activity": "activity", "discovered": "discovered",
        }
        sk = key_map.get(self._victim_sort_col, "discovered")
        data = sorted(data, key=lambda x: x.get(sk, ""), reverse=self._victim_sort_rev)

        self._vic_tree.delete(*self._vic_tree.get_children())
        LIMIT = 3000
        for v in data[:LIMIT]:
            self._vic_tree.insert("", tk.END, values=(
                v.get("group_name", ""),
                v.get("post_title", "")[:80],
                v.get("website", "")[:50],
                v.get("country", ""),
                v.get("activity", ""),
                v.get("discovered", "")[:16],
            ))

        shown = min(len(data), LIMIT)
        suffix = f" (showing {LIMIT})" if len(data) > LIMIT else ""
        self._vic_count.set(f"{shown}{suffix} victims")

    def _sort_victims(self, col: str):
        if self._victim_sort_col == col:
            self._victim_sort_rev = not self._victim_sort_rev
        else:
            self._victim_sort_col = col
            self._victim_sort_rev = False
        self._refresh_victims_table()

    def _show_victim_detail(self, _event=None):
        sel = self._vic_tree.selection()
        if not sel:
            return
        vals = self._vic_tree.item(sel[0], "values")
        group_name, post_title_trunc = vals[0], str(vals[1])
        victim = next(
            (v for v in self.victims
             if v.get("group_name") == group_name and
             v.get("post_title", "")[:80] == post_title_trunc),
            None,
        )
        if not victim:
            return

        win = tk.Toplevel(self)
        win.title(f"Victim — {victim.get('post_title', '')}")
        win.geometry("620x520")
        win.configure(bg=BG)

        txt = scrolledtext.ScrolledText(
            win, bg=OVERLAY, fg=FG,
            font=(MONO, 10), borderwidth=0, padx=10, pady=10,
            insertbackground=FG,
        )
        txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        txt.insert(tk.END, json.dumps(victim, indent=2, ensure_ascii=False))
        txt.config(state=tk.DISABLED)

    def _export_victims_csv(self):
        from tkinter import filedialog
        import csv

        grp_filter = self._vic_grp.get()
        query = self._vic_search.get().lower()

        data = self.victims
        if grp_filter and grp_filter != "All":
            data = [v for v in data if v.get("group_name") == grp_filter]
        if query:
            data = [v for v in data if
                    query in v.get("post_title", "").lower() or
                    query in v.get("website", "").lower() or
                    query in v.get("group_name", "").lower()]

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile="victims_export.csv",
            parent=self,
        )
        if not path:
            return

        cols = ["group_name", "post_title", "website", "country",
                "activity", "discovered", "published", "description", "post_url"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(data)

        self._log(f"[INFO] Exported {len(data)} victims → {path}")
        messagebox.showinfo("Export Complete", f"Exported {len(data)} victims to:\n{path}")

    # ── Console Tab ───────────────────────────────────────────────────────

    def _build_console_tab(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text="  Console  ")
        f.rowconfigure(0, weight=1)
        f.columnconfigure(0, weight=1)

        self._console = scrolledtext.ScrolledText(
            f, bg=SURFACE, fg=GREEN,
            font=(MONO, 10), borderwidth=0,
            insertbackground=FG, padx=8, pady=8,
            state=tk.DISABLED,
        )
        self._console.grid(row=0, column=0, sticky="nsew", padx=6, pady=(6, 4))

        # Tag styles
        self._console.tag_configure("err",  foreground=RED)
        self._console.tag_configure("info", foreground=ACCENT)
        self._console.tag_configure("done", foreground=GREEN)
        self._console.tag_configure("run",  foreground=YELLOW)

        btn_row = tk.Frame(f, bg=BG)
        btn_row.grid(row=1, column=0, sticky=tk.EW, padx=6, pady=(0, 6))
        ttk.Button(btn_row, text="Clear", command=self._clear_console).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(btn_row, text="Copy All", command=self._copy_console).pack(side=tk.LEFT)

        self._log("[INFO] Ransomware.live Manager started.")
        self._log(f"[INFO] DB: {db_dir}")

    def _log(self, text: str):
        self._console.config(state=tk.NORMAL)
        tag = "info" if text.startswith("[INFO]") else \
              "err"  if text.startswith("[ERROR]") else \
              "done" if text.startswith("[DONE]") else \
              "run"  if text.startswith("[RUN]") else ""
        ts = datetime.now().strftime("%H:%M:%S")
        self._console.insert(tk.END, f"[{ts}] {text}\n", tag)
        self._console.see(tk.END)
        self._console.config(state=tk.DISABLED)

    def _clear_console(self):
        self._console.config(state=tk.NORMAL)
        self._console.delete("1.0", tk.END)
        self._console.config(state=tk.DISABLED)

    def _copy_console(self):
        content = self._console.get("1.0", tk.END)
        self.clipboard_clear()
        self.clipboard_append(content)

    # ── Command Runner ────────────────────────────────────────────────────

    def _run_command(self, cmd: list, on_done=None):
        self._log(f"[RUN] {' '.join(str(c) for c in cmd)}")

        def worker():
            try:
                env = os.environ.copy()
                env["PYTHONPATH"] = str(BIN_DIR)
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=str(home),
                    env=env,
                )
                for line in proc.stdout:
                    self.after(0, self._log, line.rstrip())
                proc.wait()
                self.after(0, self._log,
                           f"[DONE] Exit code: {proc.returncode}")
                self.after(500, self._refresh_all)
                if on_done:
                    self.after(600, on_done)
            except Exception as e:
                self.after(0, self._log, f"[ERROR] {e}")

        threading.Thread(target=worker, daemon=True).start()


# ── Entry Point ────────────────────────────────────────────────────────────

def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
