"""
Clientes — Service   (Java: @Service)
"""


class ClientService:
    def create(self, name: str, email: str):
        raise NotImplementedError

    def get_by_id(self, client_id: str):
        raise NotImplementedError
