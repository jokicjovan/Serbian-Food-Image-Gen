import argparse
import os
import shutil
import uuid
import requests
import json
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

chrome_options = Options()
chrome_options.add_argument("--headless")


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
    # Init new driver
    driver = webdriver.Chrome(options=chrome_options)
    try:
        # Go to the url and wait for image to load
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
        ingredients = [
            item.get_text().strip()
            for group in ingredients_group_items
            for item in group.find_all('div') if item.get_text().strip()
        ]

        # Extract preparation steps
        preparation_section = soup.find('div', class_='sectionContent')
        preparation_group_items = preparation_section.find_all('div', class_='groupItems')
        preparation_steps = [
            item.get_text().strip()
            for group in preparation_group_items
            for item in group.find_all('div', recursive=False) if item.get_text().strip()
        ]

        # Extract image URL
        image_div = soup.find('div', class_='headMain_assetImage')
        picture_tag = image_div.find('picture')
        img_tag = picture_tag.find('img')
        image_url = img_tag.get('src')

        # Download the image
        image_name = str(uuid.uuid4()) + ".jpg"
        image_path = os.path.join('data_coolinarika/images/', image_name)
        download_and_save_image(image_url, image_path)

        # Create a Dish object with the scraped data
        return Dish(name=name, ingredients=ingredients, preparation=preparation_steps, image_path=image_path)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None
    finally:
        driver.quit()


def download_and_save_image(url, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    response = requests.get(url)
    with open(path, 'wb') as f:
        f.write(response.content)

def scrape_recipes_parallel(recipe_urls, recipes_cutoff, max_workers=5):
    dishes = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(fetch_recipe_data, url): url for url in recipe_urls}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                dish = future.result()
                if dish:
                    dishes.append(dish)
                    if len(dishes) >= recipes_cutoff:
                        break
            except Exception as e:
                print(f"Error processing {url}: {e}")
    return dishes



def scrape_listing_page(base_url, listing_url, recipes_cutoff):
    # Init new driver
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Go to the listing page
        driver.get(listing_url)

        # Scroll down until we reach the bottom of the page
        last_height = driver.execute_script("return document.body.scrollHeight")

        # Track the initial number of recipe cards
        initial_card_count = len(driver.find_elements(By.CSS_SELECTOR, 'a.cardInner'))

        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait for new recipe cards to load
            try:
                WebDriverWait(driver, 10).until(
                    lambda d: len(d.find_elements(By.CSS_SELECTOR, 'a.cardInner')) > initial_card_count
                )
            except TimeoutException:
                # Bottom is reached
                break

            # Track the new number of recipe cards
            new_card_count = len(driver.find_elements(By.CSS_SELECTOR, 'a.cardInner'))

            # If enough recipes are loaded, stop
            if new_card_count >= recipes_cutoff:
                break

            # Update the count for the next iteration
            initial_card_count = new_card_count

            # Get new height to check if we've reached the bottom
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:  # Stop if we have reached the bottom
                break
            last_height = new_height

        # Get the page source
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Extract the recipe links
        recipe_links = soup.find_all('a', {'class': 'cardInner'})
        recipe_urls = [link['href'] for link in recipe_links]
        full_urls = [base_url + url for url in recipe_urls]
        return full_urls
    finally:
        driver.quit()


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


def main(base_url, recipes_cutoff):
    # Step 0 (optional): Clear old data
    clear_data_and_images()

    # Step 1: Scrape the listing page to get individual recipe URLs
    listing_url = base_url + '/recepti/by-coolinarika'
    recipe_urls = scrape_listing_page(base_url, listing_url, recipes_cutoff)

    # Step 2: For each recipe URL, fetch the full recipe data
    dishes = scrape_recipes_parallel(recipe_urls[:recipes_cutoff], recipes_cutoff)

    # Step 3: Save the scraped data to a JSON file
    save_to_json(dishes)


if __name__ == "__main__":
    # Initialize the argument parser
    parser = argparse.ArgumentParser(description="Scrape recipes from a list of URLs.")

    # Define optional arguments
    parser.add_argument(
        "--base-url",
        type=str,
        nargs="*",
        default="https://www.coolinarika.com",
        help="Base url for scraping recipes.",
    )
    parser.add_argument(
        "--recipes-cutoff",
        type=int,
        default=10000,
        help="Maximum number of recipes to scrape.",
    )

    # Parse arguments
    args = parser.parse_args()

    # Pass parsed arguments to the main function
    main(args.base_url, args.recipes_cutoff)