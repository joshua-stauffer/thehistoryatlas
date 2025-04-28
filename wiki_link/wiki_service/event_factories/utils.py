"""Utility functions for event factories."""

from datetime import datetime
from typing import Dict

from wiki_service.types import TimeDefinition


def build_time_definition_from_claim(time_claim: Dict) -> TimeDefinition:
    """Build a TimeDefinition from a time claim."""
    # For qualifiers, the structure is flatter
    if "mainsnak" not in time_claim:
        return TimeDefinition(
            id=time_claim.get("id"),
            type=time_claim.get("type", "statement"),
            rank=time_claim.get("rank", "normal"),
            hash=time_claim.get("hash"),
            snaktype=time_claim["snaktype"],
            property=time_claim["property"],
            time=time_claim["datavalue"]["value"]["time"],
            timezone=time_claim["datavalue"]["value"]["timezone"],
            before=time_claim["datavalue"]["value"]["before"],
            after=time_claim["datavalue"]["value"]["after"],
            precision=time_claim["datavalue"]["value"]["precision"],
            calendarmodel=time_claim["datavalue"]["value"]["calendarmodel"],
        )

    # For mainsnaks, use the original structure
    return TimeDefinition(
        id=time_claim["id"],
        type=time_claim["type"],
        rank=time_claim["rank"],
        hash=time_claim["mainsnak"].get("hash"),
        snaktype=time_claim["mainsnak"]["snaktype"],
        property=time_claim["mainsnak"]["property"],
        time=time_claim["mainsnak"]["datavalue"]["value"]["time"],
        timezone=time_claim["mainsnak"]["datavalue"]["value"]["timezone"],
        before=time_claim["mainsnak"]["datavalue"]["value"]["before"],
        after=time_claim["mainsnak"]["datavalue"]["value"]["after"],
        precision=time_claim["mainsnak"]["datavalue"]["value"]["precision"],
        calendarmodel=time_claim["mainsnak"]["datavalue"]["value"]["calendarmodel"],
    )


def wikidata_time_to_text(time_def: TimeDefinition) -> str:
    """
    Convert a Wikidata time definition to a human-readable date string.

    Precision mapping:
      - 11: full date (day precision) → "December 31, 1980"
      - 10: month precision → "December 1980"
      - 9: year precision → "1980"
      - 8: decade precision → "1980s"
      - 7: century precision → "20th century"
    """
    # Remove leading '+' and any trailing parts (like the 'Z') not needed for parsing.
    raw_time = time_def.time
    is_negative = raw_time.startswith("-")
    if raw_time.startswith(("+", "-")):
        raw_time = raw_time[1:]

    # Extract year, month, and day from the raw time string
    year = int(raw_time[:4])
    month_str = raw_time[5:7]
    day_str = raw_time[8:10]
    month = int(month_str) if month_str != "00" else 1
    day = int(day_str) if day_str != "00" else 1

    # Create a valid datetime object
    dt = datetime(year=year, month=month, day=day)

    if time_def.precision == 11:
        # Full date: e.g. "December 31, 1980"
        date_str = f"{dt.strftime('%B')} {dt.day}, {dt.year}"
    elif time_def.precision == 10:
        # Month precision: e.g. "December 1980"
        date_str = dt.strftime("%B %Y")
    elif time_def.precision == 9:
        # Year precision: e.g. "1980"
        date_str = dt.strftime("%Y")
    elif time_def.precision == 8:
        # Decade precision: e.g. "1980s"
        decade = (dt.year // 10) * 10
        date_str = f"{decade}s"
    elif time_def.precision == 7:
        # Century precision: e.g. "20th century"
        century = (dt.year - 1) // 100 + 1
        # Determine the ordinal suffix (handles 11-13 as well)
        if 10 <= century % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(century % 10, "th")
        date_str = f"{century}{suffix} century"
    else:
        # Fallback: return ISO formatted date
        date_str = dt.isoformat()

    bc_suffix = " B.C.E" if is_negative else ""
    return date_str + bc_suffix
