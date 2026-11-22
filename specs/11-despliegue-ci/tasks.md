# TASKS-11 — Contenedores, integración continua y puesta en producción

> **Spec:** `specs/11-despliegue-ci/spec.md` v1.0.0 (`APROBADO` el 2026-11-22) · **Plan:** `specs/11-despliegue-ci/plan.md` v1.0.0 (`APROBADO` el 2026-11-22) · **Estado:** `EN CURSO` desde el 2026-11-22. Bloques 0 y A hechos: backend PR #41 y frontend PR #30 (`feat/docker`), en revisión.
> Marcar `[x]` al cerrar. Cada tarea tiene su verificación; no se pasa a la siguiente con tests en rojo. Cada bloque es un PR (plan §2). **Orden de merge: A antes que B; C (código) después de A.**
> Comandos de backend desde `Backend-PrestaMeDios/` (venv activo, `TEST_DATABASE_URL` definida); de frontend desde `Frontend-PrestaMeDios/`.

---

## Bloque 0 — Preparación

- [x] **T-00 · Documentación de la aprobación.** ADR-027, X1…X5 en `MEMORY.md` §5, bitácora, plan de cierre del ERS, estado del Perfil 1 en `docs/perfiles.md` y `AGENTS.md` (plan §10, fila "Al aprobar el spec").
  *Verificación:* PR a `Docs-PrestaMeDios` sin conflictos con `main`.
  ✔ 2026-11-22: en el Docs PR de la rama `docs/spec-11-despliegue`, junto con el spec, el plan y estas tareas.
- [x] **T-01 · Línea base y `downgrade`.** `develop` actualizado en ambos repos; `pytest -q`; `alembic heads` (una cabeza); sobre una base descartable, `alembic upgrade head` → `alembic downgrade base` → `alembic upgrade head`. Frontend: `npm run typecheck`, `npm run test`, `npm run build`.
  *Verificación:* resultados anotados en el PR del bloque A. Si un `downgrade` falla: DT nueva en `MEMORY.md` §4, aviso al perfil dueño en §5 y el paso queda comentado en la CI hasta resolverlo (plan §9).
  ✔ 2026-11-22: backend `develop` `5243337`, 987 pasados en 6 min (Python 3.12.3, PostgreSQL local), una sola cabeza (`0020_notifications_portada`); `upgrade head → downgrade base → upgrade head` limpio en una base descartable, así que el paso `downgrade` de la CI se puede activar desde el principio. Frontend `develop` `e0740bc`: typecheck limpio, 266 tests de Vitest (36 archivos), build correcto.

## Bloque A — Contenedores (backend `feat/docker`)

- [x] **A-01 · `Dockerfile` y `.dockerignore`.** Etapas `base`, `deps`, `final` y `dev` de plan §4.1.
  *Verificación:* `docker build --target final -t pmd-api .`; `docker run --rm pmd-api id -u` ≠ 0; `docker run --rm pmd-api ls -a /app` sin `.env`, `tests` ni `.git`; `docker run --rm pmd-api` sin `JWT_SECRET_KEY` termina con error. *Cubre:* AC-P02 (backend), AC-P03, AC-P04.
  ✔ 2026-11-22 (`feat/docker`, backend PR #41): etapas `base`, `deps`, `final` y `dev`; imagen final de 377 MB; `id -u` = 10001; `/app` sólo con `alembic`, `alembic.ini` y `app`, sin `.env` ni `.git` en todo el sistema de archivos; sin `JWT_SECRET_KEY` el contenedor termina con código 1. La etapa `dev` copia también `requirements.txt` (lo incluye `requirements-dev.txt`).
- [x] **A-02 · `compose.yaml` de desarrollo.** `db` con healthcheck y script de la base de tests, `migrate`, `api` (`target: dev`, `--reload`), `mailpit`. Bloque "Con Docker" en `.env.example`.
  *Verificación:* con los volúmenes borrados, `docker compose up` deja `GET :8000/health` en 200, `alembic current` en la cabeza y la bandeja en `:8025`; `pytest -q` desde el contenedor `api` contra `prestamedios_test` en verde. *Cubre:* AC-P01.
  ✔ 2026-11-22: con volúmenes nuevos y puertos alternativos, `docker compose up --wait` deja `db`, `mailpit` y `api` sanos y `migrate` terminado con código 0 en `0020`; `GET /health` 200 y Mailpit 200. `docker compose exec api pytest -q`: 987 pasados en 5 min 43 s contra `prestamedios_test` del contenedor. La contraseña de la base sale de `.env` (`POSTGRES_PASSWORD`, obligatoria): el compose no versiona credenciales.
- [x] **A-03 · README del backend.** Sección "Con Docker" sin quitar el camino manual (RN-P03).
  *Verificación:* un integrante que no hizo A-01 y A-02 levanta el entorno con la sección.
  ✔ 2026-11-22: sección "Con Docker" en el README y bloque `POSTGRES_PASSWORD`/puertos en `.env.example`; el camino manual queda igual. Falta que lo pruebe otro integrante.

## Bloque A-F — Contenedores (frontend `feat/docker`)

- [x] **AF-01 · `Dockerfile`, `nginx.conf` y `.dockerignore`.** Plan §4.2.
  *Verificación:* `docker build -t pmd-web .`; la imagen no contiene `node_modules`, `.env*` ni `.figma`; `assets/` con `Cache-Control: immutable` e `index.html` con `no-cache` (`curl -I`). *Cubre:* AC-P02 (frontend).
  ✔ 2026-11-22 (`feat/docker`, frontend PR #30): imagen de 75 MB (`node:22-alpine` → `nginx:1.27-alpine`) sin `node_modules`, `.env*` ni `.figma`; `index.html` con `Cache-Control: no-cache` y `assets/` con `immutable`; `X-Frame-Options`, `nosniff` y `Referrer-Policy`. `nginx.conf` como plantilla con `${API_UPSTREAM}` y la IP real desde `CF-Connecting-IP`.
- [x] **AF-02 · Mismo origen.** Levantar `pmd-web` con `API_UPSTREAM` apuntando a la API del compose de A-02.
  *Verificación:* en el navegador, login y catálogo funcionan y todas las llamadas van a `/api/v1/…` del mismo origen (pestaña de red), sin errores de CORS. Si la variable vacía no llega, aplicar la alternativa de plan §4.3. *Cubre:* AC-P05.
  ✔ 2026-11-22: `VITE_API_URL` vacío funciona sin tocar código (el bundle no tiene `localhost:8000`). Con `web` en la red del compose, login y catálogo en el navegador: `POST /api/v1/auth/login`, `GET /api/v1/inventory/…` en `localhost:8090`, todos 200, sin errores de CORS ni de consola.
- [x] **AF-03 · README del frontend.** Cómo construir y probar la imagen.

## Bloque B — Integración continua (backend y frontend `feat/ci`)

- [ ] **B-01 · Workflow del backend.** Plan §7.1.
  *Verificación:* el PR del bloque corre la CI en verde y en menos de 10 minutos (NFR-P02; si no, plan §9). *Cubre:* AC-P06 (parte positiva), AC-P09.
  ✔ 2026-11-22: sección "Imagen de producción" en el README.
- [ ] **B-02 · Workflow del frontend.** Plan §7.2.
  *Verificación:* CI en verde en el PR. *Cubre:* AC-P08 (parte positiva), AC-P09.
- [ ] **B-03 · Pruebas de que la CI falla.** PRs en borrador descartables de plan §7.3 (test roto, dos cabezas de Alembic, error de tipos).
  *Verificación:* las tres CI en rojo, con capturas en el PR del bloque; los PRs de prueba se cierran sin mergear y se borran sus ramas. *Cubre:* AC-P06, AC-P07, AC-P08.
- [ ] **B-04 · Aviso al equipo.** Comunicar X3 (CI obligatoria de hecho, `downgrade` funcional) y proponer al dueño de la organización la protección de ramas de D-05 después de una semana en verde.
  *Verificación:* fila de `MEMORY.md` §5 de X3 actualizada con la fecha del aviso.

## Bloque C — Código de `core` (backend `feat/produccion`)

- [ ] **C-01 · Tests primero.** `tests/core/test_entorno.py`, `test_salud.py`, `test_proxy.py`, `test_email_limite.py` y `test_migracion_0021.py` (plan §5.5), anotados con `# AC-P..`.
  *Verificación:* fallan por lo que falta (variables inexistentes, `404` de `/health/db`, IP del proxy contada como cliente, tabla inexistente), no por errores del test.
- [ ] **C-02 · `ENTORNO`.** Plan §5.1: variable, validador de producción y documentación de la API apagada.
  *Verificación:* `pytest tests/core/test_entorno.py -q` en verde. *Cubre:* AC-P10, AC-P11.
- [ ] **C-03 · `GET /health/db`.** Plan §5.2.
  *Verificación:* `pytest tests/core/test_salud.py -q` en verde. *Cubre:* AC-P12.
- [ ] **C-04 · IP real del cliente.** `ProxyHeadersMiddleware` en `main.py` con `FORWARDED_ALLOW_IPS`; `uvicorn[standard]>=0.30`.
  *Verificación:* `pytest tests/core/test_proxy.py tests/users -q` en verde (RN-54 sin cambios para clientes directos). *Cubre:* AC-P14 (parte automática).
- [ ] **C-05 · Límite diario de correos.** Migración `0021_core_envios_correo` (cuelga de la cabeza vigente), `app/core/models.py`, registro en `alembic/env.py` y `tests/conftest.py`, reserva atómica y `ErrorEnvioCorreo.motivo` (plan §5.4).
  *Verificación:* `pytest tests/core -q` en verde; `alembic heads` con una cabeza; ciclo `upgrade → downgrade -1 → upgrade`. *Cubre:* AC-P18.
- [ ] **C-06 · Suite completa y variables.** `.env.example` con `ENTORNO`, `FORWARDED_ALLOW_IPS` y `EMAIL_LIMITE_DIARIO`; README con `/health/db` y `ENTORNO`.
  *Verificación:* `pytest -q` completo en verde y la CI del PR en verde.

## Bloque C-D — `deploy/` (backend `feat/produccion`, mismo PR que el bloque C)

- [ ] **CD-01 · Etapa `tareas` del `Dockerfile`.** Plan §6.3, con la suma SHA-256 de `supercronic` verificada.
  *Verificación:* `docker build --target tareas`; dentro, `pg_dump --version` (16), `age --version`, `rclone version`, `supercronic -test deploy/crontab`.
- [ ] **CD-02 · `compose.prod.yaml` y `.env.prod.example`.** Plan §6.1 y §6.2.
  *Verificación:* en la máquina de un integrante, con un túnel de prueba de Cloudflare y un dominio o subdominio de prueba, la app responde por `https://`; `docker compose ps` sin puertos publicados. *Cubre:* AC-P14 (prueba manual por el dominio), parte de AC-P20.
- [ ] **CD-03 · `crontab` y `backup.sh`.** Plan §6.2, con un bucket de R2 y una cuenta de Healthchecks.io de prueba.
  *Verificación:* con el horario adelantado, la copia aparece cifrada en local y en R2, el latido llega y `docker compose logs tareas` muestra la salida; con el destino mal configurado, la tarea falla y el latido no llega. *Cubre:* AC-P16.
- [ ] **CD-04 · `restaurar.sh`.** Plan §6.2.
  *Verificación:* restaurar en **otra** máquina una copia bajada de R2 con la clave privada; la app arranca con los mismos usuarios, órdenes y archivos (comparar conteos y descargar un aval). *Cubre:* AC-P13.
- [ ] **CD-05 · `actualizar.sh`.** Plan §6.2.
  *Verificación:* actualización de un tag a otro sin errores; con una migración rota en una rama de prueba, el script se detiene y la API anterior sigue respondiendo. *Cubre:* AC-P15.
- [ ] **CD-06 · `instalar.sh`.** Plan §6.2.
  *Verificación:* corre de punta a punta en una VM con Ubuntu Server 24.04 limpia.

## Bloque D — Guías (Docs `docs/spec-11-guias`)

- [ ] **D-01 · `docs/instalacion.md`.** Spec §6.13; enlazada desde el ERS ("Requerimientos técnicos para la instalación").
  *Verificación:* revisión de otro integrante. *Cubre:* base de AC-P22.
- [ ] **D-02 · `docs/operacion.md`.** Spec §6.10, §6.11; procedimiento de actualización; qué hacer ante cada aviso; registro de pruebas de restauración; nota para pegar en la máquina (EC-P08); lista de verificación de que la clave privada no está en la máquina.
  *Verificación:* revisión del equipo de operación. Llevar §6.11 a la referente (P-05).

## Bloque E — Instalación en la máquina del laboratorio (sin PR)

> Bloqueado por P-01 y P-02. Si la máquina no está a tiempo para diciembre, las pruebas arrancan con CD-02 en la máquina de un integrante (plan §9).

- [ ] **E-01 · Cuentas, dominio y secretos.** Plan §8, pasos 1 a 4 (P-03, P-04).
  *Verificación:* cada cuenta con dos administradores; todo secreto en el gestor compartido.
- [ ] **E-02 · Correo.** Dominio verificado en el proveedor, SPF, DKIM y DMARC; `EMAIL_LIMITE_DIARIO` según el plan vigente.
  *Verificación:* recuperación de contraseña a una casilla `@untdf.edu.ar` y a una de Gmail, sin spam, con SPF y DKIM `pass` en las cabeceras. *Cubre:* AC-P17.
- [ ] **E-03 · Máquina y despliegue.** Plan §8, pasos 5 a 7; tag en `main` (RN-P09, con pedido explícito del equipo para integrar y taggear).
  *Verificación:* app en el dominio; `crear-superadmin` hecho; escaneo de puertos de la IP pública sin nada abierto; SSH sólo con clave por Tailscale. *Cubre:* AC-P20, AC-P21.
- [ ] **E-04 · Monitoreo.** UptimeRobot sobre `/health/db` y latidos de cada tarea.
  *Verificación:* desenchufar la máquina: llega el aviso de caída; al volver la energía, el sistema vuelve solo y llega el aviso de recuperación. *Cubre:* AC-P19.
- [ ] **E-05 · Pruebas de diciembre.** Aviso visible de "versión de prueba", datos de prueba, aviso al laboratorio con el dominio.
  *Verificación:* el personal entra y opera con una cuenta de prueba.
- [ ] **E-06 · Instalación limpia de febrero.** Spec §6.12, hecha por un integrante que no hizo E-03, sólo con `docs/instalacion.md`.
  *Verificación:* sistema en producción con base y secretos nuevos. *Cubre:* AC-P22.

## Bloque F — Cierre

- [ ] **F-01 · Trazabilidad y cierre.** Spec, plan y tareas en `IMPLEMENTADO` con la tabla AC → test o prueba manual; `MEMORY.md` (bitácora, P-01…P-05 respondidas, X1…X5 al día); README al día.
  *Verificación:* PR a Docs.
