import threading
import streamlit as st
import json
from datetime import datetime, timedelta
import time
import pandas as pd


class ScraperThread(threading.Thread):
    def __init__(self, target, args):
        super().__init__()
        self.target = target
        self.args = args
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        while not self._stop_event.is_set():
            self.target(*self.args)


# streamlit interface for an appointment scraper
class ScraperGUI():
    def __init__(self, scraper, commissariats_path="./data/commissariats.json") -> None:
        self.load_commissariats(commissariats_path)
        self.scraper = scraper
        self.thread = None
        self.appointments = []

    def load_commissariats(self, path):
        with open(path, 'r') as f:
            commissariats = json.load(f)
        self.commissariats = commissariats
        # take the description of the provinces
        self.provinces = list(commissariats.keys())
    
    def display_interface(self):
        st.title('Appointment Scraper')
        # the user can choose multiple provinces
        self.selected_provinces = st.sidebar.multiselect("Provinces", list(self.provinces))
        # the user can choose multiple commissariats
        # the multiselect should show the commissariat name but the scraper should use the commissariat id
        self.pd_commissariats = self.get_commissariats(self.selected_provinces)
        self.selected_commissariats = st.sidebar.multiselect("Commissariats", self.pd_commissariats)
        # transform the commissariat names into commissariat ids from the pandas dataframe 
        self.selected_commissariats = self.pd_commissariats[self.pd_commissariats["description"].isin(self.selected_commissariats)]["id"].to_list()

        # the user can choose a date or a range of dates, not both
        # the user should select if he wants to choose a date or a range of dates
        self.date_or_range = st.sidebar.radio("Date or range", ["Date", "Range"])
        # display text to explain the user that if he pick date, the appointments will be searched to be more recent than the date he picked
        # the date or the range of dates is shown depending on the user's choice
        if self.date_or_range == "Date":
            st.sidebar.write("The appointments will be searched to be more recent than the date you picked")
            self.date = st.sidebar.date_input("Date", datetime.now())
            self.date_range = None
        elif self.date_or_range == "Range":
            st.sidebar.write("The appointments will be searched to be in the range of dates you picked")
            self.date = None
            self.start_date = st.sidebar.date_input("Start date", datetime.now())
            self.end_date = st.sidebar.date_input("End date", datetime.now())
            # check if the end date is after the start date
            if self.end_date < self.start_date:
                st.sidebar.error("End date must be after start date")
            else:
                self.date_range = (self.start_date, self.end_date)

        # define the buttons if not already defined
        if not hasattr(st.session_state, "Start"):
            self.start_button = st.sidebar.button("Start")
        if not hasattr(st.session_state, "Stop"):
            self.stop_button = st.sidebar.button("Stop")

        # if the user clicks on the start button, the scraper is called
        if self.start_button:
            st.write('Scraper started...')
            self.run_scraper()
        
        # if the user clicks on the stop button, the scraper is stopped
        if self.stop_button:
            st.write('Scraper stopped...')
            self.stop_scraper()
        
        # the appointments are displayed
        self.display_appointments()
        
    def display_appointments(self):
        self.appointments = self.scraper.appointments.copy()
        # filter the appointments by date
        self.filter_appointments()

        # create an empty placeholder to display the appointments
        appointments_placeholder = st.empty()

        # loop indefinitely to update the appointments display
        while True:
            # clear the appointments placeholder
            appointments_placeholder.empty()
            # display the latest appointments
            for appointment in self.appointments:
                appointments_placeholder.write(self.appointments[appointment])
            # sleep for a short time to avoid using too many resources
            time.sleep(1)

    def get_commissariats(self, provinces):        
        commissariats = []
        for province in provinces:
            for commissariat in self.commissariats[province]:
                commissariats.append({"description": self.commissariats[province][commissariat]['descrizione'], "id": commissariat})
        return pd.DataFrame(commissariats, columns=["description", "id"])
    
    def filter_appointments(self):
        # filter the appointments dictionary by date
        if self.date_or_range == "Date":
            self.appointments = [appointment for appointment in self.appointments if appointment['date'] >= self.date]
        elif self.date_or_range == "Range":
            self.appointments = [appointment for appointment in self.appointments if self.start_date <= appointment['date'] <= self.end_date]

    def scraper_loop(self, province, commissariats, timeout=10):
        while True:
            self.scraper.scrape_appointments(province, commissariats, timeout=timeout)
            time.sleep(timeout)

    def run_scraper(self):
        self.thread = ScraperThread(target=self.scraper_loop, args=(self.selected_provinces, self.selected_commissariats))
        self.thread.start()
    
    def stop_scraper(self):
        if self.thread is not None:
            self.thread.stop()

