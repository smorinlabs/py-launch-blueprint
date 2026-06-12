# Copyright (c) 2025, Steve Morin
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Human-display string helpers for the *text* renderer (pure functions).

These live in ``core`` because result models use them in their rich-row
variants (``table_rows_rich``) — they format strings, never print. The
contract per output mode:

* **text** (terminal) — relative times and OSC-8 hyperlinks are welcome.
* **json** — never: timestamps stay ISO-8601 UTC, URLs stay raw fields.
* **markdown** — plain ``table_rows()``; use Markdown's own link syntax.
"""

from datetime import UTC, datetime

from rich.markup import escape

#: (seconds per unit, singular name) — largest first. Months/years use the
#: coarse 30/365-day buckets appropriate for "about how long ago" display.
_UNITS: list[tuple[int, str]] = [
    (365 * 86400, "year"),
    (30 * 86400, "month"),
    (86400, "day"),
    (3600, "hour"),
    (60, "minute"),
]


def relative_time(moment: datetime, *, now: datetime | None = None) -> str:
    """Render a coarse human delta: ``"2 days ago"`` / ``"in 3 hours"``.

    Anything under a minute is ``"just now"``. A naive ``moment`` is taken
    as UTC (matching the logging/JSON timestamp convention). ``now`` exists
    for tests; it defaults to the current UTC time.
    """
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    reference = now if now is not None else datetime.now(UTC)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=UTC)

    seconds = (reference - moment).total_seconds()
    future = seconds < 0
    seconds = abs(seconds)

    if seconds < 60:
        return "just now"
    for unit_seconds, name in _UNITS:
        count = int(seconds // unit_seconds)
        if count >= 1:
            phrase = f"{count} {name}" + ("s" if count != 1 else "")
            return f"in {phrase}" if future else f"{phrase} ago"
    return "just now"  # pragma: no cover — unreachable (minute bucket catches)


def rich_link(text: str, url: str) -> str:
    """Markup for a clickable terminal hyperlink (OSC 8).

    Rich emits the escape codes only on terminals that support them and
    falls back to plain ``text`` everywhere else (pipes, files, no-color).
    ``text`` is escaped — a path containing ``[`` must render literally,
    not parse as markup. The URL needs no escaping (file URIs are
    percent-encoded; markup is not parsed inside the tag).
    """
    return f"[link={url}]{escape(text)}[/link]"
