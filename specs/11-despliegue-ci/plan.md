# PLAN-11 — Plan técnico de implementación de SPEC-11

| Campo | Valor |
| --- | --- |
| **Spec** | `specs/11-despliegue-ci/spec.md` (v1.0.0, `APROBADO` el 2026-11-22) |
| **Estado del plan** | `APROBADO` — 2026-11-22 por el Perfil 1 (v1.0.0) |
| **Perfil** | 1 |
| **Entrega** | Fase A: un PR de backend y uno de frontend · Fase B: un PR de backend y uno de frontend · Fase C: un PR de backend (código de `core` y `deploy/`) y un PR de Docs (guías) · después, la instalación en la máquina (sin PR) |

---

## 1. Punto de partida (`develop` al 2026-11-21: backend `d5c38f7`, frontend `5d1278d`)

| Elemento | Situación | Impacto en el plan |
| --- | --- | --- |
| Migraciones | Cabeza única: `0020_notifications_portada` | La Fase C agrega `0021_core_envios_correo` (§5.4). Si otra migración entra antes, la nuestra cuelga de la cabeza vigente al abrir el PR (regla de C19) |
| `downgrade` | Nunca se corrió `downgrade base` sobre la cadena completa | T-01 lo prueba antes de escribir la CI. Si alguna migración no baja, se registra como DT y se avisa a su perfil **antes** de activar el paso en la CI (no se arregla un módulo ajeno) |
| `app/core/email.py` | `enviar_correo(tipo, destinatario, contexto, usuario_id=…)` sin sesión de base; manda con `smtplib` en un hilo; backends `smtp` y `memoria` | El límite diario necesita un contador compartido entre la API y `tareas` (procesos distintos): va en la base (§5.4) |
| `app/main.py` | `/health` fijo; FastAPI con `/docs` siempre; CORS desde `settings` | `ENTORNO`, `/health/db` y el middleware de cabeceras de proxy (§5.1…§5.3) |
| `users/router.py:225` | `request.client.host` para RN-54 | No se toca: el middleware hace que `client.host` sea la IP real |
| `tests/conftest.py` | Cliente httpx con `ASGITransport` | `ASGITransport(client=(ip, puerto))` permite probar el middleware de proxy sin uvicorn (AC-P14) |
| `requirements.txt` | `uvicorn[standard]` sin versión mínima | Se fija `uvicorn[standard]>=0.30` (CIDR en `forwarded_allow_ips`) |
| Frontend | `npm ci` con `package-lock.json`; `vite.config.ts` con plugins de Figma que sólo actúan en `serve` | El build de producción no los necesita; no se tocan |

---

## 2. Ramas y orden de entrega

| Orden | Fase | Backend | Frontend | Docs | Depende de |
| --- | --- | --- | --- | --- | --- |
| 1 | A | `feat/docker` | `feat/docker` | — | — |
| 2 | B | `feat/ci` | `feat/ci` | — | A mergeada (la CI construye las imágenes) |
| 3 | C (código) | `feat/produccion` | — | — | A. Puede avanzar en paralelo con B |
| 4 | C (guías) | — | — | `docs/spec-11-guias` | C (código) mergeada |
| 5 | C (instalación) | — | — | Registro en `MEMORY.md` | P-01 y P-02 respondidas; tag `v2026.12.1` en `main` |

Los PRs van a `develop`. Para las pruebas de diciembre, `develop` se integra en `main` y se taggea (RN-P09); esa integración la hace el Perfil 1 con el pedido explícito del equipo.

---

## 3. Dependencias nuevas

| Dónde | Dependencia | Motivo |
| --- | --- | --- |
| `requirements.txt` | `uvicorn[standard]>=0.30` (ya está, se fija el mínimo) | `ProxyHeadersMiddleware` con redes en CIDR |
| Imagen del backend | `postgresql-client-16` y `age` (paquetes de Debian) | `pg_dump`, `pg_restore` y cifrado de copias en `tareas` |
| Imagen del backend | `supercronic` (binario con su suma SHA-256 verificada en el `Dockerfile`) | Cron sin root (D-07) |
| Imagen del backend | `rclone` (paquete de Debian) | Subida de copias a R2 (D-13) |
| Compose | `cloudflare/cloudflared` con versión fija | Túnel (D-11) |
| Máquina | Docker Engine y Compose v2 (repositorio oficial de Docker), Tailscale | D-01, D-16 |

Ninguna dependencia nueva de Python en la aplicación.

---

## 4. Fase A — Contenedores

### 4.1 Archivos (backend, `feat/docker`)

| Archivo | Acción | Contenido |
| --- | --- | --- |
| `Dockerfile` | Crear | Etapa `base` (`python:3.12-slim`, usuario `app` uid 10001, `PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED`); etapa `deps` (`pip install --no-cache-dir -r requirements.txt` en un venv `/opt/venv`); etapa `final` (venv + `app/`, `alembic/`, `alembic.ini`; `USER app`; `EXPOSE 8000`; `HEALTHCHECK` con `python -c` contra `/health`, sin instalar `curl`; `CMD` uvicorn de spec §4.1). Una etapa `dev` agrega `requirements-dev.txt` para el compose de desarrollo |
| `.dockerignore` | Crear | `.git`, `.venv`, `.env*` (salvo `.env.example`), `tests/`, `__pycache__`, `*.log`, `uvicorn.*`, `htmlcov`, `.pytest_cache` |
| `compose.yaml` | Crear | Servicios de spec §4.3. `db` con `healthcheck` (`pg_isready`) y volumen `pgdata`; `migrate` y `api` con `depends_on: db: condition: service_healthy`; `api` con `target: dev`, `./app` montado y `--reload`; `mailpit` con `8025` |
| `docker/postgres-init/01-test-db.sql` | Crear | `CREATE DATABASE prestamedios_test` |
| `.env.example` | Modificar | Bloque "Con Docker" (`DATABASE_URL` con host `db`, `SMTP_HOST=mailpit`) |
| `README.md` | Modificar | Sección "Con Docker" (RN-P03), sin quitar el camino manual |

### 4.2 Archivos (frontend, `feat/docker`)

| Archivo | Acción | Contenido |
| --- | --- | --- |
| `Dockerfile` | Crear | Etapa `build` (`node:22-alpine`, `npm ci`, `ARG VITE_API_URL=""`, `npm run build`); etapa final (`nginx:1.27-alpine`, `dist/` en `/usr/share/nginx/html`, `nginx.conf` como plantilla de `envsubst` con `API_UPSTREAM`) |
| `nginx.conf` | Crear | `location /assets/` con `Cache-Control: public, max-age=31536000, immutable`; `index.html` con `no-cache`; `location /api/` y `= /health` y `= /health/db` → `http://${API_UPSTREAM}`; `client_max_body_size 12m` (PDF de 10 MB + margen); `proxy_set_header X-Forwarded-For $http_cf_connecting_ip` con *fallback* a `$remote_addr` si la cabecera falta (§5.3); `X-Forwarded-Proto https`; `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options DENY` |
| `.dockerignore` | Crear | `node_modules`, `dist`, `.git`, `.env*`, `.figma` |
| `README.md` | Modificar | Cómo construir y probar la imagen |

### 4.3 Verificación de AC-P05

`VITE_API_URL=""` en el build debe dejar `API_URL === ""` en `src/lib/api.ts` (`?? ` no reemplaza la cadena vacía) y `spacesApi.ts` debe resolver `"/api/v1/spaces"`. Se verifica en el navegador con la imagen detrás de `web` y la API del compose. Si Vite no pasa la variable vacía, se usa `VITE_API_URL=/` y se ajusta el `replace(/\/$/, "")` existente, que ya la deja vacía: no hace falta tocar código del frontend en ningún caso.

---

## 5. Fase C — Código de `core` (backend, `feat/produccion`)

### 5.1 `ENTORNO` (spec §6.9.1)

- `settings.py`: `entorno: Literal["desarrollo", "produccion"] = "desarrollo"` (`ENTORNO`); `forwarded_allow_ips: str = "127.0.0.1"` (`FORWARDED_ALLOW_IPS`); `email_limite_diario: int | None = Field(default=None, ge=1)` (`EMAIL_LIMITE_DIARIO`).
- `model_validator(mode="after")`: con `produccion`, error si `localhost` o `127.0.0.1` aparece en `frontend_url` o en algún origen de `cors_origins`, o si `email_backend == "memoria"`. Mensaje claro del campo que falla (la app no arranca, como con `JWT_SECRET_KEY`).
- `main.py`: `FastAPI(..., docs_url=None, redoc_url=None, openapi_url=None)` cuando `settings.entorno == "produccion"`.

### 5.2 `GET /health/db` (spec §6.9.3)

En `main.py`, junto a `/health`: `async with SessionLocal() as s: await s.execute(text("SELECT 1"))` con `asyncio.timeout(2)`. Cualquier excepción → `JSONResponse(503, {"status": "sin_base"})` y `logger.warning` con el tipo de error (no el mensaje, que puede tener la URL). Sin autenticación. Se usa la fábrica de sesiones de `app/database.py`, no `get_db`, para no depender del manejo de errores de la dependencia.

### 5.3 IP real del cliente (spec §6.9.2)

- `main.py`: `app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=settings.forwarded_allow_ips)` (de `uvicorn.middleware.proxy_headers`). Va **en la app** y no en la línea de comandos de uvicorn, para que los tests lo ejerciten con `ASGITransport` y para que valga igual en `tareas` y en desarrollo.
- El `CMD` del `Dockerfile` no repite `--proxy-headers` (uvicorn lo activa por defecto sólo para `127.0.0.1`; queda redundante y sin efecto).
- En desarrollo `FORWARDED_ALLOW_IPS=127.0.0.1`: nada cambia para quien corre sin proxy.
- En producción, red `interna` con subred fija (§6.1); `FORWARDED_ALLOW_IPS` es la IP fija de `web`.

### 5.4 Límite diario de correos (spec §6.7)

- **Migración `0021_core_envios_correo`:** tabla `envios_correo_diarios (fecha DATE PRIMARY KEY, cantidad INTEGER NOT NULL DEFAULT 0 CHECK (cantidad >= 0))`. Modelo en `app/core/models.py` (nuevo, registrado en `alembic/env.py` y en `_TABLAS` de `tests/conftest.py`). `downgrade` borra la tabla.
- **Reserva atómica** en `email.py`, antes de enviar y sólo si `email_limite_diario` está definido:

  ```sql
  INSERT INTO envios_correo_diarios (fecha, cantidad) VALUES (:hoy, 1)
  ON CONFLICT (fecha) DO UPDATE SET cantidad = envios_correo_diarios.cantidad + 1
  WHERE envios_correo_diarios.cantidad < :limite
  RETURNING cantidad
  ```

  Sin fila devuelta → `ErrorEnvioCorreo("limite_diario")` sin abrir conexión SMTP. `:hoy` es `ahora_lab().date()`. La reserva usa una sesión propia y hace `commit` en el acto: no participa de la transacción de quien llama (RN-72 ya manda el correo después del commit de negocio).
- Si el envío SMTP falla después de reservar, el cupo no se devuelve (cuenta como intento; el proveedor también lo cuenta). Se documenta.
- `ErrorEnvioCorreo` gana un atributo `motivo` (`"limite_diario"` o `"smtp"`), con `"smtp"` por defecto para no romper a quien ya la captura. `notifications` lo usa para X2.
- Sin `EMAIL_LIMITE_DIARIO`, el transporte no toca la base: los tests actuales y el backend `memoria` no cambian.

### 5.5 Archivos

| Archivo | Acción | Contenido |
| --- | --- | --- |
| `app/core/settings.py` | Modificar | §5.1 y §5.4 |
| `app/core/models.py` | Crear | `EnvioCorreoDiario` |
| `app/core/email.py` | Modificar | Reserva de §5.4, `motivo` en `ErrorEnvioCorreo` |
| `app/main.py` | Modificar | §5.1…§5.3 |
| `alembic/versions/0021_core_envios_correo.py` | Crear | §5.4 |
| `alembic/env.py`, `tests/conftest.py` | Modificar | Registrar el modelo y la tabla |
| `requirements.txt` | Modificar | `uvicorn[standard]>=0.30` |
| `.env.example` | Modificar | `ENTORNO`, `FORWARDED_ALLOW_IPS`, `EMAIL_LIMITE_DIARIO` (X4) |
| `tests/core/test_entorno.py` | Crear | AC-P10, AC-P11 |
| `tests/core/test_salud.py` | Crear | AC-P12 (503 con un `SessionLocal` que falla, por *monkeypatch*) |
| `tests/core/test_proxy.py` | Crear | AC-P14: `POST /auth/recuperacion` desde `client=("172.30.0.10", …)` (de confianza) con `X-Forwarded-For` distintos cuenta por IP; desde una IP no confiable, la cabecera se ignora |
| `tests/core/test_email_limite.py` | Crear | AC-P18 (límite, cambio de día con `ahora_lab` *monkeypatcheado*, concurrencia con dos envíos simultáneos en el último cupo) |
| `tests/core/test_migracion_0021.py` | Crear | `upgrade`/`downgrade` de la tabla |

---

## 6. Fase C — `deploy/` (backend, `feat/produccion`)

### 6.1 `compose.prod.yaml`

```
networks:
  frontal: {}                         # cloudflared ↔ web
  interna: { ipam: { config: [{ subnet: 172.30.0.0/24 }] } }   # web ↔ api ↔ db, tareas
services:
  db:          postgres:16, volumen pgdata, sólo red interna, healthcheck
  api:         build ., target final, red interna, env_file .env, WEB_CONCURRENCY=2
  web:         build ../Frontend-PrestaMeDios (VITE_API_URL=""), API_UPSTREAM=api:8000,
               redes frontal + interna (ipv4_address 172.30.0.10)
  tareas:      build ., target tareas (imagen final + supercronic, pg client, age, rclone),
               comando supercronic /app/deploy/crontab, red interna, volumen backups
  cloudflared: tunnel run, TUNNEL_TOKEN, red frontal
```

Todos con `restart: unless-stopped` y `logging` con rotación (`max-size: 10m`, `max-file: 5`) para no llenar el disco. Ningún `ports:`.

### 6.2 Scripts

| Archivo | Contenido |
| --- | --- |
| `deploy/.env.prod.example` | Plantilla de spec §6.3, con comentarios de cómo generar cada secreto |
| `deploy/crontab` | Líneas de spec §6.4 con `TZ`; cada línea termina con `&& curl -fsS -m 10 "$MONITOREO_PING_<TAREA>"` (o `python -c` si no se instala `curl`) |
| `deploy/backup.sh` | `set -euo pipefail`; `pg_dump -Fc` → `age -r "$BACKUP_CLAVE_PUBLICA"` → `backups/AAAA-MM-DD.dump.age`; borra locales de más de 7; `rclone copy` a `$BACKUP_DESTINO/diarias/`; el día 1 también a `mensuales/`; `rclone delete --min-age 30d` en `diarias/` y `--min-age 365d` en `mensuales/`; error si el disco supera el 85 % (`df`) |
| `deploy/restaurar.sh` | Recibe el nombre de la copia; `rclone copy` → `age -d -i <clave privada pedida por ruta>` → `createdb` nueva → `pg_restore` → indica cómo apuntar `DATABASE_URL` y reiniciar. No borra la base vieja |
| `deploy/actualizar.sh` | Pasos de spec §6.5; recibe el tag; se detiene ante cualquier error (`set -e`) y muestra qué paso falló |
| `deploy/instalar.sh` | Prepara una Ubuntu Server 24.04 limpia: paquetes, Docker, usuario `prestamedios`, `/opt/prestamedios`, clones en el tag pedido, copia de la plantilla `.env` con permisos 600, `unattended-upgrades`, recordatorio de lo manual (BIOS, LUKS, Tailscale, Cloudflare) |

### 6.3 Imagen `tareas`

Etapa `tareas` del mismo `Dockerfile` del backend (hereda de `final`): instala `postgresql-client-16` (repositorio PGDG, para coincidir con el servidor 16), `age`, `rclone`, `curl` y `supercronic`; copia `deploy/`. Sigue corriendo como `app`.

---

## 7. Fase B — CI

### 7.1 Backend (`.github/workflows/ci.yml`, `feat/ci`)

- `on: pull_request` y `push` a `develop` y `main`; `concurrency` por rama con `cancel-in-progress`.
- Job `tests`: `ubuntu-latest`, servicio `postgres:16` con `POSTGRES_DB=prestamedios_test` y healthcheck; `actions/setup-python` 3.12 con caché de pip; variables `TEST_DATABASE_URL`, `DATABASE_URL` (misma base de servicio, otra base `prestamedios_ci` para el ciclo de migraciones), `EMAIL_BACKEND=memoria`, `JWT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(48))')` en un paso previo con `$GITHUB_ENV`.
- Pasos: `pip install -r requirements-dev.txt` → `test "$(alembic heads | wc -l)" -eq 1` → `alembic upgrade head` → `alembic downgrade base` → `alembic upgrade head` → `pytest -q`.
- Job `imagen`: `docker build --target final .` y `--target tareas`.
- `permissions: contents: read`. Sin `secrets.*` (AC-P09).

### 7.2 Frontend (`.github/workflows/ci.yml`, `feat/ci`)

Job `verificar`: `actions/setup-node` 22 con caché de npm → `npm ci` → `npm run typecheck` → `npm run test` → `npm run build`. Job `imagen`: `docker build .`.

### 7.3 Pruebas de que fallan (AC-P06…AC-P08)

En ramas descartables `ci/prueba-*`, PRs en borrador con: un test roto, una migración con `down_revision` duplicado y un error de tipos. Se capturan los resultados en el PR de la Fase B y se cierran sin mergear.

---

## 8. Instalación en la máquina (después de P-01 y P-02)

Orden, con el registro de cada paso en `docs/operacion.md`:

1. Cuentas a nombre de la casilla del equipo (P-04): Cloudflare, proveedor de correo, UptimeRobot, Healthchecks.io, Tailscale, gestor de contraseñas. Dos administradores por cuenta.
2. Dominio (P-03): compra con renovación automática; DNS en Cloudflare.
3. Correo: dominio verificado en el proveedor; registros SPF, DKIM y DMARC (`p=quarantine`).
4. Par de claves `age`: la privada sólo en el gestor de contraseñas; la pública en `.env`.
5. Máquina: Ubuntu Server 24.04 con LUKS, BIOS con encendido al volver la energía, Tailscale, SSH sólo con clave; `instalar.sh`.
6. Túnel: crear el túnel en Cloudflare con el hostname del dominio → `http://web:80`; token en `.env`.
7. `docker compose -f compose.prod.yaml up -d`, migraciones, `crear-superadmin`.
8. Monitoreo: chequeo de `/health/db` y latidos de cada tarea.
9. Pruebas manuales AC-P13, AC-P15…AC-P17, AC-P19…AC-P21.
10. En febrero: instalación limpia (spec §6.12) siguiendo sólo `docs/instalacion.md`, por otro integrante (AC-P22).

---

## 9. Riesgos del plan

| Riesgo | Mitigación |
| --- | --- |
| Una migración ajena no baja (`downgrade`) | T-01 lo detecta; DT y aviso al perfil; el paso `downgrade` de la CI se activa cuando esté resuelto (se deja comentado con la referencia a la DT) |
| La suite tarda más de 10 minutos en la CI (NFR-P02) | Medir en el primer PR; si hace falta, `pytest -n auto` con `pytest-xdist` y una base por *worker* (cambio en `conftest.py`, del Perfil 1) |
| La máquina del laboratorio no llega a tiempo para diciembre | Las Fases A y B no dependen de ella; las pruebas de diciembre arrancan en la máquina de un integrante con el mismo `compose.prod.yaml` y el túnel, y se migran con `backup.sh`/`restaurar.sh` |
| El proveedor de correo rechaza el dominio o cambia su plan | D-14 tiene alternativa; `EMAIL_LIMITE_DIARIO` se ajusta al plan vigente |
| Compilar las imágenes en la máquina es lento (NFR-P01) | D-06 (b): publicar en GHCR desde la CI. Queda como mejora |

---

## 10. Documentación a actualizar

| Cuándo | Documento | Cambio |
| --- | --- | --- |
| Al aprobar el spec | `MEMORY.md`, ERS, `docs/perfiles.md`, `AGENTS.md` | Hecho el 2026-11-22: ADR-027, X1…X5 en §5, bitácora, plan de cierre del ERS, estado del Perfil 1 |
| Fase A | README de backend y frontend | Camino con Docker |
| Fase C (código) | README del backend | Variables nuevas, `/health/db`, `ENTORNO` |
| Fase C (guías) | `docs/instalacion.md`, `docs/operacion.md` (nuevos); ERS ("Requerimientos técnicos para la instalación" enlaza la guía) | Spec §6.13 |
| Al instalar | `MEMORY.md` | Bitácora; P-01…P-05 respondidas; dominio y fecha de puesta en marcha |
| Al cerrar | Spec, plan y tareas | `IMPLEMENTADO` con trazabilidad |

---

## 11. Historial

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 1.0.0 | 2026-11-22 | `APROBADO` por el Perfil 1, sin cambios |
| 0.1.0 | 2026-11-22 | Borrador inicial (Perfil 1, con asistencia de IA) |
