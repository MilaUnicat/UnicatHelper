from sqlalchemy import Column, BigInteger, String
from base import Base


class CustomChanges(Base):
    __tablename__ = 'custom_changes'

    server_id = Column(BigInteger, nullable=False, primary_key=True)
    command_prefix = Column(String, nullable=False)

    def __repr__(self):
        return f'CustomChanges server_id={self.server_id}, command_prefix={self.command_prefix}'

    def __init__(self, server_id, command_prefix):
        self.server_id = server_id
        self.command_prefix = command_prefix

