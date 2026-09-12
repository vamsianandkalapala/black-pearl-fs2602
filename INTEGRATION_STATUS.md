# Integration Status

## Verified in the current workspace

- P1 is the authoritative decision engine.
- P2 is vendored as the complete persistent SQLite compliance service under
  `services/p2`.
- P1-to-P2 HTTP persistence, audit verification, and replay returned success.
- A gateway now forwards decisions to P1 and snapshots to P2.
- A minimal browser client now displays the gateway's real response.
- A P1 rulebook display endpoint exists at `GET /rules/{version}`.
- Dockerfiles exist for P1, P2, and the gateway, plus a Compose file with a
  named persistent P2 volume.
- Final local process verification passed on isolated ports: P1 `8200`, P2
  `8201`, and gateway/frontend `8202`.
- The gateway health check returned HTTP 200 for both P1 and P2.
- A real gateway decision returned HTTP 200, P1 `APPROVED`, and P2
  `RECORDED`.
- Audit verification returned `VALID`; historical replay returned `MATCH`.
- After restarting P2 with the same SQLite file, audit verification remained
  `VALID` and replay remained `MATCH`.
- Repeating the same decision request returned the same decision ID and
  snapshot hash.

## Not yet verified or implemented

- A PostgreSQL adapter or migration system.
- A public deployment provider or HTTPS URL.
- Docker image builds and Compose startup, because Docker is unavailable on the
  verification machine.
- PostgreSQL production deployment.

## Honest boundary

The delivered frontend is intentionally lightweight and uses the real gateway.
It does not calculate decisions locally and does not claim public deployment.
P2 is included in the repository; PostgreSQL and public deployment remain
unverified.

## Final local integration verification

- Integrated test suite: **76 passed, 2 warnings**.
- Compileall: passed for `backend`, `gateway`, `services`, `tests`, and
  `scripts`.
- Frontend serving: HTTP 200; page contains `BLACK PEARL` and calls the real
  `/decision` endpoint.
- Frontend static-code check: no local score, probability, decision ID,
  snapshot hash, audit hash, or random decision generation.
- P1 health: HTTP 200 with `{"status":"ok"}`.
- P2 health: HTTP 200 with SQLite service status.
- Gateway health: HTTP 200 with successful P1 and P2 health responses.
- Decision request: HTTP 200; authoritative P1 decision `APPROVED`; P2
  snapshot status `RECORDED`.
- Audit verification: HTTP 200, status `VALID`.
- Historical replay: HTTP 200, status `MATCH`.
- Repeated request: identical decision ID and snapshot hash.
- P2 restart with retained database: health HTTP 200, audit `VALID`, replay
  `MATCH`.
- Docker: unavailable; build and Compose startup are unverified.
- PostgreSQL: not implemented or tested.
- Public deployment: not performed.
