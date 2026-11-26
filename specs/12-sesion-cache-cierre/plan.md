# PLAN-12 — Plan técnico de implementación de SPEC-12

| Campo | Valor |
| --- | --- |
| **Spec** | `specs/12-sesion-cache-cierre/spec.md` (v1.0.1, `APROBADO` el 2026-11-24) |
| **Estado del plan** | `EN CURSO` — v1.0.1. Fase A implementada en `fix/api-sin-cache` (2026-11-26), sin PR; Fase B sin iniciar |
| **Perfil** | 1 |
| **Entrega** | Dos PRs de backend y dos de frontend: primero la Fase A y después la B (D-06) |

---

## 1. Punto de partida (`develop` al 2026-11-24: backend `9ab4774`, frontend `de511a4`)

| Elemento | Situación | Impacto en el plan |
| --- | --- | --- |
| `app/main.py` | Sólo `CORSMiddleware` y el manejador de `AppError` | Se registra el middleware nuevo (§4.1) |
| Respuestas con `Cache-Control` propio | Sólo la descarga de archivos (`files/service.py:431`, `private, no-store`) | El middleware no pisa un encabezado existente (RN-90, AC-124) |
| `app/core/security.py` | `crear_access_token(…, auth_time)` y `TokenPayload(sub, tv, auth_time)`; `auth_time` cae en `iat` si falta (RN-68) | Se suma `sid` con el mismo patrón (§5.1) |
| `app/core/deps.py` | `_sesion_autenticada` es el único punto de validación; `SesionActual(usuario, auth_time)` | Ahí se agrega la consulta de RN-96; `SesionActual` suma `sid` |
| `users/service.py` | Login (`:256`) y cambio de contraseña (`:515`) llaman a `crear_access_token` sin `auth_time`; `renovar_sesion` y `cerrar_sesiones` pasan por `_emitir_token(usuario, auth_time=…)` | `_emitir_token` recibe también `sid`; login y cambio de contraseña generan uno nuevo |
| Migraciones | Cabeza: `0021_core_envios_correo` (SPEC-11; en `develop` desde `7893021`) | `0022_users_sesiones_cerradas`, con `down_revision` igual a la cabeza de `develop` cuando se abra el PR. Antes de mergear, `alembic heads` con una sola cabeza |
| `alembic/env.py` | Ya importa `app.modules.users.models` | El modelo nuevo va en ese archivo: no hace falta otra línea |
| Tests de backend | `tests/core/` (`test_security.py`, `test_email.py`); `tests/users/` con un archivo por tema y uno por migración | `tests/core/test_cache.py`, `tests/users/test_logout.py`, `tests/users/test_migracion_0022.py` |
| `src/lib/api.ts` | Único `fetch` de `src/` (`:128`); tiene `api.test.ts` | `cache: "no-store"` (§4.2) |
| `features/auth` | `AuthContext.tsx` (sin tests: la lógica que se prueba vive en módulos puros como `renovacion.ts`); `authApi.ts`; `ChangePasswordForm.tsx:94` usa `logout()` | La lógica nueva va en un módulo puro `sesion.ts` con su test (§5.4) |

---

## 2. Ramas y orden de entrega

| Orden | Fase | Backend | Frontend | Depende de |
| --- | --- | --- | --- | --- |
| 1 | A | `fix/api-sin-cache` | `fix/api-sin-cache` | — |
| 2 | B | `feat/auth-logout` | `feat/auth-logout` | Nada funcional; se mergea después de la A (D-06) |

Todas salen de `develop` actualizado y entran por PR hacia `develop`. En cada fase, el PR de frontend se mergea después del de backend. Las dos partes de la Fase A son independientes (cada una corrige el problema por su lado), así que pueden mergearse en cualquier orden.

---

## 3. Dependencias nuevas

Ninguna (NFR-27).

---

## 4. Fase A — API sin caché

### 4.1 Backend (`fix/api-sin-cache`)

| Archivo | Acción | Contenido |
| --- | --- | --- |
| `app/core/cache.py` | Crear | `SinCacheMiddleware`, middleware ASGI puro |
| `app/main.py` | Modificar | `app.add_middleware(SinCacheMiddleware)` |
| `tests/core/test_cache.py` | Crear | AC-123…AC-125 |
| `README.md` | Modificar | Una línea en "Seguridad transversal": las respuestas de la API no se guardan en caché |

**Middleware ASGI puro, no `BaseHTTPMiddleware`.** Envuelve `send` y, en el mensaje `http.response.start`, si `scope["path"]` empieza con `/api/` y los encabezados no traen `cache-control`, agrega `cache-control: no-store`. No lee ni copia el cuerpo, así que no afecta la descarga de archivos ni las respuestas `204`. Se registra con `add_middleware`, que lo deja por fuera de los manejadores de excepciones de FastAPI: también cubre las respuestas de `AppError`, `HTTPException` y los `422` de validación.

### 4.2 Frontend (`fix/api-sin-cache`)

| Archivo | Acción | Contenido |
| --- | --- | --- |
| `src/lib/api.ts` | Modificar | `cache: "no-store"` en el `fetch` de `apiRequest`, antes de `...rest`, para que un llamador pueda cambiarlo si algún día lo necesita (hoy ninguno lo hace) |
| `src/lib/api.test.ts` | Modificar | Verifica que `fetch` recibe `cache: "no-store"` |
| `src/features/auth/sesion.ts` | Crear | `leerIdentidadToken(token): { sub: number; sid: string \| null } \| null`, sin verificar la firma, con la misma decodificación que `leerTiemposToken` (que se mueve a un helper compartido `leerClaims` dentro de `renovacion.ts` o de `sesion.ts`, sin cambiar su contrato) |
| `src/features/auth/sesion.test.ts` | Crear | `leerIdentidadToken` con token válido, sin `sid`, mal formado y con `sub` no numérico |
| `src/features/auth/AuthContext.tsx` | Modificar | En la rehidratación: si `usuario.id !== leerIdentidadToken(token)?.sub`, `tokenStore.clear()` y `setAviso(…)` de RN-92 en lugar de `setUsuario` |

---

## 5. Fase B — Cierre de sesión en el servidor

### 5.1 Backend: token y sesión (`feat/auth-logout`)

| Archivo | Acción | Contenido |
| --- | --- | --- |
| `app/core/security.py` | Modificar | `crear_access_token(…, sid: str)` obligatorio: agrega el claim. `TokenPayload.sid: uuid.UUID \| None` (`None` si falta o no es un UUID válido; un `sid` mal formado en un token bien firmado no puede pasar, pero no se confía) |
| `app/core/deps.py` | Modificar | `SesionActual.sid`; en `_sesion_autenticada`, después de validar `token_version` y estado, si hay `sid`: `await db.get(SesionCerrada, sid)` y, si existe, `401 TOKEN_SESION_CERRADA` con `WWW-Authenticate` |
| `app/modules/users/models.py` | Modificar | `SesionCerrada` (§5.2) |
| `app/modules/users/service.py` | Modificar | `_emitir_token(usuario, *, auth_time, sid)`; login y `cambiar_password` usan `str(uuid.uuid4())`; `renovar_sesion` y `cerrar_sesiones` pasan `sesion.sid` o uno nuevo si es `None` (RN-93); `cerrar_sesion(db, sesion)` nuevo (§5.3) |
| `app/modules/users/router.py` | Modificar | `POST /logout` con `get_sesion_actual`, `status_code=204`, `responses=error_responses(401)` |
| `alembic/versions/0022_users_sesiones_cerradas.py` | Crear | §5.2 |
| `tests/users/test_logout.py` | Crear | AC-126…AC-132 |
| `tests/users/test_migracion_0022.py` | Crear | AC-133 |
| `README.md` | Modificar | `POST /api/v1/auth/logout` en la tabla de endpoints |

`SesionCerrada` importa desde `app.modules.users.models`, y `deps.py` ya importa `Usuario` de ese mismo archivo: no se agrega una dependencia nueva entre módulos.

### 5.2 Modelo y migración

```python
class SesionCerrada(Base):
    __tablename__ = "sesiones_cerradas"

    sid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), index=True
    )
    cerrada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    vence_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
```

`vence_en` lleva índice para el borrado de RN-95. La migración crea la tabla y sus índices con los nombres de `NAMING_CONVENTION`, y el downgrade la borra. Se revisa DT-26 al escribirla: si se pasa un nombre de restricción explícito, puede quedar prefijado dos veces.

### 5.3 Servicio

```python
async def cerrar_sesion(db: AsyncSession, sesion: SesionActual) -> None:
    """Cierra la sesión del token en el servidor (SPEC-12 RN-94, RN-95)."""
    ahora = datetime.now(UTC)
    await db.execute(delete(SesionCerrada).where(SesionCerrada.vence_en < ahora))
    if sesion.sid is not None:
        tope = sesion.auth_time + get_settings().jwt_sesion_max_horas * 3600
        await db.execute(
            insert(SesionCerrada)
            .values(sid=sesion.sid, usuario_id=sesion.usuario.id,
                    vence_en=datetime.fromtimestamp(tope, UTC))
            .on_conflict_do_nothing(index_elements=["sid"])
        )
    await db.commit()
```

`insert` es el de `sqlalchemy.dialects.postgresql`. Si `tope` ya pasó, la fila nace vencida y se borra en el próximo cierre: es correcto, porque esa sesión ya no puede renovarse (RN-66).

### 5.4 Frontend (`feat/auth-logout`)

| Archivo | Acción | Contenido |
| --- | --- | --- |
| `src/features/auth/authApi.ts` | Modificar | `cerrarSesionEnServidor(token)`: `apiRequest` con `auth: false` y el header `Authorization` explícito, porque el token ya se borró de `sessionStorage` (RN-97) |
| `src/features/auth/sesion.ts` | Modificar | `crearCanalSesion(Canal = globalThis.BroadcastChannel)`: `publicarCierre(sid)` y `escuchar(fn)`; si `Canal` no existe, las dos son no-op (RN-98). El constructor se inyecta para probarlo |
| `src/features/auth/sesion.test.ts` | Modificar | Canal con un `BroadcastChannel` falso: publica `{ tipo: "cierre", sid }`; ignora mensajes de otro tipo o mal formados; sin `BroadcastChannel` no falla |
| `src/features/auth/AuthContext.tsx` | Modificar | `logout(aviso?, { servidor })`: guarda el token, limpia estado y `sessionStorage`, publica el cierre con su `sid` y, sólo en el cierre pedido por el usuario, llama a `cerrarSesionEnServidor` sin esperar e ignorando errores (RN-97, RN-99). Un efecto escucha el canal y cierra con el aviso de RN-98 si el `sid` coincide con el del token propio. `TOKEN_SESION_CERRADA` suma su mensaje en `onSessionExpired` |
| `src/App.tsx`, `ChangePasswordForm.tsx` | Modificar | Los botones "Cerrar sesión" piden el cierre en el servidor |

Los cierres por `onSessionExpired`, por inactividad y el de `ResetPasswordPage` (`App.tsx:127`) no llaman al servidor (RN-99).

---

## 6. Verificación por PR

| PR | Verificación |
| --- | --- |
| Backend A | `pytest -q` completo en verde; `curl -i` a `/api/v1/auth/me` muestra `cache-control: no-store` |
| Frontend A | `npm run typecheck`, `npm run build`, `npm test`; recorrido de spec §2.3 en Chrome con DevTools → Network: `/auth/me` nunca sale de `(disk cache)` (AC-135) |
| Backend B | `pytest -q`; cobertura de lo nuevo de `core` y `users` ≥ 85 % (NFR-28); `alembic heads` con una sola cabeza; ciclo upgrade → downgrade → upgrade sobre la base de desarrollo |
| Frontend B | `npm run typecheck`, `npm run build`, `npm test`; recorridos de AC-136 en Chrome y Firefox |

---

## 7. Documentación y coordinación

| Momento | Qué | Dónde |
| --- | --- | --- |
| Al aprobar el spec | ADR-028 (D-01…D-08), estado de SPEC-12, H1 y H2 | `MEMORY.md` §1, §2 y §5; `AGENTS.md` §3 |
| Fase A mergeada | Avisar al equipo que ya se puede duplicar pestañas en demos; vaciar la caché una vez en las computadoras del laboratorio (EC-66) | `MEMORY.md` §5 |
| Fase B mergeada | `POST /auth/logout` y `TOKEN_SESION_CERRADA` en la guía técnica; estado de SPEC-12 | README del backend, `MEMORY.md` §1, `AGENTS.md` §3 |
| Despliegue (SPEC-11) | H1: el `nginx.conf` no agrega caché a `/api/` | `specs/11-despliegue-ci` |

---

## 8. Riesgos

| Riesgo | Mitigación |
| --- | --- |
| Un test existente compara los encabezados exactos de una respuesta | Se corre la suite completa en el PR de la Fase A; el middleware sólo agrega un encabezado |
| La consulta de RN-96 en cada pedido | Lectura por clave primaria sobre una tabla chica, que se vacía sola (RN-95). Si se nota, se suma con un `LEFT JOIN` a la carga del usuario |
| Carrera entre la renovación de una copia y el cierre en otra | La renovación pasa por `_sesion_autenticada`: un `sid` cerrado no se renueva. Si la renovación entró antes del cierre, el token nuevo tiene el mismo `sid` y cae en el próximo pedido (EC-61) |
| `0022` choca con una migración de otro perfil | `down_revision` se fija al abrir el PR; `alembic heads` antes de mergear |

---

## 9. Historial

| Versión | Fecha | Autor | Cambio |
| --- | --- | --- | --- |
| 1.0.1 | 2026-11-26 | Perfil 1 (con asistencia de IA) | Migración `0022` (`0021` es `core_envios_correo`, SPEC-11). Fase A implementada (tareas T-01, A-01…A-03, AF-01…AF-03) |
| 1.0.0 | 2026-11-24 | Perfil 1 (con asistencia de IA) | Plan inicial, sobre el spec v1.0.0 aprobado |
