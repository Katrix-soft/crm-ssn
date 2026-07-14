import pexpect
import sys

child = pexpect.spawn('python3 test_api.py --live --url http://localhost:8000', encoding='utf-8')
child.expect('Seleccione una opción:')
child.sendline('2')
child.expect('Usuario:')
child.sendline('broker')
child.expect('Contraseña:')
child.sendline('password123')
child.expect('Seleccione una opción:')
child.sendline('4')
child.expect('Seleccione una opción:')
child.sendline('0')
print(child.before)
