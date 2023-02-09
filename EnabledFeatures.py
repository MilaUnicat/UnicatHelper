from sqlalchemy import Column, BigInteger, Boolean
from base import Base


class EnabledFeatures(Base):
    __tablename__ = 'enabled_features'

    server_id = Column(BigInteger, nullable=False, primary_key=True)
    quotes_enabled = Column(Boolean)
    points_enabled = Column(Boolean)

    def __repr__(self):
        return f'EnabledFeatures server_id={self.server_id}, quotes_enabled={self.quotes_enabled}, ' \
               f'points_enabled={self.points_enabled}'

    def __init__(self, server_id, quotes_enabled, points_enabled):
        self.server_id = server_id
        self.quotes_enabled = quotes_enabled
        self.points_enabled = points_enabled
