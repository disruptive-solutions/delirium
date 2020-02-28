import datetime

from typing import AnyStr

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import Session, exc as orm_exc
from sqlalchemy.exc import DatabaseError

from delirium.database import Base


class DNSRecord(Base):
    """
    A DNS record object
    """
    __tablename__ = 'dns'

    id = Column(Integer, primary_key=True)
    address = Column(Integer)
    name = Column(String)
    expire_date = Column(DateTime)
    expired = Column(Boolean, default=False)

    def __repr__(self):
        return f"<DNSRecord ({self.name})>"

    def serialize(self):
        return {'id': self.id,
                'addr': self.address,
                'name': self.name,
                'expire_date': self.expire_date.isoformat(),
                'expired': self.expired}

    @staticmethod
    def add_or_update(session: Session, *, name: AnyStr, duration: int, ip_address: int):
        delta = datetime.timedelta(seconds=duration)

        try:
            record = session.query(DNSRecord).filter(DNSRecord.name == name).one()
            record.expire_date = datetime.datetime.now() + delta
        except orm_exc.NoResultFound:
            record = DNSRecord(address=int(ip_address), name=name, expire_date=datetime.datetime.now() + delta)
            session.add(record)
        except DatabaseError:
            session.rollback()
            raise

        session.commit()
        return record
