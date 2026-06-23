"""
Garantías — Repository   (Java: @Repository / JPA)
"""


class WarrantyRepository:
    def save(self, warranty):
        raise NotImplementedError

    def find_by_equipment(self, equipment_id: str):
        raise NotImplementedError
