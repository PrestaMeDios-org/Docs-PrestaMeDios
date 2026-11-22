# SPEC-11 — Contenedores, integración continua y puesta en producción

| Campo | Valor |
| --- | --- |
| **ID** | SPEC-11 |
| **Perfil responsable** | Perfil 1 — Identidad, Usuarios, Permisos, Configuración Global y Despliegue |
| **Estado** | `APROBADO` — 2026-11-22 por el Perfil 1, con las recomendaciones de §10 (D-01…D-16; ADR-027). Las preguntas de §10.1 (P-01…P-05) no bloquean las Fases A y B; P-01 y P-02 bloquean la instalación en la máquina del laboratorio (Fase C) |
| **Versión** | 1.0.0 |
| **Requisitos cubiertos** | "Sobre los entregables" del ERS: *Requerimientos técnicos para la instalación*, *Copia del software* y *Plan de cierre y puesta en producción* (ADR-026) · K8 de SPEC-03 (Docker y CI) · servidor de correo de producción (pedido del Perfil 5 del 2026-11-18) · Constitución P4.3 (secretos sólo en el entorno) y P9.2 (tests contra PostgreSQL real) |
| **Responde a** | `MEMORY.md` §5: Perfil 1 → Perfil 5 (2026-11-18, servidor de correo de producción); C-N04 de SPEC-06 (programar `enviar-correos` junto con `procesar-vencimientos`); README del backend (programar `limpiar-huerfanos`) |
| **Depende de** | Backend `develop` (`d5c38f7`) y frontend `develop` (`5d1278d`). No depende de ningún spec abierto |
| **Módulos afectados** | Backend: `app/core/settings.py`, `app/main.py` (salud y documentación de la API), raíz del repo (`Dockerfile`, `.dockerignore`, `compose*.yaml`, `.github/workflows/`, `deploy/`) · Frontend: raíz del repo (`Dockerfile`, `.dockerignore`, `nginx.conf`, `.github/workflows/`) · Docs: guía de instalación y operación |
| **Módulos ajenos** | Ninguno se modifica. Los comandos programados de `loans` (`procesar-vencimientos`) y `notifications` (`enviar-correos`) los escribe cada perfil; este spec sólo define dónde se registran y qué límite de envío respetan (§6.4, §6.7, coordinación §11) |
| **Constitución** | v1.1.0 |
| **Fuente de verdad funcional** | `docs/ERS.md` ("Sobre los entregables" y "Plan de cierre y puesta en producción"). Este spec cambia el supuesto de la instalación "en el servidor de la universidad" (§0.1): el ERS se corrige al aprobarlo |
| **Plan y tareas** | `specs/11-despliegue-ci/plan.md` y `tasks.md` (se redactan al aprobar) |

> **Regla SDD:** spec `APROBADO`. Un cambio de alcance o de contrato se propone como versión nueva y vuelve a aprobarse.

> **Numeración:** el 07 está reservado para `assistant` (Perfil 5) y el 10 es SPEC-10, así que este spec es el 11. Como es transversal, usa prefijos propios, como SPEC-10: `AC-P01…`, `RN-P01…`, `EC-P01…`, `NFR-P01…` (P de producción). Las decisiones empiezan en `D-01`.

---

## 0. Resumen ejecutivo

La entrega final (febrero de 2027) exige dejar PrestaMeDios funcionando para el laboratorio y entregar los requerimientos técnicos de instalación. Además, el personal va a probar la plataforma desde diciembre. Hoy no hay `Dockerfile`, ni CI, ni guía de producción, y nada impide mergear a `develop` un cambio que rompe los tests o la cadena de migraciones (ya pasó: C19, D-22 de SPEC-03).

### 0.1 Contexto de operación (definido el 2026-11-22)

Lo que sabemos de la universidad cambia el escenario de la v0.1.0:

- **La universidad no se hace cargo de la parte de sistemas.** Espera recibir una aplicación que ya funcione.
- **No hay presupuesto** para una nube ni para un servidor pago. El servidor es, a lo sumo, **una computadora que preste el laboratorio**, disponible desde diciembre.
- **El dominio es propio** y lo administra el equipo.
- **No hay SMTP institucional ni lugar para copias fuera del servidor:** los provee el equipo.
- **El equipo opera el sistema después de la entrega** (actualizaciones, copias, restauración): PrestaMeDios es un servicio que el equipo brinda al laboratorio.

En consecuencia, el diseño prioriza: **costo cero** (salvo el dominio), **una sola máquina física** sin IP pública ni puertos abiertos, **operación remota** por el equipo, **copias fuera del laboratorio** y **avisos automáticos** cuando algo deja de andar, porque nadie del laboratorio lo va a mirar.

### 0.2 Fases

Tres fases independientes, cada una con su PR por repo:

- **Fase A — Contenedores.** Imagen del backend, imagen del frontend (build estático servido por nginx) y un `compose.yaml` de desarrollo con PostgreSQL y Mailpit.
- **Fase B — Integración continua.** GitHub Actions en backend y frontend: tests contra PostgreSQL real, cadena de migraciones (una sola cabeza, `upgrade` y `downgrade`), typecheck, build y Vitest.
- **Fase C — Producción en la computadora del laboratorio.** Linux con Docker Compose; publicación a Internet por un **túnel saliente** (Cloudflare Tunnel) con el dominio propio y TLS, sin abrir puertos en la red de la universidad; acceso remoto del equipo; correo por un **proveedor transaccional gratuito**; copias diarias **cifradas** a un almacenamiento externo gratuito; monitoreo con avisos al equipo; guía de instalación y de operación. Incluye tres ajustes chicos en `core`.

---

## 1. Alcance

### 1.1 Dentro del alcance

1. Imágenes de contenedor reproducibles del backend y del frontend, sin secretos adentro.
2. Entorno de desarrollo completo con `docker compose up` (base, correo de prueba y API).
3. CI en los repos Backend y Frontend.
4. Preparación de la computadora del laboratorio (Linux, Docker, arranque automático) y despliegue con Compose.
5. Publicación con el dominio propio por túnel saliente, con TLS.
6. Acceso remoto seguro del equipo para operar.
7. Correo saliente por un proveedor transaccional con el dominio propio (SPF, DKIM, DMARC).
8. Tareas programadas: `limpiar-huerfanos` y las copias; lugar para `procesar-vencimientos` y `enviar-correos`.
9. Copias de seguridad cifradas, locales y externas, y restauración probada.
10. Monitoreo de disponibilidad y de las tareas programadas, con avisos al equipo.
11. Guía de instalación (entregable del ERS) y manual de operación del equipo.
12. Ajustes de `core` necesarios para correr detrás del túnel (§6.9).

### 1.2 Fuera del alcance

- Servidores o nubes pagas, orquestadores (Kubernetes, Swarm) y alta disponibilidad: hay una sola máquina (riesgo aceptado, §8).
- Despliegue continuo automático desde la CI (D-06).
- El manual de uso para el personal y los estudiantes (es otro entregable, sin código).
- Los comandos programados de `loans` y `notifications` (los escribe cada perfil).
- Un acuerdo formal de nivel de servicio con la universidad. §6.11 fija lo que el equipo se compromete a hacer.

---

## 2. Estado actual

### 2.1 Verificado en `develop` (backend `d5c38f7`, frontend `5d1278d`, 2026-11-21)

| Tema | Estado |
| --- | --- |
| Contenedores y CI | No existen `Dockerfile`, `compose*.yaml` ni `.github/` en ningún repo |
| Configuración | `app/core/settings.py` lee todo del entorno (`pydantic-settings`, `.env`); la app no arranca sin `JWT_SECRET_KEY` (≥ 32 caracteres). `.env.example` documenta cada variable |
| Base | PostgreSQL ≥ 15. `btree_gist` lo crean las migraciones `0001` y `0009` (`CREATE EXTENSION IF NOT EXISTS`); es una extensión *trusted*, así que alcanza con que el usuario de la app sea dueño de la base |
| Archivos | Avales y fotos se guardan en la base (`LargeBinary`, `files/models.py:75`). No hay volumen de archivos: **un volcado de la base es una copia completa** |
| Salud | `GET /health` responde fijo, sin consultar la base (`app/main.py:102`) |
| Documentación de la API | `/docs`, `/redoc` y `/openapi.json` siempre expuestos |
| IP del cliente | `users/router.py:225` usa `request.client.host` para el límite por IP de la recuperación de contraseña (RN-54). Detrás de un túnel o proxy, todos los pedidos llegan con la misma IP |
| Correo | SMTP configurable (`SMTP_*`, `EMAIL_FROM`); en desarrollo, Mailpit. `FRONTEND_URL` arma los enlaces de los correos (`/#/restablecer?token=…`). Hoy sólo `users` envía correos; `notifications` lo hará con su Fase C (ADR-023) |
| CLI | `users.cli crear-superadmin` (con `BOOTSTRAP_SUPERADMIN_PASSWORD` opcional) y `files.cli limpiar-huerfanos` |
| Frontend | Vite 8 + React + TS; `npm run typecheck`, `build` y `test` (Vitest). La URL de la API se fija **al compilar** (`VITE_API_URL`; si falta, `http://localhost:8000`; si está vacía, usa el mismo origen). Navegación con *hash* (`/#/…`), así que el servidor web no necesita reescribir rutas |

### 2.2 Brechas

1. No hay forma estándar de levantar el sistema ni de instalarlo.
2. Nada verifica automáticamente los PRs.
3. Detrás del túnel, el límite por IP de RN-54 se vuelve global y bloquearía la recuperación de contraseña de todos con 20 pedidos por hora.
4. La documentación interactiva de la API queda pública.
5. No hay copias, tareas programadas, correo de producción ni monitoreo.
6. Una computadora de escritorio en un laboratorio se apaga, se reinicia por cortes de luz y no tiene IP pública.

---

## 3. Actores

| Actor | Rol en este spec |
| --- | --- |
| Integrante del equipo | Levanta el entorno de desarrollo y recibe el resultado de la CI en su PR |
| **Equipo de operación** | Los integrantes que el equipo designe (al menos dos, para no depender de una sola persona). Instalan, actualizan, restauran, crean el primer superadministrador, reciben los avisos del monitoreo y custodian los secretos. Operan **en remoto** |
| Computadora del laboratorio | Servidor único. Prestada por el laboratorio, ubicada en la sede (a confirmar cuál, §10.1) |
| Personal del laboratorio | Mantiene la computadora encendida y conectada; avisa al equipo si se cambia de lugar o se apaga. No opera el sistema |
| Servicios externos gratuitos | Cloudflare (DNS, túnel y, si se elige, almacenamiento de copias), proveedor de correo transaccional, monitoreo de disponibilidad (§6) |

---

## 4. Fase A — Contenedores

### 4.1 Imagen del backend (`Backend-PrestaMeDios/Dockerfile`)

- Base `python:3.12-slim` (la versión validada, `AGENTS.md` §5), en dos etapas: dependencias y aplicación.
- Corre como usuario sin privilegios. Sin `.env`, tests ni `.git` adentro (`.dockerignore`).
- Comando por defecto: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips=$FORWARDED_ALLOW_IPS` (§6.9).
- Cantidad de *workers* configurable (`WEB_CONCURRENCY`, 2 por defecto en producción).
- `HEALTHCHECK` contra `/health`.

### 4.2 Imagen del frontend (`Frontend-PrestaMeDios/Dockerfile`)

- Etapa de build: `node:22-alpine`, `npm ci`, `npm run build` con `VITE_API_URL` como argumento de build.
- Etapa final: `nginx:alpine` con `dist/` y un `nginx.conf` propio: caché larga para `assets/` con hash, sin caché para `index.html`, cabeceras de seguridad básicas y reenvío de `/api/` y `/health` a la API (§6.1).
- En producción `VITE_API_URL` va vacío y la app llama a `/api/v1/…` en el mismo origen; la misma imagen sirve para pruebas y producción (D-02).

### 4.3 `compose.yaml` de desarrollo (en el repo Backend)

Servicios: `db` (`postgres:16`, volumen con nombre), `mailpit`, `api` (código montado y `--reload`) y `migrate` (corre `alembic upgrade head` y termina). El frontend sigue con `npm run dev` en el host (D-03). Puertos de siempre: `8000`, `8443`, `5432`, `8025`. La base de tests (nombre con `test`) se crea en el mismo PostgreSQL con un script de inicio.

### 4.4 Reglas

- **RN-P01.** Ninguna imagen contiene secretos, `.env` ni credenciales por defecto; todo llega por variables de entorno en tiempo de ejecución (P4.3). La única excepción es `VITE_API_URL`, que no es secreta.
- **RN-P02.** Las imágenes fijan versiones mayores (`python:3.12-slim`, `node:22-alpine`, `postgres:16`, `nginx:1.x-alpine`, `cloudflare/cloudflared:<versión>`), nunca `latest`.
- **RN-P03.** El `README.md` de cada repo explica el camino con Docker **y** mantiene el camino manual actual (Constitución §6.1).

---

## 5. Fase B — Integración continua (GitHub Actions)

### 5.1 Backend (`.github/workflows/ci.yml`)

Se dispara en `pull_request` y `push` a `develop` y `main`. Un job con un servicio `postgres:16`:

1. `pip install -r requirements-dev.txt` (con caché).
2. **Cadena de migraciones:** `alembic heads` devuelve exactamente una cabeza; `alembic upgrade head`, `alembic downgrade base` y otra vez `alembic upgrade head` terminan sin error (D-04).
3. `pytest -q` con `TEST_DATABASE_URL` apuntando al servicio y `EMAIL_BACKEND=memoria`.
4. `JWT_SECRET_KEY` de prueba generado en el job (no un secreto del repo).

### 5.2 Frontend (`.github/workflows/ci.yml`)

Mismos disparadores: `npm ci`, `npm run typecheck`, `npm run test`, `npm run build`.

### 5.3 Imágenes

Ambos workflows construyen la imagen (`docker build`, sin publicarla) para detectar un `Dockerfile` roto en el PR que lo rompe.

### 5.4 Reglas

- **RN-P04.** La CI no usa secretos del repositorio: todo valor que necesita es de prueba y se genera en el job.
- **RN-P05.** Los tests de integración de la CI corren contra PostgreSQL real (P9.2), nunca SQLite.
- **RN-P06.** Un PR a `develop` o `main` con la CI en rojo no se mergea. Hacerlo obligatorio con protección de ramas lo decide el equipo (D-05).

---

## 6. Fase C — Producción en la computadora del laboratorio

### 6.1 Topología (D-01, D-02, D-11)

```
Usuarios ──HTTPS──► Cloudflare (dominio propio, TLS)
                        │  túnel saliente: la PC abre la conexión, no se abren puertos
                        ▼
              PC del laboratorio (Linux + Docker Compose)
              ├── cloudflared ──► web (nginx: frontend estático, /api → api)
              ├── api (uvicorn) ──► db (PostgreSQL, sólo red interna)
              └── tareas (cron: copias, limpieza, vencimientos, correos)

Equipo de operación ──SSH por el túnel o Tailscale──► PC del laboratorio
```

- **Túnel saliente (D-11).** La computadora no necesita IP pública ni que la universidad abra puertos: `cloudflared` sale por HTTPS (443) como cualquier navegador. Cloudflare termina el TLS con el dominio propio y protege del tráfico abusivo básico. Requiere que el DNS del dominio esté en Cloudflare (plan gratuito).
- Un solo dominio (p. ej. `prestamedios.com.ar`, a definir, §10.1): sin CORS y sin una URL de API por entorno.
- Ningún servicio publica puertos en la red local, salvo SSH si se elige acceso directo dentro de la universidad.

### 6.2 La computadora (D-12)

- **Sistema:** Ubuntu Server 24.04 LTS, instalación dedicada (no Windows con Docker Desktop: se reinicia por actualizaciones, consume más y Docker Desktop no arranca sin sesión iniciada).
- **Disco cifrado** (LUKS) con desbloqueo en el arranque sin intervención (TPM o clave en un pendrive que queda conectado, según el equipo), porque la base tiene datos personales de estudiantes y la máquina está en un lugar con acceso físico de terceros. Si la máquina no lo permite, se acepta sin cifrado y se registra como riesgo.
- **Arranque solo:** BIOS en "encender al volver la energía"; Docker y los servicios con `restart: unless-stopped`; actualizaciones de seguridad automáticas (`unattended-upgrades`) con reinicio programado de madrugada.
- **Requisitos mínimos:** NFR-P01. Se verifica la máquina que preste el laboratorio antes de instalar.

### 6.3 `compose.prod.yaml` y variables

Servicios `db`, `api`, `web`, `tareas` y `cloudflared`, con volúmenes con nombre para la base y las copias locales. Las variables viven en `/opt/prestamedios/.env` (permisos 600, fuera del repo), con una plantilla versionada en `deploy/.env.prod.example`:

| Variable | Producción |
| --- | --- |
| `ENTORNO` | `produccion` (nueva, §6.9) |
| `DATABASE_URL` | Usuario propio, dueño de la base, sin superusuario |
| `JWT_SECRET_KEY` | Generado en la máquina; cambiarlo cierra todas las sesiones |
| `CORS_ORIGINS` / `FRONTEND_URL` | El dominio público con `https://` |
| `EMAIL_BACKEND`, `SMTP_*`, `EMAIL_FROM` | Proveedor transaccional (§6.7) |
| `FORWARDED_ALLOW_IPS` | Red interna de Docker donde está `web` (nueva, §6.9) |
| `TUNNEL_TOKEN` | Token del túnel de Cloudflare |
| `BACKUP_CLAVE_PUBLICA`, `BACKUP_DESTINO`, credenciales de `rclone` | §6.6 |
| `MONITOREO_PING_*` | URLs de aviso de las tareas (§6.8) |
| El resto | Los valores por defecto de `.env.example` |

### 6.4 Tareas programadas (D-07)

El servicio `tareas` usa la imagen del backend y corre `supercronic` (no necesita root) con un `crontab` versionado en `deploy/crontab` y `TZ=America/Argentina/Ushuaia`:

| Comando | Dueño | Frecuencia | Estado |
| --- | --- | --- | --- |
| `deploy/backup.sh` | Perfil 1 | Diaria, 02:00 | Este spec |
| `python -m app.modules.files.cli limpiar-huerfanos` | Perfil 1 | Diaria, 03:00 | Existe |
| `python -m app.modules.loans.cli procesar-vencimientos` | Perfil 3 | A definir en SPEC-05 | Pendiente (C5) |
| `python -m app.modules.notifications.cli enviar-correos` | Perfil 5 | A definir en SPEC-06 Fase C | Pendiente (C-N04) |

- **RN-P07.** Todo comando programado es idempotente, termina con código distinto de 0 si falla y avisa al monitoreo al terminar bien (§6.8). La salida queda en `docker compose logs tareas`.
- **RN-P08.** Agregar un comando nuevo al `crontab` es una línea, que el perfil dueño suma en su PR (coordinación §11).

### 6.5 Despliegue y actualización (D-06)

Lo hace el equipo de operación en remoto, con `deploy/actualizar.sh`:

1. Copia de seguridad previa (§6.6).
2. `git fetch` y `checkout` del tag de versión en ambos repos; `docker compose -f compose.prod.yaml build`.
3. `docker compose run --rm api alembic upgrade head`. Si falla, se detiene sin reiniciar la API (EC-P02).
4. `docker compose up -d`.
5. Verificación: `GET /health` y `GET /health/db` en 200 desde el dominio público.

- **RN-P09.** A producción sólo llega lo que está en `main` con un tag (`vAAAA.MM.N`). `develop` no se despliega en producción.
- **Primera instalación:** `deploy/instalar.sh` prepara la máquina (Docker, usuario `prestamedios`, carpeta `/opt/prestamedios`, `cloudflared`, `rclone`) y después corre `crear-superadmin` con la contraseña por prompt oculto, nunca en la línea de comandos ni en el historial.

### 6.6 Copias de seguridad (D-09, D-13)

El laboratorio no tiene dónde guardar copias, así que el equipo las saca de la máquina:

1. `deploy/backup.sh` hace `pg_dump --format=custom` y **cifra** el archivo con `age` usando una clave pública (`BACKUP_CLAVE_PUBLICA`). La clave privada **no está en la máquina**: la custodia el equipo de operación (§6.10). Si roban la computadora o la cuenta de almacenamiento, las copias no se pueden leer.
2. Guarda la copia cifrada en el volumen local (últimas 7) y la sube con `rclone` a un almacenamiento externo gratuito (D-13), con retención de 30 diarias y 12 mensuales.
3. Avisa al monitoreo (§6.8). Si la subida falla, la tarea falla y el equipo recibe el aviso.

- `deploy/restaurar.sh <archivo>` baja la copia, la descifra con la clave privada (que el operador trae en ese momento), la restaura en una base nueva y deja la app apuntando a ella.
- **RN-P10.** La restauración se prueba antes de la entrega (AC-P13) y después **una vez por mes**, en la máquina de un integrante, con una copia real descargada del almacenamiento externo. Se anota en el manual de operación.
- **Volumen estimado:** la base con avales y fotos queda por debajo de 1 GB en el primer año, así que 30 + 12 copias comprimidas entran en los 10 GB de los planes gratuitos. Se revisa cada cuatrimestre.

### 6.7 Correo saliente (D-14)

No hay SMTP de la universidad. Se usa un proveedor transaccional con plan gratuito por SMTP, así `app/core/email.py` no cambia:

- Remitente del dominio propio (p. ej. `no-responder@<dominio>`), con **SPF, DKIM y DMARC** configurados en el DNS de Cloudflare para que los correos no lleguen como spam a las casillas de la universidad.
- **Límite de envío.** Los planes gratuitos limitan los correos por día (del orden de 100 a 300). Los correos de hoy (recuperación de contraseña) están muy por debajo. El riesgo son los envíos masivos de `notifications` (un comunicado a todos los usuarios de una sede). Se agrega `EMAIL_LIMITE_DIARIO` (nueva, en `core`): el transporte cuenta los envíos del día y, al llegar al límite, responde `ErrorEnvioCorreo` sin intentar enviar, para que `enviar-correos` deje el resto pendiente en la bandeja de salida (ADR-023) y lo reintente al día siguiente (coordinación X2). La recuperación de contraseña sigue respondiendo de forma neutra (SPEC-03).
- El proveedor concreto se elige en D-14 según su límite y sus condiciones el día de la instalación.

### 6.8 Monitoreo y avisos (D-15)

Como nadie del laboratorio mira el sistema, el equipo de operación recibe avisos por correo (y, si se configura, Telegram):

- **Disponibilidad:** un servicio externo gratuito consulta `https://<dominio>/health/db` cada 5 minutos y avisa si falla dos veces seguidas. Cubre corte de luz, caída de internet del laboratorio, máquina apagada o base caída.
- **Tareas programadas:** cada tarea avisa a una URL de "latido" (Healthchecks.io, plan gratuito) al terminar bien; si el latido no llega a tiempo, avisa. Cubre copias que no se hicieron.
- **Disco:** `backup.sh` también avisa con error si el disco supera el 85 %.
- Los avisos van a una casilla del equipo, no a una personal.

### 6.9 Ajustes de código en `core` (los únicos cambios de aplicación)

1. **`ENTORNO`** (`desarrollo` por defecto, `produccion`): en producción, `FastAPI(docs_url=None, redoc_url=None, openapi_url=None)` (D-08). Con `ENTORNO=produccion`, la app no arranca si `CORS_ORIGINS` o `FRONTEND_URL` siguen en `localhost` o si `EMAIL_BACKEND=memoria`.
2. **IP real del cliente:** uvicorn corre con `--proxy-headers` y `--forwarded-allow-ips` tomado de `FORWARDED_ALLOW_IPS` (sólo `web`). nginx copia la IP real que manda Cloudflare (`CF-Connecting-IP`) a `X-Forwarded-For`, sin aceptar la que venga del cliente. Así `request.client.host` es la IP del usuario y RN-54 sigue funcionando sin tocar `users/router.py` (EC-P03).
3. **`GET /health/db`** (sin autenticación, como `/health`, P4.1): hace `SELECT 1` y responde `200 {"status": "ok"}` o `503 {"status": "sin_base"}`, sin detalles del error. `/health` sigue igual.
4. **`EMAIL_LIMITE_DIARIO`** en `app/core/email.py` (§6.7): opcional, sin límite si no se define.

### 6.10 Secretos y acceso del equipo (D-16)

- Los secretos de producción (`.env`, token del túnel, credenciales del proveedor de correo y del almacenamiento, **clave privada de las copias**, contraseña del superadministrador inicial, acceso al registrador del dominio y a Cloudflare) se guardan en un **gestor de contraseñas compartido** del equipo de operación (p. ej. una organización gratuita de Bitwarden), nunca en el repo, en chats ni en ClickUp.
- Las cuentas de los servicios externos se crean con una **casilla del equipo**, no con la de una persona, y tienen al menos dos administradores, para que el servicio no dependa de quién se gradúa o se va.
- **Acceso remoto:** SSH sólo con clave (sin contraseña, sin root), por Cloudflare Access o Tailscale (D-16). Cada operador tiene su propia clave; se revoca al dejar el equipo.

### 6.11 Compromiso de servicio del equipo

El manual de operación (`docs/operacion.md`) fija lo que el equipo se compromete a hacer, para acordarlo con la referente:

- Responder un aviso de caída dentro del mismo día hábil.
- Copias diarias y prueba de restauración mensual.
- Actualizaciones de seguridad del sistema automáticas; actualizaciones de PrestaMeDios planificadas y avisadas al laboratorio.
- Cómo contactar al equipo y qué hace el personal del laboratorio si la máquina se apaga (encenderla y avisar).
- Qué pasa si el equipo deja de operar: cómo entregar el código, las copias y los accesos a quien designe la universidad.

### 6.12 Pruebas de diciembre y paso a producción (D-10)

- Desde diciembre, la misma máquina y el mismo dominio funcionan como **entorno de pruebas**, con datos de prueba y un aviso visible ("versión de prueba").
- En febrero, antes de la entrega, se hace una **instalación limpia de producción** en la misma máquina: base nueva, secretos nuevos y superadministrador real. Los datos de prueba no pasan a producción.
- Después de febrero no hay un entorno de pruebas permanente: las versiones nuevas se prueban en la máquina de un integrante con `compose.prod.yaml` y una copia restaurada (RN-P10), antes de taggear.

### 6.13 Documentación

- `docs/instalacion.md` (entregable del ERS, "Requerimientos técnicos para la instalación"): requisitos de la máquina, cuentas externas, variables, primera instalación, dominio y túnel, correo, copias, restauración y tareas programadas.
- `docs/operacion.md` (manual del equipo): §6.10, §6.11, procedimiento de actualización, respuesta a cada aviso del monitoreo y registro de pruebas de restauración.
- Los README siguen siendo la guía del desarrollador.

---

## 7. Criterios de aceptación

### 7.1 Fase A

| ID | Criterio | Verificación |
| --- | --- | --- |
| AC-P01 | Con Docker y sin nada más instalado, `docker compose up` en el backend deja la API en `:8000`, la base migrada y Mailpit en `:8025` | Manual en una máquina limpia, documentado en el PR |
| AC-P02 | `docker build` del backend y del frontend termina sin error y ninguna imagen contiene `.env`, `tests/`, `node_modules` de desarrollo ni `.git` | `docker run --rm <img> ls -a` y `docker history` |
| AC-P03 | La imagen del backend corre como un usuario que no es root | `docker run --rm <img> id -u` ≠ 0 |
| AC-P04 | La imagen del backend no arranca sin `JWT_SECRET_KEY` (se mantiene SPEC-01) | `docker run` sin la variable termina con error |
| AC-P05 | La imagen del frontend compilada con `VITE_API_URL=""` llama a `/api/v1/…` en el mismo origen | Inspección de red con la imagen detrás de `web` |

### 7.2 Fase B

| ID | Criterio | Verificación |
| --- | --- | --- |
| AC-P06 | Un PR al backend dispara la CI, que corre `pytest` contra PostgreSQL y falla si un test falla | PR de prueba con un test roto adrede (no se mergea) |
| AC-P07 | La CI del backend falla si hay dos cabezas de Alembic o si un `downgrade` falla | PR de prueba con una migración con `down_revision` duplicado |
| AC-P08 | Un PR al frontend corre typecheck, Vitest y build, y falla si alguno falla | PR de prueba con un error de tipos |
| AC-P09 | Ningún workflow usa `secrets.*` | Revisión de los YAML |

### 7.3 Fase C

| ID | Criterio | Verificación |
| --- | --- | --- |
| AC-P10 | Con `ENTORNO=produccion`, `/docs`, `/redoc` y `/openapi.json` responden 404 | `tests/core/test_entorno.py` |
| AC-P11 | Con `ENTORNO=produccion` la app no arranca si `FRONTEND_URL` o `CORS_ORIGINS` contienen `localhost`, o si `EMAIL_BACKEND=memoria` | `tests/core/test_entorno.py` |
| AC-P12 | `GET /health/db` responde 200 con la base disponible y 503 sin ella, sin autenticación y sin detalle del error | `tests/core/test_salud.py` |
| AC-P13 | Una copia cifrada, descargada del almacenamiento externo, se restaura con `restaurar.sh` en otra máquina y la app arranca con los mismos usuarios, órdenes y archivos | Prueba manual documentada en el PR y en `docs/operacion.md` |
| AC-P14 | Detrás del túnel, el límite por IP de RN-54 cuenta por la IP del usuario y no por la del proxy; una `X-Forwarded-For` enviada por el cliente se ignora | Test de `users` con cabeceras desde una IP de confianza y desde una que no lo es, más prueba manual por el dominio |
| AC-P15 | `actualizar.sh` no reinicia la API si `alembic upgrade head` falla | Prueba manual con una migración rota en una rama de prueba |
| AC-P16 | El contenedor `tareas` corre `limpiar-huerfanos` y `backup.sh` a la hora programada, su salida aparece en `docker compose logs tareas` y el latido llega al monitoreo | Prueba manual con un horario adelantado |
| AC-P17 | Un correo de recuperación enviado desde el dominio público llega a una casilla `@untdf.edu.ar` y a una de Gmail sin caer en spam, con SPF y DKIM válidos y el enlace al dominio | Prueba manual (cabeceras del correo recibido) |
| AC-P18 | Con `EMAIL_LIMITE_DIARIO=N`, el envío N+1 del día responde `ErrorEnvioCorreo` sin contactar al servidor SMTP, y al día siguiente se vuelve a enviar | `tests/core/test_email_limite.py` |
| AC-P19 | Con la máquina desenchufada y vuelta a enchufar, el sistema vuelve a estar en línea por el dominio sin que nadie intervenga, y el monitoreo avisó la caída y la recuperación | Prueba manual en la máquina del laboratorio |
| AC-P20 | Desde fuera de la red de la universidad, un operador entra por SSH con su clave y no puede entrar con contraseña ni como root; la máquina no tiene puertos abiertos hacia Internet | Prueba manual y escaneo de puertos de la IP pública del laboratorio |
| AC-P21 | La máquina de producción no contiene la clave privada de las copias | Revisión en la instalación (lista de `docs/operacion.md`) |
| AC-P22 | Un integrante que no participó de la instalación instala el sistema en una máquina limpia siguiendo sólo `docs/instalacion.md` | Prueba con otro integrante del equipo |

---

## 8. Casos de borde y riesgos aceptados

| ID | Caso | Comportamiento |
| --- | --- | --- |
| EC-P01 | La base todavía no acepta conexiones cuando arranca la API | `api` y `migrate` esperan a `db` con `depends_on: condition: service_healthy` |
| EC-P02 | Una migración falla durante la actualización | Se detiene el procedimiento; la versión anterior sigue en servicio y se restaura la copia previa si la migración dejó cambios a medias |
| EC-P03 | Un cliente manda `X-Forwarded-For` falso | nginx la reemplaza por `CF-Connecting-IP`; la API sólo acepta cabeceras de `web` (`FORWARDED_ALLOW_IPS`) y no publica puertos |
| EC-P04 | El proveedor de correo no responde o se llegó al límite diario | Se mantiene el comportamiento de SPEC-03 (`ErrorEnvioCorreo`, respuesta neutra en la recuperación); los avisos de `notifications` quedan pendientes en la bandeja de salida |
| EC-P05 | Se cambia `JWT_SECRET_KEY` | Todas las sesiones se invalidan; el manual lo propone como medida ante una filtración |
| EC-P06 | Corte de luz o de internet en el laboratorio | El sistema queda fuera de línea mientras dure; vuelve solo (AC-P19). El monitoreo avisa al equipo. **Riesgo aceptado:** no hay segunda máquina |
| EC-P07 | Falla el disco o roban la computadora | Se instala en otra máquina con `instalar.sh` y se restaura la última copia externa: se pierden, como mucho, los datos del último día (NFR-P04). Las copias están cifradas (§6.6) |
| EC-P08 | Alguien del laboratorio apaga la máquina, la usa para otra cosa o la cambia de lugar | El monitoreo avisa; `docs/operacion.md` incluye una nota para pegar en la máquina ("Servidor de PrestaMeDios: no apagar. Contacto: …") |
| EC-P09 | Vence el dominio o la tarjeta con que se paga | Renovación automática por varios años y recordatorio en el calendario del equipo; el registrador queda a nombre de la casilla del equipo (§6.10) |
| EC-P10 | Cloudflare suspende el túnel o cambia su plan gratuito | El sistema queda fuera de línea hasta pasar a la alternativa (Tailscale Funnel u otro túnel, D-11); el manual describe el cambio |
| EC-P11 | El reloj o la zona de la máquina no es la del laboratorio | La app usa `America/Argentina/Ushuaia` (`ahora_lab`); el cron fija `TZ` igual; la máquina sincroniza la hora por NTP |

---

## 9. Requisitos no funcionales

| ID | Requisito |
| --- | --- |
| NFR-P01 | Máquina mínima: CPU x86-64 de 4 núcleos (2015 en adelante), 8 GB de RAM, disco SSD de 120 GB, conexión por cable a la red del laboratorio. Con 4 GB funciona, pero sin margen para compilar las imágenes |
| NFR-P02 | La CI de cada repo tarda menos de 10 minutos |
| NFR-P03 | Una actualización sin migraciones pesadas deja el sistema sin servicio menos de 1 minuto |
| NFR-P04 | Pérdida máxima de datos ante la pérdida total de la máquina: 24 horas (última copia externa) |
| NFR-P05 | Ningún puerto de la máquina queda expuesto a Internet; todo entra por el túnel |
| NFR-P06 | Costo recurrente: sólo el dominio. Todo servicio externo se usa en su plan gratuito |
| NFR-P07 | El equipo se entera de una caída en menos de 15 minutos |

---

## 10. Decisiones

> **Resueltas el 2026-11-22:** el Perfil 1 adoptó todas las recomendaciones.

| ID | Tema | Opciones | Recomendación |
| --- | --- | --- | --- |
| D-01 | Forma de despliegue | (a) Docker Compose; (b) servicios del sistema (systemd + nginx + PostgreSQL) | **(a)**: el equipo controla la máquina entera, y Compose hace que la instalación, la restauración en otra máquina y las pruebas locales sean la misma receta |
| D-02 | Frontend y API | (a) mismo dominio, `/api` por proxy; (b) dos subdominios con CORS | **(a)**: sin CORS, una sola imagen del frontend y un solo hostname en el túnel |
| D-03 | Frontend en el compose de desarrollo | (a) sólo backend, base y correo, y Vite en el host; (b) también el frontend | **(a)**: la recarga en caliente de Vite anda mejor en el host |
| D-04 | Verificar `downgrade` en la CI | (a) `upgrade → downgrade base → upgrade`; (b) sólo `upgrade` | **(a)**: la Constitución exige migraciones reversibles y hoy nadie lo verifica |
| D-05 | Proteger `develop` y `main` | (a) CI obligatoria para mergear; (b) sólo informativa | **(a)**, después de una semana en verde. Cambia la configuración de GitHub: lo hace el dueño de la organización |
| D-06 | Despliegue | (a) manual en remoto con `actualizar.sh` y build en la máquina; (b) imágenes publicadas en GHCR por la CI y `pull` en la máquina; (c) despliegue automático desde la CI | **(a)**: no hay que dejar credenciales de la máquina en GitHub ni exponerla a la CI. (b) es la mejora natural si compilar en la máquina resulta lento |
| D-07 | Tareas programadas | (a) contenedor `tareas` con `supercronic`; (b) cron del sistema con `docker compose run` | **(a)**: queda dentro del compose, versionado y portable a otra máquina |
| D-08 | Documentación de la API en producción | (a) apagada; (b) protegida con usuario | **(a)**: el frontend no la usa y el equipo tiene `/docs` en desarrollo |
| D-09 | Copias de seguridad | (a) `pg_dump` diario cifrado, local y externo; (b) además, WAL continuo | **(a)**: alcanza para el volumen del laboratorio y para una pérdida máxima de un día |
| D-10 | Pruebas de diciembre | (a) la misma máquina como pruebas desde diciembre e instalación limpia de producción en febrero; (b) pruebas y producción conviviendo en la máquina | **(a)**: una sola pila, menos consumo y la instalación limpia de febrero sirve de ensayo de AC-P22 |
| D-11 | Publicación a Internet | (a) Cloudflare Tunnel con el dominio propio; (b) Tailscale Funnel (dominio `*.ts.net`, no el propio); (c) pedir a la universidad IP pública y puertos abiertos | **(a)**: gratis, TLS incluido, no requiere nada de la universidad y usa el dominio propio. Pide tener el DNS del dominio en Cloudflare |
| D-12 | Sistema de la máquina | (a) Ubuntu Server LTS dedicado, disco cifrado; (b) Windows con Docker Desktop o WSL | **(a)**: arranca solo, sin sesión iniciada, y consume menos. Si el laboratorio no puede dedicar la máquina, se revisa este spec |
| D-13 | Almacenamiento de las copias externas | (a) Cloudflare R2 (10 GB gratis, misma cuenta que el túnel); (b) Backblaze B2 (10 GB gratis); (c) Google Drive de una cuenta del equipo | **(a)**: una cuenta menos para administrar y sin costo de descarga. `rclone` permite pasar a (b) o (c) cambiando la configuración |
| D-14 | Proveedor de correo | (a) Brevo (unos 300 correos por día gratis); (b) Resend (unos 100 por día gratis); (c) Gmail SMTP de una cuenta del equipo | **(a)** por el límite más alto, o **(b)** si (a) no acepta el dominio; ambos con dominio propio y DKIM. **(c)** se descarta: el remitente no sería del dominio y Google puede bloquear la cuenta por uso automático. Se confirma el límite vigente al instalar |
| D-15 | Monitoreo | (a) UptimeRobot (disponibilidad) + Healthchecks.io (tareas), planes gratuitos; (b) Uptime Kuma autoalojado | **(a)**: tiene que vivir **fuera** de la máquina, si no, no avisa cuando la máquina se cae |
| D-16 | Acceso remoto del equipo | (a) Tailscale (VPN gratuita para pocos usuarios); (b) SSH por Cloudflare Access | **(a)**: más simple de usar desde la terminal y sigue funcionando si el túnel de Cloudflare se cae. (b) queda como alternativa |

### 10.1 Preguntas que quedan

| ID | Pregunta | A quién | Afecta |
| --- | --- | --- | --- |
| P-01 | ¿Qué computadora presta el laboratorio (procesador, RAM, disco)? ¿En qué sede queda? ¿Se puede dedicar sólo a esto y borrarle el sistema? ¿Está conectada por cable y queda encendida de noche y en vacaciones? | Referente | D-12, NFR-P01, EC-P06 |
| P-02 | ¿La red de la universidad permite conexiones salientes por HTTPS desde esa máquina (sin proxy que lo bloquee)? | Referente o quien administre la red | D-11 |
| P-03 | ¿Qué nombre de dominio usamos y quién lo paga? (del orden de unos pocos miles de pesos por año en `.com.ar`) | Equipo | §6.1, NFR-P06 |
| P-04 | ¿Qué integrantes forman el equipo de operación y cuál es la casilla del equipo para las cuentas y los avisos? | Equipo | §3, §6.10 |
| P-05 | ¿La referente está de acuerdo con el compromiso de §6.11 y con que los datos personales queden en una máquina del laboratorio y en copias cifradas en un servicio externo? | Referente | §6.6, §6.11 |

---

## 11. Coordinación con otros perfiles (se registra en `MEMORY.md` §5 al aprobar)

| ID | Perfil | Pedido |
| --- | --- | --- |
| X1 | Perfil 3 | Cuando exista `loans.cli procesar-vencimientos`, sumar su línea a `deploy/crontab` en el mismo PR (con su latido de monitoreo) y declarar su frecuencia en SPEC-05 |
| X2 | Perfil 5 | Lo mismo para `notifications.cli enviar-correos` (C-N04). Además: el proveedor gratuito tiene un límite diario (§6.7). Al recibir `ErrorEnvioCorreo` por límite, `enviar-correos` deja el aviso pendiente y lo reintenta en la corrida siguiente, sin marcarlo como fallido definitivo. Conviene que priorice los avisos individuales (sanciones, órdenes) antes que los comunicados masivos |
| X3 | Todos | Desde la Fase B, un PR con la CI en rojo no se mergea. Las migraciones nuevas deben tener `downgrade` funcional, porque la CI lo prueba |
| X4 | Todos | Un módulo que necesite una variable de entorno nueva la agrega a `.env.example` y a `deploy/.env.prod.example` en el mismo PR |
| X5 | Todos | Producción sólo recibe versiones taggeadas desde `main` (RN-P09). Lo que se quiera mostrar en las pruebas de diciembre tiene que estar mergeado a `main` |

Además, al aprobar: corregir en el ERS ("Plan de cierre y puesta en producción" e Iteración 6) que la instalación no es en un servidor de la universidad sino en una computadora del laboratorio operada por el equipo, y registrar el cambio como ADR en `MEMORY.md`.

---

## 12. Trazabilidad

| Requisito / origen | Sección | Criterios |
| --- | --- | --- |
| ERS, "Requerimientos técnicos para la instalación" | §6.2, §6.13, §9 | AC-P22 |
| ERS, "Copia del software" y "Plan de cierre" (ADR-026) | §4, §6 | AC-P01, AC-P10…AC-P21 |
| K8 de SPEC-03 (Docker y CI) | §4, §5 | AC-P01…AC-P09 |
| Servidor de correo de producción (Perfil 5, 2026-11-18) | §6.7 | AC-P17, AC-P18 |
| C-N04 de SPEC-06 y README (`limpiar-huerfanos`) | §6.4 | AC-P16 |
| Operación por el equipo (contexto §0.1) | §6.5, §6.8, §6.10, §6.11 | AC-P19, AC-P20 |
| P4.3 (secretos en el entorno) | RN-P01, RN-P04, §6.10 | AC-P02, AC-P09, AC-P21 |
| P9.2 (PostgreSQL real) | RN-P05 | AC-P06 |
| RN-54 de SPEC-03 (límite por IP) | §6.9 | AC-P14 |

---

## 13. Historial de cambios

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 1.0.0 | 2026-11-22 | `APROBADO` por el Perfil 1 con las recomendaciones de §10 (ADR-027). Sin cambios de contenido respecto de la 0.2.0 |
| 0.2.0 | 2026-11-22 | Contexto de operación definido por el Perfil 1 (§0.1): la universidad no opera sistemas, no hay presupuesto, el servidor es una computadora del laboratorio, el dominio es propio y el equipo opera el servicio. Se reemplaza el "servidor de la universidad" por la máquina del laboratorio con túnel saliente (D-11, D-12), correo transaccional gratuito con límite diario (D-14, `EMAIL_LIMITE_DIARIO`, X2), copias cifradas externas (D-13), monitoreo externo (D-15), acceso remoto (D-16), secretos compartidos y compromiso de servicio (§6.10, §6.11), pruebas de diciembre en la misma máquina (D-10). AC-P17…AC-P22, EC-P06…EC-P11, NFR-P06 y NFR-P07 nuevos; preguntas reescritas |
| 0.1.0 | 2026-11-21 | Borrador inicial (Perfil 1, con asistencia de IA) |
