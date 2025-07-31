import pytest
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            
def test_valid_registration(client):
    response = client.post('/register', data={
        'email': 'user1@mail.com',
        'nickname': 'user1',
        'password': 'pass123',
    })
    assert b'Registration successful' in response.data

def test_duplicate_nickname(client):
    # Add user
    user = User(email='test@mail.com', nickname='user1', password_hash=generate_password_hash('pass123'))
    db.session.add(user)
    db.session.commit()

    # Try to register duplicate nickname
    response = client.post('/register', data={
        'email': 'new@mail.com',
        'nickname': 'user1',
        'password': 'pass123',
    })
    assert b'Nickname already taken' in response.data

def test_valid_login(client):
    # Add test user
    user = User(email='test@mail.com', nickname='user1', password_hash=generate_password_hash('pass123'))
    db.session.add(user)
    db.session.commit()

    response = client.post('/login', data={
        'email': 'test@mail.com',
        'password': 'pass123'
    })
    assert b'Welcome user1' in response.data

def test_invalid_login(client):
    response = client.post('/login', data={
        'email': 'wrong@mail.com',
        'password': 'wrongpass'
    })
    assert b'Invalid email or password' in response.data
