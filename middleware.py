from . models import LOGSFORHUMAN_THREAD


class LogsForHumansMiddleware(object):
    """Expose request to LogsForHumans.

    This middleware sets request as a local thread variable, making it
    available to the model-level utilities to allow tracking of the
    authenticated user making a change.
    """

    def process_request(self, request):
        LOGSFORHUMAN_THREAD.request = request

    def process_response(self, request, response):
        if hasattr(LOGSFORHUMAN_THREAD, 'request'):
            del LOGSFORHUMAN_THREAD.request
        return response
