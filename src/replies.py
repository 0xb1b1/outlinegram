def user_not_authorized() -> str:
    """Informs the user that they are not authorized"""
    return "You are not authorized to perform this action"


def ask_for_security_code() -> str:
    """Asks the user to enter (a) security code"""
    return "Please enter the administration security code defined in ENV"


def inform_admin() -> str:
    """Informs the user that they are now an administrator"""
    return "You are now an administrator!"


def inform_not_admin() -> str:
    """Informs the user that they are not an administrator (wrong password?)"""
    return "You are not an administrator. Please check your password and try again"


def welcome_message(username: str) -> str:
    """Sends the user a welcome message"""
    return f"Hello {username} and welcome to the Outline Manager Telegram Bot! Please send me your administrator secret code:"


def user_unknown_command(command: str) -> str:
    """Informs the user that the command is not found"""
    return f"Command not found: {command}"


def ask_for_new_user_name() -> str:
    """Asks the user to enter new user's username"""
    return "Please enter the new user's username"


def user_created(username: str) -> str:
    """Informs the user that the new Outline user they requested is created"""
    return f"Successfully created user {username}"


def user_not_created(username: str) -> str:
    """Informs the user that the new Outline user they requested is not created"""
    return f"User {username} already exists"


def user_deleted(username: str) -> str:
    """Informs the user that the Outline user they requested to be deleted is no longer present on the server"""
    return f"User {username} has been deleted from the server"


def instructions() -> str:
    """Gives the user instructions"""
    return f"Not implemented! :("


def get_access_url_ask_for_username() -> str:
    """Ask the user to enter the username they want to get the Access URL for"""
    return "Which of the following users' Access URL do you want to receive?"


def user_not_found(username: str) -> str:
    """Tells the user that the username they requested an Access URL for does not exist"""
    return f"User {username} does not exist"


def ask_for_username_to_delete() -> str:
    """Asks the user for the username they want to delete"""
    return "Which of the following users do you want to remove?"
