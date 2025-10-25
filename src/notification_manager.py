from plyer import notification

def send_notification(title, message):
    """
    Sends a desktop notification.
    :param title: The title of the notification.
    :param message: The body text of the notification.
    """
    try:
        notification.notify(
            title=title,
            message=message,
            app_name='Nora Assistant',
            # Set a timeout for the notification to disappear
            timeout=10
        )
    except Exception as e:
        # This can happen if the notification system is not available
        print(f"Failed to send notification: {e}")

if __name__ == '__main__':
    # Example usage for direct testing
    send_notification("Hello from Nora!", "This is a test notification.")
    print("Test notification sent (if your system supports it).")
