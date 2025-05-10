fake_db = {}


def get_user(username: str):
    return fake_db.get(username)


def add_user(username: str, password: str):
    fake_db[username] = {"username": username, "password": password}
