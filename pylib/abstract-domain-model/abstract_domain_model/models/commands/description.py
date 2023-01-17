from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AddDescription:
    text: str
    lang: str
    source_updated_at: str  #
    wiki_link: Optional[str] = None
    wiki_data_id: Optional[str] = None
