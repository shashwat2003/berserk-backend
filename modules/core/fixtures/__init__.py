from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class MasterDropdownFixtureDataType(BaseModel):
    label: str
    children: List[MasterDropdownFixtureDataType] = []
    max_level: Optional[int] = None
    config: Optional[int] = None
