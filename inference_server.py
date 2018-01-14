"""
- inference_worker を平行で複数実行し pipe 経由で結果を受け取る
- websocket でサービスする
"""

import threading
import time
import argparse
import json
import pprint
import re
from subprocess import Popen, PIPE
import sys
import traceback

import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.template


websockets = []
queue = []
queue_lock = threading.Lock()
obj = None
start_time = time.time()

parser = argparse.ArgumentParser()
parser.add_argument('--gpus', type=int, default=1)
parser.add_argument('--numjobs', type=int, default=1)
parser.add_argument('--port', type=int, default=9090)
parser.add_argument('--batchsize', type=int, default=10)
args = parser.parse_args()

class WebSocketHandler(tornado.websocket.WebSocketHandler):

    def check_origin(self, origin):
        return True

    def open(self):
        websockets.append(self)

    def on_message(self, message):
        pass

    def on_close(self):
        del websockets[websockets.index(self)]


class WebSocketServer(object):

    def _send_message(self, d):
        if len(websockets) == 0:
            return

        d_json = json.dumps(d, separators=(',', ':'), ensure_ascii=False)

        for s in websockets:
            s.write_message(d_json)

    def worker_func(self, websocket_server):
        # print(websocket_server)
        self.application = tornado.web.Application([
            (r'/test/(.*)', tornado.web.StaticFileHandler, {"path": "."}),
            (r'/ws', WebSocketHandler),
        ])

        self.application.listen(websocket_server._port)
        tornado.ioloop.IOLoop.instance().start()

    def shutdown_server(self):
        tornado.ioloop.IOLoop.instance().stop()

    def initialize_server(self):
        if self.worker_thread is not None:
            if self.worker_thread.is_alive():
                self.shutdown_server()

            # XXX
            while self.worker_thread.is_alive():
                time.sleep(2)

        self.worker_thread = threading.Thread(
            target=self.worker_func, args=(self,))
        self.worker_thread.daemon = True
        self.worker_thread.start()

    def __init__(self, port=9090):
        self._port = port
        self.worker_thread = None

#####################################################


def read_inference(self, cmd=None):
    global queue

    cmd = cmd or 'python3 inference_worker.py'

    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, close_fds=True)
    print(p)
    (child_stdout, child_stdin) = (p.stdout, p.stdin)
    while True:
        output = child_stdout.readline()
        if output is None:
            break
        output_str = output.decode('utf-8')
        try:
            output_json = json.loads(output_str)
            if 'p' in output_json[0]:
                for j in output_json:
                    j['t'] = time.time() - start_time
                try:
                    queue_lock.acquire()
                    queue.extend(output_json)
                finally:
                    queue_lock.release()

        except:
            #print(traceback.format_exc())
            time.sleep(1)
            continue


def launch(cmd):
    print(cmd)
    self = None
    engine_thread = threading.Thread(target=read_inference, args=(self, cmd))
    engine_thread.daemon = True
    engine_thread.start()


def start():
    global obj
    obj = WebSocketServer(port=args.port)
    obj.initialize_server()

    for i in range(args.numjobs):
        if args.gpus > 0:
            launch("python3 inference_worker.py --gpu %d --batchsize %d" % ((i % args.gpus, args.batchsize)))
        else:
            launch("python3 inference_worker.py --batchsize %d" % (args.batchsize))

def main_loop():
    global queue
    global queue_lock
    while True:
        time.sleep(0.1)
        while len(queue) > 0:
            try:
                queue_lock.acquire()
                data = queue
                queue = []
            finally:
                queue_lock.release()
            obj._send_message(data)

start()
main_loop()
