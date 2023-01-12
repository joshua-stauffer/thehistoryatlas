from dataclasses import dataclass


@dataclass(frozen=True)
class Description:
    text: str
    lang: str
    updated_at: str
