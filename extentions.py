import threading
from queue import Queue
from typing import Union
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler('extentions.log')
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

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
        self.queues_messages = {
            "YT": Queue(),
            "TW": Queue()
        }
        self.locks_messages = {
            "YT": threading.Lock(),
            "TW": threading.Lock()
        }

        self.queues_hosts = {
            "YT": Queue(),
            "TW": Queue()
        }
        self.locks_hosts = {
            "YT": threading.Lock(),
            "TW": threading.Lock()
        }

    def add_message(self, thread_name: str, item: MyMessage) -> None:
        with self.locks_messages[thread_name]:
            logger.info(f"New message thread_name: {thread_name}, host: {item.host_name}, host_info: {item.host_info},\
                                                    author: {item.author}, text: {item.text}")
            self.queues_messages[thread_name].put(item)

    def get_message(self, thread_name: str) -> Union[None, MyMessage]:
        with self.locks_messages[thread_name]:
            if not self.queues_messages[thread_name].empty():
                logger.info(f"Get message for thread_name: {thread_name}")
                return self.queues_messages[thread_name].get()
            else:
                return None

    def add_hosts_info(self, thread_name: str, item: HostsUnion) -> None:
        with self.locks_hosts[thread_name]:
            self.queues_hosts[thread_name].put(item)

    def get_hosts_info(self, thread_name: str) -> Union[None, HostsUnion]:
        with self.locks_hosts[thread_name]:
            if not self.queues_hosts[thread_name].empty():
                return self.queues_hosts[thread_name].get()
            else:
                return None