import socket
import threading
import multiprocessing as mp
import multiprocessing.connection as mpc
import logging
import sys
import signal
import time
import os
from pipeline_cluster import util


def _handle_connection(conn, caddr):
    while True:
        try:
            msg = conn.recv()
            logging.debug("[" + time.strftime("%d %m %Y %H:%M:%S") + " - " + caddr[0] + " - " + str(msg["pid"]) + "] " + msg["message"])
        except EOFError as e: # maybe this should catch all exceptions in case the client disconnects while sending
            break
        except ConnectionResetError as e:
            break
    
    conn.close()

def _serve(addr, conn_buffer_size, filename):
    signal.signal(signal.SIGINT, lambda signum, frame: exit(0))
    signal.signal(signal.SIGTERM, lambda signum, frame: exit(0))
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    file_logger = logging.FileHandler(filename, "a", "utf-8")
    root_logger.addHandler(file_logger)
    log_handler = logging.StreamHandler(sys.stdout)
    root_logger.addHandler(log_handler)
    
    with mpc.Listener(addr, "AF_INET", conn_buffer_size, None) as lst:
        while True:
            conn = lst.accept()
            caddr = lst.last_accepted
            threading.Thread(target=_handle_connection, args=(conn, caddr)).start()
        

def serve(addr, filename, conn_buffer_size=2, detach=False):
    if detach:
        proc = mp.Process(target=_serve, args=(addr, conn_buffer_size, filename), daemon=True).start()
    else:
        _serve(addr, conn_buffer_size, filename)
        

server_address = ("", 5555)

def configure(log_addr):
    global server_address
    server_address = log_addr

def log(msg, addr=None):
    addr = addr if addr is not None else server_address
    while True:
        conn = util.connect_timeout(addr, retry=True)
        try:
            conn.send({
                "pid": os.getpid(),
                "message": msg
            })
            conn.close()
            break
        except Exception:
            # possible infinit loop here if there is no log server
            # TODO: implement timeout or retry cap
            continue     
    print(msg)

