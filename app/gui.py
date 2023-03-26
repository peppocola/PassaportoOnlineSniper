import threading
import streamlit as st
import json
from datetime import datetime, timedelta
import time


# streamlit interface for an appointment scraper
class ScraperGUI():
    def __init__(self, scraper, commissariats_path="./data/commissariats.json", months=4) -> None:
        self.load_commissariats(commissariats_path)
        self.scraper = scraper
        self.months = months
        self.appointments = []
        self.thread = None

    def load_commissariats(self, path):
        with open(path, 'r') as f:
            commissariats = json.load(f)
        self.commissariats = commissariats
        self.provinces = list(commissariats.keys())
    
    def display_interface(self):
        st.title('Appointment Scraper')
        # the user can choose multiple provinces
        self.selected_provinces = st.sidebar.multiselect("Provinces", list(self.provinces))
        # the user can choose multiple commissariats
        self.selected_commissariats = st.sidebar.multiselect("Commissariats", self.get_commissariats(self.selected_provinces))

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
        # the user can choose a time range
        # checkbox to select if the user wants to use a time range or not
        self.time_or_not = st.sidebar.checkbox("Time range", False)
        # the time range is shown depending on the user's choice
        if self.time_or_not:
            # the user can choose a start time and an end time
            self.start_time = st.sidebar.slider("Start time", 0, 24, 0)
            self.end_time = st.sidebar.slider("End time", 0, 24, 0)
            # check if the end time is after the start time
            if self.end_time < self.start_time:
                st.sidebar.error("End time must be after start time")
            else:
                self.time_range = (self.start_time, self.end_time)
        else:
            self.time_range = None

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
        # create an empty placeholder to display the appointments
        appointments_placeholder = st.empty()

        # loop indefinitely to update the appointments display
        while True:
            # get the latest appointments
            latest_appointments = self.appointments.copy()
            # clear the appointments placeholder
            appointments_placeholder.empty()
            # display the latest appointments
            for appointment in latest_appointments:
                appointments_placeholder.write(appointment)
            # sleep for a short time to avoid using too many resources
            time.sleep(1)

    def get_commissariats(self, provinces):
        commissariats = []
        for province in provinces:
            for commissariat in self.commissariats[province]:
                commissariats.extend(commissariat['description'])
        return commissariats

    # ADJUST
    def run_scraper(self):
        self.thread = threading.Thread(target=self.scraping_fn, args=(self.selected_provinces, self.selected_commissariats, self.date, self.date_range, self.time_range, self.appointments))
        self.thread.start()
    
    def stop_scraper(self):
        if self.thread is not None:
            self.thread.stop()
