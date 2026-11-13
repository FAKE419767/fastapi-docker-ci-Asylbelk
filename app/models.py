from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=1000)
    price: float = Field(gt=0, allow_inf_nan=False)
    quantity: int = Field(default=0, ge=0, strict=True)


class Product(ProductCreate):
    id: int
