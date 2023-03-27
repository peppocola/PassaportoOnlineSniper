from scraper import Scraper, URL
from gui import ScraperGUI

if __name__ == "__main__":
    scraper = Scraper(URL)
    scraper.scrape_nation()
    scraper.save_commissariats()
    # create the GUI
    gui = ScraperGUI(scraper)
    # display the GUI
    gui.display_interface()