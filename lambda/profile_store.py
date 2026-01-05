from __future__ import annotations

from decimal import Decimal
from datetime import datetime, timezone
from typing import Any, Dict

from dynamo_client import get_profiles_table


def _to_dynamodb_types(value: Any) -> Any:
    """
    DynamoDB via boto3 does not like raw Python floats.
    Convert floats -> Decimal, and recurse through dict/list.
    """
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {k: _to_dynamodb_types(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_dynamodb_types(v) for v in value]
    return value


def save_profile(user_id: str, profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Overwrite by user_id.
    Stores:
      - user_id (PK)
      - updated_at (ISO timestamp)
      - profile (nested map)
    Returns the exact item we put (after float->Decimal conversion).
    """
    table = get_profiles_table()

    item = {
        "user_id": user_id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "profile": profile,
    }

    item = _to_dynamodb_types(item)

    table.put_item(Item=item)
    return item
