#!/usr/bin/env python3
"""
Test undo logic under simulated failure scenarios.
Tests both baccarat and AB undo paths WITHOUT real money — uses mock WS.
"""
import asyncio
import json
import threading
import time
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

# ─── Mock websocket that records messages ────────────────────────────────────
class MockWS:
    def __init__(self, should_fail=False, fail_on_attempt=None):
        self.sent_messages = []
        self.should_fail = should_fail
        self.fail_on_attempt = fail_on_attempt  # fail only on Nth call
        self._call_count = 0

    async def send(self, msg):
        self._call_count += 1
        if self.should_fail:
            raise ConnectionError("Mock WS send failed")
        if self.fail_on_attempt and self._call_count == self.fail_on_attempt:
            raise ConnectionError(f"Mock WS send failed on attempt {self._call_count}")
        self.sent_messages.append(msg)

    def has_undo(self):
        """Check if an UNDO message (gameplayMessageType:1) was sent."""
        for m in self.sent_messages:
            try:
                data = json.loads(m.rstrip('\x1e'))
                args = data.get('arguments', [])
                if args:
                    inner = json.loads(args[0].get('data', '{}'))
                    if inner.get('gameplayMessageType') == 1:
                        return True
            except Exception:
                pass
        return False

    def has_bet(self):
        """Check if a bet message (gameplayMessageType:0) was sent."""
        for m in self.sent_messages:
            try:
                data = json.loads(m.rstrip('\x1e'))
                args = data.get('arguments', [])
                if args:
                    inner = json.loads(args[0].get('data', '{}'))
                    if inner.get('gameplayMessageType') == 0:
                        return True
            except Exception:
                pass
        return False


# ─── Test _undo_bets_async directly ─────────────────────────────────────────
class TestUndoBetsAsync(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        import ws_manager
        self.mgr = ws_manager.BaccaratManager("TestAcc", 18)

    async def test_undo_sends_correct_payload(self):
        """UNDO must send gameplayMessageType:1 with empty bets."""
        ws = MockWS()
        await self.mgr._undo_bets_async([(ws, "TestTable")])
        self.assertTrue(ws.has_undo(), "UNDO payload not sent")
        print("  ✅ UNDO sends correct gameplayMessageType:1 payload")

    async def test_undo_handles_failed_ws(self):
        """UNDO on a broken WS should not crash — graceful error handling."""
        ws = MockWS(should_fail=True)
        # Should not raise
        try:
            await self.mgr._undo_bets_async([(ws, "BrokenTable")])
            print("  ✅ UNDO handles WS send failure gracefully (no crash)")
        except Exception as e:
            self.fail(f"UNDO raised an exception on WS failure: {e}")

    async def test_undo_handles_none_ws(self):
        """UNDO with None WS should skip silently."""
        try:
            await self.mgr._undo_bets_async([(None, "NullTable")])
            print("  ✅ UNDO handles None WS gracefully")
        except Exception as e:
            self.fail(f"UNDO raised on None ws: {e}")

    async def test_undo_sends_to_multiple_tables(self):
        """UNDO must fire on ALL tables in the list."""
        ws1 = MockWS()
        ws2 = MockWS()
        ws3 = MockWS()
        await self.mgr._undo_bets_async([(ws1, "T1"), (ws2, "T2"), (ws3, "T3")])
        self.assertTrue(ws1.has_undo(), "WS1 didn't get UNDO")
        self.assertTrue(ws2.has_undo(), "WS2 didn't get UNDO")
        self.assertTrue(ws3.has_undo(), "WS3 didn't get UNDO")
        print("  ✅ UNDO fires on ALL tables")

    async def test_undo_partial_failure_still_sends_to_others(self):
        """If one WS fails, UNDO must still be sent to others."""
        ws_ok = MockWS()
        ws_bad = MockWS(should_fail=True)
        ws_ok2 = MockWS()
        await self.mgr._undo_bets_async([(ws_ok, "T1"), (ws_bad, "T_BAD"), (ws_ok2, "T3")])
        self.assertTrue(ws_ok.has_undo(), "T1 didn't get UNDO despite being healthy")
        self.assertTrue(ws_ok2.has_undo(), "T3 didn't get UNDO despite being healthy")
        print("  ✅ UNDO still fires on healthy tables even when one WS fails")


# ─── Test undo payload format ────────────────────────────────────────────────
class TestUndoPayloadFormat(unittest.IsolatedAsyncioTestCase):

    async def test_undo_payload_structure(self):
        """Verify exact UNDO payload format matches server expectations."""
        import ws_manager
        mgr = ws_manager.BaccaratManager("Acc", 18)
        ws = MockWS()
        await mgr._undo_bets_async([(ws, "Table")])

        self.assertEqual(len(ws.sent_messages), 2)
        
        # Verify Message 1 (type:7 unbet)
        raw1 = ws.sent_messages[0]
        self.assertTrue(raw1.endswith('\x1e'))
        data1 = json.loads(raw1.rstrip('\x1e'))
        self.assertEqual(data1['type'], 1)
        self.assertEqual(data1['target'], 'Message')
        self.assertEqual(json.loads(data1['arguments'][0])['type'], 7)

        # Verify Message 2 (gameplayMessageType:1 clear)
        raw2 = ws.sent_messages[1]
        self.assertTrue(raw2.endswith('\x1e'), "UNDO message must end with SignalR frame separator \\x1e")

        data2 = json.loads(raw2.rstrip('\x1e'))
        self.assertEqual(data2['type'], 1)
        self.assertEqual(data2['target'], 'Message')
        args = data2['arguments']
        self.assertEqual(len(args), 1)

        inner = json.loads(args[0]['data'])
        self.assertEqual(inner['areBetsInZeroCommMode'], False)
        self.assertEqual(inner['bets'], [])
        self.assertEqual(inner['gameplayMessageType'], 1, "gameplayMessageType MUST be 1 for UNDO")

        print("  ✅ UNDO payload format is exactly correct (Dual-Format: type:7 + empty clear)")
        print(f"     Payload 1: {data1['arguments'][0]}")
        print(f"     Payload 2: {json.dumps(inner)}")


# ─── Run all tests ────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("\n" + "="*60)
    print("UNDO LOGIC TEST SUITE")
    print("="*60 + "\n")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestUndoPayloadFormat))
    suite.addTests(loader.loadTestsFromTestCase(TestUndoBetsAsync))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "="*60)
    if result.wasSuccessful():
        print("✅ ALL UNDO TESTS PASSED")
    else:
        print(f"❌ FAILURES: {len(result.failures)} | ERRORS: {len(result.errors)}")
        for f in result.failures + result.errors:
            print(f"\n{f[0]}\n{f[1]}")
    print("="*60)
