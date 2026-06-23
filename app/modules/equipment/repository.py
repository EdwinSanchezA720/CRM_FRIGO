"""
Equipos — Repository   (Java: @Repository / JPA)
"""


class EquipmentRepository:
    def save(self, equipment):
        raise NotImplementedError

    def find_by_id(self, equipment_id: str):
        raise NotImplementedError
