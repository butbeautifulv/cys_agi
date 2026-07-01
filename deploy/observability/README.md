# Dev observability stack (Prometheus + Grafana + Tempo)

**Preferred:** use the unified cxado observability stack from the meta-repo root:

```bash
# full default stack (veil + egregore infra + obs)
make -C ../.. cxado-up

# observability only
make dev-obs   # delegates to: make -C ../.. cxado-up-obs
```

Config and dashboards live in **`../../deploy/observability/`** (cxado root).

## Endpoints

| Service | URL | Notes |
|---------|-----|-------|
| Prometheus | http://localhost:9091 | Unified scrape: egregore + veil |
| Grafana | http://localhost:3002 | login `admin` / `admin` |
| CXado Overview | http://localhost:3002/d/cxado-overview | Platform dashboard |
| Tempo | http://localhost:3200 | Trace query API |
| Tempo OTLP | localhost:4317 | gRPC when `OTEL_ENABLED=true` |

Run `make dev` on the host so Prometheus can reach `host.docker.internal:8080/metrics`.

Reload Prometheus after config edit: `make -C ../.. cxado-obs-reload`

## Legacy local compose

`deploy/observability/docker-compose.yml` in this repo remains for standalone egregore-only dev; new work should target cxado `deploy/observability/`.
