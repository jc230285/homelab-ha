import pytest

SONARR_STATUS = {"appName": "Sonarr", "version": "3.0.0"}
SONARR_QUEUE = {"totalRecords": 3, "records": []}
SONARR_WANTED = {"totalRecords": 12, "records": []}
SONARR_CUTOFF = {"totalRecords": 5, "records": []}
SONARR_HEALTH = []  # empty = healthy
SONARR_CALENDAR = [
    {
        "title": "Severance",
        "seasonNumber": 2,
        "episodeNumber": 8,
        "airDateUtc": "2026-05-02T21:00:00Z",
        "hasFile": False,
    }
]
