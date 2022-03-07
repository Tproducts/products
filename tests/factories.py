"""
Product Factory class for making fake objects
"""
import factory
from factory.fuzzy import FuzzyChoice
from service.models import Product


class ProductFactory(factory.Factory):
    """Creates fake products that you don't have to feed"""

    class Meta:
        model = Product

    id = factory.Sequence(lambda n: n)
    name = FuzzyChoice(choices=["iPhone13", "iPad", "Macbook Air", "Macbook Pro"])
    description = factory.Faker("word")
    price = FuzzyChoice(choices=[100, 200, 300, 400])
