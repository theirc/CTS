from django.test import TestCase
from mock import patch, MagicMock
from requests.exceptions import SSLError
from ona import OnaApiClient
from ona.api import OnaApiClientException


class TestClientRequest(TestCase):
    def test_ssl_error(self):
        client = OnaApiClient('example.com', '2384729347234')
        with patch('requests.sessions.Session') as mock_session:
            mock_session.get.side_effect = SSLError
            with self.assertRaises(OnaApiClientException):
                client.get('foo')

    def test_json_parsing_error(self):
        # Make sure if the json parsing fails, we get a useful exception

        # Create a mock response that raises an exception when we try to get the json from it
        mock_response = MagicMock()
        mock_response.text = "This was the content"
        mock_response.content = mock_response.text.encode('utf-8')
        mock_response.json.side_effect = Exception("This is an exception")

        # Mock session that returns our mock response on a 'get' call.
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response

        client = OnaApiClient('example.com', '2384729347234')
        with patch.object(client, 'session') as mock_session_method:
            # 'session' method on our client returns our mock session
            mock_session_method.return_value = mock_session

            try:
                client.get('foo')
            except OnaApiClientException as e:
                # Make sure the exception has lots of useful info
                s = str(e)
                self.assertIn('could not be parsed', s)
                self.assertIn("This is an exception", s)
                self.assertIn("This was the content", s)
            else:
                self.fail("Expected OnaApiClientException")

    def test_empty_response(self):
        mock_response = MagicMock()
        mock_response.text = ""
        mock_response.content = mock_response.text.encode('utf-8')

        # Mock session that returns our mock response on a 'get' call.
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response

        client = OnaApiClient('example.com', '2384729347234')
        with patch.object(client, 'session') as mock_session_method:
            # 'session' method on our client returns our mock session
            mock_session_method.return_value = mock_session

            try:
                client.get('foo')
            except OnaApiClientException as e:
                # Make sure the exception has lots of useful info
                s = str(e)
                self.assertIn('empty', s)
                self.assertIn('foo', s)
            else:
                self.fail("Expected OnaApiClientException")
