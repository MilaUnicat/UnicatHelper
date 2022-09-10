from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(f'mysql+pymysql://{os.getenv("USER", "")}:'
                       f'{os.getenv("PASSWORD", "")}@'
                       f'{os.getenv("HOST", "")}/'
                       f'{os.getenv("DATABASE", "")}?charset=utf8mb4', pool_recycle=3600)

Session = sessionmaker(bind=engine)

Base = declarative_base()

