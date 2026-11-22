from datetime import timedelta
from typing import Final

DOMAIN: Final = "urban_arrow"
MANUFACTURER: Final = "Urban Arrow"

CONF_TOKEN: Final = "token"

# Telemetry is reported by the bike's module every few minutes at best while riding,
# and much less often when parked, so polling faster gains nothing.
SCAN_INTERVAL: Final = timedelta(minutes=5)
