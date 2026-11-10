# Diseño del sistema

Diagramas de PrestaMeDios: los que se presentaron a la cátedra durante el diseño y sus versiones actualizadas al código.

| Documento | Contenido | Original |
| --- | --- | --- |
| [arquitectura.md](arquitectura.md) | Capas, módulos del backend, dependencias entre módulos y seguridad | [arquitectura-v1.webp](historico/arquitectura-v1.webp) |
| [modelo-de-datos.md](modelo-de-datos.md) | Tablas de PostgreSQL por dominio, invariantes y equivalencias con el DER original | [der-v1.webp](historico/der-v1.webp) |
| [casos-de-uso.md](casos-de-uso.md) | Actores, casos de uso y su estado de implementación | [casos-de-uso-v1.png](historico/casos-de-uso-v1.png) |

## Originales y versiones vigentes

- **`historico/`** guarda los diagramas tal como se mostraron en la Iteración 4 (Figuras 1, 2 y 8 del ERS). No se editan: sirven para comparar y para el capítulo de iteraciones.
- **Los `.md` de esta carpeta** son la versión vigente. Están en Mermaid, que GitHub dibuja al abrir el archivo, así que se actualizan editando texto, en el mismo PR que cambia el código.

Del diseño al código hubo muchos cambios, porque la implementación siguió los specs (`specs/`) más que estos diagramas. Cada documento tiene una sección "Diferencias con el diseño original" que los resume.

## Mantenimiento

- Cada documento indica en **Estado** la fecha y la rama que refleja. Al actualizarlo, cambiar esa línea.
- Si un diagrama y el código difieren, manda el código: corregir el diagrama.
- Quien mergea una migración, un módulo o un caso de uso nuevo actualiza el documento que corresponda.
- Para exportar una imagen (por ejemplo, para una entrega), pegar el bloque en [mermaid.live](https://mermaid.live) y descargar PNG o SVG.
