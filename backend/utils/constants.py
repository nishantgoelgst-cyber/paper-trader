from enum import Enum


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    GTT = "GTT"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    TRIGGERED = "TRIGGERED"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class PositionStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class SLMode(str, Enum):
    FIXED = "FIXED"
    TRAILING = "TRAILING"


class TriggerType(str, Enum):
    MANUAL = "MANUAL"
    TARGET1 = "TARGET1"
    TARGET2 = "TARGET2"
    TARGET3 = "TARGET3"
    SL1 = "SL1"
    SL2 = "SL2"
    SL3 = "SL3"
    TRAILING_SL = "TRAILING_SL"
    GTT_ENTRY = "GTT_ENTRY"
