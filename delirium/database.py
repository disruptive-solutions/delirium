import logging

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from delirium import const


logger = logging.getLogger(__name__)
Base = declarative_base()
Session = sessionmaker()


def init_engine(db_path=const.DEFAULT_DB_URI):
    logger.debug('Initiating database with URI: sqlite:///%s', db_path)
    return create_engine(f'sqlite:///{db_path}',
                         connect_args={'check_same_thread': False},
                         poolclass=StaticPool)


def init_db(engine: None):
    logger.info("Connecting to and initializing database")
    engine = engine or init_engine()
    Session.configure(bind=engine)
    Base.metadata.bind = engine
    logger.debug("Creating tables")
    Base.metadata.create_all(engine)
    logger.debug('Successfully initialized database')
    return Session()


def drop_db(engine):
    logger.info('Dropping database')
    Base.metadata.drop_all(engine)
