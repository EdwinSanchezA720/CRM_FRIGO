"""
Reportes — Service   (Java: @Service)
Genera PDFs: memoria de cálculo y cotización.
"""


class ReportService:
    def generate_calculation_pdf(self, project_id: str) -> bytes:
        raise NotImplementedError

    def generate_quote_pdf(self, project_id: str) -> bytes:
        raise NotImplementedError
