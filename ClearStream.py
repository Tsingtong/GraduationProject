# coding:utf-8

import redis


if __name__ == '__main__':
    r = redis.Redis(host='127.0.0.1', port=6379)
    if r.exists('stream_4'):
        r.delete('stream_4')
        print('clear stream_4 success!')
    else:
        print('clear stream_4 failed!')

    if r.exists('stream_5'):
        r.delete('stream_5')
        print('clear stream_5 success!')
    else:
        print('clear stream_5 failed!')

