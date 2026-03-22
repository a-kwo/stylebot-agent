from pydantic import BaseModel
from typing import Optional, List


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChatRequest(BaseModel):
    message: str


class ResponseBlock(BaseModel):
    type: str  # "text" | "products"
    content: Optional[str] = None
    items: Optional[List[dict]] = None


class ChatResponse(BaseModel):
    blocks: List[ResponseBlock]


class WardrobeItem(BaseModel):
    id: Optional[int] = None
    name: str
    category: str
    color: Optional[str] = None
    brand: Optional[str] = None
    condition: str = "good"
    tags: List[str] = []
    image_url: Optional[str] = None
    purchase_url: Optional[str] = None


class FeedbackRequest(BaseModel):
    product_title: str
    feedback: str  # "like" or "dislike"
    price: Optional[str] = None
    category: Optional[str] = None
    seller: Optional[str] = None
    color: Optional[str] = None
    search_query: Optional[str] = None
    image_url: Optional[str] = None


class ProfileData(BaseModel):
    style_adjectives: List[str] = []
    preferred_colors: List[str] = []
    avoided_colors: List[str] = []
    preferred_brands: List[str] = []
    avoided_brands: List[str] = []
    size_tops: Optional[str] = None
    size_bottoms: Optional[str] = None
    size_shoes: Optional[str] = None
    budget_min: int = 0
    budget_max: int = 500
    occasions: List[str] = []
    fit_preferences: List[str] = []
    notes: str = ""
