import math
import os
import queue
import threading
from shutil import move


class LogWriter(threading.Thread):

    rollover_size = math.pow(1024, 2) * 100
    rollover_postfix = '.1'  # Only keep one rolled file

    def __init__(self, log_file):
        threading.Thread.__init__(self)
        self._queue = queue.Queue()
        self._log_file = log_file
        self._stop_event = threading.Event()
        self.setDaemon(True)
        self.start()

    def run(self):
        log_file = open(self._log_file, 'a')
        try:
            while not self._stop_event.is_set():
                try:
                    result = self._queue.get(timeout=15)
                    log_file.write(result)
                    log_file.flush()  # TODO: set a manual buffer instead
                    self._queue.task_done()
                    if os.fstat(log_file.fileno()).st_size > self.rollover_size:
                        log_file.close()
                        log_file = self._roll(log_file)
                except queue.Empty:
                    pass  # If we encounter a timeout
        except IOError as e:
            print(e)
        finally:
            log_file.flush()
            log_file.close()

    def stop(self):
        self._stop_event.set()
        self._queue.join()

    def write(self, p):
        self._queue.put(p)

    def _roll(self, file_obj):
        try:
            file_obj.close()
            move(self._log_file, self._log_file + self.rollover_postfix)
        except IOError as e:
            raise e
        return open(self._log_file, 'a')
