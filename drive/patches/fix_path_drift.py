"""Compatibility entry point for administrator-only, database-only path repair."""

from drive.utils.maintenance import inspect_paths


def execute():
    return inspect_paths(apply=True)
