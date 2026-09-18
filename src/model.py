from dataclasses import dataclass


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    position: int


@dataclass(frozen=True)
class Condition:
    attribute: str
    operator: str
    value: object
    connector: str | None = None


@dataclass(frozen=True)
class Query:
    projection: list[str] | None  # None represents '*'
    source: str
    conditions: list[Condition]
    order_by: str | None = None
    descending: bool = False
    limit: int | None = None
    count: bool = False
