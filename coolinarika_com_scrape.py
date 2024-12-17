import os
import requests
from bs4 import BeautifulSoup
import json

class Dish:
    def __init__(self, name=None, ingredients=None, preparation=None, image_path=None):
        self.name = name
        self.ingredients = ingredients
        self.preparation = preparation
        self.image_path = image_path

    def __str__(self):
        return f"{self.name}\n{self.ingredients}\n{self.preparation}\n{self.image_path}"

    def __repr__(self):
        return f"{self.name}\n{self.ingredients}\n{self.preparation}\n{self.image_path}"

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name):
        self.__name = name

    @property
    def ingredients(self):
        return self.__ingredients

    @ingredients.setter
    def ingredients(self, ingredients):
        self.__ingredients = ingredients

    @property
    def preparation(self):
        return self.__preparation

    @preparation.setter
    def preparation(self, preparation):
        self.__preparation = preparation

    @property
    def image_path(self):
        return self.__image_path

    @image_path.setter
    def image_path(self, image_path):
        self.__image_path = image_path


def fetch_recipe_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract name
    name = soup.find('h1', class_='headTitle').text.strip()

    # Extract image URL
    # image_url = soup.find('div', class_='headMain_assetInner').find('img')['src']

    # Extract ingredients
    ingredients_content = soup.find('div', class_='ingredientsContent')
    ingredients_group_items = ingredients_content.find_all('div', class_='groupItems')
    ingredients = []
    for group in ingredients_group_items:
        items = group.find_all('div')
        for item in items:
            ingredient_text = item.get_text(strip=True)
            ingredients.append(ingredient_text)

    # Extract preparation steps
    preparation_section = soup.find('div', class_='sectionContent')
    preparation_group_items = preparation_section.find_all('div', class_='groupItems')
    preparation_steps = []
    for group in preparation_group_items:
        items = group.find_all('div')
        for item in items:
            step = item.find('div', class_='stepContent_description')
            if step:
                preparation_step_text = step.get_text(strip=True)
                preparation_steps.append(preparation_step_text)

    print(preparation_steps)
    return

    # Download the image
    image_name = image_url.split('/')[-1]
    image_path = os.path.join('data-coolinarika-com/images', image_name)
    download_image(image_url, image_path)

    # Create a Dish object with the scraped data
    dish = Dish(name=name, ingredients=ingredients, preparation=preparation_steps, image_path=image_path)

    return dish


def download_image(url, path):
    # Create image directory if it doesn't exist
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Download image
    response = requests.get(url)
    with open(path, 'wb') as f:
        f.write(response.content)


def scrape_listing_page(listing_url):
    response = requests.get(listing_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all anchor tags with class 'cardInner' to extract the recipe URLs
    recipe_links = soup.find_all('a', {'class': 'cardInner'})
    recipe_urls = [link['href'] for link in recipe_links]

    # Full URLs for individual recipes
    full_urls = ['https://www.coolinarika.com' + url for url in recipe_urls]

    return full_urls


def save_to_json(dishes, filename='data-coolinarika-com/data.json'):
    # Convert dishes to dictionary list
    dishes_data = [{
        'name': dish.name,
        'ingredients': dish.ingredients,
        'preparation': dish.preparation,
        'image_path': dish.image_path
    } for dish in dishes]

    with open(filename, 'w') as json_file:
        json.dump(dishes_data, json_file, indent=4)


def main():
    listing_url = 'https://www.coolinarika.com/recepti/by-coolinarika'

    # Step 1: Scrape the listing page to get individual recipe URLs
    recipe_urls = scrape_listing_page(listing_url)

    # Step 2: For each recipe URL, fetch the full recipe data
    dishes = []
    for url in recipe_urls:
        print(f"Scraping {url}...")
        dish = fetch_recipe_data(url)
        dishes.append(dish)

    # Step 3: Save the scraped data to a JSON file
    save_to_json(dishes)


if __name__ == '__main__':
    main()
