from pydantic import BaseModel

class Category(BaseModel):
    id: int
    name: str
    description: str

class Topic(BaseModel):
    id: int
    category_id: int
    title: str
    level: str
