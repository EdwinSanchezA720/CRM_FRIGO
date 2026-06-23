"""
Proyectos — Repository   (Java: @Repository / JPA)
Acceso a la base de datos: CRUD de proyectos.
"""


class ProjectRepository:
    def save(self, project):
        raise NotImplementedError

    def find_by_id(self, project_id: str):
        raise NotImplementedError

    def find_all_by_tenant(self, tenant_id: str):
        raise NotImplementedError
