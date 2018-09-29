from flask import Flask, render_template, request
from kafka.Kafka import Kafka
from CConfig import CConfig
from LogFlask import Loger
import json
import uuid, time

from kafka.CKafka import CKafka

app = Flask(__name__)

log = Loger('FrontAPI', 'debug', 'log/log.txt', True)
config = CConfig()


hosts = config.getKafka('hosts')
server_name = config.getServer('serverName')




def getUUID(node=None):
    if node is None:
        node = int(time.time())
    _uuid = uuid.uuid1(node).__str__()
    return _uuid.replace('-', '')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/market/<code>')
def get_market(code):
    log.debug('开始获取合约：{}的信息...'.format(code))
    if not code:
        return json.dumps({'code': -1, 'err': '合约号为空', 'data': None})
    kafka = Kafka(hosts=hosts, loger=log)
    msg = kafka.get_market('market', code)
    log.debug('获取到信息：{}'.format(msg))
    if msg:
        return msg
    else:
        return json.dumps({'code': -2, 'err': '没有合约信息', 'data': None})

@app.route('/common', methods=['POST'])
def common():
    '''
    通用请求，用于测试
    POST: /common
    FormData:{in_topic:string, out_topic:string, action:string, data:object}
    :return: {code:int, err:string, sessionid:string, data:object}
    '''
    sessionid = None
    data = None
    try:
        in_topic = request.form.get('in_topic')
        out_topic = request.form.get('out_topic')
        action = request.form.get('action')
        sessionid = getUUID()
        data = request.form.get('data')
        log.debug('\n****************开始处理通用请求，in_topic:{}, out_topic:{}, data:{}'.format(in_topic, out_topic, data))
        data = data.replace("'", '"')
        data = json.loads(data)
        # 组合请求信息，格式必须遵循{'action': action, 'sessionid': sessionid, 'data': {}}
        msg = {'action': action, 'sessionid': sessionid, 'data': data}
        group = 'group.common.{}'.format(sessionid)

        log.debug('发送命令:{}，并等待返回值'.format(msg))
        begin = time.clock()

        kafka = Kafka(hosts=hosts, loger=None)
        kafka.start(in_topic=in_topic, out_topic=out_topic, consumer_group=group, consumer_timeout=6000, balance=False)
        rt = kafka.requestAndResponse(json.dumps(msg))
        kafka.stop()

        # kafka2 = CKafka(hosts=hosts)
        # rt = kafka2.request_response(in_topic=in_topic, out_topic=out_topic, group=group.encode('utf-8'), msg=msg)
        # rt = json.dumps(rt)

        end = time.clock()
        log.debug('成功接收返回值：{}，\n耗时：{}秒'.format(rt, end-begin))
        log.debug('\n****************结束处理通用请求\n')
        return rt
    except Exception as e:
        log.error('通用请求异常：{}'.format(e))
        return json.dumps({'code': -4, 'err': '通用请求异常：{}'.format(e), 'sessionid': sessionid, 'data': data})


if __name__ == '__main__':
    app.run()
