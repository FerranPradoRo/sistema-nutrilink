"""
Módulo de conexión y configuración de la base de datos SQLite.
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional
from contextlib import contextmanager


class DatabaseConnection:
    """Maneja la conexión y configuración de la base de datos SQLite."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Inicializa la conexión a la base de datos.
        
        Args:
            db_path: Ruta al archivo de base de datos. Si es None, usa la ruta por defecto.
        """
        if db_path is None:
            # Crear directorio data si no existe
            data_dir = Path(__file__).parent.parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            self.db_path = str(data_dir / "nutrilink.db")
        else:
            self.db_path = db_path
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Returns:
            Conexión SQLite configurada.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Permite acceder a columnas por nombre
        conn.execute("PRAGMA foreign_keys = ON")  # Habilita foreign keys
        return conn
    
    @contextmanager
    def get_cursor(self):
        """
        Context manager para manejo seguro de conexiones y cursores.
        
        Yields:
            Cursor de la base de datos.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> list:
        """
        Ejecuta una consulta SELECT y retorna los resultados.
        
        Args:
            query: Consulta SQL a ejecutar.
            params: Parámetros para la consulta.
            
        Returns:
            Lista de resultados.
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """
        Ejecuta una consulta INSERT y retorna el ID del registro creado.
        
        Args:
            query: Consulta SQL INSERT.
            params: Parámetros para la consulta.
            
        Returns:
            ID del registro insertado.
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.lastrowid
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        Ejecuta una consulta UPDATE o DELETE y retorna el número de filas afectadas.
        
        Args:
            query: Consulta SQL UPDATE/DELETE.
            params: Parámetros para la consulta.
            
        Returns:
            Número de filas afectadas.
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount
    
    def table_exists(self, table_name: str) -> bool:
        """
        Verifica si una tabla existe en la base de datos.
        
        Args:
            table_name: Nombre de la tabla a verificar.
            
        Returns:
            True si la tabla existe, False en caso contrario.
        """
        query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """
        result = self.execute_query(query, (table_name,))
        return len(result) > 0


# Instancia global de la conexión a la base de datos
db_connection = DatabaseConnection()