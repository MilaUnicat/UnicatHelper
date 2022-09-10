from sqlalchemy import Column, BigInteger, Integer, String
from base import Base


class Teams(Base):
    __tablename__ = 'teams'

    server_id = Column(BigInteger, nullable=False, primary_key=True)
    team_id = Column(BigInteger, nullable=False, primary_key=True)
    point_total = Column(Integer)
    name = Column(String, nullable=False)

    def __repr__(self):
        return f'UserPoints team_id={self.team_id}, server_id={self.server_id}, ' \
               f'name={self.name}, point_total={self.point_total}'

    def __init__(self, server_id, team_id, point_total, name):
        self.team_id = team_id
        self.server_id = server_id
        self.point_total = point_total
        self.name = name

