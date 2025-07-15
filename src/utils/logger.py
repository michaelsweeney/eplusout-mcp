

# import logging
# import logging.config
# FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s()] - %(message)s\n"
# FORMAT = "[%(levelname)s] %(funcName)s - %(filename)s:%(lineno)s -- %(message)s\n"


# logger = logging.getLogger('__main__')

# logging_config = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'simple': {
#             'format': FORMAT
#         }
#     },
#     'handlers': {
#         'stdout': {
#             'class': 'logging.StreamHandler',
#             'formatter': 'simple',
#             'stream': 'ext://sys.stdout'
#         },
#         'file': {
#             'class': 'logging.handlers.RotatingFileHandler',
#             'level': 'DEBUG',
#             'formatter': 'simple',
#             'filename': 'maplog.txt',
#             'maxBytes': 10000,
#             'backupCount': 3
#         }

#     },
#     'loggers': {
#         'root': {'level': 'DEBUG', 'handlers': ['stdout']}
#     },
# }


# def setup_logger():
#     logging.config.dictConfig(logging_config)



# setup_logger()
