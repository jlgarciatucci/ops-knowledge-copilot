from app.services.groundedness_service import GroundednessService


def test_groundedness_score():
    chunks = [{'content': 'The pump must be stopped if severe vibration occurs.'}]
    score = GroundednessService().score('The pump must be stopped for severe vibration.', chunks)
    assert score > 0
