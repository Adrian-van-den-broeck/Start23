"""Railway scheduled command for bounded Polar import retries."""

import asyncio
import logging

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.modules.integrations.polar import PolarAccessLinkClient
from app.modules.integrations.repository import SupabaseIntegrationRepository
from app.modules.integrations.service import IntegrationService


async def run() -> int:
    """Claim and process one bounded retry batch in the existing monolith."""
    settings = get_settings()
    configure_logging(settings.log_level)
    repository = SupabaseIntegrationRepository(settings)
    provider = PolarAccessLinkClient(settings)
    service = IntegrationService(repository, provider, settings)
    try:
        completed = await service.retry_due_imports(limit=20)
        logging.getLogger(__name__).info(
            "Polar import retry batch completed",
            extra={"event": "polar_import_retry_batch_completed", "count": completed},
        )
        return completed
    finally:
        await asyncio.gather(repository.aclose(), provider.aclose())


def main() -> None:
    """Console entry point used by a Railway cron service."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
