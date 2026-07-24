"""Tests for bounded EventBus history."""

from __future__ import annotations

import unittest

from event_bus import Event, EventBus


class EventBusTest(unittest.TestCase):
    def test_history_is_bounded_and_discards_old_events(self) -> None:
        bus = EventBus(max_history=3)

        for index in range(5):
            bus.publish(Event(topic=f"TOPIC_{index}", source="test"))

        history = bus.history()
        stats = bus.stats()

        self.assertEqual([event.topic for event in history], ["TOPIC_2", "TOPIC_3", "TOPIC_4"])
        self.assertEqual(bus.queue_size(), 3)
        self.assertEqual(stats["max_history"], 3)
        self.assertEqual(stats["published_count"], 5)
        self.assertEqual(stats["discarded_count"], 2)

    def test_zero_max_history_keeps_unbounded_legacy_behavior_for_tests(self) -> None:
        bus = EventBus(max_history=0)

        for index in range(5):
            bus.publish(Event(topic=f"TOPIC_{index}", source="test"))

        stats = bus.stats()

        self.assertEqual(bus.queue_size(), 5)
        self.assertEqual(stats["max_history"], 0)
        self.assertEqual(stats["discarded_count"], 0)


if __name__ == "__main__":
    unittest.main()
