# Kiosco App

Esta guia deja documentado:

- como ejecutar la app
- como funciona el nuevo sistema de licencias por instalacion
- como configurar Google Sheets como backend simple
- como generar el `.exe`

## 1. Requisitos

- Windows 10 u 11
- Python 3.12 recomendado
- `pip`

## 2. Instalar dependencias

Abri PowerShell dentro de la carpeta del proyecto y ejecuta:

```powershell
python -m pip install openpyxl pyinstaller
```

`openpyxl` se usa para exportar reportes a Excel y `pyinstaller` para generar el `.exe`.

## 3. Ejecutar la app en desarrollo

```powershell
python main.py
```

## 4. Sistema de licencias

La app ya no usa claves compartibles. Ahora funciona con un `id_instalacion` unico por cada instalacion.

Flujo:

1. La app genera un UUID la primera vez.
2. Ese ID se guarda localmente en una carpeta oculta del sistema.
3. Si la instalacion no esta activa, la app muestra el ID.
4. El cliente o revendedor te pasa ese ID.
5. Vos lo agregas manualmente en Google Sheets con estado `activa` o `bloqueada`.
6. La app consulta online esa planilla.
7. Si esta `activa`, entra.
8. Si no existe o esta `bloqueada`, no entra.

## 5. Donde se guarda el ID y la cache

En Windows, la informacion de licencia se guarda fuera de la carpeta del proyecto, en una ruta similar a:

```text
%LOCALAPPDATA%\KioscoApp\System\
```

Archivos usados:

- `install.bin`: guarda el `id_instalacion`
- `license_cache.bin`: guarda el ultimo resultado de validacion

Eso ayuda a que copiar solamente `KioscoApp.exe + data` no copie tambien la activacion.

## 6. Estructura del Google Sheet

Crea una hoja dedicada a licencias con estas columnas:

```text
id_instalacion | estado | fecha_opcional
```

Ejemplo:

```text
6de7b2f8-1d10-4e6d-a4e8-f9d0a6d29e33 | activa    | 2026-04-10
8d30f7c0-6b6a-42e0-9d8e-5a3ad3fca2d1 | bloqueada | 2026-04-10
```

Reglas simples:

- `estado=activa` habilita la app
- cualquier otro valor se toma como bloqueado
- idealmente usa una sola fila por ID
- si repetis un ID, la app toma la ultima coincidencia del CSV

## 7. Como conectar Google Sheets

La implementacion actual usa la opcion mas simple: un CSV publico de Google Sheets.

Pasos:

1. Crea la hoja con las columnas indicadas.
2. En Google Sheets, publica esa hoja en formato CSV.
3. La URL del CSV ya queda hardcodeada dentro de `modules/licencia.py`.
4. Si algun dia quieres cambiar esa URL, hay que editar el codigo y recompilar.

Parametros fijos actuales:

- `google_sheet_csv_url`: URL publica del CSV de Google Sheets embebida en el codigo
- `cache_horas`: 12
- `offline_grace_days`: 3
- `timeout_segundos`: 8

## 8. Comportamiento online y offline

Al iniciar:

- si el ID existe y esta `activa` en la planilla, la app entra
- si el ID no existe, la app se bloquea
- si el ID esta `bloqueada`, la app se bloquea

Modo offline:

- si hubo una validacion online exitosa previa, la app permite seguir hasta `offline_grace_days`
- si nunca hubo validacion online correcta, la app no entra

Cache:

- si la ultima validacion OK fue hace menos de `cache_horas`, se reutiliza cache
- esto reduce dependencia de internet
- si queres que un bloqueo pegue mas rapido, baja `cache_horas`

## 9. Comandos utiles de licencia

Mostrar el ID local:

```powershell
python -m modules.licencia --id
```

Forzar una validacion y ver el estado:

```powershell
python -m modules.licencia --estado
```

## 10. Tests automativos

```powershell
python -m compileall main.py modules ui tests
python -m unittest discover -s tests -p "test_*.py" -v
```

## 11. Generar el `.exe`

```powershell
pyinstaller KioscoApp.spec
```

El ejecutable queda en:

```text
dist\KioscoApp.exe
```

## 12. Carpeta final para entregar

Para usar el sistema fuera del proyecto, arma una carpeta final con esta estructura:

```text
KioscoApp/
|-- KioscoApp.exe
`-- data/
```

La carpeta `data` sigue siendo necesaria para:

- productos
- ventas
- empleados
- clientes
- deudas
- turnos
- registros

## 13. Regla importante

Respeta siempre esto:

- `KioscoApp.exe` y `data\` deben viajar juntos

Y ademas:

- la activacion no vive dentro de `data`
- una instalacion nueva genera otro `id_instalacion`
- la URL del backend ya no esta en un archivo editable externo

## 14. Backup

Para guardar datos del negocio, alcanza con copiar la carpeta `data\`.

Para que una instalacion siga activada en la misma maquina, no borres `%LOCALAPPDATA%\KioscoApp\System\`.

## 15. Resumen operativo

Para vos, el flujo diario queda asi:

1. El cliente abre la app y ve su `id_instalacion`.
2. Te envia ese ID.
3. Vos lo pegas en Google Sheets.
4. Le pones `activa`.
5. El cliente toca `Reintentar`.
6. Si deja de pagar, cambias `estado` a `bloqueada`.

Eso te da un esquema simple tipo SaaS basico sin base de datos propia.

## 16. Seguridad realista

Sacar `licencia_config.json` evita que un cliente comun cambie la URL o los tiempos desde un archivo visible.

Igual conviene tener presente esto:

- si entregas `main.py` y los modulos fuente, alguien tecnico igual puede modificar el codigo
- si entregas `.exe` compilado con PyInstaller, se vuelve bastante menos trivial tocarlo
- no existe proteccion perfecta en una app de escritorio offline, pero si puedes subir bastante la dificultad
