"""Unit tests for data models"""

import pytest
from datetime import datetime
from uuid import uuid4

from common.models import Event, EventType, EventStatus


def test_event_creation():
    """Test event model creation"""
    event = Event(
        event_type=EventType.PURCHASE, user_id="user_123", properties={"amount": 99.99}
    )

    assert event.event_id is not None
    assert event.event_type == EventType.PURCHASE
    assert event.user_id == "user_123"
    assert event.properties["amount"] == 99.99
    assert isinstance(event.timestamp, datetime)


def test_event_with_custom_id():
    """Test event with custom ID"""
    custom_id = uuid4()
    event = Event(event_id=custom_id, event_type=EventType.USER_SIGNUP, properties={})

    assert event.event_id == custom_id


def test_event_validation():
    """Test event validation"""
    with pytest.raises(ValueError):
        Event(event_type=EventType.PURCHASE, properties="not a dict")  # Should be dict


def test_event_types():
    """Test all event types"""
    for event_type in EventType:
        event = Event(event_type=event_type, properties={})
        assert event.event_type == event_type
