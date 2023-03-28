from collections import defaultdict
import requests
from bs4 import BeautifulSoup
import json
from tqdm import tqdm
from datetime import datetime
import time
import pandas as pd


URL = "https://www.passaportonline.poliziadistato.it/"
PROVINCE_URL = (
    f"{URL}CittadinoAction.do?codop=resultRicercaRegistiProvincia&provincia="
)

class Scraper:
    def __init__(self, url=URL, province_url=PROVINCE_URL):
        self.url = url
        self.province_url = province_url
        self.commissariats = {}
        self.appointments = defaultdict(list)
        self.commissariats_province_path = './data/commissariats.json'
        self.provinces_path = './data/provinces.json'
        self.commissariats_no_province_path = './data/commissariats_no_province.json'
    
    def scrape_nation(self, provinces=None):
        # If ./data/commissariats.json exists, load the data
        # Otherwise, scrape the data
        try:
            with open(self.commissariats_province_path, 'r') as f:
                self.commissariats = json.load(f)
        except FileNotFoundError:
            # Open the ./data/provinces.json file and load the provinces' data
            if provinces is None:
                with open(self.provinces_path, 'r') as f:
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

        # Create also a json without the provinces
        commissariats = {}
        for province in self.commissariats:
            for comm_id in self.commissariats[province]:
                commissariats[comm_id] = self.commissariats[province][comm_id]
        
        with open(self.commissariats_no_province_path, 'w') as f:
            json.dump(commissariats, f, indent=4)
    
    def scrape_appointments(self, provinces, commissariats, timeout=10):
        self.appointments = defaultdict(list)
        for province in provinces:
            response = requests.get(self.province_url + province)
            soup = BeautifulSoup(response.content, 'html.parser')
            #print(commissariats)
            for commissariat_id in commissariats:
                availability = soup.find('tr', {'id': commissariat_id}).find('td', {'headers': 'disponibilita'}).text
                if 'si' in availability.lower():
                    calendar_path = soup.find('tr', {'id': commissariat_id}).find('td', {'headers': 'selezionaStruttura'}).find('a').get('href')
                    url = f"https://www.passaportonline.poliziadistato.it/{calendar_path}"
                    date = calendar_path.split('&data=')[1]
                    # save the date object without the time
                    datetime_object = datetime.strptime(date, '%d-%m-%Y').date()
                    self.appointments[commissariat_id].append({
                        'url': url,
                        'date': datetime_object,
                    })
            time.sleep(timeout)
        return self.appointments
    

if __name__ == '__main__':
    scraper = Scraper(URL)
    scraper.scrape_nation()
    scraper.save_commissariats()
    scraper.scrape_appointments(province='BR', commissariats=scraper.commissariats['BR'])
    print(scraper.appointments)
