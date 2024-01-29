import logging
from pymongo import monitoring


class MongoCommandLogger(monitoring.CommandListener):

    def started(self, event):
        logging.debug(
            f"Command {event.command}"
        )
        logging.info(
            f"Command {event.command_name} with request id {event.request_id} started on server {event.connection_id}"
        )

    def succeeded(self, event):
        logging.info(
            f"Command {event.command_name} with request id {event.request_id} on server {event.connection_id} "
            f"succeeded in {event.duration_micros} microseconds"
        )

    def failed(self, event):
        logging.info(
            f"Command {event.command_name} with request id {event.request_id} on server {event.connection_id} "
            f"failed in {event.duration_micros} microseconds"
        )
