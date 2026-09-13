# Railway deployment

BLACK PEARL is deployed as three Railway services from this repository:

| Service | Dockerfile | Public access |
| --- | --- | --- |
| P1 | `Dockerfile.p1` | Private |
| P2 | `Dockerfile.p2` | Private |
| Gateway | `Dockerfile.gateway` | Public |

Create one Railway service for each Dockerfile and set the service Dockerfile
path in its settings. Do not create public domains for P1 or P2. Only the
Gateway service should receive a Railway public domain.

## Service configuration

The Gateway must receive these variables:

```text
P1_BASE_URL=http://<p1-private-host>:<p1-port>
P2_BASE_URL=http://<p2-private-host>:<p2-port>
```

Use the private hostnames and listening ports Railway shows for the P1 and P2
services. Do not use `localhost` or `127.0.0.1`; each service runs in its own
container. The Gateway listens on Railway's injected `PORT` value.

P1 requires no application variables. P2 may use:

```text
P2_DATABASE_PATH=/data/p2_compliance.db
```

Attach a Railway volume to the P2 service at `/data` so its SQLite audit
database survives redeployments. No PostgreSQL service or application secrets
are required by this repository.

Configure the Gateway health check as `GET /healthz`. That endpoint checks both
private upstream services and therefore confirms the complete request path.

## Local verification

The complete topology can be smoke-tested locally with:

```powershell
docker compose up --build
```

The Gateway is available at `http://127.0.0.1:8080`; P1 and P2 are reachable
only on the Compose network because their services use `expose`, not `ports`.
