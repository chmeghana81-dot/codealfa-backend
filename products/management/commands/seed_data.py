
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction

from products.models import Category, Product


class Command(BaseCommand):
    help = "Seed categories and products from JSON files"

    def handle(self, *args, **options):

        data_dir = Path(settings.BASE_DIR) / "data"

        categories_file = data_dir / "categories.json"
        products_file = data_dir / "products.json"

        # Check JSON files
        if not categories_file.exists():
            raise CommandError(
                f"Categories file not found: {categories_file}"
            )

        if not products_file.exists():
            raise CommandError(
                f"Products file not found: {products_file}"
            )

        # Load JSON data
        try:
            with open(categories_file, "r", encoding="utf-8") as file:
                categories_data = json.load(file)

            with open(products_file, "r", encoding="utf-8") as file:
                products_data = json.load(file)

        except json.JSONDecodeError as error:
            raise CommandError(f"Invalid JSON: {error}")

        category_count = 0
        product_count = 0

        try:
            with transaction.atomic():

                # -------------------------
                # 1. SEED CATEGORIES
                # -------------------------

                for item in categories_data:

                    Category.objects.update_or_create(
                        id=item["id"],
                        defaults={
                            "name": item["name"],
                            "description": item.get("description", ""),
                        }
                    )

                    category_count += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Categories seeded: {category_count}"
                    )
                )

                # -------------------------
                # 2. SEED PRODUCTS
                # -------------------------

                for item in products_data:

                    try:
                        category = Category.objects.get(
                            id=item["category"]
                        )
                    except Category.DoesNotExist:
                        raise CommandError(
                            f"Category ID {item['category']} "
                            f"not found for product {item['name']}"
                        )

                    image_path = item.get("image", "")

                    # Convert /media/products/file.avif
                    # into products/file.avif
                    if image_path.startswith("/media/"):
                        image_path = image_path.replace(
                            "/media/", "", 1
                        )

                    Product.objects.update_or_create(
                        id=item["id"],
                        defaults={
                            "category": category,
                            "name": item["name"],
                            "description": item.get("description", ""),
                            "price": item["price"],
                            "stock": item.get("stock", 0),
                            "available_sizes": item.get(
                                "available_sizes", []
                            ),
                            "available_colors": item.get(
                                "available_colors", []
                            ),
                            "image": image_path or None,
                        }
                    )

                    product_count += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Products seeded: {product_count}"
                    )
                )

        except Exception as error:
            raise CommandError(
                f"Seeding failed. Transaction rolled back: {error}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Successfully seeded all categories and products!"
            )
        )
