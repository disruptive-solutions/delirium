import datetime

from ipaddress import IPv4Address
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


def add_or_update_record(session: Session, *, name: object, duration: int, ip_address: IPv4Address) -> DNSRecord:
    """ Update DNS record expirartion time or
    add a new entry if the record does not already exist
    :rtype: object"""
    delta = datetime.timedelta(seconds=duration)

    try:
        record = session.query(DNSRecord)\
                        .filter(DNSRecord.name == name)\
                        .one()
        record.expire_date = datetime.datetime.now() + delta
    except orm_exc.NoResultFound:
        record = DNSRecord(address=int(ip_address), name=name, expire_date=datetime.datetime.now() + delta)
        session.add(record)
    except DatabaseError:
        session.rollback()
        raise

    session.commit()
    return record


def get_records_by_status(session: Session, *, expired: bool):
    """ Retrieve all active DNS records """
    return session.query(DNSRecord)\
                  .filter_by(expired=expired)\
                  .all()


def get_records_by_address(session: Session, *, address: int, expired: bool):
    """ Retrive DNS records that match given "address" and "expired" values """
    return session.query(DNSRecord)\
                  .filter_by(address=address, expired=expired)\
                  .all()


def get_records_by_name(session: Session, *, name: str, expired: bool):
    """ Retrive DNS records that match given "name" and "expired" values """
    return session.query(DNSRecord)\
                  .filter_by(name=name, expired=expired)\
                  .all()


def delete_record(session: Session):
    """ Remove DNS record from database """
    session.query(DNSRecord)\
           .filter(DNSRecord.expire_date <= datetime.datetime.now())\
           .delete()
    session.commit()


def mark_record_expired(session: Session):
    """ Change DNS record's "expired" value to True """
    session.query(DNSRecord)\
           .filter(DNSRecord.expire_date <= datetime.datetime.now())\
           .update({'expired': True})
    session.commit()
