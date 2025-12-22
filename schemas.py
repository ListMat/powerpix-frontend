from pydantic import BaseModel, Field, field_validator
from typing import List

class DrawNumbersSchema(BaseModel):
    white: List[int] = Field(..., min_length=5, max_length=5, description="5 números brancos oficiais")
    powerball: List[int] = Field(..., min_length=1, max_length=1, description="1 Powerball oficial")

    @field_validator('white')
    @classmethod
    def validate_white_numbers(cls, v):
        for num in v:
            if not (1 <= num <= 69):
                raise ValueError(f"Número branco {num} inválido. Deve estar entre 1 e 69")
        return v

    @field_validator('powerball')
    @classmethod
    def validate_powerball_number(cls, v):
        for num in v:
            if not (1 <= num <= 26):
                raise ValueError(f"Powerball {num} inválido. Deve estar entre 1 e 26")
        return v
