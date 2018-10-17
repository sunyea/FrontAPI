#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @File  : app4.py
# @Author: Liaop
# @Date  : 2018-10-15
# @Desc  : 使用消息队列封装包(使用测试环境)

from flask import Flask, request
from multiprocessing import Process, Queue
import time, json

from kafka.KafkaFrontAPI import KafkaFrontAPI, APIItem, getUUID

hosts = '192.168.100.70:9092,192.168.100.71:9092,192.168.100.72:9092'
apis = dict()

# 定义多个API服务
item1 = APIItem()
item1.Name = 'common'
item1.OutTopic = 'tp.test.common'
item1.InTopic = 'tp.test.common.response'
item1.GroupID = 'gp.api.test.common'
apis[item1.Name] = item1

item2 = APIItem()
item2.Name = 'common2'
item2.OutTopic = 'tp.test.common2'
item2.InTopic = 'tp.test.common2.response'
item2.GroupID = 'gp.api.test.common2'
apis[item2.Name] = item2
# 定义API结束

app = Flask(__name__)
kafka = KafkaFrontAPI(hosts=hosts, apis=apis)

app.send_pro = dict()
app.send_que = dict()
app.get_pro = dict()
app.get_que = dict()
for key in apis.keys():
    app.send_que[key] = Queue()
    app.send_pro[key] = Process(target=kafka.send_process, args=(app.send_que[key], key))
    app.get_que[key] = Queue()
    app.get_pro[key] = Process(target=kafka.get_process, args=(app.get_que[key], key))

@app.route('/')
def hello_world():
    return '<h1>Welcome to KDSAPI</h1>'


@app.route('/common', methods=['POST'])
def common():
    '''
    通用测试1
    :return:
    '''
    key = 'common'

    sessionid = getUUID()
    data = request.form.get('data')
    data = data.replace("'", '"').replace('":,', '":"",')
    data = json.loads(data)
    msg = {'action': 'resp', 'sessionid': sessionid, 'data': data}
    print('[Request][{}] json:{}'.format(key, json.dumps(msg)))
    app.send_que[key].put(json.dumps(msg))
    start = time.clock()
    while True:
        end = time.clock()
        if (end-start) > 2:
            rt = json.dumps({'code': -4, 'err': '请求超时', 'sessionid': sessionid, 'data': data})
            break
        if not app.get_que[key].empty():
            print('[Queue-{}] size:{}'.format(key, app.get_que[key].qsize()))
            value = app.get_que[key].get(True)
            value = value.replace("'", '"').replace('":,', '":"",')
            j_value = json.loads(value)
            rt_sessionid = j_value.get('sessionid')
            if rt_sessionid is not None:
                if rt_sessionid != sessionid:
                    app.get_que[key].put(value)
                else:
                    rt = value
                    break
        else:
            time.sleep(0.001)
    end = time.clock()
    print('[{}][USETIME:{}]'.format(key, end-start))
    print('[Response][{}] json:{}'.format(key, rt))
    return rt

@app.route('/common2', methods=['POST'])
def common2():
    '''
    通用测试2
    :return:
    '''
    key = 'common2'

    sessionid = getUUID()
    data = request.form.get('data')
    data = data.replace("'", '"').replace('":,', '":"",')
    data = json.loads(data)
    msg = {'action': 'resp', 'sessionid': sessionid, 'data': data}
    print('[Request][{}] json:{}'.format(key, json.dumps(msg)))
    app.send_que[key].put(json.dumps(msg))
    start = time.clock()
    while True:
        end = time.clock()
        if (end-start) > 2:
            rt = json.dumps({'code': -4, 'err': '请求超时', 'sessionid': sessionid, 'data': data})
            break
        if not app.get_que[key].empty():
            value = app.get_que[key].get(True)
            value = value.replace("'", '"').replace('":,', '":"",')
            j_value = json.loads(value)
            rt_sessionid = j_value.get('sessionid')
            if rt_sessionid is not None:
                if rt_sessionid != sessionid:
                    app.get_que[key].put(value)
                else:
                    rt = value
                    break
        else:
            time.sleep(0.001)
    end = time.clock()
    print('[{}][USETIME:{}]'.format(key, end-start))
    print('[Response][{}] json:{}'.format(key, rt))
    return rt


if __name__ == '__main__':
    print("the server is beginning..")
    for key in apis.keys():
        app.send_pro[key].start()
        app.get_pro[key].start()

    time.sleep(4)
    app.run(host='192.168.100.69', port=8000)