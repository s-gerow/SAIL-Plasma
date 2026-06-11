import logging
import queue

class QueueHandler(logging.Handler):
    '''
    logging handler puts records into a queue instead of writing them to file or console. then the gui can disseminate the logs 
    as it sees fit
    '''
    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record: logging.LogRecord):
        self.log_queue.put(record)


########
# Notes:
# emit() must be called by all logging.Handlers. In this case it just applies the LogRecord created by logger.info/warning/etc
# to the thread queue we create in the controller. this is passed to the gui to be put into files or terminal etc.