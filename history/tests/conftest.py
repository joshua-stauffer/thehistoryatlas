import sys


class MockBroker:
    def __init__(self, *args, **kwargs):
        pass


class MockHistoryConfig:
    """minimal class for setting up an in memory db for this test"""

    def __init__(self):
        self.DB_URI = "sqlite+pysqlite:///:memory:"
        self.DEBUG = False  # outputs all activity


broker_module = type(sys)("broker")
broker_module.Broker = MockBroker
sys.modules["broker"] = broker_module

# config_module = type(sys)('history_config')
# config_module.HistoryConfig = MockHistoryConfig
# sys.modules['history_config'] = config_module
