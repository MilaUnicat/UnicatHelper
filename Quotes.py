from sqlalchemy import Column, BigInteger, String, Date, Identity
from base import Base


class Quote(Base):
    __tablename__ = 'quotes'

    user_id = Column(BigInteger, nullable=False)
    server_id = Column(BigInteger, nullable=False)
    quote_id = Column(BigInteger, Identity(start=0, cycle=True), nullable=False, primary_key=True)
    quote_text = Column(String, nullable=False)
    date_quoted = Column(Date)

    def __repr__(self):
        return f'Quotes user_id={self.user_id}, server_id={self.server_id}, ' \
               f'quote_id={self.quote_id}, quote_text={self.quote_text}, date_quoted={self.date_quoted}'

    def __init__(self, user_id, server_id, quote_id, quote_text, date_quoted):
        self.user_id = user_id
        self.server_id = server_id
        self.quote_id = quote_id
        self.quote_text = quote_text
        self.date_quoted = date_quoted

