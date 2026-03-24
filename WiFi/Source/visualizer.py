"""
Script Name - visualizer.py

Post-run WiFi session visualizations.  Produces a 2-column summary figure:

  Left column  (full height) — Message Sequence Chart (MCS annotated per arrow)
  Right column, row 0        — Connection State Timeline
  Right column, row 1        — Frame Exchange Heatmap

Created by Michael Samelsohn, 24/03/26.
"""

# Imports #
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.gridspec import GridSpec


# ── Colour palettes ────────────────────────────────────────────────────────────

_CAT_COLORS = {
    "Management": "#4C72B0",
    "Control":    "#DD8452",
    "Data":       "#55A868",
    "Other":      "#8C8C8C",
}

_STATE_COLORS = {
    "Advertising":    "#95a5a6",
    "Scanning":       "#f39c12",
    "Authenticating": "#e74c3c",
    "Authenticated":  "#3498db",
    "Associating":    "#9b59b6",
    "Associated":     "#2ecc71",
}

_MANAGEMENT = {
    "beacon", "probe request", "probe response",
    "authentication", "association request", "association response",
    "disassociation", "deauthentication",
}
_CONTROL = {"ack", "rts", "cts"}
_DATA    = {"data"}


def _category(frame_type: str) -> str:
    t = frame_type.lower()
    if t in _MANAGEMENT: return "Management"
    if t in _CONTROL:    return "Control"
    if t in _DATA:       return "Data"
    return "Other"


# ── State-machine helpers ──────────────────────────────────────────────────────

def _ap_state_transitions(stats: list) -> list:
    """Return (frame_index, state_name) transition list from the AP's perspective."""
    first_auth_rx = last_auth_tx = first_assoc_rx = first_assoc_resp_tx = None

    for i, f in enumerate(stats):
        t = f.get("TYPE", "")
        d = f.get("DIRECTION", "")
        if d == "RX" and t == "Authentication" and first_auth_rx is None:
            first_auth_rx = i
        if d == "TX" and t == "Authentication":
            last_auth_tx = i
        if d == "RX" and "request" in t.lower() and "association" in t.lower() and first_assoc_rx is None:
            first_assoc_rx = i
        if d == "TX" and "association" in t.lower() and "response" in t.lower() and first_assoc_resp_tx is None:
            first_assoc_resp_tx = i

    milestones = [
        (first_auth_rx,       "Authenticating"),
        (last_auth_tx,        "Authenticated"),
        (first_assoc_rx,      "Associating"),
        (first_assoc_resp_tx, "Associated"),
    ]

    transitions = [(0, "Advertising")]
    for idx, state in sorted((m for m in milestones if m[0] is not None), key=lambda x: x[0]):
        transitions.append((idx + 1, state))
    return transitions


def _sta_state_transitions(stats: list) -> list:
    """Return (frame_index, state_name) transition list from the STA's perspective."""
    first_auth_tx = last_auth_rx = first_assoc_tx = first_assoc_rx = None

    for i, f in enumerate(stats):
        t = f.get("TYPE", "")
        d = f.get("DIRECTION", "")
        if d == "TX" and t == "Authentication" and first_auth_tx is None:
            first_auth_tx = i
        if d == "RX" and t == "Authentication":
            last_auth_rx = i
        if d == "TX" and "request" in t.lower() and "association" in t.lower() and first_assoc_tx is None:
            first_assoc_tx = i
        if d == "RX" and "association" in t.lower() and "response" in t.lower() and first_assoc_rx is None:
            first_assoc_rx = i

    milestones = [
        (first_auth_tx,  "Authenticating"),
        (last_auth_rx,   "Authenticated"),
        (first_assoc_tx, "Associating"),
        (first_assoc_rx, "Associated"),
    ]

    transitions = [(0, "Scanning")]
    for idx, state in sorted((m for m in milestones if m[0] is not None), key=lambda x: x[0]):
        transitions.append((idx + 1, state))
    return transitions


# ── Subplot renderers ──────────────────────────────────────────────────────────

def _plot_msc(ax, ap_stats: list, ap_id: str, sta_id: str):
    """Message Sequence Chart drawn from the AP's frame log."""
    ax.set_title("Message Sequence Chart", fontweight="bold", pad=8)

    n = len(ap_stats)
    if n == 0:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        return

    AP_X, STA_X = 0.18, 0.82

    # Swim-lane lines
    ax.plot([AP_X,  AP_X],  [0.5, n + 0.5], color="#555", lw=2, zorder=0)
    ax.plot([STA_X, STA_X], [0.5, n + 0.5], color="#555", lw=2, zorder=0)
    ax.text(AP_X,  n + 0.8, ap_id,  ha="center", va="bottom", fontweight="bold", fontsize=11)
    ax.text(STA_X, n + 0.8, sta_id, ha="center", va="bottom", fontweight="bold", fontsize=11)

    for i, frame in enumerate(ap_stats):
        y        = n - i
        ftype    = frame.get("TYPE", "?")
        color    = _CAT_COLORS[_category(ftype)]
        retries  = frame.get("RETRY_ATTEMPTS", 0)
        dropped  = retries > 0 and not frame.get("CONFIRMED", True)
        ls       = "--" if dropped else "-"

        if frame.get("DIRECTION") == "TX":
            x_from, x_to = AP_X, STA_X
        else:
            x_from, x_to = STA_X, AP_X

        ax.annotate(
            "", xy=(x_to, y), xytext=(x_from, y),
            arrowprops=dict(arrowstyle="-|>", color=color, lw=1.6, linestyle=ls),
        )

        rate  = frame.get("PHY_RATE")
        label = ftype
        if retries:
            label += f"  [×{retries}{'  dropped' if dropped else ''}]"
        ax.text(
            (x_from + x_to) / 2, y + 0.2, label,
            ha="center", va="bottom", fontsize=7, color=color, clip_on=True,
        )
        if rate is not None:
            ax.text(
                (x_from + x_to) / 2, y - 0.2, f"{rate} Mbps",
                ha="center", va="top", fontsize=6, color=color, clip_on=True,
                style="italic",
            )

    ax.set_xlim(0, 1)
    ax.set_ylim(0, n + 2)
    ax.axis("off")

    legend_elements = [
        mpatches.Patch(facecolor=v, label=k)
        for k, v in _CAT_COLORS.items() if k != "Other"
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=8, framealpha=0.9)


def _plot_state_machine(ax, ap_stats: list, sta_stats: list, ap_id: str, sta_id: str):
    """Gantt-style connection-state timeline for AP and STA."""
    ax.set_title("Connection State Timeline", fontweight="bold", pad=8)

    ap_trans  = _ap_state_transitions(ap_stats)
    sta_trans = _sta_state_transitions(sta_stats)
    max_ap    = max(len(ap_stats), 1)
    max_sta   = max(len(sta_stats), 1)

    def draw_row(transitions, max_t, row_y):
        for k, (start, state) in enumerate(transitions):
            end   = transitions[k + 1][0] if k + 1 < len(transitions) else max_t
            color = _STATE_COLORS.get(state, "#8C8C8C")
            width = max(end - start, 0.3)
            ax.barh(row_y, width, left=start, height=0.55,
                    color=color, edgecolor="white", linewidth=0.6)
            if width >= 1.5:
                ax.text(start + width / 2, row_y, state,
                        ha="center", va="center", fontsize=7,
                        color="white", fontweight="bold", clip_on=True)

    draw_row(ap_trans,  max_ap,  1.0)
    draw_row(sta_trans, max_sta, 0.0)

    ax.set_yticks([0.0, 1.0])
    ax.set_yticklabels([sta_id, ap_id], fontsize=9)
    ax.set_xlabel("Frame Index", fontsize=9)
    ax.set_ylim(-0.5, 1.8)
    ax.spines[["top", "right"]].set_visible(False)

    patches = [mpatches.Patch(color=v, label=k) for k, v in _STATE_COLORS.items()]
    ax.legend(handles=patches, fontsize=7, loc="upper right", ncol=2, framealpha=0.88)


def _plot_heatmap(ax, ap_stats: list, sta_stats: list, ap_id: str, sta_id: str):
    """Frame-count matrix: rows = TX/RX per device, columns = frame type."""
    ax.set_title("Frame Exchange Heatmap", fontweight="bold", pad=8)

    all_types = sorted({f.get("TYPE", "?") for f in ap_stats + sta_stats})
    if not all_types:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        return

    row_labels = [f"{ap_id} TX", f"{ap_id} RX", f"{sta_id} TX", f"{sta_id} RX"]
    sources    = [
        (ap_stats,  "TX"),
        (ap_stats,  "RX"),
        (sta_stats, "TX"),
        (sta_stats, "RX"),
    ]

    matrix = np.array([
        [
            sum(1 for f in stats
                if f.get("DIRECTION") == d and f.get("TYPE") == ft)
            for ft in all_types
        ]
        for stats, d in sources
    ], dtype=float)

    im = ax.imshow(matrix, aspect="auto", cmap="YlOrRd", vmin=0)

    ax.set_xticks(range(len(all_types)))
    ax.set_xticklabels(all_types, rotation=40, ha="right", fontsize=7)
    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels(row_labels, fontsize=8)

    for r in range(len(row_labels)):
        for c in range(len(all_types)):
            v = int(matrix[r, c])
            if v > 0:
                ax.text(c, r, str(v),
                        ha="center", va="center",
                        fontsize=9, fontweight="bold", color="black")

    plt.colorbar(im, ax=ax, label="Frame Count", shrink=0.85)


# ── Public entry point ─────────────────────────────────────────────────────────

def plot_wifi_summary(ap, sta):
    """
    Render the three-panel WiFi session summary figure and display it.

    Layout:
        Left column  (full height) : Message Sequence Chart (with MCS per arrow)
        Right column, row 0        : Connection State Timeline
        Right column, row 1        : Frame Exchange Heatmap

    :param ap:  CHIP instance with role='AP'.
    :param sta: CHIP instance with role='STA'.
    """
    ap_stats  = ap.mac._statistics
    sta_stats = sta.mac._statistics
    ap_id     = ap._identifier
    sta_id    = sta._identifier

    fig = plt.figure(figsize=(18, 12))
    fig.suptitle("WiFi Simulation — Session Summary",
                 fontsize=15, fontweight="bold", y=0.99)

    gs = GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.35)

    _plot_msc(          fig.add_subplot(gs[:, 0]),  ap_stats, ap_id, sta_id)
    _plot_state_machine(fig.add_subplot(gs[0, 1]),  ap_stats, sta_stats, ap_id, sta_id)
    _plot_heatmap(      fig.add_subplot(gs[1, 1]),  ap_stats, sta_stats, ap_id, sta_id)

    plt.show()
