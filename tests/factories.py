"""
Product Factory class for making fake objects
"""
import factory
from factory.fuzzy import FuzzyChoice
from service.models import Product


class ProductFactory(factory.Factory):
    """Creates fake products for test cases"""

    class Meta:
        model = Product

    id = factory.Sequence(lambda n: str(n))
    name = FuzzyChoice(choices=["iPhone13", "iPad", "Macbook Air", "Macbook Pro"])
    category = FuzzyChoice(choices=["Phone", "Laptop", "Earphone", "Keyboard", "Mouse"])
    description = factory.Faker("word")
    price = FuzzyChoice(choices=["50", "100", "200", "1000"])
    stock = FuzzyChoice(choices=["0", "1", "2", "3"])
