import json
import logging
from datetime import datetime

# 配置logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class CustomEncoder(json.JSONEncoder):
    """处理datetime等不可序列化对象"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def _format_message(message, **kwargs):
    log_entry = {'message': message}
    if kwargs:
        log_entry['data'] = kwargs
    return json.dumps(log_entry, ensure_ascii=False, cls=CustomEncoder)


def info(message, **kwargs):
    logger.info(_format_message(message, **kwargs))


def warn(message, **kwargs):
    logger.warning(_format_message(message, **kwargs))


def error(message, **kwargs):
    logger.error(_format_message(message, **kwargs))


def begin(function_name='Lambda'):
    logger.info(_format_message(f'{function_name} execution started'))


def end(function_name='Lambda'):
    logger.info(_format_message(f'{function_name} execution ended'))
