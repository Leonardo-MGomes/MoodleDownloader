from requests import Session
import re

from .models import Resource
from .config import AppConfig, DEFAULT_CONFIG


class MoodleDownloader:
    def __init__(self, session: Session, app_config: AppConfig = DEFAULT_CONFIG):
        self.session = session
        self.base_url = app_config.BASE_URL
        self.user_agent = app_config.USER_AGENT

    def _get_download_url(self, resource: Resource) -> str:
        return f"{self.base_url}/mod/{resource.Type.value}/view.php?id={resource.Id}"

    def download_resource(self, resource: Resource) -> str:
            with self.session.get(self._get_download_url(resource), stream=True) as r:
                r.raise_for_status()
                filename = re.findall(r'filename="([^"]+)"', r.headers['Content-Disposition'])[0]
                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=16*1024):
                        f.write(chunk)
            return filename
