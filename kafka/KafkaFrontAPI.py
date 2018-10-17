#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @File  : KafkaFrontAPI.py
# @Author: Liaop
# @Date  : 2018-10-15
# @Desc  : Kafka前置API端封装包

from pykafka import KafkaClient
from pykafka.topic import OffsetType
from pykafka.producer import CompressionType

import time, uuid

def getUUID():
    _node = int(time.time())
    _uuid = uuid.uuid1(_node).__str__()
    return _uuid.replace('-', '')

class APIItem(object):
    def __init__(self):
        self.Name = None
        self.OutTopic = None
        self.InTopic = None
        self.GroupID = None

class KafkaFrontAPI(object):
    '''
    针对快单手前置API服务，专用Python封装类
    '''

    def __init__(self, hosts, apis, encoding='utf-8'):
        self.__hosts = hosts
        self.__apis = apis
        self.__encoding = encoding

    def send_process(self, queue, name):
        '''
        发送信息进程
        :param queue: 消息队列
        :param name: api名称
        :return:
        '''
        _client = KafkaClient(hosts=self.__hosts)
        _out_topic = self.__apis[name].OutTopic
        if not isinstance(_out_topic, bytes):
            _out_topic = _out_topic.encode(self.__encoding)
        _producer = (_client.topics[_out_topic]).get_producer(linger_ms=0, compression=CompressionType.GZIP)
        try:
            while True:
                if not queue.empty():
                    _value = queue.get(True)
                    if not isinstance(_value, bytes):
                        _value = _value.encode(self.__encoding)
                    _producer.produce(_value)
                else:
                    time.sleep(0.001)
        finally:
            _producer.stop()

    def get_process(self, queue, name):
        '''
        接收信息进程
        :param queue: 消息队列
        :param name: api名称
        :return:
        '''
        _client = KafkaClient(hosts=self.__hosts)
        _in_topic = self.__apis[name].InTopic
        if not isinstance(_in_topic, bytes):
            _in_topic = _in_topic.encode(self.__encoding)
        _group_id = self.__apis[name].GroupID
        if not isinstance(_group_id, bytes):
            _group_id = _group_id.encode(self.__encoding)
        _consumer = (_client.topics[_in_topic]).get_balanced_consumer(consumer_group=_group_id,
                                                                      auto_offset_reset=OffsetType.LATEST,
                                                                      managed=True)
        try:
            while True:
                for _msg in _consumer:
                    if _msg is not None:
                        _value = _msg.value.decode(self.__encoding)
                        queue.put(_value)
                        _consumer.commit_offsets()
        finally:
            _consumer.stop()



