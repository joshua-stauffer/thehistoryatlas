from .synthetic_events import SYNTHETIC_EVENTS

EVENTS = [
    event
    for events in SYNTHETIC_EVENTS
    for event in events
]
