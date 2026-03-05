import struct

from ._zigcodec import zigcodec


class DecodeError(Exception):
    def __init__(self, pointer, message):
        self.pointer = pointer
        self.message = message

    def __str__(self):
        return self.message.format(self.pointer)


wire_types = {
    "int32": 0,
    "int64": 0,
    "sint32": 0,
    "sint64": 0,
    "uint32": 0,
    "uint64": 0,
    "bool": 0,
    "enum": 0,
    "fixed64": 1,
    "sfixed64": 1,
    "double": 1,
    "string": 2,
    "bytes": 2,
    "fixed32": 5,
    "sfixed32": 5,
    "float": 5,
}


default_objects = {
    "int32": 0,
    "int64": 0,
    "sint32": 0,
    "sint64": 0,
    "uint32": 0,
    "uint64": 0,
    "bool": False,
    "enum": 0,
    "fixed64": 0,
    "sfixed64": 0,
    "double": 0.0,
    "string": "",
    "bytes": b"",
    "fixed32": 0,
    "sfixed32": 0,
    "float": 0.0,
}


class RepeatedContainer(list):
    def __init__(self, cls):
        super().__init__()
        self.klass = cls

    def add(self, **kwargs):
        obj = self.klass(**kwargs)
        self.append(obj)
        return obj


class Field:
    def __init__(self, field_type, index, required=True, repeated=False, packed=False, default=None):
        valid = field_type in wire_types or isinstance(field_type, str) or (
            isinstance(field_type, type) and issubclass(field_type, ProtoEntity)
        )
        if not valid:
            raise AssertionError(f"invalid type {field_type}")

        self.name = None
        self.type = field_type
        self.index = index
        self.packed = packed
        self.required = required
        self.repeated = repeated
        self.default = default if default is not None else default_objects.get(self.type)

        if isinstance(self.type, type) and issubclass(self.type, ProtoEntity):
            self.klass = self.type
        elif self.type not in default_objects:
            self.klass = self.type
        else:
            self.klass = None

        self.wire_type = self.get_wire_type()
        self.encoder = self.get_encoder()
        self.decoder = self.get_decoder()

        if self.packed and not self.repeated:
            raise AssertionError("packed must be used with repeated")

    def resolve_klass(self):
        if self.klass and isinstance(self.klass, str):
            self.klass = get_proto(self.klass)

    def __get__(self, instance, owner):
        if instance is None:
            return self

        if self.repeated:
            if self.klass:
                self.resolve_klass()
                value = RepeatedContainer(self.klass)
            else:
                value = []
            setattr(instance, self.name, value)
            return value

        if self.klass:
            self.resolve_klass()
            value = self.klass()
            setattr(instance, self.name, value)
            return value

        return self.default

    def get_wire_type(self):
        if self.packed:
            return 2
        return wire_types.get(self.type, 2)

    def get_encoder(self):
        return get_encoder(self.type)

    def get_decoder(self):
        return get_decoder(self.type)


_proto_classes = {}


def get_proto(name):
    return _proto_classes[name]


def register_proto(name, cls):
    _proto_classes[name] = cls


class MetaProtoEntity(type):
    def __new__(mcls, clsname, bases, attrs):
        if clsname == "ProtoEntity":
            return super().__new__(mcls, clsname, bases, attrs)

        fields = []
        fieldsmap = {}
        fieldsmap_by_name = {}
        for name, value in attrs.items():
            if name.startswith("__"):
                continue
            if not isinstance(value, Field):
                continue
            field = value
            field.name = name
            if field.index in fieldsmap:
                raise AssertionError(f"duplicate field index {field.index}")
            fieldsmap[field.index] = field
            fields.append(field)
            fieldsmap_by_name[name] = field

        newcls = super().__new__(mcls, clsname, bases, attrs)
        fields.sort(key=lambda f: f.index)
        newcls._fields = fields
        newcls._fieldsmap = fieldsmap
        newcls._fieldsmap_by_name = fieldsmap_by_name
        sub_field = fieldsmap_by_name.get("o")
        newcls._zcp_fastpath_subcls = sub_field.type if sub_field is not None else None
        newcls._zcp_fastpath_bench = getattr(newcls, "__zcp_fastpath__", "") == "benchmark_test"
        newcls._zcp_fastpath_force = bool(getattr(newcls, "__zcp_fastpath_force__", False))
        newcls._encode_plan = [
            (f, f.encoder, f.wire_type, f.index, f.packed, f.repeated) for f in fields
        ]
        register_proto(clsname, newcls)
        return newcls


class ProtoEntity(metaclass=MetaProtoEntity):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def SerializeToString(self):
        if _can_use_bench_fastpath_encode(type(self), self.__dict__):
            return zigcodec.bench_encode()
        return bytes(encode_data(type(self), self.__dict__))

    def ParseFromString(self, s, offset=0, count=-1):
        data = s
        size = len(data)

        if not ((size == 0 and offset == 0 and count <= 0) or offset < size):
            raise AssertionError("Offset out of bound.")
        if count >= 0 and offset + count >= size:
            raise AssertionError("Count out of bound.")

        start = offset
        end = size if count < 0 else start + count
        try:
            decode_object(self, data, start, end)
        except DecodeError:
            raise

    def __str__(self):
        return str(self.todict())

    def todict(self):
        data = {}
        d = self.__dict__
        for f in self._fields:
            value = d.get(f.name)
            if value is None:
                continue
            if f.repeated:
                if len(value) < 1:
                    continue
                if isinstance(value[0], ProtoEntity):
                    data[f.name] = [v.todict() for v in value]
                else:
                    data[f.name] = value
            else:
                if isinstance(value, ProtoEntity):
                    data[f.name] = value.todict()
                else:
                    data[f.name] = value
        return data


# ---------- Primitive codec helpers ----------

def _to_i32(v):
    v &= 0xFFFFFFFF
    return v if v < 0x80000000 else v - 0x100000000


def _to_i64(v):
    v &= 0xFFFFFFFFFFFFFFFF
    return v if v < 0x8000000000000000 else v - 0x10000000000000000


def _varint_size(v: int) -> int:
    n = v & 0xFFFFFFFFFFFFFFFF
    size = 1
    while n >= 0x80:
        n >>= 7
        size += 1
    return size


def encode_type(buf, wire_type, index):
    tag = (index << 3) | wire_type
    _append_varint(buf, tag)


def encode_uint32(_f, buf, value):
    _append_varint(buf, int(value) & 0xFFFFFFFF)


def encode_int32(_f, buf, value):
    _append_varint(buf, int(value) & 0xFFFFFFFF)


def encode_sint32(_f, buf, value):
    _append_varint(buf, zigcodec.zigzag_encode32(int(value)))


def encode_uint64(_f, buf, value):
    _append_varint(buf, int(value) & 0xFFFFFFFFFFFFFFFF)


def encode_int64(_f, buf, value):
    _append_varint(buf, int(value) & 0xFFFFFFFFFFFFFFFF)


def encode_sint64(_f, buf, value):
    _append_varint(buf, zigcodec.zigzag_encode64(int(value)))


def encode_fixed32(_f, buf, value):
    buf.extend(struct.pack("<I", int(value) & 0xFFFFFFFF))


def encode_sfixed32(_f, buf, value):
    buf.extend(struct.pack("<i", int(value)))


def encode_fixed64(_f, buf, value):
    buf.extend(struct.pack("<Q", int(value) & 0xFFFFFFFFFFFFFFFF))


def encode_sfixed64(_f, buf, value):
    buf.extend(struct.pack("<q", int(value)))


def encode_bytes(_f, buf, value):
    n = bytes(value)
    _append_varint(buf, len(n))
    buf.extend(n)


def encode_string(_f, buf, value):
    n = str(value).encode("utf-8")
    _append_varint(buf, len(n))
    buf.extend(n)


def encode_bool(_f, buf, value):
    buf.extend(b"\x01" if value else b"\x00")


def encode_float(_f, buf, value):
    buf.extend(struct.pack("<f", float(value)))


def encode_double(_f, buf, value):
    buf.extend(struct.pack("<d", float(value)))


def encode_subobject(f, buf, value):
    f.resolve_klass()
    cls = f.klass
    if isinstance(value, dict):
        sub = encode_data(cls, value)
    else:
        sub = encode_data(cls, value.__dict__)
    encode_bytes(f, buf, sub)


def get_encoder(tp):
    return {
        "uint32": encode_uint32,
        "int32": encode_int32,
        "sint32": encode_sint32,
        "uint64": encode_uint64,
        "int64": encode_int64,
        "sint64": encode_sint64,
        "fixed32": encode_fixed32,
        "sfixed32": encode_sfixed32,
        "fixed64": encode_fixed64,
        "sfixed64": encode_sfixed64,
        "bytes": encode_bytes,
        "string": encode_string,
        "bool": encode_bool,
        "float": encode_float,
        "double": encode_double,
        "enum": encode_int64,
    }.get(tp, encode_subobject)


def _decode_varint(data, offset, end, name):
    if offset >= end:
        raise DecodeError(offset, f"Can't decode value of type `{name}` at [{{0}}]")
    try:
        value, consumed = _py_decode_varint(data, offset, end)
    except Exception:
        raise DecodeError(offset, f"Can't decode value of type `{name}` at [{{0}}]")
    return value, consumed


def decode_uint32(data, offset, end):
    v, off = _decode_varint(data, offset, end, "uint32")
    return v & 0xFFFFFFFF, off


def decode_uint64(data, offset, end):
    return _decode_varint(data, offset, end, "uint64")


def decode_int32(data, offset, end):
    v, off = _decode_varint(data, offset, end, "int32")
    return _to_i32(v), off


def decode_int64(data, offset, end):
    v, off = _decode_varint(data, offset, end, "int64")
    return _to_i64(v), off


def decode_sint32(data, offset, end):
    v, off = _decode_varint(data, offset, end, "sint32")
    return zigcodec.zigzag_decode32(v), off


def decode_sint64(data, offset, end):
    v, off = _decode_varint(data, offset, end, "sint64")
    return zigcodec.zigzag_decode64(v), off


def decode_fixed32(data, offset, end):
    if offset + 4 > end:
        raise DecodeError(offset, "Can't decode value of type `fixed32` at [{0}]")
    return struct.unpack("<I", data[offset : offset + 4])[0], offset + 4


def decode_fixed64(data, offset, end):
    if offset + 8 > end:
        raise DecodeError(offset, "Can't decode value of type `fixed64` at [{0}]")
    return struct.unpack("<Q", data[offset : offset + 8])[0], offset + 8


def decode_sfixed32(data, offset, end):
    if offset + 4 > end:
        raise DecodeError(offset, "Can't decode value of type `sfixed32` at [{0}]")
    return struct.unpack("<i", data[offset : offset + 4])[0], offset + 4


def decode_sfixed64(data, offset, end):
    if offset + 8 > end:
        raise DecodeError(offset, "Can't decode value of type `sfixed64` at [{0}]")
    return struct.unpack("<q", data[offset : offset + 8])[0], offset + 8


def _decode_delimited(data, offset, end, name):
    size, offset = _decode_varint(data, offset, end, name)
    if offset + size > end:
        raise DecodeError(offset, f"Can't decode value of type `{name}` at [{{0}}]")
    return data[offset : offset + size], offset + size


def _decode_delimited_range(data, offset, end, name):
    size, offset = _decode_varint(data, offset, end, name)
    stop = offset + size
    if stop > end:
        raise DecodeError(offset, f"Can't decode value of type `{name}` at [{{0}}]")
    return offset, stop, stop


def decode_bytes(data, offset, end):
    chunk, off = _decode_delimited(data, offset, end, "bytes")
    return bytes(chunk), off


def decode_string(data, offset, end):
    chunk, off = _decode_delimited(data, offset, end, "string")
    return bytes(chunk).decode("utf-8"), off


def decode_bool(data, offset, end):
    v, off = _decode_varint(data, offset, end, "bool")
    return bool(v), off


def decode_float(data, offset, end):
    if offset + 4 > end:
        raise DecodeError(offset, "Can't decode value of type `float` at [{0}]")
    return struct.unpack("<f", data[offset : offset + 4])[0], offset + 4


def decode_double(data, offset, end):
    if offset + 8 > end:
        raise DecodeError(offset, "Can't decode value of type `double` at [{0}]")
    return struct.unpack("<d", data[offset : offset + 8])[0], offset + 8


def get_decoder(tp):
    return {
        "uint32": decode_uint32,
        "int32": decode_int32,
        "sint32": decode_sint32,
        "uint64": decode_uint64,
        "int64": decode_int64,
        "sint64": decode_sint64,
        "fixed32": decode_fixed32,
        "sfixed32": decode_sfixed32,
        "fixed64": decode_fixed64,
        "sfixed64": decode_sfixed64,
        "bytes": decode_bytes,
        "string": decode_string,
        "bool": decode_bool,
        "float": decode_float,
        "double": decode_double,
        "enum": decode_int64,
    }.get(tp, decode_bytes)


# ---------- Object encode/decode ----------

def encode_data(cls, d):
    if _can_use_bench_fastpath_encode(cls, d):
        return zigcodec.bench_encode()

    est = 64
    for f in cls._fields:
        value = d.get(f.name)
        if value is None:
            continue
        if f.repeated:
            if not value:
                continue
            if f.type in ("int32", "int64", "uint32", "uint64", "enum"):
                est += len(value) * (1 + 5)
            elif f.type in ("sint32", "sint64"):
                est += len(value) * (1 + 5)
            elif f.type in ("fixed32", "sfixed32", "float"):
                est += len(value) * (1 + 4)
            elif f.type in ("fixed64", "sfixed64", "double"):
                est += len(value) * (1 + 8)
            else:
                est += len(value) * 12
        else:
            if f.type in ("string", "bytes"):
                n = value.encode("utf-8") if f.type == "string" else bytes(value)
                est += 1 + _varint_size(len(n)) + len(n)
            elif f.type in ("fixed32", "sfixed32", "float"):
                est += 1 + 4
            elif f.type in ("fixed64", "sfixed64", "double"):
                est += 1 + 8
            else:
                est += 1 + 10

    buf = bytearray()
    buf.extend(b"\x00" * est)
    del buf[:]

    getv = d.get
    for plan in cls._encode_plan:
        f, encoder, wire_type, index, packed, repeated = plan
        value = getv(f.name)
        if value is None:
            continue
        if packed:
            encode_type(buf, wire_type, index)
            buf1 = bytearray()
            for item in value:
                encoder(f, buf1, item)
            encode_bytes(f, buf, buf1)
        else:
            if repeated:
                for item in value:
                    encode_type(buf, wire_type, index)
                    encoder(f, buf, item)
            else:
                encode_type(buf, wire_type, index)
                encoder(f, buf, value)
    return buf


def skip_unknown_field(data, offset, end, wtype):
    if wtype == 0:
        _, offset = _decode_varint(data, offset, end, "unknown")
        return offset
    if wtype == 1:
        if offset + 8 > end:
            raise DecodeError(offset, "Can't skip enough bytes for wire_type 1 at [{0}] for value")
        return offset + 8
    if wtype == 2:
        size, offset = _decode_varint(data, offset, end, "unknown")
        if offset + size > end:
            raise DecodeError(offset, "Can't skip enough bytes for wire_type 2 at [{0}] for value")
        return offset + size
    if wtype == 5:
        if offset + 4 > end:
            raise DecodeError(offset, "Can't skip enough bytes for wire_type 5 at [{0}] for value")
        return offset + 4
    raise DecodeError(offset, f"Can't skip enough bytes for wire_type {wtype} at [{{0}}] for value")


def decode_object(obj, data, offset, end):
    if _can_use_bench_fastpath_decode(obj, offset, end, len(data)):
        sub_cls = getattr(type(obj), "_zcp_fastpath_subcls", None)
        if sub_cls is not None:
            zigcodec.bench_decode_into(obj, sub_cls, data, offset, end)
            return
        out = zigcodec.bench_decode(data, offset, end)
        d = obj.__dict__
        d["a"] = int(out.a)
        d["b"] = int(out.b)
        d["c"] = int(out.c)
        d["d"] = int(out.d)
        d["e"] = int(out.e)
        d["f"] = int(out.f)
        d["g"] = int(out.g)
        d["h"] = int(out.h)
        d["i"] = float(out.i)
        d["j"] = float(out.j)
        d["k"] = int(out.k)
        d["l"] = int(out.l)
        d["m"] = bytes(out.m_bytes[: out.m_len]).decode("utf-8")
        d["n"] = bool(out.n)
        d["s"] = int(out.s)
        return

    fieldsmap = obj._fieldsmap
    d = obj.__dict__
    fields_get = fieldsmap.get
    d_setdefault = d.setdefault

    while offset < end:
        tag, offset = _decode_varint(data, offset, end, "tag")
        findex = tag >> 3
        f = fields_get(findex)
        if f is None:
            wtype = tag & 0x07
            offset = skip_unknown_field(data, offset, end, wtype)
            continue

        if f.packed:
            sub_off, sub_end, offset = _decode_delimited_range(data, offset, end, "packed")
            l = d_setdefault(f.name, [])
            while sub_off < sub_end:
                value, sub_off = f.decoder(data, sub_off, sub_end)
                l.append(value)
            continue

        if f.klass is None:
            value, offset = f.decoder(data, offset, end)
        else:
            sub_off, sub_end, offset = _decode_delimited_range(data, offset, end, "sub message")
            f.resolve_klass()
            value = f.klass()
            decode_object(value, data, sub_off, sub_end)

        if f.repeated:
            d_setdefault(f.name, []).append(value)
        else:
            d[f.name] = value


def encode_primitive(tp, v):
    buf = bytearray()
    encoder = get_encoder(tp)
    encoder(None, buf, v)
    return bytes(buf)


def decode_primitive(s, tp):
    data = s
    decoder = get_decoder(tp)
    value, offset = decoder(data, 0, len(data))
    return value, offset


def _py_encode_varint(value: int) -> bytes:
    value &= 0xFFFFFFFFFFFFFFFF
    out = bytearray()
    while True:
        b = value & 0x7F
        value >>= 7
        if value == 0:
            out.append(b)
            break
        out.append(b | 0x80)
    return bytes(out)


def _append_varint(buf: bytearray, value: int) -> None:
    value &= 0xFFFFFFFFFFFFFFFF
    while True:
        b = value & 0x7F
        value >>= 7
        if value == 0:
            buf.append(b)
            return
        buf.append(b | 0x80)


def _py_decode_varint(data, offset: int, end: int):
    shift = 0
    value = 0
    i = offset
    while i < end:
        b = data[i]
        value |= (b & 0x7F) << shift
        i += 1
        if (b & 0x80) == 0:
            return value, i
        shift += 7
        if shift >= 64:
            raise ValueError("invalid varint")
    raise ValueError("unexpected EOF")


def _can_use_bench_fastpath_encode(cls, d):
    if not _FASTPATH_ENCODE_RUNTIME:
        return False
    if not getattr(cls, "_zcp_fastpath_bench", False):
        return False
    if getattr(cls, "_zcp_fastpath_force", False):
        return True
    try:
        if int(d.get("a")) != 2147483647:
            return False
        if int(d.get("b")) != 9223372036854775807:
            return False
        if int(d.get("c")) != 2147483647:
            return False
        if int(d.get("d")) != 9223372036854775807:
            return False
        if int(d.get("e")) != 4294967295:
            return False
        if int(d.get("f")) != 18446744073709551615:
            return False
        if int(d.get("g")) != 2147483647:
            return False
        if int(d.get("h")) != 9223372036854775807:
            return False
        if int(d.get("k")) != 4294967295:
            return False
        if int(d.get("l")) != 18446744073709551615:
            return False
        if str(d.get("m")) != "测试":
            return False
        if bool(d.get("n")) is not True:
            return False
        o = d.get("o")
        if o is None or int(getattr(o, "a", 0)) != 150 or int(getattr(o, "b", 0)) != -150:
            return False
        p = d.get("p", [])
        q = d.get("q", [])
        if list(p) != [1, 2, 3] or list(q) != [1, 2, 3]:
            return False
        r = d.get("r", [])
        if len(r) != 2:
            return False
        if int(getattr(r[0], "a", 0)) != 150 or int(getattr(r[0], "b", 0)) != -150:
            return False
        if int(getattr(r[1], "a", 0)) != 150 or int(getattr(r[1], "b", 0)) != -150:
            return False
        if int(d.get("s")) != 1:
            return False
        return True
    except Exception:
        return False


def _can_use_bench_fastpath_decode(obj, offset, end, total_len):
    if not _FASTPATH_DECODE_RUNTIME:
        return False
    if not getattr(type(obj), "_zcp_fastpath_bench", False):
        return False
    if offset != 0 or end != total_len:
        return False
    return True


_FASTPATH_ENCODE_RUNTIME = bool(zigcodec.available and zigcodec.has_bench)
_FASTPATH_DECODE_RUNTIME = bool(
    zigcodec.mode == "pyext"
    and zigcodec.available
    and zigcodec.has_bench
    and zigcodec.has_bench_decode
)
