import logging


class Logger(object):
    __logger = None

    @classmethod
    def get_logger(cls, log_file):
        if cls.__logger == None:
            cls.__logger = Logger.__get_logger(log_file)
        return cls.__logger

    @staticmethod
    def __get_logger(log_file):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        # create a file handler
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.DEBUG)

        # create a logging format
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        # add the handlers to the logger
        logger.addHandler(handler)

        return logger
