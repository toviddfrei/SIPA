# ==========================================================
# CITADEL CORE - Sistema de Integridad y Gestión
# Archivo: models.py
# Versión: 0.2.5 (Referencia unificada)
# Módulo: Core
# Certificación: FHS-Compliant | Norma: ISO/IEC 27001 (Simulada)
# Autor: Daniel Miñana
# ---------------------------------------------------------
# Descripción: Definición de modelos de datos para la
#              gestión de identidad, noticias de seguridad y
#              cronograma de roadmap.
# ==========================================================

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class PerfilProfesional(db.Model):
    """
    ENTIDAD MAESTRA (ROOT IDENTITY): Define al propietario y los 
    metadatos de contacto que alimentan el Index.html.
    """
    __tablename__ = 'perfil_profesional'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    profesion = db.Column(db.String(100))
    
    # --- Datos Punto 11 (Círculo de identidad) ---
    email = db.Column(db.String(120), unique=True)
    telefono = db.Column(db.String(20)) # Almacenado pero no visible en Index
    biografia_corta = db.Column(db.Text)
    imagen_perfil = db.Column(db.String(255), default='profile_default.png')
    ubicacion = db.Column(db.String(100), default='España')

    # Relaciones de Integridad
    noticias = db.relationship('NoticiaSeguridad', backref='autor', lazy=True)
    hitos = db.relationship('CronogramaRoadmap', backref='propietario', lazy=True)

class NoticiaSeguridad(db.Model):
    """
    INTELIGENCIA DE AMENAZAS: Almacena feeds de INCIBE/OSI para 
    el motor de búsqueda y pedagogía de ciberseguridad.
    """
    __tablename__ = 'noticias_seguridad'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(255), nullable=False)
    url_fuente = db.Column(db.String(500), nullable=False)
    resumen = db.Column(db.Text)
    fecha_publicacion = db.Column(db.DateTime, default=datetime.utcnow)
    fuente_nombre = db.Column(db.String(50)) # Ejemplo: "INCIBE"
    
    # Hash para asegurar que la noticia no ha sido alterada en BD
    hash_transparencia = db.Column(db.String(64))
    perfil_id = db.Column(db.Integer, db.ForeignKey('perfil_profesional.id'))

class CronogramaRoadmap(db.Model):
    """
    MOTOR OPERATIVO: Gestión de tareas, proyectos y visión 
    estratégica del constructor.
    """
    __tablename__ = 'cronograma_roadmap'
    id = db.Column(db.Integer, primary_key=True)
    tarea = db.Column(db.String(200), nullable=False)
    categoria = db.Column(db.String(50)) # Proyecto, Formacion, Hito_CV
    tags = db.Column(db.String(100))
    prioridad = db.Column(db.Integer, default=5) # Escala 1-10
    
    # Visibilidad: 'Public', 'Private', 'Root_Only'
    visibilidad = db.Column(db.String(20), default='Root_Only')
    razon_aprendizaje = db.Column(db.Text)
    
    # Control de Estado (Punto 1: Publicado/Despublicado)
    estado = db.Column(db.String(20), default='Borrador') 
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    perfil_id = db.Column(db.Integer, db.ForeignKey('perfil_profesional.id'))