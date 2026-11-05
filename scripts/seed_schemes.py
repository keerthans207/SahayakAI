#!/usr/bin/env python
"""Seed the database with the scheme registry from data/.

Usage (from project root):
    python scripts/seed_schemes.py

This reads data/central/schemes.json and data/<state>/schemes.json and upserts
each scheme into the database. It is idempotent — running it twice does not
duplicate records.
"""

from __future__ import annotations

import asyncio
import os
import sys

# Add backend/ to import path.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.config import get_settings
from app.database.session import db_session, init_db
from app.services.scheme_service import SchemeService
from app.models.db import Scheme, SchemeRule, SchemeSource
from sqlalchemy import select


async def seed() -> None:
    settings = get_settings()
    print("Database: configured")
    await init_db()

    svc = SchemeService()
    print(f"Registry: {len(svc.schemes)} schemes found in data/")

    async with db_session() as db:
        for s in svc.schemes:
            existing = await db.execute(select(Scheme).where(Scheme.scheme_id == s["scheme_id"]))
            row = existing.scalar_one_or_none()
            if row is None:
                row = Scheme(
                    scheme_id=s["scheme_id"],
                    official_name=s["official_name"],
                    description=s["description"],
                    category=s["category"],
                    department=s.get("department"),
                    government_level=s["government_level"],
                    applicable_state=s.get("applicable_state"),
                    target_beneficiaries=s.get("target_beneficiaries", []),
                    benefit_description=s.get("benefit_description"),
                    benefit_amount=s.get("benefit_amount"),
                    benefit_frequency=s.get("benefit_frequency"),
                    required_documents=s.get("required_documents", []),
                    prerequisite_services=s.get("prerequisite_services", []),
                    application_url=s.get("application_url"),
                    official_contact=s.get("official_contact"),
                    scheme_status=s.get("scheme_status", "active"),
                    confidence_status=s.get("confidence_status", "needs_verification"),
                )
                db.add(row)
                await db.flush()
                # Add rules.
                for rule in s.get("rules", []):
                    db.add(SchemeRule(scheme_id=row.id, rule_type=rule["rule_type"], rule=rule["rule"], description=rule.get("description")))
                # Add sources.
                for src in s.get("sources", []):
                    db.add(SchemeSource(scheme_id=row.id, title=src["title"], url=src["url"], publisher=src.get("publisher")))
                print(f"  Inserted: {s['scheme_id']}")
            else:
                print(f"  Exists:   {s['scheme_id']}")
        await db.commit()

    print("Done.")


if __name__ == "__main__":
    asyncio.run(seed())
