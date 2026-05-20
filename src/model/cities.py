from enum import Enum
from pydantic import BaseModel, Field

class CambodianCity(str, Enum):
    PHNOM_PENH = "Phnom Penh"
    SIEM_REAP = "Siem Reap"
    BATTAMBANG = "Battambang"
    SIHANOUKVILLE = "Sihanoukville"
    POIPET = "Poipet"
    KAMPONG_CHAM = "Kampong Cham"
    PURSAT = "Pursat"
    TA_KHMAU = "Ta Khmau"
    KAMPONG_SPEU = "Kampong Speu"
    TAKEO = "Takeo"
    KAMPOT = "Kampot"
    KAMPONG_CHHNANG = "Kampong Chhnang"
    KOH_KONG = "Koh Kong"
    PREY_VENG = "Prey Veng"
    KAMPONG_THOM = "Kampong Thom"
    RATANAKIRI = "Ratanakiri"
    MONDULKIRI = "Mondulkiri"
    KEP = "Kep"
    STUNG_TRENG = "Stung Treng"
    KRATIE = "Kratie"
    ODDAR_MEANCHEY = "Oddar Meanchey"
    PAILIN = "Pailin"
    BANTEAY_MEANCHEY = "Banteay Meanchey"
    SVAY_RIENG = "Svay Rieng"
    TBOUNG_KHMUM = "Tboung Khmum"

class LocationSelection(BaseModel):
    # ប្រើសម្រាប់ POST (បង្កើតថ្មី)
    city: CambodianCity = Field(..., description="Select a city in Cambodia")

class LocationUpdate(BaseModel):
    # ប្រើសម្រាប់ PUT (កែប្រែ)
    city: CambodianCity = Field(..., description="Update to a new city in Cambodia")



class CityCreate(BaseModel):
    city_name: str = Field(..., min_length=2, max_length=100)


class CityUpdate(BaseModel):
    city_name: str = Field(..., min_length=2, max_length=100)