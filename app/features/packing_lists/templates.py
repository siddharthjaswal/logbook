"""
Default packing list templates.

Provides common packing list templates for different trip types.
"""

from app.shared.enums import PackingCategory, Priority


# General travel essentials
ESSENTIALS_TEMPLATE = [
    {"name": "Passport", "category": PackingCategory.DOCUMENTS, "quantity": 1, "priority": Priority.CRITICAL},
    {"name": "Driver's License/ID", "category": PackingCategory.DOCUMENTS, "quantity": 1, "priority": Priority.CRITICAL},
    {"name": "Travel Insurance Documents", "category": PackingCategory.DOCUMENTS, "quantity": 1, "priority": Priority.HIGH},
    {"name": "Credit/Debit Cards", "category": PackingCategory.DOCUMENTS, "quantity": 2, "priority": Priority.CRITICAL},
    {"name": "Cash", "category": PackingCategory.DOCUMENTS, "quantity": 1, "priority": Priority.HIGH},
    {"name": "Phone Charger", "category": PackingCategory.ELECTRONICS, "quantity": 1, "priority": Priority.CRITICAL},
    {"name": "Medications", "category": PackingCategory.MEDICATIONS, "quantity": 1, "priority": Priority.CRITICAL},
    {"name": "Toothbrush", "category": PackingCategory.TOILETRIES, "quantity": 1, "priority": Priority.HIGH},
    {"name": "Toothpaste", "category": PackingCategory.TOILETRIES, "quantity": 1, "priority": Priority.HIGH},
]

# Clothing basics
CLOTHING_TEMPLATE = [
    {"name": "Underwear", "category": PackingCategory.CLOTHING, "quantity": 7, "priority": Priority.HIGH},
    {"name": "Socks", "category": PackingCategory.CLOTHING, "quantity": 7, "priority": Priority.HIGH},
    {"name": "T-Shirts", "category": PackingCategory.CLOTHING, "quantity": 5, "priority": Priority.MEDIUM},
    {"name": "Pants/Jeans", "category": PackingCategory.CLOTHING, "quantity": 3, "priority": Priority.MEDIUM},
    {"name": "Jacket", "category": PackingCategory.CLOTHING, "quantity": 1, "priority": Priority.MEDIUM},
    {"name": "Comfortable Walking Shoes", "category": PackingCategory.CLOTHING, "quantity": 1, "priority": Priority.HIGH},
    {"name": "Sleepwear", "category": PackingCategory.CLOTHING, "quantity": 2, "priority": Priority.MEDIUM},
]

# Toiletries
TOILETRIES_TEMPLATE = [
    {"name": "Shampoo", "category": PackingCategory.TOILETRIES, "quantity": 1, "priority": Priority.MEDIUM},
    {"name": "Conditioner", "category": PackingCategory.TOILETRIES, "quantity": 1, "priority": Priority.LOW},
    {"name": "Body Wash/Soap", "category": PackingCategory.TOILETRIES, "quantity": 1, "priority": Priority.MEDIUM},
    {"name": "Deodorant", "category": PackingCategory.TOILETRIES, "quantity": 1, "priority": Priority.HIGH},
    {"name": "Razor", "category": PackingCategory.TOILETRIES, "quantity": 1, "priority": Priority.LOW},
    {"name": "Sunscreen", "category": PackingCategory.TOILETRIES, "quantity": 1, "priority": Priority.MEDIUM},
    {"name": "Moisturizer", "category": PackingCategory.TOILETRIES, "quantity": 1, "priority": Priority.LOW},
]

# Electronics
ELECTRONICS_TEMPLATE = [
    {"name": "Smartphone", "category": PackingCategory.ELECTRONICS, "quantity": 1, "priority": Priority.CRITICAL},
    {"name": "Laptop/Tablet", "category": PackingCategory.ELECTRONICS, "quantity": 1, "priority": Priority.MEDIUM},
    {"name": "Camera", "category": PackingCategory.ELECTRONICS, "quantity": 1, "priority": Priority.LOW},
    {"name": "Power Bank", "category": PackingCategory.ELECTRONICS, "quantity": 1, "priority": Priority.MEDIUM},
    {"name": "Headphones", "category": PackingCategory.ELECTRONICS, "quantity": 1, "priority": Priority.LOW},
    {"name": "Universal Adapter", "category": PackingCategory.ELECTRONICS, "quantity": 1, "priority": Priority.HIGH},
]

# Beach vacation additions
BEACH_TEMPLATE = [
    {"name": "Swimsuit", "category": PackingCategory.CLOTHING, "quantity": 2, "priority": Priority.CRITICAL},
    {"name": "Beach Towel", "category": PackingCategory.ACCESSORIES, "quantity": 1, "priority": Priority.HIGH},
    {"name": "Sunglasses", "category": PackingCategory.ACCESSORIES, "quantity": 1, "priority": Priority.MEDIUM},
    {"name": "Hat/Cap", "category": PackingCategory.ACCESSORIES, "quantity": 1, "priority": Priority.MEDIUM},
    {"name": "Flip-Flops/Sandals", "category": PackingCategory.CLOTHING, "quantity": 1, "priority": Priority.HIGH},
    {"name": "Waterproof Phone Case", "category": PackingCategory.ACCESSORIES, "quantity": 1, "priority": Priority.LOW},
]

# Business trip additions
BUSINESS_TEMPLATE = [
    {"name": "Business Cards", "category": PackingCategory.DOCUMENTS, "quantity": 1, "priority": Priority.HIGH},
    {"name": "Formal Shirt", "category": PackingCategory.CLOTHING, "quantity": 3, "priority": Priority.CRITICAL},
    {"name": "Dress Pants", "category": PackingCategory.CLOTHING, "quantity": 2, "priority": Priority.CRITICAL},
    {"name": "Blazer/Suit Jacket", "category": PackingCategory.CLOTHING, "quantity": 1, "priority": Priority.HIGH},
    {"name": "Dress Shoes", "category": PackingCategory.CLOTHING, "quantity": 1, "priority": Priority.HIGH},
    {"name": "Belt", "category": PackingCategory.ACCESSORIES, "quantity": 1, "priority": Priority.MEDIUM},
    {"name": "Tie", "category": PackingCategory.ACCESSORIES, "quantity": 2, "priority": Priority.MEDIUM},
]

# Winter/Ski trip additions
WINTER_TEMPLATE = [
    {"name": "Winter Coat", "category": PackingCategory.CLOTHING, "quantity": 1, "priority": Priority.CRITICAL},
    {"name": "Thermal Underwear", "category": PackingCategory.CLOTHING, "quantity": 2, "priority": Priority.HIGH},
    {"name": "Gloves", "category": PackingCategory.ACCESSORIES, "quantity": 1, "priority": Priority.HIGH},
    {"name": "Scarf", "category": PackingCategory.ACCESSORIES, "quantity": 1, "priority": Priority.MEDIUM},
    {"name": "Winter Hat/Beanie", "category": PackingCategory.ACCESSORIES, "quantity": 1, "priority": Priority.HIGH},
    {"name": "Warm Socks", "category": PackingCategory.CLOTHING, "quantity": 5, "priority": Priority.HIGH},
    {"name": "Lip Balm", "category": PackingCategory.TOILETRIES, "quantity": 1, "priority": Priority.MEDIUM},
]

# Camping/Hiking additions
CAMPING_TEMPLATE = [
    {"name": "Tent", "category": PackingCategory.CAMPING_GEAR, "quantity": 1, "priority": Priority.CRITICAL},
    {"name": "Sleeping Bag", "category": PackingCategory.CAMPING_GEAR, "quantity": 1, "priority": Priority.CRITICAL},
    {"name": "Sleeping Pad", "category": PackingCategory.CAMPING_GEAR, "quantity": 1, "priority": Priority.HIGH},
    {"name": "Hiking Boots", "category": PackingCategory.SPORTS_GEAR, "quantity": 1, "priority": Priority.CRITICAL},
    {"name": "Backpack", "category": PackingCategory.CAMPING_GEAR, "quantity": 1, "priority": Priority.CRITICAL},
    {"name": "Water Bottle", "category": PackingCategory.CAMPING_GEAR, "quantity": 2, "priority": Priority.HIGH},
    {"name": "First Aid Kit", "category": PackingCategory.MEDICATIONS, "quantity": 1, "priority": Priority.HIGH},
    {"name": "Flashlight/Headlamp", "category": PackingCategory.CAMPING_GEAR, "quantity": 1, "priority": Priority.HIGH},
    {"name": "Map/Compass", "category": PackingCategory.CAMPING_GEAR, "quantity": 1, "priority": Priority.MEDIUM},
]


# Template registry
TEMPLATES = {
    "essentials": ESSENTIALS_TEMPLATE,
    "clothing": CLOTHING_TEMPLATE,
    "toiletries": TOILETRIES_TEMPLATE,
    "electronics": ELECTRONICS_TEMPLATE,
    "beach": BEACH_TEMPLATE,
    "business": BUSINESS_TEMPLATE,
    "winter": WINTER_TEMPLATE,
    "camping": CAMPING_TEMPLATE,
}


def get_template(template_name: str) -> list:
    """Get a packing template by name."""
    return TEMPLATES.get(template_name, [])


def get_combined_template(template_names: list[str]) -> list:
    """Combine multiple templates into one list."""
    combined = []
    for name in template_names:
        template = get_template(name)
        combined.extend(template)
    return combined


def list_available_templates() -> list[str]:
    """List all available template names."""
    return list(TEMPLATES.keys())
