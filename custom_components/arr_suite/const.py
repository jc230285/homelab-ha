DOMAIN = "arr_suite"

ARR_TYPES = ["sonarr", "radarr", "lidarr", "prowlarr"]

DEFAULT_SCAN_INTERVAL = 60       # seconds
CALENDAR_SCAN_INTERVAL = 300     # seconds
REQUEST_TIMEOUT = 10             # seconds

CONF_ARR_TYPE = "arr_type"
CONF_API_KEY = "api_key"

# API paths per arr type
API_PATHS = {
    "sonarr":   {"base": "/api/v3", "calendar": "/api/v3/calendar"},
    "radarr":   {"base": "/api/v3", "calendar": "/api/v3/calendar"},
    "lidarr":   {"base": "/api/v1", "calendar": "/api/v1/calendar"},
    "prowlarr": {"base": "/api/v1", "calendar": None},
}
