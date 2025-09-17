# NutriLink - Sistema de Registro de Pacientes

## Descripción

NutriLink es una aplicación de escritorio con interfaz gráfica diseñada para la gestión de pacientes en consultorios de nutrición. Permite a los nutriólogos llevar un control digital, seguro y eficiente de la información clínica y de contacto de sus pacientes.

## Características Principales

- 🔐 **Sistema de autenticación seguro** con login por correo y contraseña
- 👥 **Gestión completa de pacientes** (CRUD - Crear, Leer, Actualizar, Eliminar)
- 🧮 **Cálculos automáticos** de indicadores de salud (IMC, TMB, grasa corporal, peso ideal)
- 📊 **Generación de reportes** en formato PDF
- 🔄 **Recálculo automático** cuando se actualizan datos relevantes
- 🛡️ **Seguridad de datos** con hash seguro de contraseñas

## Stack Tecnológico

- **Lenguaje**: Python 3.12+
- **Framework GUI**: PyQt6
- **Base de Datos**: SQLite
- **Hash de Contraseñas**: bcrypt
- **Generación PDF**: ReportLab/WeasyPrint
- **Testing**: pytest

## Instalación

### Prerequisitos

- Python 3.12 o superior
- Git

### Pasos de Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/usuario/nutrilink.git
   cd nutrilink
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   ```

3. **Activar entorno virtual**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

5. **Ejecutar la aplicación**
   ```bash
   python main.py
   ```

## Estructura del Proyecto

```
nutrilink/
├── src/
│   ├── auth/          # Módulo de autenticación
│   ├── database/      # Gestión de base de datos
│   ├── gui/           # Interfaz gráfica
│   ├── calculations/  # Cálculos de indicadores
│   ├── reports/       # Generación de reportes
│   └── utils/         # Utilidades generales
├── tests/             # Pruebas unitarias
├── config/            # Configuración
├── docs/              # Documentación
├── data/              # Base de datos (generada automáticamente)
├── exports/           # Reportes PDF exportados
├── main.py            # Punto de entrada de la aplicación
└── requirements.txt   # Dependencias
```

## Desarrollo

### Ejecutar Pruebas

```bash
pytest tests/
```

### Formateo de Código

```bash
black src/ tests/
```

### Análisis de Código

```bash
flake8 src/ tests/
```

## Contribución en Git

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/NewFeature`)
3. Commit tus cambios (`git commit -m 'Add some Feature'`)
4. Push a la rama (`git push origin feature/NewFeature`)
5. Abre un Pull Request

---

**Versión**: 1.0.0  
**Fecha**: Septiembre 2025