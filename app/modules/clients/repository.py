"""
Clientes — Repository   (Java: @Repository / JPA)
"""


class ClientRepository:
    def save(self, client):
        raise NotImplementedError

    def find_by_id(self, client_id: str):
        raise NotImplementedError
