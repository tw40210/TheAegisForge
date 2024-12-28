from enum import Enum


class RequestType(Enum):
    SELL = "sell"
    BUY = "buy"


class OrderType(Enum):
    LIMIT = "limit"
    MARKET = "market"


class TimeForce(Enum):
    DAY = "day"
    IOC = "ioc"
    FOK = "fok"


class AssetType(Enum):
    Stock = "Stock"
    Crypto = "Crypto"
