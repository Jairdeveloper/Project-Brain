"""
Configuración de conexión a PostgreSQL
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import os

# Obtener DATABASE_URL del ambiente o usar default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/chatbot_db"
)

# Crear engine
# NullPool: No mantiene conexiones idle (mejor para serverless)
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
    echo=False,  # Cambiar a True para debug SQL
)

# Crear session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Session:
    """
    Dependency para FastAPI
    
    Uso:
    @app.get("/endpoint")
    def get_data(db: Session = Depends(get_db)):
        return db.query(Tenant).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Crea todas las tablas en la BD"""
    from app.models.database import Base
    Base.metadata.create_all(bind=engine)


def drop_db():
    """Elimina todas las tablas (PELIGROSO - solo para testing)"""
    from app.models.database import Base
    Base.metadata.drop_all(bind=engine)


def test_connection():
    """Prueba la conexión a la BD"""
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ Conexión a PostgreSQL exitosa")
            return True
    except Exception as e:
        print(f"❌ Error conectando a PostgreSQL: {e}")
        return False
