from pydantic import BaseModel


class Review(BaseModel):
    """
    Represents the data structure of a Review.
    """

    user: str
    review_date: str
    rating: str
    review_text: str