# Sistema de Registro de Pacientes para un Consultorio Nutricionista

**Versión:** 1.0.0  
**Fecha:** 17/09/2025  
**Equipo de Desarrollo:** Equipo 3

---

## Descripción del Proyecto

El proyecto consiste en desarrollar una **aplicación de escritorio con interfaz gráfica (GUI)** orientada a la gestión de pacientes en consultorios de nutrición. Esta herramienta permitirá a los nutriólogos llevar un control digital, seguro y eficiente de la información clínica y de contacto de sus pacientes.

### Funcionalidades Principales

- **Módulo de acceso** con sistema de login seguro
- **Módulo principal** para registrar, editar, eliminar y visualizar pacientes
- **Módulo de cálculos automáticos** para indicadores de salud
- **Módulo de reportes** para generar documentos PDF
- **Recálculo automático** de indicadores cuando se actualizan datos relevantes

### Cálculos Automáticos Incluidos

- **Índice de Masa Corporal (IMC)**
- **Porcentaje de grasa corporal estimado**
- **Peso ideal**
- **Tasa Metabólica Basal (TMB)**

---

## Stack Tecnológico

### Lenguaje de Programación
- **Python** - Lenguaje principal para el desarrollo

### Framework GUI
- **PyQt6** - Framework para la interfaz gráfica de usuario
- Proporciona componentes nativos y multiplataforma
- Excelente rendimiento y estabilidad

### Base de Datos
- **SQLite** - Base de datos relacional embebida
- **sqlite3** - Módulo nativo de Python (incluido en la instalación estándar)
- Base de datos sin servidor, ideal para aplicaciones de escritorio simples

### Librerías Adicionales
- **bcrypt/argon2** - Hash seguro de contraseñas
- **ReportLab/WeasyPrint** - Generación de reportes PDF
- **sqlite3** - Módulo nativo Python para SQLite (sin dependencias adicionales)

### Plataforma Objetivo
- **Windows 10 o superior**
- Arquitectura de 64 bits recomendada

---

## Justificación del Proyecto

### Problemática Actual
- Muchos consultorios nutricionales utilizan métodos tradicionales:
  - Libretas físicas
  - Hojas de Excel
  - Agendas físicas
- Estos métodos presentan riesgos:
  - **Ineficiencia** en la gestión de datos
  - **Riesgo de confidencialidad**
  - **Dificultad en el seguimiento** del progreso de pacientes

### Solución Propuesta
- **Digitalización** del control de pacientes de manera accesible y segura
- **Automatización** de cálculos nutricionales y generación de reportes
- **Reducción** significativa del trabajo manual del profesional
- **Enfoque** en el tratamiento en lugar de la gestión de datos

---

## Arquitectura del Sistema

### Módulos Principales

#### 1. Módulo de Autenticación
- Login con correo y contraseña
- Hash seguro de credenciales
- Gestión de sesiones de usuario
- Límite de intentos de acceso

#### 2. Módulo de Gestión de Pacientes
- **Funciones CRUD** completas:
  - Crear nuevos pacientes
  - Leer/visualizar información
  - Actualizar datos existentes
  - Eliminar registros
- Validación de datos en tiempo real
- Búsqueda y filtrado de pacientes

#### 3. Módulo de Cálculos
- Cálculo automático de indicadores de salud
- Recálculo en tiempo real al modificar datos
- Validación de fórmulas oficiales
- Manejo de diferentes unidades de medida

#### 4. Módulo de Reportes
- Exportación a PDF
- Formato tabular profesional
- Previsualización antes de exportar
- Personalización de reportes

### Base de Datos

#### Tabla: usuarios
```sql
- id_usuario (Primary Key)
- nombre
- correo (Unique)
- contraseña_hash
- fecha_creacion
```

#### Tabla: pacientes
```sql
- id_paciente (Primary Key)
- id_usuario (Foreign Key)
- nombre
- apellidos
- sexo
- edad
- peso
- altura
- telefono_contacto
- correo_contacto
- fecha_registro
- fecha_ultima_actualizacion
```

---

## Objetivos del Proyecto

### Objetivo General
Desarrollar una aplicación de escritorio con interfaz gráfica que permita a los nutriólogos llevar un control detallado, organizado y seguro de sus pacientes, con capacidad de realizar cálculos automáticos de salud y exportar reportes.

### Objetivos Específicos
1. **Sistema de Autenticación**: Implementar validación segura de usuarios mediante correo y contraseña
2. **Gestión CRUD**: Crear módulo completo de gestión de pacientes
3. **Cálculos Automáticos**: Automatizar el cálculo de indicadores como IMC, TMB, grasa corporal y peso ideal
4. **Exportación PDF**: Integrar funcionalidad de exportación de datos
5. **Interfaz Intuitiva**: Asegurar una interfaz accesible y consistente
6. **Seguridad de Datos**: Garantizar validación y seguridad de la información

---

## Seguridad y Validaciones

### Medidas de Seguridad Implementadas
- **Hash seguro de contraseñas** con bcrypt/argon2 y sal aleatoria
- **Protección contra inyección SQL** mediante consultas parametrizadas o ORM
- **Validación de datos** tanto en frontend como backend
- **Límite de intentos de login** para prevenir ataques de fuerza bruta
- **Cierre automático** por inactividad

### Validaciones de Datos
- **Formatos de correo** y teléfono válidos
- **Rangos de edad** lógicos (0-120 años)
- **Valores numéricos** positivos para peso y altura
- **Campos obligatorios** claramente marcados
- **Mensajes de error** contextuales y descriptivos

---

## Características Técnicas

### Rendimiento
- **Tiempo de carga** de vistas principales ≤ 3 segundos
- **Respuesta de sistema** en condiciones normales < 3 segundos
- **Búsquedas** eficientes hasta 1,000 registros
- **Optimización** de consultas a base de datos

### Usabilidad
- **Guía de estilo** consistente en toda la aplicación
- **Validación en línea** con mensajes contextuales
- **Navegación intuitiva** entre módulos
- **Accesibilidad** básica implementada

### Compatibilidad
- **Windows 10** o superior
- **Hardware mínimo**: 4GB RAM, 1GB espacio en disco
- **Base de datos local** - sin dependencia de internet
- **Instalación independiente** - no requiere servicios externos

---

## Cronograma de Desarrollo

### Fase 1: Planeación y Requerimientos (15 días)
- Identificación de usuarios y roles
- Definición de funcionalidades
- Redacción de requerimientos funcionales y no funcionales
- **Milestone 1**: Aprobación de requerimientos

### Fase 2: Diseño (14 días)
- Arquitectura de software
- Diseño de base de datos
- Wireframes y prototipo UI
- Diagramas UML

### Fase 3: Desarrollo (Iterativo - 30 días)
- **Iteración 1**: Módulos básicos (Login, Pacientes básico)
- **Iteración 2**: Funciones avanzadas, optimización
- **Milestone 2**: Funcionalidades core implementadas

### Fase 4: Pruebas (13 días)
- Diseño de casos de prueba
- Pruebas funcionales, rendimiento y usabilidad
- **Milestone 3**: QA completado

### Fase 5: Cierre y Entrega (8 días)
- Corrección de errores críticos
- Documentación final
- Entrega y presentación

**Duración Total**: Aproximadamente 80 días (4 meses)

---

## Gestión de Riesgos

### Riesgos Identificados y Medidas de Mitigación

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|-----------|
| Acceso no autorizado | Posible | Crítico | Hash seguro, límite de intentos |
| Inyección SQL | Posible | Severo | ORM o consultas parametrizadas |
| Pérdida de datos | Unlikely | Severo | Confirmaciones, lógica de papelera |
| Cálculos incorrectos | Unlikely | Significativo | Validación con fórmulas oficiales |
| Interfaz confusa | Unlikely | Menor | Guía de estilo, validaciones en línea |

---

## Viabilidad del Proyecto

### Viabilidad Técnica
- **Tecnologías estables**: Python, PyQt6 y SQLite son tecnologías maduras y ampliamente utilizadas
- **Documentación abundante**: Amplio soporte de la comunidad
- **Instalación simplificada**: SQLite no requiere servidor separado ni configuración compleja
- **Portabilidad**: Base de datos en archivo único, fácil de respaldar y migrar
- **Rendimiento adecuado**: SQLite es eficiente para aplicaciones con pocos usuarios concurrentes
- **Compatibilidad**: Funciona en la mayoría de computadoras actuales sin dependencias adicionales

### Viabilidad Económica
- **Herramientas completamente gratuitas**: Todo el stack es de código abierto
- **Cero dependencias externas**: SQLite viene incluido con Python
- **Sin infraestructura adicional**: No requiere instalación ni configuración de servidor de base de datos
- **Sin licencias**: No requiere inversión en software propietario
- **Mantenimiento mínimo**: Aplicación completamente independiente
- **Respaldos simples**: Base de datos en archivo único facilita copias de seguridad

---

## Entregables del Proyecto

### Documentación
- Manual de usuario
- Manual técnico de instalación
- Documentación de arquitectura
- Guía de mantenimiento

### Software
- Aplicación ejecutable
- Código fuente completo
- Scripts de base de datos
- Casos de prueba

### Capacitación
- Demostración del sistema
- Sesión de Q&A con stakeholders
- Documentación de mejores prácticas

---

## Conclusión

Este sistema de registro de pacientes para consultorios nutricionistas representa una solución integral que combina **tecnología robusta** con **facilidad de uso**. El stack tecnológico seleccionado garantiza **estabilidad, seguridad y escalabilidad**, mientras que el enfoque en **automatización** y **usabilidad** permitirá a los profesionales de la nutrición enfocarse en lo más importante: el cuidado de sus pacientes.

La implementación de este sistema digitalizará y modernizará la gestión de consultorios nutricionales, proporcionando una base sólida para el crecimiento y la mejora continua de los servicios de salud nutricional.