from outline_vpn.outline_vpn import OutlineVPN


class OutlineAPI:
    def __init__(self, host: str, port: int, key: str) -> None:
        self.client = OutlineVPN(api_url=f"https://{host}:{port}/{key}")

    def _get_access_urls(self) -> list:
        return [i.access_url for i in self.client.get_keys()]

    def _get_key_ids(self) -> list:
        return [i.key_id for i in self.client.get_keys()]

    def _get_access_port(self) -> int:
        """Sets Outline access port for new users"""
        return self.client.get_server_information().portForNewAccessKeys()

    def _set_access_port(self, port: int) -> bool:
        """Sets Outline access port for new users and returns True on success
        On error code 409 (port used by other service) raises Exception; else returns False"""
        if type(port) is not int:
            raise Exception("`port' is not an integer")
        if not 0 < port < 65536:
            raise Exception("The requested port wasn't an integer from 1 through 65535")
        return self.client.set_port_new_for_access_keys(port)

    def _get_key_id(self, username: str) -> int:
        if username == 'admin':
            return 0
        clients = self.client.get_keys()
        return next((i.key_id for i in clients if i.name == username), None)

    def get_key_names(self) -> list:
        return [i.name for i in self.client.get_keys()]

    def create_user(self, username: str) -> bool:
        """Creates a new Outline user and sets their username"""
        if username not in self.get_key_names() and username != 'admin':
            key_id = self.client.create_key().key_id
            self.client.rename_key(key_id, username)
            return True
        return False

    def delete_user(self, username: str) -> None:
        """Deletes user from the Outline server"""
        self.client.delete_key(self._get_key_id(username))

    def get_access_url(self, username: str) -> str:
        """Returns user's Outline access url; if user is not found, returns None"""
        key_id = self._get_key_id(username)
        clients = self.client.get_keys()
        return next((i.access_url for i in clients if i.key_id == key_id), None)

    def revoke(self, username: str) -> bool:
        """Changes Outline user's data limit to 0b"""
        try:
            self.client.add_data_limit(self._get_key_id(username), 0)
            return True
        except Exception:
            return False

    def unrevoke(self, username: str) -> None:
        """Removes Outline username's data limit"""
        self.client.delete_data_limit(self._get_key_id(username))

    def is_revoked(self, username: str) -> bool:
        """[NOT IMPLEMENTED] Returns True is username is revoked, else False"""
        pass

    def get_usage(self, username: str) -> int:
        """Returns Gigabytes transferred by username in 30 days"""
        try:
            self.client.get_transferred_data()["bytesTransferredByUserId"][self._get_key_id(username)] // 1073741824
        except KeyError:
            if username in self.get_key_names():
                return 0
            else:
                raise KeyError

    def get_server_usage(self) -> int:
        """[NOT IMPLEMENTED] Returns Gigabytes transferred by all users in 30 days"""
        pass  # return self.server.get
