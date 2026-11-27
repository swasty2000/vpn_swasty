import os
import httpx
from fastapi import FastAPI, HTTPException, Header

app = FastAPI(title="Swasty VPN Backend")

AWG_API_URL = "http://amneziawg:51821"
PANEL_PASSWORD = os.getenv("PASSWORD", "")
APP_TOKEN = os.getenv("API_SECRET_TOKEN", "")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "swasty-vpn-backend"}


@app.post("/api/get-config/{client_name}")
async def get_client_config(client_name: str, x_token: str = Header(None)):
    # Проверяем секретный токен, чтобы посторонние не могли забирать ключи
    if x_token != APP_TOKEN:
        raise HTTPException(status_code=401, detail="Неверный токен доступа")

    async with httpx.AsyncClient(base_url=AWG_API_URL) as client:
        # 1. Авторизуемся во внутренней панели AmneziaWG
        auth = await client.post("/api/session", json={"password": PANEL_PASSWORD})
        if auth.status_code != 200:
            raise HTTPException(status_code=500, detail="Ошибка авторизации в ядре VPN")

        # 2. Проверяем, есть ли уже ключ для этого друга
        clients_resp = await client.get("/api/wireguard/client")
        clients = clients_resp.json()
        existing = next((c for c in clients if c["name"] == client_name), None)

        # 3. Если ключа еще нет — создаем новый автоматически
        if not existing:
            create_resp = await client.post(
                "/api/wireguard/client", json={"name": client_name}
            )
            if create_resp.status_code != 200:
                raise HTTPException(status_code=500, detail="Не удалось создать ключ")
            clients_resp = await client.get("/api/wireguard/client")
            existing = next(
                (c for c in clients_resp.json() if c["name"] == client_name), None
            )

        # 4. Скачиваем готовый текст .conf файла и отдаем приложению
        conf_resp = await client.get(
            f"/api/wireguard/client/{existing['id']}/configuration"
        )
        return {"client": client_name, "config": conf_resp.text}