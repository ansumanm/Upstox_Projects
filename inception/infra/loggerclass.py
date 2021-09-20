import logging
import telegram
import time
from logging import Formatter
from logging.handlers import RotatingFileHandler


class TelegramLogger(logging.Handler):
    def __init__(self):
        super().__init__()
    chat_id = 0
    token = 0
    Chat_ID_AKN = "243181507"
    Chat_ID_ANSU = "336975256"
    Chat_ID_BRAHMA = "688610986"
    #bot = telegram.Bot(token)

    def emit(self, record):
        """
        Implement your telegram code here.
        I am writing some boiler plate code.
        """
        logEntry = self.format(record)
        logEntry += "\n"
        logEntry = '`{0}`'.format(logEntry)
        try:
            logging.disable(logging.DEBUG)
            TelegramLogger.bot.send_message(TelegramLogger.Chat_ID_AKN, text=logEntry, parse_mode="Markdown")
            TelegramLogger.bot.send_message(TelegramLogger.Chat_ID_ANSU, text=logEntry, parse_mode="Markdown")
            TelegramLogger.bot.send_message(TelegramLogger.Chat_ID_BRAHMA, text=logEntry, parse_mode="Markdown")
            logging.disable(logging.NOTSET)
        except Exception as e:
            logging.disable(logging.NOTSET)
            print(e)

class ConsoleLogger(logging.Handler):
    def __init__(self):
        super().__init__()

    def emit(self, record):
        """
        Implement your telegram code here.
        I am writing some boiler plate code.
        """
        logEntry = self.format(record)
        print(logEntry)

def xlogger(file_name, chat_id, token):
    formatter = logging.Formatter(
                    '%(asctime)s %(message)s')
    telegram_logger = TelegramLogger()
    telegram_logger.setLevel(logging.CRITICAL)
    telegram_logger.setFormatter(formatter)
    TelegramLogger.chat_id = chat_id
    TelegramLogger.token = token
    TelegramLogger.bot = telegram.Bot(token)

    console_logger = ConsoleLogger()
    console_logger.setLevel(logging.INFO)
    console_logger.setFormatter(formatter)

    rot_handler = RotatingFileHandler(file_name, maxBytes=2**20, backupCount=2)
    rot_handler.setFormatter(formatter)
    rot_handler.setLevel(logging.DEBUG)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(telegram_logger)
    logger.addHandler(console_logger)
    logger.addHandler(rot_handler)
    '''


    print("Trying to log")
    logging.info("INfo Testing botLogger.")
    logging.debug("Debug Testing botLogger.")

    '''

def xlogger_f(file_name, chat_id, token, tsb):
    msg_format = '%(asctime)s [{}] %(message)s'.format(tsb)
    print("msg_format ", msg_format)
    formatter = logging.Formatter(msg_format)
    telegram_logger = TelegramLogger()
    telegram_logger.setLevel(logging.CRITICAL)
    telegram_logger.setFormatter(formatter)
    TelegramLogger.chat_id = chat_id
    TelegramLogger.token = token
    TelegramLogger.bot = telegram.Bot(token)

    console_logger = ConsoleLogger()
    console_logger.setLevel(logging.INFO)
    console_logger.setFormatter(formatter)

    rot_handler = RotatingFileHandler(file_name, maxBytes=2**20, backupCount=2)
    rot_handler.setFormatter(formatter)
    rot_handler.setLevel(logging.DEBUG)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(telegram_logger)
    logger.addHandler(console_logger)
    logger.addHandler(rot_handler)


def xlogger_ansu(file_name, chat_id, token, tsb):
    msg_format = '%(asctime)s [{}] %(message)s'.format(tsb)
    print("msg_format ", msg_format)
    formatter = logging.Formatter(msg_format)
    telegram_logger = TelegramLogger()
    telegram_logger.setLevel(logging.CRITICAL)
    telegram_logger.setFormatter(formatter)
    TelegramLogger.chat_id = chat_id
    TelegramLogger.token = token
    TelegramLogger.bot = telegram.Bot(token)

    console_logger = ConsoleLogger()
    console_logger.setLevel(logging.INFO)
    console_logger.setFormatter(formatter)

    rot_handler = RotatingFileHandler(file_name, maxBytes=2**20, backupCount=2)
    rot_handler.setFormatter(formatter)
    rot_handler.setLevel(logging.DEBUG)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(telegram_logger)
    logger.addHandler(console_logger)
    logger.addHandler(rot_handler)
