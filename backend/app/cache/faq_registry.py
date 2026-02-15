"""FAQ registry — pre-defined answers for common queries (zero GPT cost).

Add entries here for company-specific FAQ that never need an LLM call.
"""

from __future__ import annotations

import re
from typing import Optional

# Each entry: (list of regex patterns, answer text)
_FAQ_ENTRIES: list[tuple[list[str], str]] = [
    (
        [r"\bleave policy\b", r"\bhow many leaves\b", r"\bleave entitlement\b"],
        (
            "**Leave Policy:**\n"
            "- **Casual Leave:** 12 days/year\n"
            "- **Sick Leave:** 10 days/year\n"
            "- **Earned Leave:** 15 days/year\n\n"
            "Unused earned leave can be carried forward (max 30 days). "
            "Casual leaves cannot be carried forward."
        ),
    ),
    (
        [r"\bcompany holidays\b", r"\bpublic holidays\b", r"\bholiday list\b"],
        (
            "**Company Holidays 2026:**\n"
            "- Jan 26 — Republic Day\n"
            "- Mar 14 — Holi\n"
            "- Apr 14 — Ambedkar Jayanti\n"
            "- May 1 — May Day\n"
            "- Aug 15 — Independence Day\n"
            "- Oct 2 — Gandhi Jayanti\n"
            "- Oct 20 — Dussehra\n"
            "- Nov 9 — Diwali\n"
            "- Dec 25 — Christmas"
        ),
    ),
    (
        [r"\bworking hours\b", r"\boffice timings?\b", r"\bwork schedule\b"],
        (
            "**Working Hours:** 9:00 AM to 6:00 PM (Mon-Fri)\n"
            "**Lunch Break:** 1:00 PM to 2:00 PM\n"
            "Flexible timing available with manager approval."
        ),
    ),
    (
        [r"\bhelp\b", r"\bwhat can you do\b", r"\bcapabilities\b"],
        (
            "I'm your **HRMS Agent**. I can help you with:\n"
            "- 🔍 Employee lookup (by code or name)\n"
            "- 📋 Leave management (apply, status, approve/reject)\n"
            "- ⏰ Attendance records\n"
            "- 💰 Payroll & salary slips\n"
            "- 📊 Company statistics\n"
            "- ➕ Add/update employees (HR admin only)\n"
            "- 🚪 Resignation management (HR admin only)\n"
            "- 👥 Role management (super admin only)\n\n"
            "Just ask in plain English!"
        ),
    ),
]


def match_faq(query: str) -> Optional[str]:
    """Return a static answer if the query matches an FAQ pattern, else None."""
    lower = query.lower().strip()
    for patterns, answer in _FAQ_ENTRIES:
        for pattern in patterns:
            if re.search(pattern, lower):
                return answer
    return None
