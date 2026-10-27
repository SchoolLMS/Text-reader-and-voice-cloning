from fastapi.testclient import TestClient
from app import app

client=TestClient(app)

def test_home_and_health():
    assert client.get('/').status_code==200
    assert client.get('/health').json()['status']=='ok'

def test_requires_consent():
    result=client.post('/api/generate',data={'text':'Hello','language':'en'},files={'speaker':('ref.wav',b'audio','audio/wav')})
    assert result.status_code==422

def test_bad_language():
    result=client.post('/api/generate',data={'text':'Hello','language':'bad','consent':'true'},files={'speaker':('ref.wav',b'audio','audio/wav')})
    assert result.status_code==422

def test_audio_path_validation():
    assert client.get('/api/audio/invalid.wav').status_code==404
