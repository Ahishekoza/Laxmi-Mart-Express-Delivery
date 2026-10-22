"""
Model package.

Every ORM model module (added in a later plan) must be imported here once
it exists, so that `Base.metadata` is complete before Alembic
`--autogenerate` runs. Empty for now — this plan only establishes the
connection/session layer, not the business tables.
"""
