import sys
sys.path.append("api-crm")
import ssn_test as db

res = db.validar_licencia(
    clave="KTX-CRM-DQUK-LEGD-73A2",
    dispositivo_id="test-device-id",
    email_cliente="",
    dispositivo_nombre="test-device-name",
    ip_address="127.0.0.1"
)
print("Result with empty email:", res)

res2 = db.validar_licencia(
    clave="KTX-CRM-DQUK-LEGD-73A2",
    dispositivo_id="test-device-id",
    email_cliente="broker@katrix.com",
    dispositivo_nombre="test-device-name",
    ip_address="127.0.0.1"
)
print("Result with broker@katrix.com email:", res2)

res3 = db.validar_licencia(
    clave="KTX-CRM-DQUK-LEGD-73A2",
    dispositivo_id="test-device-id",
    email_cliente="exe20230909@gmail.com",
    dispositivo_nombre="test-device-name",
    ip_address="127.0.0.1"
)
print("Result with exe20230909@gmail.com email:", res3)
