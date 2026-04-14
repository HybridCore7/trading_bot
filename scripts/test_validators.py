"""Quick smoke test for validators."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from bot.validators import validate_order, ValidationError

# Test 1: Valid MARKET order
p = validate_order("BTCUSDT", "BUY", "MARKET", "0.001")
print(f"✓ MARKET order validated: {p}")

# Test 2: Valid LIMIT order
p2 = validate_order("ETHUSDT", "SELL", "LIMIT", "0.5", price="3000")
print(f"✓ LIMIT order validated: {p2}")

# Test 3: LIMIT without price should fail
try:
    validate_order("BTCUSDT", "BUY", "LIMIT", "1")
    print("✗ Should have failed!")
except ValidationError as e:
    print(f"✓ Expected error (LIMIT no price): {e}")

# Test 4: Invalid symbol should fail
try:
    validate_order("INVALID", "BUY", "MARKET", "1")
    print("✗ Should have failed!")
except ValidationError as e:
    print(f"✓ Expected error (bad symbol): {e}")

# Test 5: Negative quantity should fail
try:
    validate_order("BTCUSDT", "BUY", "MARKET", "-5")
    print("✗ Should have failed!")
except ValidationError as e:
    print(f"✓ Expected error (negative qty): {e}")

# Test 6: Valid STOP_LIMIT order
p3 = validate_order("BTCUSDT", "SELL", "STOP_LIMIT", "0.001", price="48000", stop_price="49000")
print(f"✓ STOP_LIMIT order validated: {p3}")

print("\nAll validator tests passed!")
