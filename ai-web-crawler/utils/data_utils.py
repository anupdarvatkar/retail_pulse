import csv

from models.review import Review


def is_duplicate_review(review_text: str, seen_names: set) -> bool:
    return review_text in seen_names


def is_complete_review(review: dict, required_keys: list) -> bool:
    return all(key in review for key in required_keys)


def save_reviews_to_csv(reviews: list, filename: str):
    if not reviews:
        print("No reviews to save.")
        return

    # Use field names from the Review model
    fieldnames = Review.model_fields.keys()

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(reviews)
    print(f"Saved {len(reviews)} reviews to '{filename}'.")
