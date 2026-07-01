.PHONY: dev dev-infra dev-api dev-ui dev-worker dev-workers dev-docker dev-langfuse dev-langfuse-fresh langfuse-dev-setup langfuse-setup-judge dev-obs dev-tool-gateway obs-reload test-batches domain-gate verify-architecture verify-import-boundaries arch-gate

dev-infra:
	docker compose up -d

dev-api:
	PROMETHEUS_MULTIPROC_DIR=$${PROMETHEUS_MULTIPROC_DIR:-/tmp/egregore-prom-multiproc} mkdir -p $${PROMETHEUS_MULTIPROC_DIR:-/tmp/egregore-prom-multiproc}
	PROMETHEUS_MULTIPROC_DIR=$${PROMETHEUS_MULTIPROC_DIR:-/tmp/egregore-prom-multiproc} uv run egregore serve --port 8080

dev-worker:
	PROMETHEUS_MULTIPROC_DIR=$${PROMETHEUS_MULTIPROC_DIR:-/tmp/egregore-prom-multiproc} mkdir -p $${PROMETHEUS_MULTIPROC_DIR:-/tmp/egregore-prom-multiproc}
	PROMETHEUS_MULTIPROC_DIR=$${PROMETHEUS_MULTIPROC_DIR:-/tmp/egregore-prom-multiproc} uv run egregore worker --daemon --idle-timeout 0

dev-workers:
	@replicas=$${WORKER_REPLICAS:-2}; \
	idle=$${WORKER_IDLE_TIMEOUT:-0}; \
	mpdir=$${PROMETHEUS_MULTIPROC_DIR:-/tmp/egregore-prom-multiproc}; \
	mkdir -p "$$mpdir"; \
	for i in $$(seq 1 $$replicas); do \
	  echo "Starting worker $$i/$$replicas..."; \
	  PROMETHEUS_MULTIPROC_DIR="$$mpdir" uv run egregore worker --daemon --idle-timeout $$idle & \
	done; \
	wait

dev-ui:
	cd ui && npm run dev

dev-langfuse:
	docker compose -f deploy/langfuse/docker-compose.yml up -d

langfuse-dev-setup:
	@chmod +x scripts/langfuse-dev-bootstrap.sh
	@./scripts/langfuse-dev-bootstrap.sh

langfuse-setup-judge:
	@chmod +x scripts/langfuse-setup-llm-judge.sh
	@./scripts/langfuse-setup-llm-judge.sh

# Reset Langfuse data and re-apply headless init (dev only)
dev-langfuse-fresh: langfuse-dev-setup
	docker compose -f deploy/langfuse/docker-compose.yml down -v
	docker compose -f deploy/langfuse/docker-compose.yml up -d
	@echo "Langfuse fresh install: http://localhost:3001 (dev@egregore.local / egregore-dev)"

dev-obs:
	@$(MAKE) -C ../.. cxado-up-obs

# Optional — not started by `make dev`; set USE_TOOL_GATEWAY=true in .env to route worker tools via gateway
dev-tool-gateway:
	uv run uvicorn interfaces.gateways.tool.server:create_app --factory --host 0.0.0.0 --port 8092

obs-reload:
	curl -fsS -X POST http://localhost:9091/-/reload

dev:
	@chmod +x scripts/dev.sh
	@./scripts/dev.sh

dev-docker:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile app up -d --build --scale worker=$${WORKER_REPLICAS:-2}

test-batches:
	@./scripts/pytest_batches.sh $(ARGS)

domain-gate:
	@./scripts/pytest_batches.sh tests/domain --cov --domain-gate

verify-architecture:
	@chmod +x scripts/verify_no_langfuse_in_core.sh
	@./scripts/verify_no_langfuse_in_core.sh
	@$(MAKE) verify-import-boundaries

verify-import-boundaries:
	@uv run python scripts/verify_import_boundaries.py

arch-gate:
	@./scripts/pytest_batches.sh tests/architecture
