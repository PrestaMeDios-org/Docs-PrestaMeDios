# Guía de instalación de PrestaMeDios

> Entregable "Requerimientos técnicos para la instalación" del ERS. Detalle técnico y decisiones: SPEC-11 (`specs/11-despliegue-ci/`), ADR-027 en `MEMORY.md`. El manual del equipo que opera el sistema es [`operacion.md`](operacion.md).
>
> **Estado (2026-11-22):** los archivos que nombra esta guía (`compose.prod.yaml` y `deploy/` del backend, `Dockerfile` y `nginx.conf` del frontend) están en los PRs de SPEC-11 (backend #41, #42 y #45; frontend #30 y #31). La guía vale desde el primer tag que los incluya.

---

## 1. Cómo queda instalado

```
Usuarios ──HTTPS──► Cloudflare (dominio propio, certificado TLS)
                        │  túnel saliente: la computadora abre la conexión
                        ▼
          Computadora del laboratorio · Ubuntu Server 24.04 · Docker Compose
          ├── cloudflared ──► web (nginx: la aplicación y /api → api)
          ├── api (FastAPI) ──► db (PostgreSQL 16, sólo red interna)
          └── tareas (copias diarias cifradas, limpieza, avisos)

Equipo de operación ──Tailscale + SSH──► la computadora
Copias cifradas ──rclone──► almacenamiento externo (Cloudflare R2)
Monitoreo externo (UptimeRobot, Healthchecks.io) ──avisos──► casilla del equipo
```

- **No hace falta nada de la universidad**: ni IP pública, ni puertos abiertos, ni servidor de correo. La computadora sólo necesita salir a Internet por HTTPS, como un navegador.
- **Ningún puerto queda abierto hacia Internet.** Todo entra por el túnel.
- **Costo recurrente:** sólo el dominio. Los servicios externos se usan en sus planes gratuitos.

---

## 2. Requisitos

### 2.1 La computadora

| Recurso | Mínimo | Recomendado |
| --- | --- | --- |
| Procesador | x86-64 de 4 núcleos (2015 en adelante) | — |
| Memoria | 4 GB (funciona, sin margen para compilar) | 8 GB |
| Disco | SSD de 120 GB | SSD de 240 GB |
| Red | Cable a la red del laboratorio, con salida HTTPS (443) | — |
| Energía | Encendida todo el día, también de noche y en vacaciones | Una UPS chica |

Se borra el sistema que tenga y se instala **Ubuntu Server 24.04 LTS**, dedicada sólo a PrestaMeDios.

### 2.2 Cuentas y servicios externos

Todas se crean con la **casilla del equipo** (no con la de una persona) y con **dos administradores** como mínimo. Cada contraseña y cada token van al gestor de contraseñas del equipo ([`operacion.md`](operacion.md) §2).

| Servicio | Para qué | Plan |
| --- | --- | --- |
| Registrador de dominios (p. ej. NIC Argentina para `.com.ar`) | El dominio propio | Pago anual, con renovación automática |
| Cloudflare | DNS del dominio, túnel y almacenamiento de copias (R2) | Gratuito. **R2 pide registrar un medio de pago para activarse**, aunque no cobra dentro de los 10 GB. Si eso no es posible, usar Backblaze B2 (§7.3) |
| Proveedor de correo transaccional (Brevo o Resend) | Correos de la plataforma con remitente del dominio | Gratuito (del orden de 100 a 300 correos por día) |
| Healthchecks.io | Avisa si una tarea programada no corrió | Gratuito |
| UptimeRobot | Avisa si el sistema no responde | Gratuito |
| Tailscale | Acceso remoto del equipo | Gratuito |
| Gestor de contraseñas compartido (p. ej. Bitwarden, organización gratuita) | Secretos de producción | Gratuito |

### 2.3 Lo que necesita el operador en su propia máquina

`git`, un cliente SSH, Tailscale, y [`age`](https://github.com/FiloSottile/age) para generar la clave de las copias (§7.1).

---

## 3. Preparar la computadora

1. **BIOS/UEFI:** activar el encendido automático al volver la energía (suele llamarse *Restore on AC Power Loss → Power On*). Desactivar la suspensión.
2. **Instalar Ubuntu Server 24.04 LTS:**
   - Disco completo con LVM.
   - **Cifrado del disco (LUKS):** recomendado, porque la base tiene datos personales y la máquina está en un lugar con acceso de terceros. **Ojo:** con el cifrado común, después de cada corte de luz alguien tiene que escribir la frase en la máquina, y el sistema no vuelve solo. Elegir según la máquina:
     - si tiene TPM 2.0, usar el cifrado respaldado por hardware del instalador, que desbloquea solo;
     - si no lo tiene, instalar **sin cifrado del disco** y dejarlo registrado como riesgo aceptado en `MEMORY.md`. Las copias van cifradas igual (§7).
   - Usuario administrador personal del operador. Activar OpenSSH.
3. **Acceso remoto con Tailscale** (con la cuenta del equipo):
   ```bash
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up
   ```
   Desde ese momento, el equipo entra con `ssh <usuario>@<nombre-en-tailscale>` desde cualquier lugar.
4. **SSH sólo con clave** (después de copiar la clave pública de cada operador con `ssh-copy-id`). En `/etc/ssh/sshd_config.d/50-prestamedios.conf`:
   ```
   PasswordAuthentication no
   PermitRootLogin no
   ```
   y `sudo systemctl restart ssh`. Comprobar desde otra terminal que se sigue pudiendo entrar **antes** de cerrar la sesión.
5. **Firewall** (opcional y recomendado): sólo SSH por Tailscale.
   ```bash
   sudo ufw default deny incoming
   sudo ufw allow in on tailscale0 to any port 22 proto tcp
   sudo ufw enable
   ```

---

## 4. Instalar Docker y el código

`deploy/instalar.sh` del backend lo hace todo: Docker Engine y Compose del repositorio oficial, actualizaciones de seguridad automáticas con reinicio a las 04:30, el usuario `prestamedios`, la carpeta `/opt/prestamedios`, los clones en el tag pedido y el archivo `.env` desde la plantilla, con permisos 600.

```bash
curl -fsSLO https://raw.githubusercontent.com/PrestaMeDios-org/Backend-PrestaMeDios/v2026.12.1/deploy/instalar.sh
less instalar.sh                 # leerlo antes de correrlo
sudo bash instalar.sh v2026.12.1
```

Queda así:

```
/opt/prestamedios/
├── Backend-PrestaMeDios/        ← compose.prod.yaml, deploy/, .env (no versionado)
└── Frontend-PrestaMeDios/       ← se compila desde acá
```

> **Tags:** a producción sólo llegan versiones taggeadas desde `main` (`vAAAA.MM.N`, el mismo en los dos repos). Crear un tag es una decisión del equipo ([`operacion.md`](operacion.md) §5.1).

---

## 5. Dominio, túnel y correo

### 5.1 Dominio en Cloudflare
1. Comprar el dominio con renovación automática, a nombre de la casilla del equipo.
2. En Cloudflare, *Add a domain* (plan Free) y cambiar los servidores DNS en el registrador por los que indica Cloudflare.

### 5.2 Túnel
1. Cloudflare → *Zero Trust* → *Networks* → *Tunnels* → *Create a tunnel* → tipo **Cloudflared**, nombre `prestamedios`.
2. Copiar el **token** (la cadena larga del comando que muestra). Va a `TUNNEL_TOKEN` en `.env`. No instalar el conector en la máquina: lo corre el contenedor `cloudflared`.
3. *Public hostname*: el dominio (p. ej. `prestamedios.com.ar`) → servicio **HTTP**, URL **`web:80`**.

### 5.3 Correo
1. En el proveedor (Brevo o Resend), agregar y **verificar el dominio**. El proveedor da los registros DNS: cargarlos en Cloudflare **sin proxy** (nube gris).
2. Agregar también un registro DMARC: tipo TXT, nombre `_dmarc`, valor `v=DMARC1; p=quarantine; rua=mailto:<casilla del equipo>`.
3. Crear las credenciales SMTP del proveedor. Van a `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER` y `SMTP_PASSWORD`.
4. `EMAIL_FROM`: `PrestaMeDios <no-responder@<dominio>>`. `EMAIL_LIMITE_DIARIO`: el límite diario del plan, con un margen (p. ej. 280 si el plan da 300).

---

## 6. Variables de entorno

Como el usuario `prestamedios` (`sudo -iu prestamedios`), completar `/opt/prestamedios/Backend-PrestaMeDios/.env`. Cada variable está explicada en `deploy/.env.prod.example`. Resumen:

| Variable | Valor |
| --- | --- |
| `POSTGRES_PASSWORD` | `openssl rand -base64 32` |
| `JWT_SECRET_KEY` | `openssl rand -base64 48` |
| `FRONTEND_URL`, `CORS_ORIGINS` | `https://<dominio>` (la app no arranca con `localhost`) |
| `SMTP_*`, `EMAIL_FROM`, `EMAIL_LIMITE_DIARIO` | §5.3 |
| `TUNNEL_TOKEN` | §5.2 |
| `BACKUP_CLAVE_PUBLICA`, `BACKUP_DESTINO`, `RCLONE_CONFIG_R2_*` | §7 |
| `MONITOREO_PING_BACKUP`, `MONITOREO_PING_LIMPIEZA` | §8 |

`ENTORNO=produccion` y `DATABASE_URL` los arma `compose.prod.yaml`: no van en `.env`. Guardar una copia del `.env` completo en el gestor de contraseñas.

---

## 7. Copias de seguridad

### 7.1 Clave de cifrado (en la máquina del operador, **no** en la del laboratorio)
```bash
age-keygen -o prestamedios-copias.key
# Muestra "Public key: age1…": eso va a BACKUP_CLAVE_PUBLICA.
```
Guardar el contenido de `prestamedios-copias.key` en el gestor de contraseñas como nota segura y **borrar el archivo** (`shred -u prestamedios-copias.key`). Sin esa clave no se puede restaurar ninguna copia; con ella, cualquiera puede leerlas.

### 7.2 Cloudflare R2
1. Cloudflare → *R2* → crear el bucket `prestamedios-copias`.
2. *Manage R2 API Tokens* → token con permiso **Object Read & Write** sólo sobre ese bucket.
3. En `.env`: `BACKUP_DESTINO=r2:prestamedios-copias`, `RCLONE_CONFIG_R2_ACCESS_KEY_ID`, `RCLONE_CONFIG_R2_SECRET_ACCESS_KEY` y `RCLONE_CONFIG_R2_ENDPOINT=https://<id-de-cuenta>.r2.cloudflarestorage.com`.

### 7.3 Alternativa sin medio de pago: Backblaze B2
Crear un bucket privado y una *application key* restringida a él. En `.env`, en lugar de las variables de R2:
```
BACKUP_DESTINO=b2:<nombre-del-bucket>
RCLONE_CONFIG_B2_TYPE=b2
RCLONE_CONFIG_B2_ACCOUNT=<keyID>
RCLONE_CONFIG_B2_KEY=<applicationKey>
```

---

## 8. Monitoreo

1. **Healthchecks.io:** crear un *check* por tarea, con la planificación del `deploy/crontab` y la zona `America/Argentina/Ushuaia`:
   - `backup`: `0 2 * * *`, gracia de 1 hora;
   - `limpieza`: `0 3 * * *`, gracia de 1 hora.

   Copiar la URL de cada uno a `MONITOREO_PING_BACKUP` y `MONITOREO_PING_LIMPIEZA`. Avisos a la casilla del equipo.
2. **UptimeRobot:** monitor HTTP(s) a `https://<dominio>/health/db`, cada 5 minutos, con aviso a la casilla del equipo.

---

## 9. Primer arranque

Como `prestamedios`, en `/opt/prestamedios/Backend-PrestaMeDios`:

```bash
docker compose -f compose.prod.yaml build
docker compose -f compose.prod.yaml up -d db
docker compose -f compose.prod.yaml run --rm api alembic upgrade head
docker compose -f compose.prod.yaml up -d
docker compose -f compose.prod.yaml exec api python -m app.modules.users.cli crear-superadmin \
    --email <email> --nombre <nombre> --apellido <apellido> --dni <dni> --telefono <teléfono>
```

El último comando pide la contraseña por consola: **no** pasarla en la línea de comandos. Guardarla en el gestor de contraseñas.

---

## 10. Verificación

| Qué | Cómo | Esperado |
| --- | --- | --- |
| Servicios | `docker compose -f compose.prod.yaml ps` | `db`, `api`, `web`, `tareas` y `cloudflared` en `Up`; `db` y `api` *healthy*; ningún puerto publicado |
| Sitio | `https://<dominio>` en un navegador | Pantalla de inicio de sesión, con candado |
| Base | `https://<dominio>/health/db` | `{"status":"ok"}` |
| Documentación de la API apagada | `docker compose -f compose.prod.yaml exec web wget -S -qO /dev/null http://api:8000/docs` | `404 Not Found` (por el dominio, `/docs` muestra la aplicación, no la API) |
| Correo | "¿Olvidaste tu contraseña?" con una casilla `@untdf.edu.ar` y una de Gmail | Llegan a la bandeja de entrada, no a spam |
| Copia | `docker compose -f compose.prod.yaml exec tareas /app/deploy/backup.sh` | Termina con `backup: listo` y la copia aparece en R2 |
| Restauración | [`operacion.md`](operacion.md) §6, en **otra** máquina | La app arranca con los mismos datos |
| Puertos | Desde fuera de la universidad, escanear la IP pública del laboratorio | Nada de PrestaMeDios abierto |
| Corte de luz | Desenchufar y volver a enchufar | Vuelve solo; el monitoreo avisó la caída y la recuperación |
| Clave privada | `sudo grep -rl "AGE-SECRET-KEY" / 2>/dev/null` | Sin resultados |

Anotar el resultado en el registro de [`operacion.md`](operacion.md) §9.

---

## 11. Problemas frecuentes

| Síntoma | Causa probable | Qué hacer |
| --- | --- | --- |
| `api` no arranca y el log dice `Configuración inválida para ENTORNO=produccion` | `localhost` en `FRONTEND_URL` o `CORS_ORIGINS`, o `EMAIL_BACKEND=memoria` | Corregir `.env` y `docker compose -f compose.prod.yaml up -d` |
| `docker compose` dice `definir POSTGRES_PASSWORD en .env` | Falta la variable | Completarla |
| El sitio da error 1033 de Cloudflare | `cloudflared` no está conectado | `docker compose -f compose.prod.yaml logs cloudflared`: revisar `TUNNEL_TOKEN` y la salida a Internet |
| Error 502 en el sitio | `web` no llega a `api` | `docker compose -f compose.prod.yaml logs api web` |
| Los correos no llegan o van a spam | Dominio sin verificar, o faltan SPF, DKIM o DMARC | Revisar §5.3 y las cabeceras de un correo recibido (`spf=pass`, `dkim=pass`) |
| Llegan algunos correos y otros no | Se alcanzó `EMAIL_LIMITE_DIARIO` | Los avisos quedan pendientes y se reintentan al día siguiente; revisar el plan del proveedor |
| Healthchecks.io avisa que no llegó el latido de la copia | La copia falló | `docker compose -f compose.prod.yaml logs tareas`; [`operacion.md`](operacion.md) §4 |
| La copia falla con "el disco está al …%" | Poco espacio | `df -h`, `docker system df`; borrar imágenes viejas con `docker image prune` |
