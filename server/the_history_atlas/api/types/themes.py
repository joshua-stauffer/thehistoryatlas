from uuid import UUID

from pydantic import BaseModel


class ThemeResponse(BaseModel):
    id: UUID
    name: str
    slug: str


class ThemeCategoryResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    children: list[ThemeResponse]


class ThemesResponse(BaseModel):
    categories: list[ThemeCategoryResponse]
