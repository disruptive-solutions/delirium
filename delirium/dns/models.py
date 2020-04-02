import datetime

from typing import AnyStr

import ipaddress

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.exc import DatabaseError, IntegrityError
from sqlalchemy.orm import Session

from delirium.database import Base


class AddressPoolDepletionError(Exception):
    """Raises an error if there are no addresses available"""


class NoRecordsFoundError(Exception):
    """Raises an error if there are no no records found"""


class DNSRecord(Base):
    """
    A DNS record object
    """
    __tablename__ = 'dns'

    id = Column(Integer, primary_key=True)
    address = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    expire_date = Column(DateTime)  # Nullable to facilitate unexpiring records
    expired = Column(Boolean, default=False)

    def __repr__(self):
        return f"<DNSRecord ({self.name} @ {ipaddress.ip_address(self.address)})>"

    def serialize(self):
        return {'id': self.id,
                'addr': self.address,
                'name': self.name,
                'expire_date': self.expire_date.isoformat(),
                'expired': self.expired}


def update_record(session: Session, *, name: AnyStr, duration: int) -> DNSRecord:
    """ Update DNS record expirartion time """
    try:
        record = get_records(session, name=name, expired=False)[0]
        delta = datetime.timedelta(seconds=duration)
        record.expire_date = datetime.datetime.now() + delta
        session.commit()
    except DatabaseError:
        session.rollback()
        raise
    except IndexError as e:
        raise NoRecordsFoundError('No records were found to update') from e
    else:
        return record


def add_record(session: Session, *, name: AnyStr, duration: int, address: int) -> DNSRecord:
    """Add a new entry if the record does not already exist """
    try:
        delta = datetime.timedelta(seconds=duration)
        record = DNSRecord(address=address, name=name, expire_date=datetime.datetime.now() + delta)
        session.add(record)
        session.commit()
    except IntegrityError as e:
        session.rollback()
        raise AddressPoolDepletionError('No address available to assign') from e
    except DatabaseError:
        session.rollback()
        raise
    else:
        return record


def get_records(session: Session, *, address: int = None, name: str = None, expired: bool = False):
    """ Retrive DNS records that match given "address" or "name" and/or "expired" values """
    if address:
        return session.query(DNSRecord)\
                      .filter_by(address=address, expired=expired)\
                      .all()
    if name:
        return session.query(DNSRecord)\
                      .filter_by(name=name, expired=expired)\
                      .all()

    return session.query(DNSRecord)\
                  .filter_by(expired=expired)\
                  .all()


def delete_record(session: Session):
    """ Remove DNS record from database """
    session.query(DNSRecord)\
           .filter(DNSRecord.expire_date <= datetime.datetime.now())\
           .delete()
    session.commit()
    # TODO - return number of records deleted


def mark_record_expired(session: Session):
    """ Change DNS record's "expired" value to True """
    session.query(DNSRecord)\
           .filter(DNSRecord.expire_date <= datetime.datetime.now())\
           .update({'expired': True})
    session.commit()
