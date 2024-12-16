import requests
from bs4 import BeautifulSoup

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
    


pageCounter = 0

for pageCounter in range(1):
    # URL of the page you want to scrape
    url = 'https://www.recepti.com/kuvar/glavna-jela/' + str(pageCounter * 16 + 1)

    # Send a GET request to the URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # find all li items from ul tag with class re-list
        ul = soup.find('ul', class_='re-list')
        li_dishes = ul.find_all('li')
        for li_dish in li_dishes:
            dish = Dish()
            title = li_dish.find('a').text
            print(title)
            break
        exit()
    else:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")