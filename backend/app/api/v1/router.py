"""
Aggregates every /api/v1/* sub-router into one `api_router`, so main.py
only has to include a single router instead of one per file.
"""
from fastapi import APIRouter

from app.api.v1 import admin, auth, institutions, notifications, partners, pickups, rewards, users, wallet

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(wallet.router)
api_router.include_router(notifications.router)
api_router.include_router(pickups.router)
api_router.include_router(partners.router)
api_router.include_router(institutions.router)
api_router.include_router(rewards.router)
api_router.include_router(admin.router)
