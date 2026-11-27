import os
import subprocess
import tempfile
import requests
from pathlib import Path


class VPNManager:
    def __init__(self, server_url: str, api_token: str, client_name: str):
        self.server_url = server_url.rstrip("/")
        self.api_token = api_token
        self.client_name = client_name
        # Имя сетевого туннеля в Windows
        self.tunnel_name = "swasty_awg"
        self.config_path = Path(tempfile.gettempdir()) / f"{self.tunnel_name}.conf"
        # Стандартный путь к установленному движку AmneziaWG на Windows
        self.awg_exe = Path(r"C:\Program Files\AmneziaWG\amneziawg.exe")

    def fetch_config(self) -> str:
        """Запрашивает персональный конфиг с вашего бэкенда."""
        url = f"{self.server_url}/api/get-config/{self.client_name}"
        headers = {"x-token": self.api_token}

        response = requests.post(url, headers=headers, timeout=10)
        if response.status_code == 401:
            raise PermissionError("Неверный секретный токен доступа")
        response.raise_for_status()

        data = response.json()
        return data["config"]

    def connect(self) -> str:
        """Скачивает ключ, сохраняет его и поднимает системный туннель."""
        if not self.awg_exe.exists():
            raise FileNotFoundError(
                "Не найден движок AmneziaWG. Установите клиент AmneziaWG для Windows."
            )

        config_text = self.fetch_config()
        self.config_path.write_text(config_text, encoding="utf-8")

        # Устанавливаем и запускаем туннель как службу Windows
        subprocess.run(
            [str(self.awg_exe), "/installtunnelservice", str(self.config_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        return self.get_current_ip()

    def disconnect(self):
        """Останавливает туннель и удаляет временный ключ с диска."""
        if self.awg_exe.exists():
            subprocess.run(
                [str(self.awg_exe), "/uninstalltunnelservice", self.tunnel_name],
                capture_output=True,
                text=True,
            )
        if self.config_path.exists():
            self.config_path.unlink()

    @staticmethod
    def get_current_ip() -> str:
        """Проверяет текущий внешний IP-адрес после подключения."""
        try:
            resp = requests.get("https://ipify.org", timeout=5)
            return resp.json().get("ip", "Unknown")
        except Exception:
            return "Connected (IP hidden)"
