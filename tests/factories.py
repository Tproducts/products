"""
Product Factory to make fake objects for testing
"""
import factory
from factory.fuzzy import FuzzyChoice
from service.models import Product


class ProductFactory(factory.Factory):
    """Creates fake products that you don't have to feed"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps factory to data model"""

        model = Product

    name = factory.Faker("word")
    category = FuzzyChoice(choices=["Phone", "Laptop", "Earphone", "Keyboard", "Mouse"])
    available = FuzzyChoice(choices=[True, False])
    price = FuzzyChoice(choices=[50, 100, 200, 1000])
    description = factory.Faker("sentence")
