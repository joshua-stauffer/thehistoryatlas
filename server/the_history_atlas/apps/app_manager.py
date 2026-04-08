from the_history_atlas.apps.accounts.accounts_app import AccountsApp
from the_history_atlas.apps.config import Config
from the_history_atlas.apps.database import DatabaseApp
from the_history_atlas.apps.history import HistoryApp
import logging
import atexit

log = logging.getLogger(__name__)


class AppManager:
    config_app: Config
    database_app: DatabaseApp
    accounts_app: AccountsApp
    history_app: HistoryApp

    def __init__(self, config_app: Config):
        self.config_app = config_app
        self.database_app = DatabaseApp(config_app=self.config_app)
        self.accounts_app = AccountsApp(
            config=self.config_app, database_client=self.database_app.client()
        )
        self.history_app = HistoryApp(
            config_app=self.config_app,
            database_client=self.database_app.client(),
        )

        # Prime the cache and start the refresh thread
        try:
            log.info("Initializing default story cache")
            self.history_app.prime_cache(cache_size=100)
            self.history_app.start_cache_refresh(
                refresh_interval_seconds=3600
            )  # Refresh every hour

            # Register cleanup function to stop the thread on application shutdown
            atexit.register(self._cleanup)
        except Exception as e:
            log.error(f"Failed to initialize cache: {e}")

    def _cleanup(self):
        """Clean up resources when the application shuts down"""
        log.info("Shutting down AppManager, stopping cache refresh thread")
        try:
            self.history_app.stop_cache_refresh()
        except Exception as e:
            log.error(f"Error during cleanup: {e}")
