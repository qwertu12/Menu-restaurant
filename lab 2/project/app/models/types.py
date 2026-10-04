import enum
from enum import IntEnum

from sqlalchemy.types import Integer, TypeDecorator


class IntEnumType(TypeDecorator):
    impl = Integer
    cache_ok = True

    def __init__(self, enum_type: type[IntEnum], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enum_type = enum_type

    def process_bind_param(self, value, dialect):
        if isinstance(value, enum.Enum):
            return value.value
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return self.enum_type(value)
