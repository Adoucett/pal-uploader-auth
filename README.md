# PAL auth broker

Holds the Widen token for the PAL uploader page. The browser asks for the token
once, then uploads the GeoTIFF directly to Widen. No file bytes pass through
this service.

Secrets live in Render environment variables (`ACQUIA_API_TOKEN`, `PAL_GATE`,
optional `MAPBOX_ACCESS_TOKEN`). Nothing secret belongs in this repository.
