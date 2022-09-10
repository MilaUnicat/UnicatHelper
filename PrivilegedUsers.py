from sqlalchemy import Column, BigInteger, Boolean
from base import Base


class PrivilegedUsers(Base):
    __tablename__ = 'privileged_users'

    user_id = Column(BigInteger)
    server_id = Column(BigInteger, nullable=False, primary_key=True)
    role_id = Column(BigInteger)
    allow_points = Column(Boolean)
    allow_teams = Column(Boolean)

    def __repr__(self):
        return f'PrivilegedUser user_id={self.user_id}, server_id={self.server_id}, ' \
               f'role_id={self.role_id}, allow_points={self.allow_points}, allow_teams={self.allow_teams}'

    def __init__(self, user_id, server_id, role_id, allow_points, allow_teams):
        self.allow_points = allow_points
        self.user_id = user_id
        self.server_id = server_id
        self.role_id = role_id
        self.allow_teams = allow_teams

