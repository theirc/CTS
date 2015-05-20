import logging

import requests
from requests.exceptions import SSLError

from django.conf import settings


logger = logging.getLogger(__name__)


class OnaApiClientException(Exception):
    def __init__(self, status_code, message, url=None, *args, **kwargs):
        self.status_code = status_code
        self.error_message = message
        self.url = url
        super(OnaApiClientException, self).__init__(status_code, message, *args, **kwargs)

    def __str__(self):
        if self.url:
            return "OnaApiClientException(%s, %d, %s)" % (self.url, self.status_code,
                                                          self.error_message)
        else:
            return "OnaApiClientException(%d, %s)" % (self.status_code, self.error_message)


class OnaApiClient(object):
    """
    Simple client to access Ona API
    """

    def __init__(self, domain=None, api_key=None):
        self.domain = domain or settings.ONA_DOMAIN
        self.api_key = api_key or settings.ONA_API_ACCESS_TOKEN
        assert self.domain is not None
        assert self.api_key is not None

    def session(self):
        session = requests.Session()
        session.headers.update({'Authorization': 'Token {0}'.format(self.api_key)})
        return session

    def _request(self, method, endpoint, expected_status_code=200, **kwargs):
        if method not in ['get', ]:
            raise Exception("Unsupported method: {0}".format(method))

        url = 'https://{0}/api/v1/{1}.json'.format(self.domain, endpoint)
        method = getattr(self.session(), method)
        try:
            response = method(url, **kwargs)
        except SSLError as e:
            logger.exception("Got an SSLError accessing url %s" % url)
            for arg in e.args:
                logger.error("SSLError arg: %s" % arg)
            raise OnaApiClientException(0, "SSL error, see log (%s)" % e, url=url)
        try:
            data = response.json()
        except Exception as e:
            # I hate catching ALL exceptions, but the python docs don't say what
            # exceptions `json.loads` might raise. Just try to capture as much info
            # as possible from whatever exception we run into.
            raise OnaApiClientException(0, "ONA response could not be parsed as JSON: exception "
                                           "%s, content %s" % (e, response.text), url=url)

        if response.status_code != expected_status_code:
            if 'detail' in data:
                raise OnaApiClientException(response.status_code, data['detail'], url=url)
            raise OnaApiClientException(response.status_code, 'Unexpected error', url=url)

        return data

    def get(self, endpoint, query_params=None, expected_status_code=200):
        """
        Create a GET request based on supplied endpoint and optional
        query_params dictionary.

        Returns a JSON structure.
        """
        return self._request('get', endpoint, expected_status_code, params=query_params)

    def get_form_submissions(self, form_id, since=None):
        kwargs = None
        if since:
            query = '{"_submission_time": {"$gt": "%s"}}' % since.strftime("%Y-%m-%dT%H:%M:%S")
            kwargs = {'query': query}
        return self.get('data/{0}'.format(form_id), query_params=kwargs)

    def get_form_definition(self, form_id):
        return self.get('forms/{0}/form'.format(form_id))
