from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class AuditEntry:
    user_id: Optional[int]
    action_type: str
    object_type: str
    object_id: str
    previous_data: Optional[Dict]
    new_data: Optional[Dict]
    ip_address: Optional[str]
