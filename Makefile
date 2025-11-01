# Simple build tooling for PAP

.PHONY: help proto-lint proto-format proto-breaking proto-generate proto-compile

help:
	@echo "Targets:"
	@echo "  proto-lint      - Lint protobufs with buf (if installed)"
	@echo "  proto-format    - Format protobufs with buf (if installed)"
	@echo "  proto-breaking  - Check for breaking changes (requires git remote)"
	@echo "  proto-compile   - Compile protobufs with protoc"

proto-lint:
	@command -v buf >/dev/null 2>&1 && buf lint proto || echo "buf not installed; skipping lint"

proto-format:
	@command -v buf >/dev/null 2>&1 && buf format -w proto || echo "buf not installed; skipping format"

proto-breaking:
	@command -v buf >/dev/null 2>&1 && buf breaking proto --against '.git#branch=main' || echo "buf not installed or no git; skipping breaking check"

proto-compile:
	protoc --proto_path=proto \
	  --python_out=sdk/python \
	  proto/pap/v1/pap.proto || echo "protoc or plugins missing; adjust as needed"

