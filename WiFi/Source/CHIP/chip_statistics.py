# Imports #
import textwrap

from WiFi.Settings.wifi_settings import *


class ChipStatistics:
    def print_statistics(self):
        """
        Print a formatted table of MAC-layer frame statistics for this chip, followed by an aggregate summary.

        Iterates over all frames recorded in the MAC statistics buffer and displays a bordered table with one row per
        frame, containing the following columns:
            * Direction         - TX --> (transmitted) or RX <-- (received).
            * Frame Description - The frame type (e.g., DATA, ACK, RTS, CTS).
            * Frame Size (B)    - PSDU size in bytes for the frame; "N/A" if not recorded.
            * PHY Rate (Mbps)   - The PHY data rate used for the frame (e.g., 6, 9, 12, ... 54); "N/A" if not recorded.
            * Retries           - Number of retransmission attempts for TX frames; "N/A" for RX frames or frames with no
                                  retry tracking. Appends "(frame dropped)" if retries were exhausted.
            * MAC Address (HEX) - Source address for RX frames, destination address for TX frames, formatted as a
                                  colon-separated hex string.

        After the per-frame table, an aggregate summary block is printed containing:
            * Frame counts       - Total TX and RX frames, broken down by frame type.
            * Total bytes        - Sum of FRAME_SIZE across all TX and RX frames.
            * Retry rate         - Percentage of TX frames (requiring confirmation) that needed at least one retry.
            * Frame drop rate    - Percentage of TX frames (requiring confirmation) that were ultimately dropped.
            * PHY rate stats     - Min, average, and max PHY rate across all frames with a recorded rate.
        """

        if not self.mac._statistics:
            log.info(f"({self._identifier}) No frame statistics available")
            return

        rows = []

        for frame in self.mac._statistics:
            direction = frame.get("DIRECTION", "UNKNOWN")
            frame_type = frame.get("TYPE", "UNKNOWN")
            frame_size = str(frame["FRAME_SIZE"]) if "FRAME_SIZE" in frame else "N/A"
            phy_rate = str(frame["PHY_RATE"]) if "PHY_RATE" in frame else "N/A"

            # Base description and retries.
            if direction == "RX":
                direction += " <--"
                description = frame_type
                retries = "N/A"
                mac = frame["SOURCE_ADDRESS"]
            elif direction == "TX":
                direction += " -->"
                description = frame_type
                mac = frame["DESTINATION_ADDRESS"]

                if "RETRY_ATTEMPTS" not in frame:
                    retries = "N/A"
                else:
                    retries = str(frame["RETRY_ATTEMPTS"])
                    if frame["RETRY_ATTEMPTS"] > 0 and not frame.get("CONFIRMED", False):
                        retries += " (frame dropped)"
            else:
                direction = "UNKNOWN"
                description = "UNKNOWN FRAME"
                retries = "N/A"
                mac = []

            mac_hex = ":".join(f"{b:02X}" for b in mac)
            rows.append((direction, description, frame_size, phy_rate, retries, mac_hex))

        # Column widths, ensure headers fit.
        dir_col_width     = max(max(len(r[0]) for r in rows), len("Direction"))          + 2
        desc_col_width    = max(max(len(r[1]) for r in rows), len("Frame Description"))  + 2
        size_col_width    = max(max(len(r[2]) for r in rows), len("Frame Size (B)"))     + 2
        rate_col_width    = max(max(len(r[3]) for r in rows), len("PHY Rate (Mbps)"))   + 2
        retries_col_width = max(max(len(r[4]) for r in rows), len("Retries"))            + 2
        mac_col_width     = max(max(len(r[5]) for r in rows), len("MAC Address (HEX)")) + 2

        # Headers.
        header_dir     = "Direction".center(dir_col_width)
        header_desc    = "Frame Description".center(desc_col_width)
        header_size    = "Frame Size (B)".center(size_col_width)
        header_rate    = "PHY Rate (Mbps)".center(rate_col_width)
        header_retries = "Retries".center(retries_col_width)
        header_mac     = "MAC Address (HEX)".center(mac_col_width)

        # Borders.
        top_border = ("+" + "-" * dir_col_width + "+" + "-" * desc_col_width + "+" + "-" * size_col_width +
                      "+" + "-" * rate_col_width + "+" + "-" * retries_col_width + "+" + "-" * mac_col_width + "+")
        mid_border = top_border
        bottom_border = top_border

        # Print table.
        log.info(f"({self._identifier}) Frame exchange statistics:")
        log.info(f"({self._identifier}) {top_border}")
        log.info(f"({self._identifier}) |{header_dir}|{header_desc}|{header_size}|{header_rate}|{header_retries}|{header_mac}|")
        log.info(f"({self._identifier}) {mid_border}")

        for direction, description, frame_size, phy_rate, retries, mac_hex in rows:
            # Wrap description if needed.
            wrapped_desc = textwrap.wrap(description, width=desc_col_width - 2) or [""]

            for i, line in enumerate(wrapped_desc):
                dir_col     = direction.center(dir_col_width)     if i == 0 else " " * dir_col_width
                desc_col    = line.center(desc_col_width)
                size_col    = frame_size.center(size_col_width)   if i == 0 else " " * size_col_width
                rate_col    = phy_rate.center(rate_col_width)     if i == 0 else " " * rate_col_width
                retries_col = retries.center(retries_col_width)   if i == 0 else " " * retries_col_width
                mac_col     = mac_hex.center(mac_col_width)       if i == 0 else " " * mac_col_width
                log.info(f"({self._identifier}) |{dir_col}|{desc_col}|{size_col}|{rate_col}|{retries_col}|{mac_col}|")

        log.info(f"({self._identifier}) {bottom_border}")

        # ── Aggregate summary ────────────────────────────────────────────── #

        tx_frames = [f for f in self.mac._statistics if f.get("DIRECTION") == "TX"]
        rx_frames = [f for f in self.mac._statistics if f.get("DIRECTION") == "RX"]

        # Frame counts by type.
        tx_counts = {}
        for f in tx_frames:
            tx_counts[f.get("TYPE", "UNKNOWN")] = tx_counts.get(f.get("TYPE", "UNKNOWN"), 0) + 1
        rx_counts = {}
        for f in rx_frames:
            rx_counts[f.get("TYPE", "UNKNOWN")] = rx_counts.get(f.get("TYPE", "UNKNOWN"), 0) + 1

        # Total bytes.
        tx_bytes = sum(f["FRAME_SIZE"] for f in tx_frames if "FRAME_SIZE" in f)
        rx_bytes = sum(f["FRAME_SIZE"] for f in rx_frames if "FRAME_SIZE" in f)

        # Retry and drop rates (only frames that track retries).
        confirmed_tx = [f for f in tx_frames if "RETRY_ATTEMPTS" in f]
        retried      = [f for f in confirmed_tx if f["RETRY_ATTEMPTS"] > 0]
        dropped      = [f for f in confirmed_tx if f["RETRY_ATTEMPTS"] > 0 and not f.get("CONFIRMED", False)]
        retry_rate = (len(retried) / len(confirmed_tx) * 100) if confirmed_tx else 0.0
        drop_rate  = (len(dropped) / len(confirmed_tx) * 100) if confirmed_tx else 0.0

        # PHY rate stats.
        phy_rates = [f["PHY_RATE"] for f in self.mac._statistics if "PHY_RATE" in f]
        if phy_rates:
            phy_min = min(phy_rates)
            phy_avg = sum(phy_rates) / len(phy_rates)
            phy_max = max(phy_rates)
            phy_str = f"{phy_min} / {phy_avg:.1f} / {phy_max} Mbps"
        else:
            phy_str = "N/A"

        # Build and print summary lines.
        tx_type_str = ", ".join(f"{t}: {n}" for t, n in sorted(tx_counts.items()))
        rx_type_str = ", ".join(f"{t}: {n}" for t, n in sorted(rx_counts.items()))

        log.info(f"({self._identifier}) Aggregate summary:")
        log.info(f"({self._identifier})   TX frames      : {len(tx_frames)}  ({tx_type_str})")
        log.info(f"({self._identifier})   RX frames      : {len(rx_frames)}  ({rx_type_str})")
        log.info(f"({self._identifier})   Total bytes TX : {tx_bytes} B")
        log.info(f"({self._identifier})   Total bytes RX : {rx_bytes} B")
        log.info(f"({self._identifier})   Retry rate     : {retry_rate:.1f}%  ({len(retried)}/{len(confirmed_tx)} frames)")
        log.info(f"({self._identifier})   Drop rate      : {drop_rate:.1f}%  ({len(dropped)}/{len(confirmed_tx)} frames)")
        log.info(f"({self._identifier})   PHY rate min/avg/max : {phy_str}")
