import requests

url = "http://127.0.0.1:8000/licencias/validar"
payload = {
    "clave": "KTX-CRM-DQUK-LEGD-73A2",
    "dispositivo_id": "test-device-id",
    "email_cliente": "",
    "dispositivo_nombre": "test-device-name"
}

try:
    res = requests.post(url, json=payload)
    print("Status code:", res.status_code)
    print("Response JSON:", res.json())
except Exception as e:
    print("Error:", e)
