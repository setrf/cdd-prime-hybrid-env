#!/usr/bin/env python3
"""Contract check for Prime OpenAPI snapshot used by this repo."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_PATH_METHODS: dict[str, set[str]] = {
    "/api/v1/pods/": {"get", "post"},
    "/api/v1/evaluations/": {"get", "post"},
    "/api/v1/evaluations/{evaluation_id}": {"get", "put", "delete"},
    "/api/v1/images/build": {"post"},
    "/api/v1/sandbox": {"get", "post", "delete"},
    "/api/v1/user/whoami": {"get"},
}

REQUIRED_SCHEMAS = {
    "APIPodConfig",
    "CreateEvaluationRequest",
    "CreateEvaluationResponse",
    "CreateSandboxRequest",
    "BuildImageRequest",
    "WhoamiResponse",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Prime OpenAPI contract checker")
    p.add_argument("--openapi", default="primeintellect_openapi.json")
    p.add_argument("--min-paths", type=int, default=30)
    p.add_argument("--min-schemas", type=int, default=60)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    obj = json.loads(Path(args.openapi).read_text())
    errors: list[str] = []

    openapi_version = str(obj.get("openapi", ""))
    if not openapi_version.startswith("3."):
        errors.append(f"unexpected openapi version: {openapi_version}")

    paths = obj.get("paths")
    if not isinstance(paths, dict):
        errors.append("missing paths object")
        paths = {}

    schemas = obj.get("components", {}).get("schemas", {})
    if not isinstance(schemas, dict):
        errors.append("missing components.schemas object")
        schemas = {}

    if len(paths) < args.min_paths:
        errors.append(f"path count too small: {len(paths)} < {args.min_paths}")
    if len(schemas) < args.min_schemas:
        errors.append(f"schema count too small: {len(schemas)} < {args.min_schemas}")

    for path, expected_methods in REQUIRED_PATH_METHODS.items():
        ops = paths.get(path)
        if not isinstance(ops, dict):
            errors.append(f"missing required path: {path}")
            continue
        methods = {m.lower() for m in ops.keys()}
        missing = expected_methods - methods
        if missing:
            errors.append(f"path {path} missing methods: {sorted(missing)}")

    missing_schemas = sorted(REQUIRED_SCHEMAS - set(schemas.keys()))
    if missing_schemas:
        errors.append(f"missing schemas: {missing_schemas}")

    if errors:
        print("OPENAPI CONTRACT CHECK FAILED")
        for e in errors:
            print(f"- {e}")
        raise SystemExit(1)

    print("OPENAPI CONTRACT CHECK PASSED")
    print(f"openapi_version={openapi_version} paths={len(paths)} schemas={len(schemas)}")


if __name__ == "__main__":
    main()
