from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import timezone, datetime
from database import Base, engine


class CategoryDB(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String, unique=True)
    description = Column(String)

    notes = relationship("SuccessDB", back_populates="category", passive_deletes=True)


class SuccessDB(Base):
    __tablename__ = "success_notes"

    id = Column(Integer, primary_key=True, index=True)
    header = Column(String)
    description = Column(String)
    priority = Column(Integer)
    creation_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"))
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

    category = relationship("CategoryDB", back_populates="notes")
    owner = relationship("UserDB", back_populates="notes")


class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    hashed_pass = Column(String)
    avatar_path = Column(String, nullable=True)

    notes = relationship("SuccessDB", back_populates="owner", passive_deletes=True)


# Команда для создания таблицы
def create_tables():
    Base.metadata.create_all(bind=engine)
