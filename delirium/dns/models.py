import datetime
import logging

from ipaddress import IPv4Address
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import Session, exc as orm_exc
from sqlalchemy.exc import DatabaseError

from delirium.database import Base


logger = logging.getLogger(__name__)


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
        return f"<DNSRecord ({self.name} @ {IPv4Address(self.address)})>"

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
        logging.info('Revisiting record: %s ==> %s', name, ip_address)
    except orm_exc.NoResultFound:
        record = DNSRecord(address=int(ip_address), name=name, expire_date=datetime.datetime.now() + delta)
        logging.info('Adding record: %s ==> %s', record.name, ip_address)
        session.add(record)
    except DatabaseError:
        logging.error('Rolling back database due to error')
        session.rollback()
        raise

    session.commit()
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
    logging.debug('Deleting stale records from database')
    session.query(DNSRecord)\
           .filter(DNSRecord.expire_date <= datetime.datetime.now())\
           .delete()
    session.commit()
    # add message about records deleted


def mark_record_expired(session: Session):
    """ Change DNS record's "expired" value to True """
    logging.debug('Marking stale records')
    session.query(DNSRecord)\
           .filter(DNSRecord.expire_date <= datetime.datetime.now())\
           .update({'expired': True})
    session.commit()
