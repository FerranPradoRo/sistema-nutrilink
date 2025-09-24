"""
Definición del esquema de la base de datos.
"""

from .connection import db_connection


class DatabaseSchema:
    """Creación y gestión del esquema de la base de datos."""
    
    @staticmethod
    def create_users_table():
        query = """
            CREATE TABLE IF NOT EXISTS usuarios (
                id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                correo TEXT UNIQUE NOT NULL,
                contraseña_hash TEXT NOT NULL,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        with db_connection.get_cursor() as cursor:
            cursor.execute(query)
    
    @staticmethod
    def create_patients_table():
        query = """
            CREATE TABLE IF NOT EXISTS pacientes (
                id_paciente INTEGER PRIMARY KEY AUTOINCREMENT,
                id_usuario INTEGER NOT NULL,
                nombre TEXT NOT NULL,
                apellidos TEXT NOT NULL,
                sexo TEXT NOT NULL CHECK (sexo IN ('M', 'F')),
                edad INTEGER NOT NULL CHECK (edad > 0 AND edad <= 120),
                peso REAL NOT NULL CHECK (peso > 0),
                altura REAL NOT NULL CHECK (altura > 0),
                telefono_contacto TEXT,
                correo_contacto TEXT,
                fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
                fecha_ultima_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario) ON DELETE CASCADE
            )
        """
        with db_connection.get_cursor() as cursor:
            cursor.execute(query)
    
    @staticmethod
    def create_calculated_metrics_table():
        """
        IMPLEMENTAR: Esta tabla se actualice automáticamente cuando cambien los datos del paciente.
        """
        query = """
            CREATE TABLE IF NOT EXISTS metricas_calculadas (
                id_metrica INTEGER PRIMARY KEY AUTOINCREMENT,
                id_paciente INTEGER NOT NULL,
                imc REAL,
                tmb REAL,
                porcentaje_grasa REAL,
                peso_ideal REAL,
                fecha_calculo DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_paciente) REFERENCES pacientes (id_paciente) ON DELETE CASCADE
            )
        """
        with db_connection.get_cursor() as cursor:
            cursor.execute(query)
    
    @staticmethod
    def create_indexes():
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_usuarios_correo ON usuarios (correo)",
            "CREATE INDEX IF NOT EXISTS idx_pacientes_usuario ON pacientes (id_usuario)",
            "CREATE INDEX IF NOT EXISTS idx_pacientes_nombre ON pacientes (nombre, apellidos)",
            "CREATE INDEX IF NOT EXISTS idx_metricas_paciente ON metricas_calculadas (id_paciente)"
        ]
        
        with db_connection.get_cursor() as cursor:
            for index_query in indexes:
                cursor.execute(index_query)
    
    @staticmethod
    def create_triggers():
        # Trigger para actualizar fecha_ultima_actualizacion en pacientes
        trigger_update_patient = """
            CREATE TRIGGER IF NOT EXISTS update_patient_timestamp
            AFTER UPDATE ON pacientes
            FOR EACH ROW
            BEGIN
                UPDATE pacientes 
                SET fecha_ultima_actualizacion = CURRENT_TIMESTAMP 
                WHERE id_paciente = NEW.id_paciente;
            END
        """
        
        with db_connection.get_cursor() as cursor:
            cursor.execute(trigger_update_patient)
    
    @staticmethod
    def initialize_database():
        """
        Inicializa completamente la base de datos
        """
        print("Inicializando base de datos...")
        
        # Crear tablas
        DatabaseSchema.create_users_table()
        print("✓ Tabla 'usuarios' creada")
        
        DatabaseSchema.create_patients_table()
        print("✓ Tabla 'pacientes' creada")
        
        DatabaseSchema.create_calculated_metrics_table()
        print("✓ Tabla 'metricas_calculadas' creada")
        
        # Crear índices
        DatabaseSchema.create_indexes()
        print("✓ Índices creados")
        
        # Crear triggers
        DatabaseSchema.create_triggers()
        print("✓ Triggers creados")
        
        print("Base de datos inicializada correctamente.")
    
    @staticmethod
    def drop_all_tables():
        """
        USAR SOLO EN DESARROLLO.
        """
        tables = ["metricas_calculadas", "pacientes", "usuarios"]
        
        with db_connection.get_cursor() as cursor:
            cursor.execute("PRAGMA foreign_keys = OFF")
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
            cursor.execute("PRAGMA foreign_keys = ON")
        
        print("Todas las tablas han sido eliminadas.")
    
    @staticmethod
    def reset_database():
        """
        Reinicia completamente la base de datos eliminando y recreando todas las tablas.
        USAR SOLO EN DESARROLLO.
        """
        DatabaseSchema.drop_all_tables()
        DatabaseSchema.initialize_database()