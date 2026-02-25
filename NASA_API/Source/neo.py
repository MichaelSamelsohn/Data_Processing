"""
Script Name - neo.py

Purpose - Query near-Earth object (NEO) data from NASA's NEO Web Service.
For full API documentation - https://api.nasa.gov/

Created by Michael Samelsohn, 25/02/26.
"""

# Imports #
import re

from datetime import datetime, timedelta
from NASA_API.Settings.api_settings import (
    log, NEO_URL_PREFIX, NEO_MAX_DATE_RANGE, API_KEY
)
from NASA_API.Source.api_utilities import get_request


class NEO:
    def __init__(self, start_date: str, end_date: str):
        log.neo("Initializing the NEO class")

        self.start_date = start_date
        self.end_date = end_date
        self._neo_feed = None  # Populated by near_earth_objects().

    @staticmethod
    def validate_date(date: str) -> bool:
        """
        Validate whether the provided date string is in the correct format and represents a real calendar date.

        The date must:
        - Be in the 'YYYY-MM-DD' format.
        - Represent a valid calendar date (e.g., not February 30).

        Note: Future dates are allowed because the NEO API includes orbital predictions for upcoming close approaches.

        :param date: The date string to validate.

        :return: True if the date is well-formed, False otherwise.
        """

        log.debug(f"Validating NEO date - {date}")

        # Step (1) - Verify the string matches the YYYY-MM-DD pattern.
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date):
            log.error("Incorrect date format (expected - YYYY-MM-DD)")
            return False

        # Step (2) - Verify the date represents a real calendar date.
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            log.error("Invalid calendar date (e.g., February 30 does not exist)")
            return False

        return True

    @staticmethod
    def validate_date_range(start_date: str, end_date: str) -> bool:
        """
        Validate that the date range is ordered correctly and does not exceed the API's 7-day window limit.

        Both dates are assumed to already be in YYYY-MM-DD format and individually valid before this call.

        :param start_date: The range start date string (YYYY-MM-DD).
        :param end_date:   The range end date string (YYYY-MM-DD).

        :return: True if start_date ≤ end_date and the span is ≤ NEO_MAX_DATE_RANGE days, False otherwise.
        """

        log.debug(f"Validating NEO date range - {start_date} to {end_date}")

        start = datetime.strptime(start_date, "%Y-%m-%d")
        end   = datetime.strptime(end_date,   "%Y-%m-%d")

        # The start date must not be later than the end date.
        if start > end:
            log.error(f"Start date ({start_date}) must not be later than end date ({end_date})")
            return False

        # The NEO API enforces a maximum 7-day window per request.
        delta = (end - start).days
        if delta > NEO_MAX_DATE_RANGE:
            log.error(
                f"Date range spans {delta} days — the NEO API allows a maximum of "
                f"{NEO_MAX_DATE_RANGE} days per request"
            )
            return False

        return True

    @property
    def neo_feed(self):
        """Get the feed data returned by the most recent near_earth_objects() call."""
        return self._neo_feed

    def near_earth_objects(self) -> bool:
        """
        Query the NEO feed for asteroid close-approach data within the configured date window.

        The full response is stored in _neo_feed. The response includes:
        - element_count: total number of unique NEOs in the window.
        - near_earth_objects: a dict keyed by date, each containing a list of asteroid records with
          orbital data, estimated diameter, hazard flag, and close-approach details.

        :return: True if the query succeeded, False on validation error or network failure.
        """

        log.neo(f"Querying NEO feed from {self.start_date} to {self.end_date}")

        # Step (1) - Validate all parameters before making the request.
        if not self.validate_date(self.start_date):
            return False
        if not self.validate_date(self.end_date):
            return False
        if not self.validate_date_range(self.start_date, self.end_date):
            return False

        # Step (2) - Build the request URL.
        url = (
            f"{NEO_URL_PREFIX}feed"
            f"?start_date={self.start_date}&end_date={self.end_date}&{API_KEY}"
        )

        # Step (3) - Perform the API request.
        json_object = get_request(url=url)
        if json_object is None:
            log.error("API request failed - check logs for details")
            return False

        # Step (4) - Store the results and log a high-level summary.
        self._neo_feed = json_object
        element_count = json_object.get("element_count", 0)
        log.neo(f"Retrieved {element_count} near-Earth object(s) across the requested window")

        # Log one summary line per date bucket.
        for date_key, asteroids in json_object.get("near_earth_objects", {}).items():
            log.neo(f"  {date_key}: {len(asteroids)} object(s)")
            for asteroid in asteroids:
                name       = asteroid.get("name", "N/A")
                hazardous  = asteroid.get("is_potentially_hazardous_asteroid", False)
                approaches = asteroid.get("close_approach_data", [{}])
                miss_km    = approaches[0].get("miss_distance", {}).get("kilometers", "N/A")
                log.neo(
                    f"    • {name} | hazardous={hazardous} | "
                    f"miss distance={miss_km} km"
                )

        return True

    def display_feed(self):
        """
        Display NEO close-approach data in an interactive matplotlib window.

        The window shows:
        - Left panel: scatter plot of miss distance (km) vs. close-approach date.
          Each point represents one asteroid. Color encodes hazard status (red = hazardous,
          green = non-hazardous) and marker size scales with estimated diameter.
          Click any point to inspect the full asteroid record.
        - Right panel: formatted details card for the selected asteroid.
        - Bottom: name search box and a hazardous-only toggle button.

        Requires near_earth_objects() to have been called successfully beforehand.
        """

        if not self._neo_feed:
            log.neo("No feed data to display — run near_earth_objects() first")
            return

        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from matplotlib.lines import Line2D
        from matplotlib.widgets import TextBox, Button

        # Flatten all close-approach records across every date bucket into a single list.
        records = []
        for date_str, asteroids in self._neo_feed.get("near_earth_objects", {}).items():
            for ast in asteroids:
                for approach in ast.get("close_approach_data", [{}]):
                    try:
                        approach_date = datetime.strptime(
                            approach.get("close_approach_date", date_str), "%Y-%m-%d"
                        )
                    except ValueError:
                        approach_date = datetime.strptime(date_str, "%Y-%m-%d")

                    diam_min = ast.get("estimated_diameter", {}).get("meters", {}).get("estimated_diameter_min", 0)
                    diam_max = ast.get("estimated_diameter", {}).get("meters", {}).get("estimated_diameter_max", 0)

                    records.append({
                        "name":      ast.get("name", "Unknown"),
                        "id":        ast.get("id", "N/A"),
                        "date":      approach_date,
                        "miss_km":   float(approach.get("miss_distance", {}).get("kilometers", 0)),
                        "speed_kph": float(approach.get("relative_velocity", {}).get("kilometers_per_hour", 0)),
                        "diameter":  (diam_min + diam_max) / 2.0,
                        "hazardous": ast.get("is_potentially_hazardous_asteroid", False),
                        "full":      ast,
                    })

        if not records:
            log.neo("No close-approach records to display")
            return

        # Mutable state shared across closures.
        haz_only_flag = [False]
        search_text   = [""]
        scatter_ref   = [None]
        filtered_ref  = [records[:]]

        fig = plt.figure(figsize=(15, 8))
        fig.patch.set_facecolor('#0a0a1a')
        fig.suptitle(
            f"NEO Close Approaches  ·  {self.start_date}  →  {self.end_date}  "
            f"·  {self._neo_feed.get('element_count', 0)} object(s)",
            fontsize=13, fontweight='bold', color='white'
        )

        ax_scatter = fig.add_axes([0.15, 0.18, 0.47, 0.73])
        ax_details = fig.add_axes([0.66, 0.18, 0.32, 0.73])
        ax_search  = fig.add_axes([0.15, 0.04, 0.32, 0.07])
        ax_btn     = fig.add_axes([0.49, 0.04, 0.13, 0.07])

        for ax in (ax_scatter, ax_details):
            ax.set_facecolor('#0d1b2a')
            ax.tick_params(colors='#cccccc')
            for spine in ax.spines.values():
                spine.set_edgecolor('#223355')

        ax_details.axis('off')

        def _get_filtered():
            query = search_text[0].lower().strip()
            haz   = haz_only_flag[0]
            return [
                r for r in records
                if (not haz or r["hazardous"]) and (not query or query in r["name"].lower())
            ]

        def _show_details(record):
            ax_details.cla()
            ax_details.set_facecolor('#0d1b2a')
            ax_details.axis('off')
            od = record["full"].get("orbital_data", {})
            lines = [
                f"  {record['name']}",
                "  " + "─" * 32,
                f"  ID:             {record['id']}",
                f"  Approach date:  {record['date'].strftime('%Y-%m-%d')}",
                f"  Miss distance:  {record['miss_km']:>15,.0f} km",
                f"  Rel. velocity:  {record['speed_kph']:>15,.0f} km/h",
                f"  Est. diameter:  {record['diameter']:>14.1f} m (avg)",
                f"  Hazardous:      {'YES  ⚠' if record['hazardous'] else 'No'}",
            ]
            if od:
                lines += [
                    "  " + "─" * 32,
                    f"  Orbit class:    {od.get('orbit_class', {}).get('orbit_class_type', 'N/A')}",
                    f"  Semi-major ax:  {od.get('semi_major_axis', 'N/A')}",
                    f"  Eccentricity:   {od.get('eccentricity', 'N/A')}",
                    f"  Inclination:    {od.get('inclination', 'N/A')}°",
                    f"  Period (days):  {od.get('orbital_period', 'N/A')}",
                ]
            ax_details.text(
                0.01, 0.98, "\n".join(lines),
                transform=ax_details.transAxes,
                fontsize=8.5, va='top', ha='left', fontfamily='monospace', color='#d0eaff',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='#102040', alpha=0.95, edgecolor='#2255aa')
            )
            ax_details.set_title("Object Details", fontsize=10, color='white', pad=6)
            fig.canvas.draw_idle()

        def _redraw(*_):
            ax_scatter.cla()
            ax_scatter.set_facecolor('#0d1b2a')
            ax_details.cla()
            ax_details.set_facecolor('#0d1b2a')
            ax_details.axis('off')
            ax_details.set_title("Object Details  ·  click a point", fontsize=9, color='#aaaacc', pad=6)

            filtered = _get_filtered()
            filtered_ref[0] = filtered

            if not filtered:
                ax_scatter.text(0.5, 0.5, "No matching objects", ha='center', va='center',
                                transform=ax_scatter.transAxes, fontsize=13, color='#556677')
                ax_scatter.set_title(f"0 / {len(records)} object(s) shown",
                                     fontsize=9, color='#aaaacc')
                fig.canvas.draw_idle()
                return

            dates  = [r["date"]    for r in filtered]
            misses = [r["miss_km"] for r in filtered]
            # Clamp marker size so even tiny or giant objects remain visible.
            sizes  = [max(25, min(r["diameter"] * 0.4, 350)) for r in filtered]
            colors = ['#e74c3c' if r["hazardous"] else '#2ecc71' for r in filtered]

            sc = ax_scatter.scatter(
                dates, misses, s=sizes, c=colors, alpha=0.75,
                edgecolors='#ffffff44', linewidths=0.5,
                picker=True, pickradius=8, zorder=3
            )
            scatter_ref[0] = sc

            ax_scatter.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            ax_scatter.xaxis.set_major_locator(mdates.AutoDateLocator())
            ax_scatter.tick_params(axis='x', colors='#ccccdd', labelrotation=20)
            ax_scatter.tick_params(axis='y', colors='#ccccdd')
            ax_scatter.set_ylabel("Miss Distance (km)", color='#ccccdd', fontsize=9)
            ax_scatter.set_xlabel("Close Approach Date", color='#ccccdd', fontsize=9)
            ax_scatter.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
            ax_scatter.set_title(
                f"{len(filtered)} / {len(records)} object(s)  ·  click a point for details",
                fontsize=9, color='#aaaacc'
            )
            ax_scatter.grid(linestyle='--', alpha=0.2, color='#334455')
            for spine in ax_scatter.spines.values():
                spine.set_edgecolor('#223355')

            legend_elements = [
                Line2D([0], [0], marker='o', color='w', markerfacecolor='#e74c3c',
                       markersize=9, label='Hazardous'),
                Line2D([0], [0], marker='o', color='w', markerfacecolor='#2ecc71',
                       markersize=9, label='Non-hazardous'),
                Line2D([0], [0], marker='o', color='w', markerfacecolor='#aaaaaa',
                       markersize=5, label='size ∝ diameter'),
            ]
            ax_scatter.legend(handles=legend_elements, loc='upper right', fontsize=8,
                              facecolor='#102030', edgecolor='#334455', labelcolor='#ccddee')
            fig.canvas.draw_idle()

        def _on_pick(event):
            if event.artist is not scatter_ref[0]:
                return
            _show_details(filtered_ref[0][event.ind[0]])

        def _on_search(text):
            search_text[0] = text
            _redraw()

        def _on_toggle(_):
            haz_only_flag[0] = not haz_only_flag[0]
            btn.label.set_text("All Objects" if haz_only_flag[0] else "⚠ Hazardous Only")
            btn.color      = '#5a0000' if haz_only_flag[0] else '#2a3a2a'
            btn.hovercolor = '#7a0000' if haz_only_flag[0] else '#3a5a3a'
            _redraw()

        text_box = TextBox(ax_search, "  Search name: ", initial="",
                           color='#102040', hovercolor='#1a3060', label_pad=0.02)
        text_box.label.set_color('white')
        text_box.text_disp.set_color('#d0eaff')
        text_box.on_text_change(_on_search)

        btn = Button(ax_btn, "⚠ Hazardous Only", color='#2a3a2a', hovercolor='#3a5a3a')
        btn.label.set_color('white')
        btn.on_clicked(_on_toggle)

        fig.canvas.mpl_connect('pick_event', _on_pick)
        _redraw()
        plt.show()

    @staticmethod
    def lookup(asteroid_id: str) -> dict | None:
        """
        Look up a specific asteroid by its NASA JPL Small-Body SPK-ID.

        Returns the full record for that object including orbital data, estimated diameter,
        close-approach history, and whether it is classified as potentially hazardous.

        :param asteroid_id: The SPK-ID of the asteroid (e.g., '3542519').

        :return: Asteroid data as a dictionary, or None if the request failed.
        """

        log.neo(f"Looking up asteroid with SPK-ID {asteroid_id}")

        url = f"{NEO_URL_PREFIX}neo/{asteroid_id}?{API_KEY}"
        result = get_request(url=url)

        if result is None:
            log.error(f"Lookup failed for asteroid ID {asteroid_id}")
            return None

        log.neo(f"Asteroid: {result.get('name', 'N/A')} | "
                f"hazardous={result.get('is_potentially_hazardous_asteroid', 'N/A')}")
        return result
