
from typing import Any, List, Optional
from dataclasses import dataclass
from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class AssetDocsPayload():

    uuid: Optional[str] = None
    owner_sub: Optional[str] = None
    lock_sub: Optional[str] = None
    locked_at: Optional[str] = None
    subs_for_select: Optional[List[str]] = None
    roles_for_select: Optional[List[str]] = None
    subs_for_update: Optional[List[str]] = None
    roles_for_update: Optional[List[str]] = None
    data: Optional[Any] = None
    attrs: Optional[Any] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    comments: Optional[str] = None
    published: Optional[bool] = None
    published_at: Optional[str] = None
    object_type_uuid: Optional[str] = None
    slug: Optional[str] = None
    asset_geom: Optional[str] = None
    dataset_extent_geom: Optional[str] = None
    dataset_start_time: Optional[str] = None
    dataset_end_time: Optional[str] = None
