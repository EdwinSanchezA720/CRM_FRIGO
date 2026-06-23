"""
Reportes — Repository   (Java: @Repository / JPA)
Guarda los reportes generados y sus metadatos.
"""


class ReportRepository:
    def save(self, report):
        raise NotImplementedError

    def find_by_project(self, project_id: str):
        raise NotImplementedError
