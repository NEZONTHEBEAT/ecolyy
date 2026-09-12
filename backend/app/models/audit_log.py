"""
Collection: audit_logs
{ _id, actor_id, actor_role, action, target_collection, target_id, meta, created_at }
Written by admin_service whenever an admin mutates data, for accountability.
"""
from datetime import datetime, timezone


class AuditLogModel:
    collection_name = "audit_logs"

    @staticmethod
    def new(actor_id: str, actor_role: str, action: str, target_collection: str, target_id: str, meta: dict | None = None) -> dict:
        return {
            "actor_id": actor_id,
            "actor_role": actor_role,
            "action": action,
            "target_collection": target_collection,
            "target_id": target_id,
            "meta": meta or {},
            "created_at": datetime.now(timezone.utc),
        }
