from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    id: str
    title: str
    author: str
    publisher: str
    pub_date: str
