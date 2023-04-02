import threading
from utils import convert_appointments_to_dataframe, filter_appointments, get_commissariats
import streamlit as st
import json
from datetime import datetime
import time


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
    def __init__(self, scraper) -> None:
        self.scraper = scraper
        self.thread = None
        self.appointments = []
        self.load_commissariats()


    def load_commissariats(self):
        with open(self.scraper.commissariats_province_path, 'r') as f:
            commissariats = json.load(f)
        self.commissariats = commissariats
        # take the description of the provinces
        self.provinces = list(commissariats.keys())
        # open the commissariats without province
        with open(self.scraper.commissariats_no_province_path, 'r') as f:
            commissariats = json.load(f)
        self.commissariats_no_province = commissariats
    
    def display_interface(self):
        st.title('Appointment Scraper')
        # placeholder for the appointments table
        self.appointments_placeholder = st.empty()
        # the user can choose multiple provinces
        self.selected_provinces = st.sidebar.multiselect("Provinces", list(self.provinces))
        # the user can choose multiple commissariats
        # the multiselect should show the commissariat name but the scraper should use the commissariat id
        self.pd_commissariats = get_commissariats(self.selected_provinces, self.commissariats)
        self.selected_commissariats = st.sidebar.multiselect("Commissariats", self.pd_commissariats)
        # transform the commissariat names into commissariat ids from the pandas dataframe 
        self.selected_commissariats = self.pd_commissariats[self.pd_commissariats["description"].isin(self.selected_commissariats)]["id"].to_list()

        # the user can choose a date or a range of dates, not both
        # the user should select if he wants to choose a date or a range of dates
        self.date_or_range = st.sidebar.radio("Date or range", ["Any", "Before Date", "Range"])
        # display text to explain the user that if he pick date, the appointments will be searched to be more recent than the date he picked
        # the date or the range of dates is shown depending on the user's choice
        if self.date_or_range == "Before Date":
            st.sidebar.write("The appointments will be searched to be more recent than the date you picked")
            self.date = st.sidebar.date_input("Before Date", datetime.now())
            self.date_range = None
            self.start_date = None
            self.end_date = None
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
        elif self.date_or_range == "Any":
            st.sidebar.write("All appointments will be searched ")
            self.date = None
            self.date_range = None
            self.start_date = None
            self.end_date = None

        # define the buttons if not already defined
        if not hasattr(st.session_state, "Start"):
            self.start_button = st.sidebar.button("Start")
        if not hasattr(st.session_state, "Stop"):
            self.stop_button = st.sidebar.button("Stop")

        # if the user clicks on the start button, the scraper is called
        if self.start_button:
            with st.spinner(text="Scraping..."):
                self.running=True
                while self.running:
                    self.appointments = self.scraper.scrape_appointments(self.selected_provinces, self.selected_commissariats)
                    self.display_appointments()
                    time.sleep(10)
        # if the user clicks on the stop button, the scraper is stopped
        if self.stop_button:
            self.running=False
            st.write('Scraper stopped...')


        # the appointments are displayed
        self.display_appointments()
        
    def display_appointments(self):

        # filter the appointments by date
        self.appointments = filter_appointments(self.date_or_range,
                                                self.date,
                                                self.start_date,
                                                self.end_date,
                                                self.scraper.appointments.copy())
        # create an empty placeholder to display the appointments

        # clear the appointments placeholder
        self.appointments_placeholder.empty()

        df = convert_appointments_to_dataframe(self.appointments, self.commissariats_no_province)
        self.appointments_placeholder.dataframe(df.set_index(df.index + 1))
        
        # display the latest appointments as a table

    def run_scraper(self):
        self.thread = threading.Thread(target=self.scraper.scraping_loop, args=(self.selected_provinces, self.selected_commissariats))
        self.thread.start()
    
    def stop_scraper(self):
        if self.thread is not None:
            self.scraper.stop_scraping()

