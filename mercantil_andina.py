import os
import time
import httpx
from typing import Any

class MercantilAndinaError(Exception):
    def __init__(self, status_code: int, detail: Any):
        self.status_code = status_code
        self.detail = detail
        super().__init__(str(detail))

class MercantilAndinaClient:
    def __init__(self):
        self.base_url = os.getenv("MERCANTIL_API_BASE_URL", "https://apidev.mercantilandina.com.ar").rstrip("/")
        self.subscription_key = os.getenv("MERCANTIL_API_SUBSCRIPTION_KEY", "")
        self.client_id = os.getenv("MERCANTIL_API_CLIENT_ID", "api-clientes-login")
        self.login_user = os.getenv("MERCANTIL_API_LOGIN_USER", "JCORGTST")
        self.login_pass = os.getenv("MERCANTIL_API_LOGIN_PASS", "jcor2026")

        self._token = None
        self._expires = 0
        self._token_expires_at = 0

    async def _login(self):
        url = f"{self.base_url}/credenciales/v2"

        headers = {
            "Ocp-Apim-Subscription-Key": self.subscription_key,
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "client_id": self.client_id,
            "grant_type": "password",
            "username": self.login_user,
            "password": self.login_pass,
        }

        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(url, headers=headers, data=data)

        if r.status_code != 200:
            raise MercantilAndinaError(r.status_code, r.text)

        j = r.json()

        self._token = j["access_token"]
        self._expires = time.time() + int(j.get("expires_in", 3600)) - 60
        self._token_expires_at = self._expires

    async def _token_ok(self):
        if self._token is None or time.time() >= self._expires:
            await self._login()
        return self._token
    
    async def get_token(self):
        return await self._token_ok()

    async def _request(self, method, path, params=None, json_body=None):
        token = await self._token_ok()

        headers = {
            "Authorization": f"Bearer {token}",
            "Ocp-Apim-Subscription-Key": self.subscription_key,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.request(
                method,
                self.base_url + path,
                params=params,
                json=json_body,
                headers=headers,
            )

        if r.status_code >= 400:
            try:
                err = r.json()
            except Exception:
                err = r.text
            raise MercantilAndinaError(r.status_code, err)

        return r.json()

    # --- VEHICULOS ---
    async def obtener_marcas(self):
        return await self._request("GET", "/vehiculos/v1/marcas")

    async def obtener_vehiculo(self, codigo):
        return await self._request("GET", f"/vehiculos/v1/{codigo}")

    async def obtener_infoauto(self, codigo):
        return await self._request("GET", "/vehiculos/v1/infoauto", params={"codigo": codigo})

    async def obtener_modelos_por_marca(self, marca, anio=2020, tipo="AUTO", offset=1, limit=100):
        return await self._request("GET", "/vehiculos/v1", params={
            "q": marca.lower(),
            "anio": anio,
            "tipo": tipo,
            "offset": offset,
            "limit": limit,
        })

    # --- COTIZACION ---
    async def cotizar_auto(self, payload):
        return await self._request("POST", "/coti-ins-emi/v1/cotizacion/auto", json_body=payload)

    async def cotizar_moto(self, payload):
        return await self._request("POST", "/coti-ins-emi/v1/cotizacion/moto", json_body=payload)

    # --- PRODUCTORES Y CARTERA ---
    async def obtener_productores(self):
        return await self._request("GET", "/productores/v1/")

    async def get_operaciones(self, cuenta_id, desde, hasta, size=50, page=1):
        params = {
            "cuentas": cuenta_id,
            "desde": desde,
            "hasta": hasta,
            "size": size,
            "page": page
        }
        return await self._request("GET", "/cartera/v1/operaciones", params=params)

    # --- CLIENTES ---
    async def get_cliente_por_doc(self, dni, sexo="M"):
        params = {
            "dni": dni,
            "sexo": sexo
        }
        return await self._request("GET", "/clientes/v1/personas", params=params)

    async def get_cliente_por_cuit(self, cuit):
        return await self._request("GET", "/clientes/v1/personas", params={"CUIT": cuit})

    # --- POLIZAS ---
    async def get_poliza_detalle(self, poliza, endoso=0):
        return await self._request("GET", f"/polizas/v1/{poliza}/{endoso}")

