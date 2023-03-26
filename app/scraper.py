from collections import defaultdict
import requests
from bs4 import BeautifulSoup
import json
from tqdm import tqdm
from datetime import datetime

url = "https://www.passaportonline.poliziadistato.it/"
province_url = (
    f"{url}CittadinoAction.do?codop=resultRicercaRegistiProvincia&provincia="
)

class Scraper:
    def __init__(self, url=url, date_or_range=None, date=None, date_range=None, time_or_not=None, time_range=None, province_url=province_url):
        self.url = url
        self.province_url = province_url
        self.commissariats = {}
        self.date_or_range = date_or_range
        self.date = date
        self.date_range = date_range
        self.time_or_not = time_or_not
        self.time_range = time_range
        self.appointments = {}
        self.running = False
    
    def scrape_nation(self, provinces=None):
        # If ./data/commissariats.json exists, load the data
        # Otherwise, scrape the data
        try:
            with open('./data/commissariats.json', 'r') as f:
                self.commissariats = json.load(f)
        except FileNotFoundError:
            # Open the ./data/provinces.json file and load the provinces' data
            if provinces is None:
                with open('./data/provinces.json', 'r') as f:
                    provinces = json.load(f)
            # Progress bar with the provinces' names
            bar = tqdm(provinces.keys())
            for province in bar: 
                bar.set_description(f"Scraping {province}")
                self.scrape_province(province)

    def scrape_province(self, province):
        excluded_details = ["disponibilita", "selezionaStruttura"]
        # Send a request to the URL and store the response
        response = requests.get(self.province_url + province)

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the table that contains the commissariats' information
        table = soup.find('table', attrs={'class': 'imposta_utenti'})

        # Extract the rows of the table
        # Catch the exception if the table is empty
        try:
            rows = table.find_all('tr', {'class' : 'data'})
        except AttributeError:
            self.commissariats[province] = {}
            return

        # Loop through each row and extract the relevant information
        data = {}
        for row in rows:
            comm_id = row.get('id')
            cols = row.find_all('td')
            commissariat = {col.get('headers')[0]: col.text.strip() for col in cols if col.get('headers')[0] not in excluded_details}
            data[comm_id] = commissariat

        self.commissariats[province] = data

    def save_commissariats(self):
        # Export the commissariats to a JSON file
        with open('./data/commissariats.json', 'w') as f:
            json.dump(self.commissariats, f, indent=4)

    
    def scrape_appointments(self, province, commissariats):
        response = requests.get(self.province_url + province)
        soup = BeautifulSoup(response.content, 'html.parser')

        appointments = defaultdict(list)
        for commissariat_id in commissariats.keys():
            availability = soup.select_one(f"#{commissariat_id} td[headers='disponibilita']").get_text(strip=True, default="No")
            calendar_path = soup.select_one(f"#{commissariat_id} td[headers='selezionaStruttura'] a")['href']
            if 'si' in availability.lower():
                url = f"https://www.passaportonline.poliziadistato.it/{calendar_path}"
                date = calendar_path.split('&data=')[1]
                datetime_object = datetime.strptime(date, '%d-%m-%Y')
                appointments[commissariat_id].append((url, datetime_object))


if __name__ == '__main__':
    scraper = Scraper(url)
    scraper.scrape_nation()
    scraper.save_commissariats()
