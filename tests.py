import os
import main
import unittest
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
engine = create_engine('sqlite:///test.db')
session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base.query = session.query_property()
            
class MainTestCase(unittest.TestCase):

    def setUp(self):
        main.app.config['TESTING'] = True
        self.app = main.app.test_client()
        with main.app.app_context():
            Base.metadata.create_all(engine)


    def tearDown(self):
        session.remove()
        Base.metadata.drop_all(engine)

    def test_create_db(self):
        rv = self.app.post('/database')

    def test_fetch_commands(self):
        rv1 = self.app.post('/database')
        assert b'Database creation successful.' in rv1.data
        rv = self.app.get('/commands')
        assert b'Commands not found' in rv.data

    def test_drop_db(self):
        rv = self.app.delete('/database')
        assert b'Database deletion successful.' in rv.data


if __name__ == '__main__':
    unittest.main()