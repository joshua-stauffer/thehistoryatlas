import boto3
from botocore.config import Config as Boto3Config
from pydantic import HttpUrl
from pydantic_settings import BaseSettings


class StorageSettings(BaseSettings):
    STORAGE_ENDPOINT_URL: HttpUrl
    STORAGE_REGION: str
    STORAGE_KEY: str
    STORAGE_SECRET: str
    STORAGE_MODEL_BUCKET: str


class Storage:
    def __init__(self):
        session = boto3.session.Session()
        self._config = StorageSettings()
        self._client = session.client(
            service_name="s3",
            endpoint_url=self._config.STORAGE_ENDPOINT_URL,
            config=Boto3Config(s3={"addressing_style": "virtual"}),
            region_name=self._config.STORAGE_REGION,
            aws_access_key_id=self._config.STORAGE_KEY,
            aws_secret_access_key=self._config.STORAGE_SECRET,
        )

    def get_objects(self, source: str, dest: str) -> None:
        self._client.download_file(self._config.STORAGE_MODEL_BUCKET, source, dest)

    def list_objects(self) -> list[str]:
        response = self._client.list_objects(Bucket=self._config.STORAGE_MODEL_BUCKET)
        return [obj["Key"] for obj in response["Contents"]]
