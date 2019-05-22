import redis   # 导入redis模块，通过python操作redis 也可以直接在redis主机的服务端操作缓存数据库

r = redis.Redis(host='localhost', port=6379, decode_responses=True)   # host是redis主机，需要redis服务端和客户端都启动 redis默认端口是6379
# a = r.xadd(name="mystream", id="*", fields={"name": "32"})
# print(a)
# print(str(a))
# b = r.xread(streams={"mystream": 1}) # 非阻塞读取最后一条
# print(b)
# r.xack("mystream", *[a])  # ack消费组消息

if r.exists('stream_4'):
    r.delete('stream_4')
r1 = r.xadd('stream_4', {'name': 'jack'})
r2 = r.xadd('stream_4', {'name': 'Tom'})
r3 = r.xadd('stream_4', {'name': 'Will'})
r.xgroup_create('stream_4', 'group_1', id=0)
# >号表示从当前消费组的last_delivered_id后面开始读
# 每当消费者读取一条消息，last_delivered_id变量就会前进
print("r.xinfo_consumers:", r.xinfo_consumers('stream_4', 'group_1'))
ret = r.xreadgroup('group_1', 'consumer_1', {'stream_4': ">"}, count=1)
print("r.xinfo_consumers:", r.xinfo_consumers('stream_4', 'group_1'))
# [['stream_4', [(b'1543455084777-0', {b'name': b'jack'})]]]
temp = r.xreadgroup('group_1', 'consumer_2', {'stream_4': ">"}, count=2)
print("r.xinfo_consumers:", r.xinfo_consumers('stream_4', 'group_1'))
# idle空闲了多长时间ms没有读取消息了
# [{'name': b'consumer_1', 'pending': 3, 'idle': 1}]
print(r.xpending('stream_4', 'group_1'))
# {'pending': 3, 'min': b'1543455084777-0', 'max': b'1543455084777-2', 'consumers': [{'name': b'consumer_1', 'pending': 3}]}
# ack 2条消息
r.xack('stream_4', 'group_1', *[r1, r2])
print(r.xinfo_consumers('stream_4', 'group_1'))
print('ret:', ret)
print('temp:', temp)
# [{'name': b'consumer_1', 'pending': 1, 'idle': 1}] pending减少了