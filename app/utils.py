import pandas as pd

def get_commissariats(selected_provinces, commissariats):        
    province_commissariats = []
    for province in selected_provinces:
        for commissariat in commissariats[province]:
            province_commissariats.append({"description": commissariats[province][commissariat]['descrizione'], "id": commissariat})
    return pd.DataFrame(province_commissariats, columns=["description", "id"])


def filter_appointments(date_or_range, date, start_date, end_date, appointments):
    # if appointments is empty, pass
    if appointments:
        # filter the appointments dictionary by date
        if date_or_range == "Date":
            for commissariat in appointments:
                appointments[commissariat] = [appointment for appointment in appointments[commissariat] if appointment['date'] <= date] 
        elif date_or_range == "Range":
            for commissariat in appointments:
                appointments[commissariat] = [appointment for appointment in appointments[commissariat] if appointment['date'] >= start_date and appointment['date'] <= end_date]
    return appointments

def convert_appointments_to_dataframe(appointments, commissariats_no_province):
    df = pd.DataFrame(columns=["commissariat", "date", "url"])
    for commissariat in appointments:
        commissariat_name = commissariats_no_province[commissariat]['descrizione']
        for appointment in appointments[commissariat]:
            appointment_date = appointment['date']
            appointment_url = appointment['url'] 
            row = pd.DataFrame({"commissariat": [commissariat_name], "date": [appointment_date], "url": [appointment_url]})
            df = pd.concat([df, row], axis=0, ignore_index=True)
    return df