# Manual de operación de PrestaMeDios

> Para el **equipo de operación**: los integrantes que mantienen el servicio funcionando para el laboratorio después de la entrega (SPEC-11 §6.10 y §6.11, ADR-027). La instalación está en [`instalacion.md`](instalacion.md).
>
> Comandos: como el usuario `prestamedios` en la máquina del laboratorio (`ssh` por Tailscale, después `sudo -iu prestamedios`), en `/opt/prestamedios/Backend-PrestaMeDios`. Para abreviar, `dc` = `docker compose -f compose.prod.yaml`.

---

## 1. Quiénes y cómo

| Rol | Quién | Contacto |
| --- | --- | --- |
| Operador principal | *(P-04, a definir)* | |
| Operador suplente | *(P-04, a definir)* | |
| Casilla del equipo (cuentas y avisos) | *(P-04, a definir)* | |
| Referente del laboratorio | Natalia Ader | |

Siempre hay **al menos dos operadores** con acceso a todo: la máquina, las cuentas y el gestor de contraseñas. El servicio no puede depender de una sola persona.

---

## 2. Secretos y cuentas

- **Todos los secretos están en el gestor de contraseñas del equipo**, en una colección "PrestaMeDios — producción":
  - el `.env` completo;
  - el token del túnel;
  - las credenciales SMTP y de R2;
  - la **clave privada de las copias**;
  - la contraseña del superadministrador inicial;
  - el acceso al registrador del dominio, a Cloudflare, al proveedor de correo, a Healthchecks.io, a UptimeRobot y a Tailscale.
- **Nunca** en el repositorio, en chats, en ClickUp ni en correos.
- Cada cuenta externa está a nombre de la casilla del equipo y tiene dos administradores.
- **La clave privada de las copias nunca se guarda en la máquina del laboratorio.** Se trae sólo para restaurar y se borra al terminar.

### 2.1 Alta y baja de un operador

| Paso | Alta | Baja |
| --- | --- | --- |
| Gestor de contraseñas | Invitar a la colección | Quitar el acceso |
| Tailscale | Invitar a la red del equipo | Quitar el dispositivo y el usuario |
| SSH | Agregar su clave pública a `~/.ssh/authorized_keys` del usuario administrador | Borrar su clave |
| Cuentas externas | Sumarlo como administrador donde haga falta | Quitarlo |
| Secretos | — | **Rotar** lo que haya podido copiar (§7) |

---

## 3. Rutina

| Cuándo | Qué |
| --- | --- |
| Cada día | Nada a mano: las copias y la limpieza corren solas, y el monitoreo avisa si algo falla |
| Cada semana | Mirar que no haya avisos pendientes en Healthchecks.io y UptimeRobot |
| **Cada mes** | **Prueba de restauración** en la máquina de un operador (§6.2) y anotarla en §9 |
| Cada cuatrimestre | Revisar el espacio en disco (`df -h`, `docker system df`), el tamaño de las copias en R2 (que no pasen los 10 GB gratuitos) y el uso del plan de correo |
| Cada año | Confirmar la renovación del dominio y que los dos administradores de cada cuenta siguen activos |

---

## 4. Qué hacer ante cada aviso

| Aviso | Primer paso | Si sigue |
| --- | --- | --- |
| **UptimeRobot: el sitio no responde** | Entrar por Tailscale. Si no hay respuesta, la máquina está apagada o sin red: pedirle al laboratorio que la revise (§8) | Si la máquina responde: `dc ps` y `dc logs --tail 100 api web cloudflared` |
| UptimeRobot: `/health/db` da 503 | `dc ps db` y `dc logs --tail 100 db` | `dc restart db api`. Si la base no arranca, restaurar la última copia (§6.1) |
| **Healthchecks.io: falta el latido de `backup`** | `dc logs --tail 200 tareas` | Correrla a mano: `dc exec tareas /app/deploy/backup.sh`. Causas comunes: credenciales de R2 vencidas, disco lleno, base caída |
| Healthchecks.io: falta el latido de `limpieza` | `dc logs --tail 200 tareas` | `dc exec tareas python -m app.modules.files.cli limpiar-huerfanos` |
| La copia falla por disco | `df -h` y `docker system df` | `docker image prune -a` (borra imágenes sin usar) y revisar las copias en `/backups` |
| Quejas de correos que no llegan | `dc logs api \| grep "Correo no enviado"` y el panel del proveedor | Si dice `motivo=limite_diario`, se alcanzó el límite: se reintenta al día siguiente. Si el uso crece, cambiar de plan o de proveedor |
| Cloudflare avisa de un problema con el túnel | `dc logs --tail 100 cloudflared` | `dc restart cloudflared`. Si Cloudflare suspendió el túnel, pasar a la alternativa de SPEC-11 D-11 (Tailscale Funnel) |

**Compromiso:** responder un aviso de caída dentro del mismo día hábil (§10).

---

## 5. Actualizar a una versión nueva

### 5.1 Preparar la versión
1. Lo que va a producción tiene que estar mergeado en `main` en los dos repos, con la CI en verde.
2. Probar la versión con la pila de producción en la máquina de un operador y una copia restaurada (§6.2).
3. Crear el **mismo tag** en los dos repos y subirlo:
   ```bash
   git checkout main && git pull
   git tag -a v2026.12.2 -m "Versión 2026.12.2"
   git push origin v2026.12.2
   ```
4. Avisar al laboratorio el día y la hora (unos minutos sin servicio).

### 5.2 Aplicarla
```bash
deploy/actualizar.sh v2026.12.2
```
El script:
1. hace una copia;
2. pasa los dos repos al tag;
3. compila las imágenes;
4. corre las migraciones;
5. reinicia y verifica `/health/db`.

Si falla el build o la migración, **vuelve los repos al tag anterior y no reinicia**: la versión en servicio sigue andando. Verificar después `https://<dominio>/health/db` desde afuera.

### 5.3 Volver atrás
Si la versión nueva tiene un error después de reiniciar:
- **Sin migraciones nuevas:** `deploy/actualizar.sh <tag anterior>`.
- **Con migraciones nuevas:** restaurar la copia que hizo el paso 1 (§6.1) y después `deploy/actualizar.sh <tag anterior>`.

---

## 6. Restaurar una copia

### 6.1 En producción
1. Traer la clave privada desde el gestor de contraseñas a un archivo temporal en la máquina (p. ej. `/tmp/clave-age`, permisos 600).
2. Elegir la copia: las locales, con `dc exec tareas ls -1t /backups`; las externas, en el bucket de R2 (`diarias/`, `mensuales/`).
3. Restaurar en una base **nueva**, sin tocar la que está en uso:
   ```bash
   deploy/restaurar.sh prestamedios-AAAA-MM-DD_HHMM.dump.age /tmp/clave-age
   ```
4. Seguir las indicaciones del script: cambiar `POSTGRES_DB` en `.env` y `dc up -d api tareas`.
5. Verificar `/health/db` y entrar a la app.
6. **Borrar la clave:** `shred -u /tmp/clave-age`.

### 6.2 Prueba mensual (en la máquina de un operador)
1. Clonar los dos repos uno al lado del otro y crear un `.env` de prueba:
   - `FRONTEND_URL` con un dominio cualquiera que no sea `localhost`;
   - `BACKUP_DESTINO` y las credenciales de R2 con permiso de **sólo lectura**.
2. Levantar la pila sin túnel:
   ```bash
   # Nombre de proyecto propio: nunca "prestamedios", que es el de producción.
   export COMPOSE_PROJECT_NAME=prestamedios-prueba
   export PMD_ENV_FILE=$PWD/prueba.env COMPOSE_EXTRA="-f deploy/compose.prueba-local.yaml --env-file $PWD/prueba.env"
   docker compose -f compose.prod.yaml $COMPOSE_EXTRA up -d --build db api web tareas
   deploy/restaurar.sh <copia de ayer> <clave>
   ```
3. Pasar a la base restaurada y entrar a `http://127.0.0.1:8080`.
4. Comprobar los datos: usuarios, una orden reciente y un aval descargable.
5. Anotar el resultado en §9.
6. Limpiar: `docker compose -p prestamedios-prueba down -v` (**nunca** en la máquina del laboratorio), y borrar la clave y el `.env` de prueba.

---

## 7. Rotar secretos

| Secreto | Cuándo | Cómo | Efecto |
| --- | --- | --- | --- |
| `JWT_SECRET_KEY` | Sospecha de filtración, o baja de un operador | Generar uno nuevo, editar `.env` y `dc up -d api` | Se cierran todas las sesiones (EC-P05) |
| `POSTGRES_PASSWORD` | Baja de un operador | `dc exec db psql -U prestamedios -c "ALTER USER prestamedios PASSWORD '…'"`, después `.env` y `dc up -d` | — |
| Credenciales SMTP, R2 y túnel | Baja de un operador o filtración | Regenerarlas en el panel del servicio, editar `.env` y `dc up -d` | — |
| Clave de las copias | Filtración de la clave privada | Generar un par nuevo (instalación §7.1) y cambiar `BACKUP_CLAVE_PUBLICA`. **Conservar la clave vieja** mientras haya copias cifradas con ella | Las copias nuevas usan la clave nueva |

Actualizar siempre el gestor de contraseñas en el mismo momento.

---

## 8. Para el personal del laboratorio

Imprimir y pegar en la computadora:

> **Servidor de PrestaMeDios — no apagar ni desenchufar.**
> Si se apaga por un corte de luz, vuelve sola. Si no vuelve, encenderla con el botón y avisar.
> No usarla para otra cosa ni cambiarla de lugar sin avisar antes.
> Contacto del equipo: *(casilla y teléfono, P-04)*.

El personal no opera el sistema: sólo mantiene la máquina encendida y conectada, y avisa.

---

## 9. Registro

### 9.1 Pruebas de restauración (RN-P10)

| Fecha | Operador | Copia | Máquina | Resultado | Notas |
| --- | --- | --- | --- | --- | --- |
| 2026-11-22 | Perfil 1 | Copia de prueba (base descartable) | Máquina de desarrollo, pila local | Correcta | Bajada del destino externo (ruta local), descifrada y cargada en una base nueva; la app pasó a esa base. Antes de usar R2 |

### 9.2 Instalaciones, actualizaciones e incidentes

| Fecha | Operador | Qué | Resultado |
| --- | --- | --- | --- |
| | | | |

### 9.3 Lista de verificación de la instalación

- [ ] Ningún puerto de PrestaMeDios abierto hacia Internet (escaneo desde afuera)
- [ ] SSH sólo con clave, sin root, por Tailscale
- [ ] **La clave privada de las copias no está en la máquina** (`sudo grep -rl "AGE-SECRET-KEY" / 2>/dev/null` sin resultados)
- [ ] `.env` con permisos 600 y copia en el gestor de contraseñas
- [ ] La copia diaria llega a R2 y Healthchecks.io recibe los latidos
- [ ] UptimeRobot avisa la caída y la recuperación (prueba de desenchufar)
- [ ] Correo de recuperación recibido en `@untdf.edu.ar` y Gmail, con SPF y DKIM `pass`
- [ ] Nota de §8 pegada en la máquina

---

## 10. Compromiso de servicio

A acordar con la referente (SPEC-11 §6.11, P-05):

- **Caídas:** el equipo responde un aviso dentro del mismo día hábil.
- **Copias:** diarias, guardadas 30 días (y una por mes durante un año), con una prueba de restauración por mes. Ante la pérdida total de la máquina, se pierde como mucho un día de datos.
- **Actualizaciones:** las de seguridad del sistema son automáticas (reinicio a las 04:30). Las de PrestaMeDios se planifican y se avisan al laboratorio.
- **Disponibilidad:** depende de la luz y de la red del laboratorio. No hay una segunda máquina; un corte deja el sistema fuera de línea mientras dure.
- **Si el equipo deja de operar:** se entregan a quien designe la universidad el código (repos públicos de la organización), la última copia con su clave privada y los accesos a cada cuenta. Con esta guía y [`instalacion.md`](instalacion.md) alcanza para seguir.
