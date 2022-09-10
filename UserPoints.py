from sqlalchemy import Column, BigInteger, Integer
from base import Base


class UserPoints(Base):
    __tablename__ = 'user_points'

    user_id = Column(BigInteger, primary_key=True, nullable=False)
    server_id = Column(BigInteger, nullable=False, primary_key=True)
    team_id = Column(BigInteger)
    point_total = Column(Integer)

    def __repr__(self):
        return f'UserPoints user_id={self.user_id}, server_id={self.server_id}, ' \
               f'team_id={self.team_id}, point_total={self.point_total}'

    def __init__(self, user_id, server_id, team_id, point_total):
        self.team_id = team_id
        self.user_id = user_id
        self.server_id = server_id
        self.point_total = point_total

