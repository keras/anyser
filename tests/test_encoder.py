import unittest
from datetime import datetime
import json
from uuid import UUID

from anyser import Serializer, Codec

dt = datetime(2019, 2, 3, 1, 23, 45, 12300)
uid = UUID('152e4227-6852-4f8e-912d-bd75478c7eaa')


class MyType:
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def __repr__(self):
        return 'MyType(%s)' % ', '.join(
            '%s=%r' % item
            for item in vars(self).items()
        )

    def __eq__(self, other):
        return vars(self) == vars(other)


class CoderTestCase(unittest.TestCase):
    def test_datetime(self):
        spec = [
            Codec(
                name='dt',
                kind=datetime,
                to_primitive=lambda dt: dt.isoformat(),
                from_primitive=lambda body: datetime.strptime(body, '%Y-%m-%dT%H:%M:%S.%f'),
            )
        ]
        coder = Serializer(spec, encoder=json.dumps, decoder=json.loads)

        self.assertEqual(
            coder.to_primitive(dt),
            '$dt:2019-02-03T01:23:45.012300'
        )

        self.assertEqual(
            coder.from_primitive('$dt:2019-02-03T01:23:45.012300'),
            dt
        )

    def test_uuid(self):
        spec = [
            Codec(
                name='uuid',
                kind=UUID,
                to_primitive=str,
                from_primitive=UUID,
            )
        ]
        coder = Serializer(spec, encoder=json.dumps, decoder=json.loads)

        self.assertEqual(
            coder.to_primitive(uid),
            '$uuid:152e4227-6852-4f8e-912d-bd75478c7eaa'
        )
        self.assertEqual(
            coder.from_primitive('$uuid:152e4227-6852-4f8e-912d-bd75478c7eaa'),
            uid
        )

    def test_mytytpe(self):
        spec = [
            Codec(
                name='mytype',
                kind=MyType,
                to_primitive=lambda obj: [obj.a, obj.b, obj.c],
                from_primitive=lambda data: MyType(*data),
            )
        ]
        coder = Serializer(spec, encoder=json.dumps, decoder=json.loads)

        my_obj = MyType('hello', 3.14, ['world'])

        self.assertEqual(
            coder.to_primitive(my_obj),
            {'$t': 'mytype', 'v': ['hello', 3.14, ['world']]}
        )

        self.assertEqual(
            coder.from_primitive({'$t': 'mytype', 'v': ['hello', 3.14, ['world']]}),
            my_obj
        )

    def test_complex(self):
        spec = [
            Codec(
                name='uuid',
                kind=UUID,
                to_primitive=str,
                from_primitive=UUID,
            ),
            Codec(
                name='dt',
                kind=datetime,
                to_primitive=lambda dt: dt.isoformat(),
                from_primitive=lambda body: datetime.strptime(body, '%Y-%m-%dT%H:%M:%S.%f'),
            ),
            Codec(
                name='mytype',
                kind=MyType,
                to_primitive=lambda obj: [obj.a, obj.b, obj.c],
                from_primitive=lambda data: MyType(*data),
            )
        ]
        coder = Serializer(spec, encoder=json.dumps, decoder=json.loads)

        my_obj = MyType(
            'hello',
            MyType(dt, uid, {
                'foo': MyType(None, 1, [MyType('a', 'b', 'c')]),
                'bar': MyType(1, 2, 3),
            }),
            None
        )
        as_primitives = {
            '$t': 'mytype',
            'v': [
                'hello',
                {
                    '$t': 'mytype',
                    'v': [
                        '$dt:2019-02-03T01:23:45.012300',
                        '$uuid:152e4227-6852-4f8e-912d-bd75478c7eaa',
                        {
                            'bar': {'$t': 'mytype', 'v': [1, 2, 3]},
                            'foo': {
                                '$t': 'mytype',
                                'v': [
                                    None,
                                    1,
                                    [{
                                        '$t': 'mytype',
                                        'v': ['a', 'b', 'c']}]]}}]},
                None]}

        self.assertEqual(
            coder.to_primitive(my_obj),
            as_primitives
        )

        self.assertEqual(
            coder.from_primitive(as_primitives),
            my_obj
        )


class EncoderTestCase(unittest.TestCase):
    def test_uuid_json(self):
        spec = [
            Codec(
                name='uuid',
                kind=UUID,
                to_primitive=str,
                from_primitive=UUID,
            )
        ]
        coder = Serializer(spec, encoder=json.dumps, decoder=json.loads)

        self.assertEqual(
            coder.dumps(uid),
            '"$uuid:152e4227-6852-4f8e-912d-bd75478c7eaa"'
        )
        self.assertEqual(
            coder.loads('"$uuid:152e4227-6852-4f8e-912d-bd75478c7eaa"'),
            uid
        )

    def test_mytytpe(self):
        spec = [
            Codec(
                name='mytype',
                kind=MyType,
                to_primitive=lambda obj: [obj.a, obj.b, obj.c],
                from_primitive=lambda data: MyType(*data),
            )
        ]
        coder = Serializer(spec, encoder=json.dumps, decoder=json.loads)

        my_obj = MyType('hello', 3.14, ['world'])

        self.assertEqual(
            coder.dumps(my_obj),
            '{"$t": "mytype", "v": ["hello", 3.14, ["world"]]}'
        )

        self.assertEqual(
            coder.loads('{"$t": "mytype", "v": ["hello", 3.14, ["world"]]}'),
            my_obj
        )
