"""
Equipos — Service   (Java: @Service)
"""


class EquipmentService:
    def create(self, model: str, brand: str, capacity_btuh: float):
        raise NotImplementedError

    def get_by_id(self, equipment_id: str):
        raise NotImplementedError
