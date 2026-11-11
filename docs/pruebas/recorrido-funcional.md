# Recorrido funcional con la cliente

> Guion para revisar la aplicación junto con la cliente, rol por rol, sobre lo que hoy está implementado en `develop` (Backend y Frontend).
> Usado en el recorrido con la cliente del 10/11/2026, después de verificarlo en local ese mismo día.

## Cómo usar este guion

- Cada paso tiene una **acción** y un **resultado esperado**. Durante la reunión marcar la columna **OK** (✔ / ✘) y anotar en **Observaciones** lo que diga la cliente.
- Los pasos están ordenados: algunos dependen de lo hecho antes (por ejemplo, la admin aprueba la cuenta que quedó pendiente).
- Conviene usar dos ventanas del navegador (una normal y otra privada) para tener abiertas dos sesiones a la vez, por ejemplo el docente y la admin.
- Todos los datos son ficticios. Las credenciales están en `demo/credenciales.md`, en la raíz del workspace, y **no se versionan**.

## Preparación (antes de la reunión)

1. Backend: `cd Backend-PrestaMeDios && source .venv/bin/activate && uvicorn app.main:app --reload` (puerto 8000).
2. Frontend: `cd Frontend-PrestaMeDios && npm run dev` (abrir `http://localhost:8443`).
3. Datos de prueba cargados con `demo/seed_demo.py`:
   - **Usuarios:** estudiante, docente y admin local de Ushuaia; un estudiante de Río Grande; una aspirante pendiente de aprobación.
   - **Catálogo:** 5 categorías y 7 equipos, con unidades en las dos sedes. Una Canon queda en mantenimiento y la Sony A7 III es de alta gama.
   - **Espacios:** Aula-Estudio e Isla de Edición 1 en Ushuaia, y Aula-Estudio Río Grande.
   - **Otros:** un comunicado global de bienvenida y una reserva **pendiente** del docente en el Aula-Estudio, de 10 a 12, dos días hábiles después de la carga.
4. Revisar la sección [Observaciones detectadas](#observaciones-detectadas-en-la-preparación) y decidir si se corrigen antes o se mencionan en la reunión.

| Usuario de prueba | Rol | Sede |
| :-- | :-- | :-- |
| Lucía Prueba | Estudiante | Ushuaia |
| Martín Prueba | Docente | Ushuaia |
| Carla Prueba | Administradora local | Ushuaia |
| Joaquín Prueba | Estudiante | Río Grande |
| Sofía Prueba | Estudiante (pendiente) | Ushuaia |
| Superadministrador | Superadministrador | Ambas |

---

## 1. Acceso público (sin sesión)

| # | Acción | Resultado esperado | Req. | OK | Observaciones |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 1.1 | Abrir la aplicación. | Se ve la pantalla de inicio de sesión con los enlaces "¿Olvidaste tu contraseña?" y "Registrate". | USR-01 | | |
| 1.2 | Ingresar con un email existente y una contraseña incorrecta. | Mensaje de error genérico, que no revela si el email existe. | USR-01 | | |
| 1.3 | Ir a **Registrate** y mirar el formulario, sin enviarlo. | Pide nombre, apellido, DNI, email, teléfono (opcional), sede, "Soy" (Estudiante / Docente) y la contraseña dos veces. | USR-05 | | |
| 1.4 | Intentar ingresar con la cuenta de **Sofía** (pendiente). | No puede entrar: la cuenta todavía no fue aprobada. | USR-05 | | |
| 1.5 | Ir a **¿Olvidaste tu contraseña?** e ingresar un email. | Muestra un mensaje neutro ("si el email existe, te llegará un enlace"). *En local no hay servidor de correo configurado: sólo mostrar la pantalla.* | USR-02 | | |

## 2. Estudiante — Lucía (Ushuaia)

| # | Acción | Resultado esperado | Req. | OK | Observaciones |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 2.1 | Iniciar sesión como Lucía. | Entra al **Catálogo de Equipos**. El menú lateral muestra Catálogo, Reservas de Espacios, Novedades y Mis Solicitudes. Abajo figura "Estudiante · Ushuaia". | USR-01 | | |
| 2.2 | Mirar la parte superior del catálogo. | Indica "7 disp. de 7", con chips por categoría (Audio 2, Cámaras 2, Iluminación 1, Notebooks 1, Trípodes 1). | PRE-01 | | |
| 2.3 | Filtrar por **Cámaras** y después buscar "zoom". | El filtro deja sólo las cámaras y la búsqueda encuentra el Grabador Zoom H5. | PRE-02 | | |
| 2.4 | Mirar la tarjeta de la **Canon EOS M50**. | Indica "2/3 uds.": una unidad está en mantenimiento y no cuenta como disponible. | PRE-14 | | |
| 2.5 | Abrir el detalle de la **Sony A7 III**. | Muestra marca, modelo, plazo máximo (4 días), locker, la etiqueta **Alta Gama** y la disponibilidad por día del mes. | PRE-01, PRE-05 | | |
| 2.6 | Mirar la tarjeta de la Sony A7 III. | No tiene botón de carrito: por ahora los equipos de alta gama no se pueden pedir (falta el circuito del aval). | PRE-05 | | |
| 2.7 | Agregar la Canon y el trípode al **Carrito** y abrirlo. | El carrito lista los dos equipos con su plazo máximo y permite cambiar la cantidad, quitar o vaciar. | PRE-03 | | |
| 2.8 | Mirar el botón **Continuar con la solicitud**. | Está deshabilitado ("Disponible próximamente"): el envío de la solicitud todavía no tiene pantalla. Ver *Fuera de este recorrido*. | PRE-03 | | |
| 2.9 | Ir a **Reservas de Espacios**, elegir Aula-Estudio y un día hábil a partir de pasado mañana. | Aparecen las franjas de 09:00 a 16:00, una por hora. Los días pasados se ven deshabilitados. | RES-01, GLO-02 | | |
| 2.10 | Elegir **mañana** y una franja que empiece antes de la hora actual (o sea, a menos de 24 h). | No permite reservarla: la anticipación mínima es de 24 h (parámetro `solicitud.anticipacion_min_horas`). | RES-02 | | |
| 2.11 | Hacer clic en una franja de un día válido. | La reserva queda creada y aparece en **Mis reservas** como **Pendiente**. *(Se crea con un solo clic.)* | RES-02 | | |
| 2.12 | **Cancelar** esa reserva desde Mis reservas. | Desaparece de Mis reservas. | RES-03 | | |
| 2.13 | Crear otra reserva en la **Isla de Edición 1** y dejarla pendiente. | Queda pendiente: la admin la va a rechazar en el paso 4.8. | RES-02 | | |
| 2.14 | Abrir **Novedades**. | Se ve el comunicado global "Bienvenida al sistema de préstamos", con fecha y autor. Lucía no tiene botón para publicar. | NOV-02 | | |
| 2.15 | Abrir **Mis Solicitudes**. | Pantalla "pendiente de implementación". | USR-06 | | |
| 2.16 | Abrir **Mi Perfil** (menú del avatar). | Muestra los datos de la cuenta (rol, sede y estado, sin poder editarlos) y deja editar los datos de contacto, la foto, la contraseña y cerrar todas las sesiones. | USR-03 | | |
| 2.17 | Cambiar el teléfono y guardar. Subir una foto de perfil. | Se guardan los cambios y la foto aparece en el avatar. | USR-03 | | |
| 2.18 | Cambiar entre tema claro y oscuro (icono de luna). | Toda la interfaz cambia de tema. | — | | |
| 2.19 | Cerrar sesión. | Vuelve al inicio de sesión. | — | | |

## 3. Docente — Martín (Ushuaia)

| # | Acción | Resultado esperado | Req. | OK | Observaciones |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 3.1 | Iniciar sesión como Martín. | Mismo menú de recursos que el estudiante, con el grupo **GESTIÓN** (Validaciones Pendientes, todavía sin implementar). Abajo figura "Docente · Ushuaia". | USR-01 | | |
| 3.2 | Ir a **Reservas de Espacios** → Mis reservas. | Figura la reserva del Aula-Estudio de 10:00 a 12:00 en estado **Pendiente**. | RES-02 | | |
| 3.3 | Dejar esta sesión abierta (en otra ventana) para ver el cambio de estado después. | — | — | |

## 4. Administradora local — Carla (Ushuaia)

| # | Acción | Resultado esperado | Req. | OK | Observaciones |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 4.1 | Iniciar sesión como Carla. | El menú tiene los grupos RECURSOS, OPERATIVA DIARIA y ADMINISTRACIÓN. Abajo figura "Administrador local · Ushuaia". | USR-01 | | |
| 4.2 | Ir a **Gestión de Usuarios → Pendientes**. | Aparece Sofía Prueba, con las acciones Aprobar, Rechazar y Editar. | USR-05 | | |
| 4.3 | **Aprobar** a Sofía. | Sale de Pendientes. Con eso Sofía ya puede iniciar sesión (repetir el paso 1.4 para comprobarlo). | USR-05 | | |
| 4.4 | Ir a **Directorio**. | Lista sólo cuentas de **Ushuaia**: no aparecen Joaquín (Río Grande) ni el superadmin. Carla no puede gestionar su propia cuenta ni la de otros administradores. | USR-04, GLO-01 | | |
| 4.5 | Filtrar por rol y estado, y buscar "90000002". | Encuentra a Martín por DNI. | USR-04 | | |
| 4.6 | **Suspender** a Lucía con un motivo y después **Reactivarla**. | El estado cambia a Suspendida y vuelve a Activa. Mientras está suspendida, Lucía no puede entrar. | USR-04 | | |
| 4.7 | Ir a **Reservas de Espacios** → Solicitudes pendientes y **Aprobar** la reserva del docente. | Sale de pendientes. En la sesión de Martín (recargar) la reserva figura como **Aprobada**, y la franja aparece ocupada en el calendario. | RES-05 | | |
| 4.8 | **Rechazar** la reserva de Lucía en la Isla de Edición, con un motivo. | Sale de pendientes y queda Rechazada. | RES-05 | | |
| 4.9 | **Bloquear** el Aula-Estudio un día completo con el motivo "Mantenimiento". | El día queda bloqueado y estudiantes y docentes no pueden reservarlo. | RES-04, GLO-04 | | |
| 4.10 | **Cargar nuevo espacio**, por ejemplo "Isla de Edición 2". | Aparece en la lista de espacios de Ushuaia. | — | | |
| 4.11 | Ir al **Catálogo**: cada tarjeta tiene botones para editar y dar de baja. Usar **+ Nuevo Equipo** para dar de alta uno, con una o dos unidades. | El equipo nuevo aparece en el catálogo y en Control de Stock. | PRE-19 | | |
| 4.12 | Editar el equipo recién creado (por ejemplo, la descripción). | El cambio se ve en la tarjeta. | PRE-12 | | |
| 4.13 | Ir a **Control de Stock** y desplegar la Canon (▸). | Se ven sus unidades con número de serie, código de inventario, locker y estado (una en mantenimiento). Sólo se listan las unidades de Ushuaia. | PRE-12 | | |
| 4.14 | Pasar una unidad a **mantenimiento** y después rehabilitarla. | En el catálogo, la cantidad disponible baja y vuelve a subir. | PRE-14 | | |
| 4.15 | **Dar de baja** el equipo creado en 4.11. Tildar "Mostrar equipos dados de baja" en el catálogo. | Desaparece del catálogo y sólo se ve con el filtro tildado. | PRE-12 | | |
| 4.16 | Ir a **Novedades → Nuevo comunicado** y publicar uno para Ushuaia. | Aparece en la lista. Al entrar como Lucía se ve, y al entrar como Joaquín (Río Grande) **no**. | NOV-02 | | |
| 4.17 | **Archivar** el comunicado. | Pide confirmación y deja de verse para estudiantes y docentes. | NOV-02 | | |
| 4.18 | Ir a **Parámetros**. | Lista las 8 reglas operativas (horario 09:00–16:00, plazos, anticipaciones) con el aviso "Sólo el Superadministrador puede modificar estos valores". | GLO-03 | | |
| 4.19 | Abrir Bandeja de Validaciones, Gestión de Entregas, Historial, Calendario de Operaciones y Anotaciones. | Muestran "pendiente de implementación". | — | | |

## 5. Superadministrador

| # | Acción | Resultado esperado | Req. | OK | Observaciones |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 5.1 | Iniciar sesión con la cuenta de superadmin. | El selector **SEDE** permite elegir Ushuaia, Río Grande o ambas. | GLO-01 | | |
| 5.2 | En el catálogo, cambiar entre Ushuaia y Río Grande. | Río Grande muestra 3 equipos (Canon, Rode, trípode), con 1 unidad cada uno. | GLO-01, PRE-02 | | |
| 5.3 | Ir a **Gestión de Usuarios → Directorio**. | Se ven las cuentas de las dos sedes, Joaquín incluido. | USR-04 | | |
| 5.4 | Usar **+ Nueva cuenta** para dar de alta un docente de Río Grande con una contraseña inicial. | La cuenta queda Activa. Al iniciar sesión con ella, pide cambiar la contraseña antes de entrar. | USR-04 | | |
| 5.5 | Editar a Carla: cambiarle la sede a Río Grande y volverla a Ushuaia. | Se guarda, y el cambio queda registrado en el historial de la cuenta. | USR-04 | | |
| 5.6 | Ir a **Parámetros**, cambiar el horario de cierre a 17:00 con un motivo y abrir **Historial**. | El valor sube de versión y el historial muestra el valor anterior, el nuevo, quién lo cambió y el motivo. En Reservas de Espacios aparece la franja 16:00–17:00. | GLO-03, GLO-02 | | |
| 5.7 | Volver el horario de cierre a 16:00. | — | GLO-03 | | |
| 5.8 | Publicar un comunicado **global**. | Lo ven usuarios de las dos sedes (comprobar con Joaquín). | NOV-02 | | |

## 6. Aislamiento de sedes — Joaquín (Río Grande)

| # | Acción | Resultado esperado | Req. | OK | Observaciones |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 6.1 | Iniciar sesión como Joaquín. | El catálogo muestra sólo lo que hay en Río Grande. No puede cambiar de sede. | GLO-01 | | |
| 6.2 | Ir a **Reservas de Espacios**. | Sólo aparece "Aula-Estudio Río Grande". | GLO-01 | | |
| 6.3 | Ir a **Novedades**. | Ve los comunicados globales, pero no el de Ushuaia del paso 4.16. | NOV-02 | | |

---

## Fuera de este recorrido (todavía no tiene pantalla)

Para contarle a la cliente qué viene después:

- **Solicitud de préstamo de equipamiento** (PRE-03, PRE-04, PRE-06…PRE-11, USR-06): el backend ya recibe la orden, la valida y la aprueba o rechaza asignando unidades (SPEC-05, fases 1 y 2). Faltan las pantallas: enviar la solicitud desde el carrito, *Mis Solicitudes*, *Bandeja de Validaciones* y *Validaciones Pendientes* del docente.
- **Pedidos de alta gama con aval en PDF** (PRE-05): el backend ya acepta el PDF; falta la pantalla.
- **Entregas, devoluciones, historial y calendario de operaciones** (PRE-13, PRE-15…PRE-18, PRE-20, USR-07, USR-08).
- **Anotaciones internas** (GLO-05) y **llamados de atención y faltas** (USR-09).
- **Notificaciones por correo y avisos de vencimiento** (NOV-02…NOV-04) y **asistente IA** (IA-01…IA-03).
- **Pendientes del Perfil 1:** horario por sede, teléfono obligatorio y delegación temporal (ADR-022); despliegue.

## Observaciones detectadas en la preparación

Se vieron al recorrer la aplicación en local el 10/11/2026. Cada una le corresponde al perfil dueño del módulo. Las del Perfil 2 están en `MEMORY.md` como DT-31 y DT-32:

1. **Mini-calendario del detalle de equipo sin estilos** (paso 2.5): los días del mes salen en una columna en lugar de una grilla, porque las clases `mc-*` de `MiniCalendario.tsx` no tienen CSS. → DT-31, Perfil 2.
2. **El texto del detalle de equipo no se lee en modo oscuro** (paso 2.5 con tema oscuro): `EquipmentDetailModal.tsx` no define color de texto, así que queda `#1A1A1A` sobre el fondo oscuro. Mientras no se corrija, mostrar el detalle en modo claro. → DT-32, Perfil 2.
3. **La reserva de espacio se crea con un solo clic** (paso 2.11), sin confirmación y sin pedir motivo. → Perfil 4.
4. **La franja sigue marcada después de cancelar** una reserva (paso 2.12), hasta recargar la página. → Perfil 4.
5. **"Usuario #3" en las reservas pendientes** de la admin (paso 4.7): muestra el id del usuario en lugar de su nombre. → K1 de SPEC-03, Perfil 4.

## Registro de la reunión

| Fecha | Participantes | Pasos recorridos | Pedidos de cambio |
| :-- | :-- | :-- | :-- |
| | | | |
