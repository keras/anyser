"""
Wrapper for serializing custom data types with any serializer

In [1]: from anyser import Codec, Serializer
   ...: import json as _json
   ...: import dateutil.parser
   ...: import dateutil.tz
   ...: from datetime import datetime
   ...: from uuid import uuid4, UUID
   ...: spec = [
   ...:     Codec(
   ...:         name='uuid',
   ...:         kind=UUID,
   ...:         to_primitive=str,
   ...:         from_primitive=UUID,
   ...:     ),
   ...:     Codec(
   ...:         name='dt',
   ...:         kind=datetime,
   ...:         to_primitive=lambda dt: dt.isoformat(),
   ...:         from_primitive=dateutil.parser.parse,
   ...:     )
   ...: ]
   ...: json_extended = Serializer(spec, encoder=_json.dumps, decoder=_json.loads)

In [2]: json_extended.dumps({
   ...:     'uuid': uuid4(),
   ...:     'datetime': datetime.now(dateutil.tz.gettz('Europe/Helsinki'))
   ...: })
Out[2]: '{"uuid": "$uuid:f06ffa42-d5fb-4f65-b9a7-94d3b92d5c85", "datetime": "$dt:2019-02-10T23:19:39.728538+02:00"}'

In [3]: json_extended.loads('{"uuid": "$uuid:f06ffa42-d5fb-4f65-b9a7-94d3b92d5c85", "datetime": "$dt:2019-02-10T23:19:39.728538+02:00"}')
Out[3]:
{'uuid': UUID('f06ffa42-d5fb-4f65-b9a7-94d3b92d5c85'),
 'datetime': datetime.datetime(2019, 2, 10, 23, 19, 39, 728538, tzinfo=tzoffset(None, 7200))}
"""

from typing import Any, Callable, Dict, Generic, Iterable, Tuple, Type, TypeVar
import re

T = TypeVar('T')
P = TypeVar('P')


class Codec(Generic[T, P]):
    def __init__(self, name: str, kind: T, to_primitive: Callable[[T], P], from_primitive: Callable[[P], T]):
        self.name = name
        self.kind = kind
        self.to_primitive: Callable[[T], P] = to_primitive
        self.from_primitive: Callable[[P], T] = from_primitive


class Serializer:
    def __init__(self, codecs: Iterable[Codec], encoder: Callable[[Any], str], decoder: Callable[[str], Any]):
        self.codecs = list(codecs)
        self.encoder = encoder
        self.decoder = decoder
        self._by_kind: Dict[Type, Tuple[str, Callable[[T], P]]] = {
            c.kind: (c.name, c.to_primitive)
            for c in self.codecs
        }
        self._by_name = {
            c.name: c.from_primitive
            for c in self.codecs
        }
        self._escape_char = '/'
        self._type_char = '$'
        self._type_key = '{type_char}t'.format(type_char=self._type_char)
        self._value_key = 'v'
        self._typed_string_parser = re.compile(
            r'^\{}(\w+)(?::(.+))?'.format(self._type_char)
        )

    def from_primitive(self, obj: P) -> Any:
        by_name = self._by_name

        def filter_dict_keys(key):
            if key.startswith(self._escape_char):
                return key[1:]
            elif key.startswith(self._type_char):
                m = self._typed_string_parser.match(key)
                if m:
                    tpe, body = m.groups()
                else:
                    raise ValueError('Invalid type on %r' % key)
                return by_name[tpe](body)
            else:
                return key

        def inner(obj: P) -> Any:
            if isinstance(obj, dict):
                if self._type_key in obj:
                    tpe = obj[self._type_key]
                    return by_name[tpe](inner(obj[self._value_key]))
                else:
                    return {
                        filter_dict_keys(k): inner(v)
                        for k, v in obj.items()
                    }
            elif isinstance(obj, list):
                return list(map(inner, obj))
            elif isinstance(obj, str):
                if obj.startswith(self._escape_char):
                    return obj[1:]
                if obj.startswith(self._type_char):
                    m = self._typed_string_parser.match(obj)
                    if m:
                        tpe, body = m.groups()
                    else:
                        raise ValueError('Invalid type on %r' % obj)
                    return by_name[tpe](body)
                return obj
            return obj

        return inner(obj)

    def to_primitive(self, obj) -> P:
        # TODO: simplify
        by_kind = self._by_kind

        def filter_dict_keys(key):
            obj_type = type(key)
            if isinstance(key, str) and key.startswith((self._type_char, self._escape_char)):
                return self._escape_char + key
            elif obj_type in by_kind:
                name, writer = by_kind[obj_type]
                return '%s%s:%s' % (self._type_char, name, writer(key))
            else:
                return key

        def inner(obj):
            obj_type = type(obj)

            if isinstance(obj, dict):
                return {
                    filter_dict_keys(k): inner(v)
                    for k, v in obj.items()
                }
            elif isinstance(obj, list):
                return list(map(inner, obj))
            elif obj_type is int:
                return obj
            elif obj_type in by_kind:
                name, writer = by_kind[obj_type]
                v = writer(obj)
                if v is not None:
                    v = inner(v)
                    if isinstance(v, str):
                        return '%s%s:%s' % (self._type_char, name, v)
                    else:
                        return {
                            self._type_key: name,
                            self._value_key: v

                        }
                else:
                    return '%s%s' % (self._type_char, name)
            elif isinstance(obj, str) and obj.startswith(
                    (self._type_char, self._escape_char)):
                return self._escape_char + obj
            return obj

        return inner(obj)

    def dumps(self, data: Any) -> str:
        return self.encoder(self.to_primitive(data))

    def loads(self, data: str) -> Any:
        return self.from_primitive(self.decoder(data))
