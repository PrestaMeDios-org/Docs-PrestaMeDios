# Presentación final — banco de preguntas y registro de devoluciones

> **Provisorio.** Respuestas cortas (menos de un minuto) para el bloque 3. Cada una dice quién responde y dónde está el respaldo. Revisarlas con el estado real la semana del final.

## Cómo manejamos el bloque

1. Quien modera (Perfil 1) repite la pregunta en voz alta y la deriva al dueño del dominio.
2. Se responde corto; si piden detalle, se ofrece el anexo o el documento.
3. Si no sabemos, lo decimos y lo anotamos como devolución. No inventar.
4. Una persona que no esté respondiendo completa la tabla del final.

## Producto y alcance

| Pregunta | Respuesta | Quién | Respaldo |
| :-- | :-- | :-- | :-- |
| ¿Qué porcentaje del ERS está implementado? | `[__]` de 47 de punta a punta; lo que falta es `[…]` y quedó afuera por `[…]` | P1 | Lámina 6, anexo, análisis §4.1 |
| ¿Por qué no hicieron el asistente IA? *(si no está)* | Priorizamos el circuito de préstamo, que es lo que reemplaza al formulario. La arquitectura ya lo contempla: consume la misma API | P5 | Lámina 15, ERS IA-02 |
| ¿Lo está usando el Laboratorio? | `[Todavía no / piloto desde __]`. Para usarlo falta servidor, inventario real y un responsable | P1 | Lámina 14, análisis §5 |
| ¿Qué pasa con los préstamos de alta gama? | El estudiante o docente adjunta el PDF de la resolución del Consejo; el admin la verifica antes de aprobar; el docente de la materia no lo descarga | P3 | PRE-05, SPEC-03 RN-60 |
| ¿Cómo sabe el docente qué solicitudes son de su materia? | `[Respuesta según cómo se resuelva N1 del análisis: lista de asignaturas cargada por el admin…]` | P3 | Análisis §3.1 N1 |
| ¿Por qué una web y no una app móvil? | El ERS pide web con posibilidad de móvil; la API ya lo permite | P1 | ERS, Plataformas |

## Técnica

| Pregunta | Respuesta | Quién | Respaldo |
| :-- | :-- | :-- | :-- |
| ¿Por qué un monolito y no microservicios? | Cinco personas y un cuatrimestre: un despliegue y una base. Igual aislamos dominios con dueños y funciones públicas, así que separar uno después es viable | P1 | Lámina 7, ADR-002 |
| ¿Cómo evitan reservas superpuestas con dos pedidos simultáneos? | La base lo impide con `EXCLUDE USING gist` sobre rangos de tiempo; el servicio valida antes para dar un mensaje claro, y la base es la garantía final | P4 | ADR-004, ADR-019 |
| ¿Y dos admins asignando la misma unidad? | Bloqueo de filas (`FOR UPDATE`) en orden de id; la prueba falla sin el bloqueo y pasa con él | P2 / P3 | DT-28, SPEC-05 T2.8 |
| ¿Por qué FastAPI y PostgreSQL? | Asincronía y OpenAPI automático (el asistente lo consume); PostgreSQL por las restricciones de exclusión y la integridad transaccional | P1 | ERS, Arquitectura |
| ¿Por qué no SQLite en los tests? | Porque las garantías que importan (exclusión, bloqueos) son de PostgreSQL; un test en SQLite pasaría sin probarlas | P2 | `AGENTS.md` §7 |
| ¿Cómo manejan la sesión? ¿Por qué no refresh token? | JWT de 30 minutos que se renueva con actividad, tope de 8 h, guardado en `sessionStorage` porque las PC del Laboratorio son compartidas. Más simple que un refresh token y suficiente | P1 | ADR-015, ADR-024 |
| ¿Cómo garantizan que un admin de Río Grande no vea Ushuaia? | La sede sale del usuario autenticado, nunca del pedido; cada consulta pasa por `resolver_alcance_sede`; hay tests por sede | P1 | SPEC-02 |
| ¿Cómo cambian las reglas (plazos, horarios)? | Desde el panel de parámetros, con bloqueo optimista, versión e historial de quién cambió qué | P1 | GLO-03, ADR-006 |
| ¿Qué cobertura de tests tienen? | `[__] %` global; 96 % en core/users/files y 98 % en inventory al momento de cerrar cada spec | P2 | Lámina 10 |

## Proceso y uso de IA

| Pregunta | Respuesta | Quién | Respaldo |
| :-- | :-- | :-- | :-- |
| ¿Cuánto del código lo escribió una IA? | `[Respuesta honesta y consensuada.]` La IA redactó e implementó bajo specs aprobados por personas; cada PR lo revisó un integrante; las decisiones están firmadas por perfil | P1 | Constitución, `AGENTS.md`, bitácora de `MEMORY.md` |
| ¿Cómo evitaron que la IA rompa la arquitectura? | Reglas escritas que el agente lee al empezar: no tocar módulos ajenos, no código sin spec aprobado, tests por criterio. Y revisión humana | P3 | `AGENTS.md` §7 |
| ¿Cómo se coordinaron cinco personas? | Un dueño por módulo; los pedidos entre módulos se escriben en la memoria compartida y en el spec (ítems C, K, S) | P3 | `MEMORY.md` §5 |
| ¿En qué se equivocaron al estimar? | `[Números de ClickUp: estimado contra real.]` El préstamo, el corazón, quedó para el final; la coordinación entre módulos llevó más que el código | P5 | Lámina 12 |
| ¿Qué harían distinto? | Empezar por el préstamo, desplegar desde el primer mes, pantalla y backend en el mismo sprint | P5 | Lámina 12 |
| ¿Cómo validaron los requisitos? | Reglamento, tres entrevistas y recorridos con software funcionando; donde el Reglamento no fija números, los propuso el equipo y son configurables | P1 | Lámina 4, análisis §2–3 |

## Producción y futuro

| Pregunta | Respuesta | Quién | Respaldo |
| :-- | :-- | :-- | :-- |
| ¿Quién lo mantiene después de la materia? | `[Respuesta acordada con el Laboratorio y la universidad.]` | P1 | Análisis §5.5 |
| ¿Qué datos personales guardan y cómo los protegen? | DNI, teléfono, correo y foto. Contraseñas con Argon2id, acceso por rol y sede, sin datos personales en logs. Falta la política de privacidad (Ley 25.326) antes de producción | P1 | Anexo de seguridad |
| ¿Cuánto cuesta ponerlo en marcha? | Un servidor chico con Docker, PostgreSQL y una casilla de correo institucional; `[estimar con el área de sistemas]` | P1 | Análisis §5.2 |
| ¿Sirve para otros laboratorios? | Sí, el modelo de sedes, roles y parámetros es genérico; es una propuesta nuestra | P5 | Lámina 15 |

## Registro de devoluciones

| # | Quién (profesor, jurado, público) | Devolución | Tipo (error, mejora, requisito, documentación) | Acción | Responsable | ClickUp |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |

> Después de la presentación: cargar cada fila en ClickUp y, si cambia un requisito o una decisión, registrarla en `MEMORY.md` (bitácora y, si corresponde, ADR).
