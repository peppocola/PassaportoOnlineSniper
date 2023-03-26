from scraper import Scraper
from gui import ScraperGUI

# create a scraper
scraper = Scraper()
# run the scraper to get commissariats
scraper.scrape_nation()
# create a GUI
gui = ScraperGUI(scraper)
# run the GUI
gui.display_interface()