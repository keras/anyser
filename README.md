# Anyser

Wrapper for serializing custom data types with a chosen backend


```python
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
```
