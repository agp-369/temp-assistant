import pytest
from unittest.mock import MagicMock, patch
import context
from plugins.phone_integration import PhoneIntegrationPlugin

@patch('plugins.phone_integration.Client')
def test_send_sms_success(mock_twilio_client):
    """Tests that the send_sms command correctly calls the Twilio client."""
    # Mock the assistant and the Twilio client
    assistant = MagicMock()
    mock_client_instance = MagicMock()
    mock_twilio_client.return_value = mock_client_instance

    # Set the necessary environment variables for the test
    with patch.dict('os.environ', {
        "TWILIO_ACCOUNT_SID": "test_sid",
        "TWILIO_AUTH_TOKEN": "test_token",
        "TWILIO_PHONE_NUMBER": "+15551234567"
    }):
        plugin = PhoneIntegrationPlugin()

    # --- 1. Call the send_sms method ---
    args = {"to_number": "+1234567890", "message": "Hello from the test"}
    plugin.send_sms(args, assistant)

    # --- 2. Assert that the Twilio client was called correctly ---
    mock_client_instance.messages.create.assert_called_with(
        to="+1234567890",
        from_=plugin.twilio_number,
        body="Hello from the test"
    )

    # --- 3. Assert that the assistant spoke the correct response ---
    assistant.speak.assert_called_with("I've sent the message to +1234567890.")

@patch('plugins.phone_integration.Client')
def test_send_sms_no_credentials(mock_twilio_client):
    """Tests that the plugin handles missing credentials gracefully."""
    # Mock the assistant
    assistant = MagicMock()

    # Unset environment variables to simulate missing credentials
    with patch.dict('os.environ', {}, clear=True):
        plugin = PhoneIntegrationPlugin()
        args = {"to_number": "+1234567890", "message": "This should not send"}
        plugin.send_sms(args, assistant)

    # Assert that the assistant spoke the correct error message
    assistant.speak.assert_called_with("I'm sorry, the phone integration is not configured. Please set up your Twilio credentials.", is_error=True)
