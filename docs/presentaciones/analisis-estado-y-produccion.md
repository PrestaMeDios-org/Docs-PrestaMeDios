# Análisis de estado: fuentes, validación, pendientes y salida a producción

> **Fecha:** 10/11/2026; estado por requisito (§1 y §4) actualizado el 12/11 sobre `develop` de Backend (`1c89c53`) y Frontend (`6ae5db4`) · **Base original:** `develop` de Backend (`e54ad16`) y Frontend (`e1ae84e`), `docs/ERS.md` (con el Docs PR #25), `MEMORY.md` (última actualización 10/11) y `docs/pruebas/recorrido-funcional.md`.
> **Para qué sirve:** preparar la demo del 12/11 y la presentación final, y acordar en el equipo qué falta para que la aplicación la use el Laboratorio de verdad.
> **Cómo se armó:** lectura del ERS, la memoria, los specs, el código y la historia de PR de los dos repos, con asistencia de IA. El estado por requisito es una estimación del equipo: cada perfil debería revisar su fila antes de citar los números afuera.

---

## 1. Resumen

- **De dónde sale lo que sabemos:** el Reglamento del LMA (Res. CICSE 056/2023), tres entrevistas con la referente (27/08, 04/09 y 16/10), un pedido puntual de permisos (18–21/09) y el recorrido funcional del 10/11. Todo lo demás son decisiones del equipo (ADR), y varias no se validaron con la referente.
- **Estado:** de los 47 requisitos del ERS, **34 funcionan desde la pantalla (72 %)** al 12/11 (eran 22 el 10/11: el 11/11 entraron el formulario de solicitud, la bandeja de validaciones, el aval, el horario por sede y las mejoras de espacios) y **13 no empezaron**. La cátedra pide al menos un 80 % para el final.
- **Lo que más riesgo tiene sin corroborar:** cómo sabe el sistema qué docente está a cargo de qué asignatura (PRE-03, PRE-20), las cantidades de las sanciones (USR-09) y si la regla de 24 h aplica a docentes.
- **Documentación desactualizada:** el snapshot de `MEMORY.md` §1 decía que `notifications`, la Fase 2 de `loans` y la disponibilidad de `inventory` estaban en PR abiertos (corregido el 10/11), y `tasks.md` de SPEC-05 no marca T2.9 ni T2.10 aunque ya están en `develop`. Y el ERS tiene vacías secciones que la cátedra exige para aprobar el final (§6).
- **Para "salir a la calle"** falta, además del circuito de préstamo en pantalla: un servidor con HTTPS, copias de seguridad, correo institucional, el inventario real cargado, términos y condiciones con aval del Laboratorio, y un responsable del sistema después de la materia (§5).

---

## 2. De dónde sacamos la información

| # | Fuente | Fecha | Qué aportó | Dónde quedó |
| :-- | :-- | :-- | :-- | :-- |
| F1 | **Reglamento del LMA**, Res. CICSE N° 056/2023 | 2023 | Plazos (4 días general, 15 notebooks), préstamos especiales con aval, horario con supervisión presencial | ERS, Referencias. **El PDF no está en ningún repo** |
| F2 | **Primera entrevista** con la referente | 27/08/2026 | Problema actual, lockers, horario 09–16, Isla de Digitalización como requisito futuro | ERS, Iteración 1 |
| F3 | **Segunda entrevista** | 04/09/2026 | El estudiante pide directo al administrador (el docente sólo observa); se elimina el "Administrador ICSE" | ERS, Iteración 2; ADR-001 |
| F4 | **Pedido de permisos** de la referente | 18–21/09/2026 | Rol Superadministrador con ambas sedes; admins locales sólo su sede | ERS, Iteración 3; GLO-01 |
| F5 | **Prototipos en Figma** y DER | Iteración 4 | Pantallas de estudiante, docente y admin; modelo de datos | ERS, Diseño; `docs/diseno/` |
| F6 | **Tercera entrevista y demo del Sprint 1** | 16/10/2026 | Horario por sede, teléfono obligatorio, correo del laboratorio, renovación de notebooks como nueva solicitud, aval PDF también para docentes, llamados de atención | ERS, Iteración 5; ADR-022 |
| F7 | **Decisiones del equipo** donde las fuentes no alcanzaban | 07/10 en adelante | Cantidades de sanciones, delegación de superadmin, interpretación de las 24 h, políticas de sesión y contraseña | `MEMORY.md` §2 (ADR-008…024) y §13 de cada spec |
| F8 | **Recorrido funcional** con la cliente | 10/11/2026 | Revisión rol por rol de lo implementado | `docs/pruebas/recorrido-funcional.md`. **El registro de la reunión quedó vacío** |
| F9 | Bibliografía de método | — | IEEE 830 (estructura del ERS) y Scrum | ERS, Referencias |

> **Observación:** casi todo el conocimiento del negocio viene de **una sola persona** (la referente). No hay entrevistas con los admins locales (Victoria y Facundo), con docentes ni con estudiantes. Es el principal sesgo del relevamiento.

---

## 3. Qué no se corroboró

### 3.1 Reglas que definió el equipo y no validó la referente

| # | Tema | Qué asumimos | Origen | Riesgo si está mal | Cómo cerrarlo |
| :-- | :-- | :-- | :-- | :-- | :-- |
| N1 | **Docente ↔ asignatura ↔ estudiante** | PRE-03 pide la asignatura y PRE-20 muestra al docente las solicitudes "de su asignatura", pero **no existe un modelo de asignaturas ni de inscripciones** (C3 abierto en SPEC-05) | ERS | **Alto:** sin esto PRE-20 no se puede implementar y la asignatura es texto libre | Pedir a la referente la lista de materias de la Licenciatura y quién las dicta; decidir si el estudiante elige la materia o se carga a mano |
| N2 | Cantidades de **sanciones** | 3 llamados = 1 falta; 1 falta → el admin decide; 2 faltas → suspensión automática; duración fija | ADR-022 (d, e), el Reglamento no fija números | Medio: sancionar de más o de menos | Preguntas abiertas de `MEMORY.md` §6.2 (¿el contador vuelve a cero? ¿las faltas vencen? ¿cuántos días de suspensión?) |
| N3 | **24 h de anticipación para docentes** | Aplica también a docentes | ADR-011; la entrevista sólo lo confirmó para estudiantes | Medio: un docente no puede pedir para la clase de mañana | `MEMORY.md` §6.1 |
| N4 | Qué significa "plazos mínimos (24 horas)" | Anticipación mínima entre la solicitud y el retiro | ADR-011 (interpretación interna) | Bajo | Confirmar con la referente y con el Reglamento (F1) |
| N5 | **Delegación de superadmin** | Sólo a un admin local, con duración fija y revocable | ADR-022 (g) | Bajo | Confirmar en la próxima reunión |
| N6 | Tolerancia de retiro | 2 h (`prestamo.tolerancia_retiro_horas`) | Ejemplo del texto de PRE-08 | Medio: cancela reservas de quien llega tarde | La entrevista confirmó que hay tolerancia, no el valor |
| N7 | **Horario de Río Grande** | 10:00–17:00 | Dado "por ejemplo" en la entrevista | Medio: franjas mal ofrecidas | Confirmar horarios reales de cada sede |
| N8 | Plazo máximo de los **docentes** | PRE-07 fija 4 días "para los estudiantes"; para docentes no hay número | ERS | Medio | Preguntar |
| N9 | Correo sin restricción de dominio | Cualquier email válido; la validación manual filtra | ADR-009 | Bajo | Informar a la referente |
| N10 | Cuentas rechazadas se conservan y se pueden volver a registrar | Sí | ADR-010 | Bajo | Informar |
| N11 | Sesión en computadoras compartidas | Se cierra al cerrar la pestaña; renovación cada 30 min con tope de 8 h | ADR-015, ADR-024 | Bajo: puede molestar a un admin con turno largo | Probar en las PC del Laboratorio |
| N12 | Lockers 1–7 **por sede** | Igual numeración en las dos sedes | Entrevista 1, sólo Ushuaia | Bajo | Confirmar en Río Grande |
| N13 | **Términos y Condiciones** (PRE-03) | Una casilla que el estudiante acepta | ERS | Medio: no hay texto | Redactarlo desde el Reglamento y pedir aval al Laboratorio |
| N14 | Manual, reglas de cuidado y **video instructivo** (PRE-01) | El sistema tiene el campo del video; el contenido lo pone el Laboratorio | ERS | Bajo | Pedir los enlaces o decidir que es opcional |

### 3.2 Cosas que nunca se probaron con usuarios reales

- **Resultado del recorrido del 10/11:** la tabla "Registro de la reunión" de `docs/pruebas/recorrido-funcional.md` está vacía. Si la cliente pidió cambios, hoy no constan en ningún lado. **Completarla antes del jueves.**
- **Usabilidad:** ningún estudiante ni docente usó la aplicación. Tampoco se probó en celulares, aunque es probable que los estudiantes la usen desde ahí.
- **Volumen:** no sabemos cuántos equipos, solicitudes por semana ni picos (inicio de cuatrimestre, entregas de TIF) maneja cada sede. No se hizo prueba de carga.
- **Datos reales:** el inventario de la demo es inventado. No se vio la planilla real (códigos de inventario, series, lockers, alta gama).
- **Reglamento:** nadie del equipo dejó registrado que los números del ERS (4 y 15 días, 09–16 h) coinciden con el texto de la Res. 056/2023, y el PDF no está en el repo.
- **Correo real:** la recuperación de contraseña se probó con un servidor SMTP local (sin Mailpit); falta probarla con una casilla institucional.

### 3.3 Proceso y documentación sin cerrar

| Tema | Situación | Qué hacer |
| :-- | :-- | :-- |
| Constitución | v1.1.0 sin ratificación del equipo; enmienda 1.1.1 propuesta (ADR-019, ADR-021) | Ratificarla en una reunión y dejarlo en la bitácora |
| SPEC-04 v1.2.0 | `BORRADOR`, pero su addendum (backend PR #19) y la Fase B (backend PR #24, frontend PR #13) ya están en `develop` | Aprobar la versión o documentar la excepción (P1.1) |
| SPEC-05 v1.0.1 | Corrige EC-L10 y espera el OK del Perfil 1 | Darlo o pedir cambios |
| SPEC-06 | Spec aprobado, plan y tareas en `BORRADOR`, Fase A ya mergeada (backend #22, frontend #12) | Aprobar plan y tareas |
| SPEC-09 | Horario y correo por sede y teléfono obligatorio. **Aprobado el 11/11** (Docs PR #31); Fase A en `develop` (backend #35, frontend #26), Fase B en revisión (backend #38, frontend #27) | Revisar y mergear la Fase B; que `spaces` y `loans` lean el horario por sede (H1, H2) |
| `MEMORY.md` §1 | Decía que `notifications`, la Fase 2 de `loans` y la disponibilidad estaban en PR abiertos, y que había 320 tests | **Corregido el 10/11** (backend #22, #23, #24, #28; frontend #12, #13, #18; 895 tests) |
| `tasks.md` de SPEC-05 | T2.9 (cancelar una orden aprobada) y T2.10 (ajuste horario) figuraban `[ ]` aunque estaban en `develop` desde el backend PR #28 | **Corregido por el Perfil 3 el 11/11** |
| Versión de Python | No está fija para producción (K8 de SPEC-03); se probó con 3.12 y 3.14 | Fijarla en el spec de despliegue |

---

## 4. Qué quedó pendiente

### 4.1 Estado por requisito

Leyenda: **✔** funciona desde la pantalla · **◐** funciona con salvedades · **B** backend listo, sin pantalla · **✘** sin empezar.

| Req. | Estado | Nota |
| :-- | :-- | :-- |
| USR-01 Registro e inicio de sesión | ✔ | |
| USR-02 Recuperación de contraseña | ◐ | Falta probar con correo real |
| USR-03 Datos de contacto y foto | ✔ | |
| USR-04 Gestión de usuarios | ✔ | |
| USR-05 Registro con validación manual | ◐ | Teléfono obligatorio en revisión (SPEC-09 Fase B, rama `feat/users-telefono`) |
| USR-06 Panel de solicitudes | ✔ | Mis solicitudes (préstamos, frontend PR #24) y Mis reservas (espacios) |
| USR-07 Historial de actividad | ◐ | Historial de espacios confirmados y usados (frontend PR #20) y órdenes pasadas en Mis solicitudes; falta una vista unificada |
| USR-08 Logs de auditoría global | ✘ | Hay historiales parciales (parámetros, cuentas, órdenes) |
| USR-09 Llamados de atención y suspensiones | ✘ | Depende de N2 |
| PRE-01 Catálogo con disponibilidad | ✔ | DT-31 y DT-32 resueltas (frontend PR #23) |
| PRE-02 Búsqueda y filtros | ✔ | |
| PRE-03 Carrito y orden de pedido | ✔ | Formulario de solicitud desde el carrito (frontend PR #24) |
| PRE-04 Validación del formulario | ✔ | Errores por campo en el formulario de solicitud |
| PRE-05 Alta gama con aval PDF | ✔ | Aval con `files` (backend PR #34); la admin lo descarga desde la bandeja |
| PRE-06 Fechas y franjas horarias | ✔ | Con el horario global: falta leer el horario por sede (T1.13) |
| PRE-07 Límite de 4 días | ✔ |
| PRE-08 Cancelación automática | ✘ | Necesita una tarea programada |
| PRE-09 Solicitudes de docentes | ✔ |
| PRE-10 Aprobación o rechazo | ✔ | Bandeja: aprobar eligiendo unidades libres, rechazar con motivo |
| PRE-11 Renovación de notebooks | ✘ | Responde `501` |
| PRE-12 Gestión de stock | ◐ | Falta el historial por unidad en pantalla |
| PRE-13 Entrega y devolución | ✘ | Fase 3 de SPEC-05 |
| PRE-14 Bloqueo por mantenimiento | ✔ | |
| PRE-15 Bandeja centralizada | ✔ | Bandeja de Validaciones por jurisdicción |
| PRE-16 Calendario maestro | ✘ | |
| PRE-17 Cancelación forzada | ◐ | La admin cancela una orden aprobada con motivo; falta la alerta al usuario (NOV-04) y `reservas_afectadas` en `inventory` |
| PRE-18 Modificar horario al aprobar | ✔ | Ajuste de horario en el modal de aprobación |
| PRE-19 Alta de equipamiento | ✔ | |
| PRE-20 Panel docente | ✘ | Bloqueado por N1 |
| RES-01 Calendario de espacios | ✔ | |
| RES-02 Solicitud de turno | ✔ | Confirmación previa y franjas contiguas en una sola reserva (frontend PR #20) |
| RES-03 Cancelación | ✔ | También cancela una reserva aprobada (backend PR #32) |
| RES-04 Bloqueo administrativo | ✔ | |
| RES-05 Aprobación o rechazo | ✔ | Muestra el nombre del solicitante sólo a la admin (K1, backend PR #32) |
| NOV-01 Portal estático | ✔ | |
| NOV-02 Comunicados por sede | ✔ | |
| NOV-03 Alertas de devolución | ✘ | Fase C de SPEC-06 |
| NOV-04 Campanita | ✘ | Hoy muestra datos fijos |
| GLO-01 Sedes y jerarquía | ◐ | Falta la delegación temporal |
| GLO-02 Horarios operativos | ◐ | El horario por sede ya existe en `config`, pero `spaces` y `loans` todavía leen el global |
| GLO-03 Panel de parámetros | ◐ | Horario y correo de contacto por sede (SPEC-09 Fase A, PR #35 y #26); faltan las claves de sanciones (USR-09) |
| GLO-04 Calendario dinámico | ✔ | Bloqueos reversibles, con motivo al pasar el mouse (SPEC-08, PR #32 y #20) |
| GLO-05 Anotaciones privadas | ✘ | |
| GLO-06 Tema y menú | ✔ | |
| IA-01…IA-03 Asistente | ✘ | SPEC-07 sin redactar |

**Totales al 12/11:** ✔ 26 · ◐ 8 · B 0 · ✘ 13. "De punta a punta" (✔ + ◐) = 34 de 47 (72 %). Al 10/11 eran ✔ 11 · ◐ 11 · B 10 · ✘ 15 (22 de 47).

### 4.2 Deuda y observaciones que se ven en una demo

- ~~DT-31 y DT-32 (detalle de equipo)~~ y ~~reserva con un clic, franja marcada después de cancelar y "Usuario #N" (K1)~~: resueltas el 11/11 (frontend PR #20 y #23, backend PR #32).
- La campanita de la barra superior muestra datos fijos (`Navbar.tsx`) hasta la Fase B de SPEC-06.
- Cambiar el horario de una sede en Parámetros todavía no mueve las franjas de espacios ni de préstamos (leen el horario global).
- Pantallas "pendiente de implementación": Gestión de Entregas, Historial, Calendario de Operaciones, Anotaciones y Validaciones Pendientes del docente.

### 4.3 Para llegar al 80 %

Al 12/11 hay 34 de 47 (72 %). Para pasar el 80 % (38) hacen falta al menos 4 de: PRE-13, PRE-20, PRE-11, PRE-08, NOV-03, NOV-04, PRE-16. **IA-01…03, GLO-05 y USR-08 pueden quedar como trabajo futuro** si la cátedra lo acepta: conviene preguntarlo en la demo del 12/11.

---

## 5. Qué necesitamos para que la app "salga a la calle"

Pensado como un **piloto**: una sede (Ushuaia), uno o dos cuatrimestres, conviviendo un tiempo con el formulario de Google.

### 5.1 Funcionalidad mínima para el piloto

- [ ] Circuito de préstamo completo en pantalla: solicitud con asignatura y términos, mis solicitudes, bandeja, aprobación con ajuste de horario.
- [ ] Entrega y devolución en el mostrador, con préstamos demorados en rojo (PRE-13).
- [ ] Aval PDF de alta gama conectado (K3).
- [ ] Al menos un aviso por correo: aprobación/rechazo y vencimiento (NOV-03).
- [ ] Horario por sede y teléfono obligatorio (SPEC-09): Fase A en `develop`, Fase B en revisión; falta que `spaces` y `loans` lean el horario por sede.
- [ ] Corregir lo de §4.2.

### 5.2 Infraestructura y operación

- [ ] **Dónde corre:** servidor de la UNTDF (área de sistemas) o un proveedor; hay que decidirlo y pedir el espacio. Es la decisión más lenta: arrancar ya.
- [ ] Dominio (por ejemplo, un subdominio de la universidad) y **HTTPS**.
- [ ] Imágenes Docker de backend y frontend, `docker compose` y un `README` de despliegue (ADR-018, Perfil 1).
- [ ] PostgreSQL con `btree_gist`, usuario sin privilegios de superusuario y migraciones con `alembic upgrade head`.
- [ ] **Copias de seguridad** automáticas diarias y una prueba de restauración documentada.
- [ ] **Correo saliente** con una casilla institucional (SMTP, SPF/DKIM para no caer en spam).
- [ ] Tareas programadas: `procesar-vencimientos` (PRE-08, NOV-03) y `enviar-correos` (SPEC-06), y limpieza de archivos huérfanos.
- [ ] CI en GitHub Actions: tests de backend contra PostgreSQL, typecheck, tests y build del frontend en cada PR.
- [ ] Logs y monitoreo mínimo (que alguien se entere si la app se cae).
- [ ] Ramas: llevar `develop` → `staging` → `main`; hoy `main` del backend es anterior a SPEC-02.

### 5.3 Seguridad y datos personales

- [ ] `JWT_SECRET_KEY` nueva y fuera del repo, CORS sólo con el dominio real, `DEBUG` apagado, Swagger restringido o desactivado en producción.
- [ ] Revisión de seguridad básica (OWASP Top 10): límite de intentos en el login, cabeceras HTTP, tamaño de archivos subidos.
- [ ] **Ley 25.326 de Protección de Datos Personales:** guardamos DNI, teléfono, correo y foto. Hace falta una política de privacidad, informar para qué se usan y quién es el responsable de la base, y consultar con la universidad si corresponde registrarla.
- [ ] Credenciales del superadmin creadas en el servidor con la CLI, nunca por defecto.

### 5.4 Datos iniciales

- [ ] Inventario real de las dos sedes (equipos, unidades, series, códigos, lockers, alta gama, plazos) desde la planilla del Laboratorio, con un script de importación revisado por el Perfil 2.
- [ ] Espacios reales de cada sede y sus horarios.
- [ ] Cuentas de los administradores reales (superadmin y admins locales).
- [ ] Lista de asignaturas y docentes (N1).
- [ ] Textos: términos y condiciones, portal estático (normativas, horarios), comunicado de lanzamiento.

### 5.5 Institucional

- [ ] Aval del Laboratorio y del ICSE para usar el sistema como canal oficial.
- [ ] **Quién mantiene el sistema cuando termine la materia:** dueño de los repositorios (la organización de GitHub), del servidor y del dominio, y a quién se reportan errores. Sin esto, la app no sobrevive al cuatrimestre.
- [ ] Licencia del código y transferencia formal a la universidad, si corresponde.

### 5.6 Adopción

- [ ] Manual corto para administradores (mostrador, aprobaciones, stock, parámetros) y una guía de una página para estudiantes.
- [ ] Capacitación de una hora con la referente y los admins locales, en las PC del Laboratorio.
- [ ] Prueba de usabilidad con 3 a 5 estudiantes, en celular y en computadora.
- [ ] Canal para reportar errores (un formulario o un correo) y alguien que lo mire.
- [ ] Plan de convivencia: durante cuántas semanas sigue el formulario de Google y cuándo se apaga.

### 5.7 Criterios para salir (sí / no)

1. La referente aprueba un recorrido completo de un préstamo, de la solicitud a la devolución, con datos reales.
2. Toda la suite de tests en verde en la CI, y la restauración de una copia de seguridad probada.
3. HTTPS, correo saliente y tareas programadas funcionando en el servidor.
4. Inventario real cargado y revisado por el Laboratorio.
5. Responsable de mantenimiento designado por escrito.

---

## 6. Lo que la cátedra pide y el ERS todavía no tiene

Revisando `docs/ERS.md`:

- **Cronograma por requerimientos:** la tabla es la plantilla ("Requerimiento 1…n").
- **Adecuación de la metodología:** tiene la nota "Para futuras entregas escribir cómo nosotros nos adaptamos a la metodología" (18/09). Material hay de sobra: SDD, perfiles, IA con Constitución y `AGENTS.md`.
- **Sobre las iteraciones:** pide analizar "el error en las estimaciones de tiempo". No hay nada escrito.
- **Sobre los entregables** (requerida para aprobar): "Aplicaciones y plataformas" y "Requerimientos técnicos para la instalación" están vacías.
- **Presentación visual para aprobar final:** vacía. Esta presentación y sus guiones (`docs/presentaciones/final/`) pueden ir enlazados ahí.
- La portada dice "Entrega parcial 09/10/2026".

---

## 7. Preguntas para llevar

**A la referente:** N1 (asignaturas y docentes), N2 (sanciones), N3 (24 h docentes), N6 (tolerancia), N7 (horario de Río Grande), N8 (plazo de docentes), N13 (términos), planilla del inventario real, y si acepta un piloto en Ushuaia.

**A la cátedra (jueves 12):** fecha y formato del final; si el asistente IA puede quedar como trabajo futuro; cómo cuentan el 80 % (por requisito, por caso de uso o por funcionalidad); si el final tiene que estar desplegado o alcanza con una instalación local.

**Al equipo:** quién pide el servidor a la universidad; quién completa las secciones del ERS de §6; ratificar la Constitución; aprobar SPEC-04 v1.2.0, SPEC-05 v1.0.1 y SPEC-08.
