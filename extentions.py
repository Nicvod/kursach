import threading
from queue import Queue
from typing import Union

class MyMessage:
    def __init__(self, host_name="", host_info="", author="", text=""):
        self.host_name = host_name
        self.host_info = host_info
        self.author = author
        self.text = text


class HostsUnion:
    def __init__(self, tw_info, yt_info, status: bool):
        self.tw_info = tw_info
        self.yt_info = yt_info
        self.status = status


class ThreadCommunication:
    def __init__(self):
        self.queues = {
            "YT": Queue(),
            "TW": Queue(),
            "TW_CNG": Queue(),
            "YT_CNG": Queue()
        }
        self.locks = {
            "YT": threading.Lock(),
            "TW": threading.Lock(),
            "TW_CNG": threading.Lock(),
            "YT_CNG": threading.Lock()
        }

    def add_message(self, thread_name: str, item: MyMessage) -> None:
        with self.locks[thread_name]:
            self.queues[thread_name].put(item)

    def get_message(self, thread_name: str) -> Union[None, MyMessage]:
        with self.locks[thread_name]:
            if not self.queues[thread_name].empty():
                return self.queues[thread_name].get()
            else:
                return None

    def add_hosts_info(self, thread_name: str, item: HostsUnion) -> None:
        with self.locks[thread_name]:
            self.queues[thread_name].put(item)

    def get_hosts_info(self, thread_name: str) -> Union[None, HostsUnion]:
        with self.locks[thread_name]:
            if not self.queues[thread_name].empty():
                return self.queues[thread_name].get()
            else:
                return None