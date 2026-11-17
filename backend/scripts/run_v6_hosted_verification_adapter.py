"""Explicit isolated verifier process; never referenced by production startup.

Only launch AFTER separate target/account/source execution approval. This command
does not create accounts, targets, migrations, permissions or an enabling file.
"""

import argparse
import logging
import os
import subprocess
from pathlib import Path

import uvicorn

from app.core.config import Settings
from app.verification_v6 import VerificationManifest, create_verification_app
from scripts.verify_v6_hosted_auth import cli_management_token


def protect(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name == "nt":
        sid = (
            subprocess.check_output(
                ["whoami", "/user", "/fo", "csv", "/nh"], encoding="utf-8"
            )
            .strip()
            .split(",")[-1]
            .strip('"')
        )
        if not sid.startswith("S-1-"):
            raise RuntimeError("Unable to establish private directory owner")
        result = subprocess.run(
            [
                "icacls",
                str(directory),
                "/inheritance:r",
                "/grant:r",
                "*" + sid + ":(OI)(CI)F",
                "*S-1-5-18:(OI)(CI)F",
            ],
            capture_output=True,
            check=False,
        )
        if result.returncode:
            raise RuntimeError("Unable to protect synthetic verification journal")
    else:
        directory.chmod(0o700)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-approved-isolated-hosted-only", action="store_true")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--settings-file", type=Path, required=True)
    parser.add_argument("--journal-directory", type=Path, required=True)
    parser.add_argument("--enabling-file", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8017)
    args = parser.parse_args()
    if not args.execute_approved_isolated_hosted_only or not 1024 <= args.port <= 65535:
        parser.error("Explicit approved isolated execution is required")
    manifest = VerificationManifest.model_validate_json(args.manifest.read_text())
    if args.enabling_file.read_text().strip() != manifest.digest():
        parser.error("Independent enabling file does not match manifest")
    protect(args.journal_directory)
    settings = Settings(_env_file=args.settings_file)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    app = create_verification_app(
        settings,
        manifest,
        management_token=cli_management_token(),
        journal_directory=args.journal_directory,
        kill_file=args.enabling_file,
    )
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=args.port,
        workers=1,
        access_log=False,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
