---
titulo: SIPAweb - Manual establecer entorno de trabajo
subtitulo: Crear tú entorno de trabajo, para publicar tú sitio web
estado: actualizado
fecha_creacion: 15/03/2026
fecha_publicacion: 15/03/2026
tag: manuales, documentación, guías
tipo: post
autor: Daniel Miñana
---

# Estableciendo tu Entorno de Trabajo

Para dar vida a un proyecto como SIPAweb, no necesitas una supercomputadora, pero sí una **arquitectura de herramientas** coherente. En esta guía te explico el entorno que yo utilizo, detallando por qué cada pieza es importante, para que seas libre de replicarlo o adaptarlo a tus propias preferencias.

---

## 1. El Sistema Operativo: La Base de Operaciones

El motor de construcción de este sitio corre sobre **Python 3**. Esto significa que cualquier sistema que pueda ejecutar Python es válido.

- **Mi elección: Ubuntu (Linux).** **¿Por qué?** Por su gestión nativa de paquetes, seguridad y estabilidad. En ciberseguridad, Linux es el estándar. Si buscas un entorno limpio donde los scripts "simplemente funcionen", esta es la opción lógica.
      - **Tu alternativa:**
            - **Windows:** Si prefieres no salir de Windows, mi recomendación profesional es instalar **WSL2 (Windows Subsystem for Linux)**. Tendrás un Ubuntu corriendo dentro de tu Windows, evitando conflictos de rutas o permisos.
            - **macOS:** Funciona de forma excelente al ser un sistema basado en Unix.

## 2. El Editor de Código (IDE): Tu Mesa de Dibujo

No estamos escribiendo en un procesador de textos tradicional (como Word); estamos escribiendo **Markdown**, un lenguaje que separa el contenido del diseño.

- **Mi elección: Visual Studio Code.**
      - **¿Por qué?** Es gratuito,ligero y extremadamente potente.Lo que lo hace imbatible son sus extensiones:
            - **Markdownlint:** Te avisa si tu sintaxis tiene errores antes de que publiques.
            - **Python:** Proporciona depuración y resaltado para el motor de SIPAweb.
            - **GitLens:** Para ver la trazabilidad de cada cambio que haces.
      - **Tu alternativa:**
            - **Cursor:** Si quieres experimentar con asistencia de IA integrada.
            - **VSCodium:** Si prefieres una versión 100% libre de telemetría de Microsoft, manteniendo la misma compatibilidad.

## 3. Filosofía de Trabajo

Independientemente de lo que elijas, el objetivo es el mismo: **Fluidez**. Tu entorno debe permitirte pasar de una idea en un fichero `.md` a una página web visible en pocos segundos.

> **Nota de Seguridad:** Elijas el sistema que elijas, asegúrate siempre de trabajar en entornos virtuales (venv) para Python. Esto mantiene las dependencias de tu web aisladas del resto de tu equipo, evitando "contaminaciones" de software.
