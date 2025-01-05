import sys
from recipe_crypt import scrapers
from recipe_crypt import utils


def save_recipe(url):

    if utils.check_url(url) == False:
        print("%s does not exist", url)
        return 2

    if "allrecipes.com" in url:
        scraper = scrapers.AllRecipes(url)
    elif "thepioneerwoman.com" in url:
        scraper = scrapers.PioneerWoman(url)
    elif "food.com" in url:
        scraper = scrapers.FoodCom(url)
    else:
        raise ValueError("Unrecognized site: " + url)

    scraper.write(to_file=True, path="~/tmp")