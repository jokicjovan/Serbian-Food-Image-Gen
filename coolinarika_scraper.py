import os
import shutil
import time
import requests
from bs4 import BeautifulSoup
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

max_recipes_count = 10
base_url = "https://www.coolinarika.com"
chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(options=chrome_options)

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

    def make_json(self):
        return {
            "name": self.name,
            "ingredients": self.ingredients,
            "preparation": self.preparation,
            "image_path": self.image_path
        }


def fetch_recipe_data(url):
    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, 'picture img'))
    )

    # parse page with executed javascript
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Extract name
    name = soup.find('h1', class_='headTitle').text.strip()

    # Extract ingredients
    ingredients_content = soup.find('div', class_='ingredientsContent')
    ingredients_group_items = ingredients_content.find_all('div', class_='groupItems')
    ingredients = []
    for group in ingredients_group_items:
        items = group.find_all('div')
        for item in items:
            ingredient_text = item.get_text()
            if ingredient_text != '':
                ingredients.append(ingredient_text)

    # Extract preparation steps
    preparation_section = soup.find('div', class_='sectionContent')
    preparation_group_items = preparation_section.find_all('div', class_='groupItems')
    preparation_steps = []
    for group in preparation_group_items:
        items = group.find_all('div', recursive=False)
        for item in items:
            preparation_step_text = item.get_text()
            if preparation_step_text != '':
                preparation_steps.append(preparation_step_text)

    # Extract image URL
    image_div = soup.find('div', class_='headMain_assetImage')
    picture_tag = image_div.find('picture')
    img_tag = picture_tag.find('img')
    image_url = img_tag.get('src')

    # Download the image
    image_name = name.replace(" ", "_").lower() + ".jpg"
    image_path = os.path.join('data_coolinarika/images/', image_name)
    download_and_save_image(image_url, image_path)

    # Create a Dish object with the scraped data
    dish = Dish(name=name, ingredients=ingredients, preparation=preparation_steps, image_path=image_path)
    return dish


def download_and_save_image(url, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    response = requests.get(url)
    with open(path, 'wb') as f:
        f.write(response.content)


def scrape_listing_page(listing_url):
    # Go to the listing page
    driver.get(listing_url)

    # Scroll down until we reach the bottom of the page
    last_height = driver.execute_script("return document.body.scrollHeight")

    # Track the initial number of 'cardInner' elements
    initial_card_count = len(driver.find_elements(By.CSS_SELECTOR, 'a.cardInner'))
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait for the page to load new content
        time.sleep(1)

        # Track the new number of 'cardInner' elements
        new_card_count = len(driver.find_elements(By.CSS_SELECTOR, 'a.cardInner'))

        # If no new elements are added, we assume we've reached the bottom
        if new_card_count == initial_card_count or new_card_count >= max_recipes_count:
            break

        # Update the count for the next iteration
        initial_card_count = new_card_count

        # Get new height to check if we've reached the bottom
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:  # Stop if we have reached the bottom
            break
        last_height = new_height

    # Now that we've scrolled, get the page source
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Extract the recipe links
    recipe_links = soup.find_all('a', {'class': 'cardInner'})
    recipe_urls = [link['href'] for link in recipe_links]
    full_urls = [base_url + url for url in recipe_urls]
    return full_urls


def save_to_json(dishes, filename='data_coolinarika/data.json'):
    dishes_data = [dish.make_json() for dish in dishes]
    with open(filename, 'w', encoding="utf-8") as json_file:
        json.dump(dishes_data, json_file, ensure_ascii=False, indent=4)

def clear_data_and_images():
    # Clear data.json if it exists
    data_json_path = 'data_coolinarika/data.json'
    if os.path.exists(data_json_path):
        os.remove(data_json_path)
        print(f"Deleted {data_json_path}")

    # Clear the entire images folder if it exists
    images_folder_path = 'data_coolinarika/images'
    if os.path.exists(images_folder_path) and os.path.isdir(images_folder_path):
        shutil.rmtree(images_folder_path)
        print(f"Deleted {images_folder_path}")

def main():
    # Step 0 (optional): Clear old data
    clear_data_and_images()

    # Step 1: Scrape the listing page to get individual recipe URLs
    listing_url = base_url + '/recepti/by-coolinarika'
    recipe_urls = scrape_listing_page(listing_url)

    # Step 2: For each recipe URL, fetch the full recipe data
    dishes = []
    for url in recipe_urls:
        print(f"Scraping {url}...")
        dish = fetch_recipe_data(url)
        if dish:
            dishes.append(dish)
            if len(dishes) > max_recipes_count:
                break

    # Step 3: Save the scraped data to a JSON file
    save_to_json(dishes)


if __name__ == '__main__':
    main()
