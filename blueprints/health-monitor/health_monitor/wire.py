"""Bounded structural checks for the monitor's SDK-provided FlatBuffers schemas.

Field layouts come from the pinned SDK's BFBS metadata, not duplicated offsets.
Only the scalar/string/object/vector/struct-array types used by these three
telemetry schemas are supported. This is not a general SDK verifier or type proof.
"""

from functools import lru_cache
import importlib
import struct

SCHEMAS = {"state": ("locomotion_status_schema_meta", "locomotion.LocomotionStatus"),
           "battery": ("bms_state_schema_meta", "bms.BmsState"),
           "system": ("sm_status_schema_meta", "sm.SmStatus")}
SCALARS = {1: 1, 2: 1, 3: 1, 4: 1, 5: 2, 6: 2, 7: 4, 8: 4,
           9: 8, 10: 8, 11: 4, 12: 8}
STRING, VECTOR, OBJECT, ARRAY = 13, 14, 15, 17
MAX_BYTES, MAX_DEPTH, MAX_OBJECTS = 1024 * 1024, 64, 65536


class Buffer:
    def __init__(self, data):
        self.data = memoryview(data).cast("B")
        if not 8 <= len(self.data) <= MAX_BYTES:
            raise ValueError("invalid FlatBuffer size")

    def span(self, position, size, alignment=1):
        if position < 0 or size < 0 or position + size > len(self.data) or position % alignment:
            raise ValueError("invalid FlatBuffer bounds or alignment")

    def integer(self, position, size=4, *, signed=False):
        self.span(position, size, size)
        return int.from_bytes(self.data[position:position + size], "little", signed=signed)

    def target(self, position):
        distance = self.integer(position)
        if distance < 4:
            raise ValueError("invalid FlatBuffer offset")
        result = position + distance
        self.span(result, 4, 4)
        return result

    def table(self, position):
        distance = self.integer(position, signed=True)
        if not distance:
            raise ValueError("invalid FlatBuffer vtable offset")
        vtable = position - distance
        length, size = self.integer(vtable, 2), self.integer(vtable + 2, 2)
        if length < 4 or length % 2 or size < 4:
            raise ValueError("invalid FlatBuffer table header")
        self.span(vtable, length, 2)
        self.span(position, size, 4)
        return position, vtable, length, size

    def field(self, table, index, size=4, alignment=4):
        position, vtable, length, object_size = table
        slot = 4 + 2 * index
        offset = self.integer(vtable + slot, 2) if slot < length else 0
        if not offset:
            return None
        if offset < 4 or offset + size > object_size:
            raise ValueError("FlatBuffer field exceeds table")
        result = position + offset
        self.span(result, size, alignment)
        return result

    def scalar(self, table, index, size=4, default=0, *, signed=False):
        position = self.field(table, index, size, size)
        return default if position is None else self.integer(position, size, signed=signed)

    def pointer(self, table, index):
        position = self.field(table, index)
        return None if position is None else self.target(position)

    def vector(self, position, size=4, alignment=4):
        count = self.integer(position)
        self.span(position + 4, count * size, alignment)
        return range(position + 4, position + 4 + count * size, size)

    def string(self, position):
        size = self.integer(position)
        self.span(position + 4, size + 1)
        if self.data[position + 4 + size] != 0:
            raise ValueError("unterminated FlatBuffer string")
        return self.data[position + 4:position + 4 + size]


class Schema:
    def __init__(self, data, root_name):
        # The BFBS is trusted, version-pinned SDK metadata. Reject unknown layout
        # features before opening a device session rather than guessing widths.
        source = Buffer(data)
        if bytes(source.data[4:8]) != b"BFBS":
            raise ValueError("missing BFBS identifier")
        schema = source.table(source.target(0))
        objects = source.pointer(schema, 0)
        root = source.pointer(schema, 4)
        if objects is None or root is None:
            raise ValueError("missing schema objects or root")
        positions = [source.target(slot) for slot in source.vector(objects)]
        self.root = positions.index(root)
        self.objects = []
        for position in positions:
            table = source.table(position)
            name = bytes(source.string(source.pointer(table, 0))).decode("utf-8")
            fields = []
            for slot in source.vector(source.pointer(table, 1)):
                field = source.table(source.target(slot))
                kind = source.table(source.pointer(field, 1))
                if source.scalar(field, 13, 1):  # reflection.Field.offset64
                    raise ValueError("64-bit field offsets are not supported")
                fields.append((source.scalar(field, 2, 2), source.scalar(field, 3, 2),
                               bool(source.scalar(field, 7, 1)), source.scalar(kind, 0, 1),
                               source.scalar(kind, 1, 1), source.scalar(kind, 2, signed=True, default=-1),
                               source.scalar(kind, 3, 2)))
            self.objects.append((name, bool(source.scalar(table, 2, 1)),
                                 source.scalar(table, 3), source.scalar(table, 4), fields))
        if self.objects[self.root][0] != root_name or self.objects[self.root][1]:
            raise ValueError("schema root mismatch")
        for _, is_struct, _, _, fields in self.objects:
            for _, _, _, base, element, index, count in fields:
                if base not in (*SCALARS, STRING, VECTOR, OBJECT, ARRAY):
                    raise ValueError("unsupported schema field type")
                if base in (VECTOR, ARRAY) and element not in (*SCALARS, STRING, OBJECT):
                    raise ValueError("unsupported schema element type")
                if base == ARRAY and (not is_struct or element not in SCALARS or not count):
                    raise ValueError("unsupported inline array")
                if (base == OBJECT or (base == VECTOR and element == OBJECT)) and not 0 <= index < len(self.objects):
                    raise ValueError("invalid schema object reference")

    def shape(self, base, index, element=0, count=0):
        if base in SCALARS:
            return SCALARS[base], SCALARS[base]
        if base == OBJECT and self.objects[index][1]:
            return self.objects[index][3], self.objects[index][2]
        if base == ARRAY:
            return count * SCALARS[element], SCALARS[element]
        return 4, 4

    def verify(self, payload):
        buffer = Buffer(payload)
        seen = set()

        def string(position):
            buffer.string(position)

        def object_at(position, index, depth):
            if depth > MAX_DEPTH or len(seen) >= MAX_OBJECTS:
                raise ValueError("FlatBuffer verification limit exceeded")
            identity = position, index
            if identity in seen:
                return
            seen.add(identity)
            _, is_struct, alignment, size, fields = self.objects[index]
            if is_struct:
                buffer.span(position, size, alignment)
            table = None if is_struct else buffer.table(position)
            for field_id, offset, required, base, element, target, count in fields:
                width, align = self.shape(base, target, element, count)
                slot = position + offset if is_struct else buffer.field(table, field_id, width, align)
                if slot is None:
                    if required:
                        raise ValueError("missing required FlatBuffer field")
                    continue
                buffer.span(slot, width, align)
                if is_struct and offset + width > size:
                    raise ValueError("inline field exceeds struct")
                if base == STRING:
                    string(buffer.target(slot))
                elif base == OBJECT:
                    object_at(slot if self.objects[target][1] else buffer.target(slot), target, depth + 1)
                elif base == VECTOR:
                    width, align = self.shape(element, target)
                    for item in buffer.vector(buffer.target(slot), width, align):
                        if element == OBJECT:
                            object_at(item if self.objects[target][1] else buffer.target(item), target, depth + 1)
                        elif element == STRING:
                            string(buffer.target(item))

        object_at(buffer.target(0), self.root, 0)


@lru_cache(maxsize=3)
def validator(stream):
    module_name, root_name = SCHEMAS[stream]
    meta = importlib.import_module(module_name)
    try:
        if meta.ROOT_TYPE_NAME != root_name:
            raise ValueError("SDK root type mismatch")
        return Schema(meta.SCHEMA_BFBS, root_name)
    except (ValueError, TypeError, IndexError, struct.error) as error:
        raise RuntimeError("unsupported SDK schema; check the pinned release pairing") from error
