from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from delirium import const


Base = declarative_base()
Session = sessionmaker()


def init_engine(db_path=const.DEFAULT_DB_URI):
    return create_engine(f'sqlite:///{db_path}',
                         connect_args={'check_same_thread': False},
                         poolclass=StaticPool)


def init_db(engine: None):
    engine = engine or init_engine()
    Session.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    return Session()


def get_session():
    return Session()


def drop_db(engine):
    Base.metadata.drop_all(engine)
