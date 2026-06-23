"""
Proyectos — Service   (Java: @Service)
Lógica de negocio: crear, consultar, gestionar entregables.
"""


class ProjectService:
    def create(self, name: str, client_id: str):
        raise NotImplementedError

    def get_by_id(self, project_id: str):
        raise NotImplementedError
