# PAL auth broker

Holds one Widen token per superuser for the PAL uploader page. The browser
asks for the signed-in person's token once, then uploads the GeoTIFF directly
to Widen. No file bytes pass through this service.

The "Upload as" list is whoever has a key configured. Adding a person later
is env vars only, after Molly issues their key:

```
PAL_OPERATORS=aaron|Aaron Doucett,seve|Seve Name
PAL_TOKEN_AARON=planet/...
PAL_TOKEN_SEVE=planet/...
```

An id with no `PAL_TOKEN_<ID>` is left off the list. `aaron` falls back to
`ACQUIA_API_TOKEN` when `PAL_TOKEN_AARON` is unset.

`PAL_GATE` is the passphrase the browser sends on `/api/operators` and
`/api/token`. Nothing secret belongs in this repository.
