from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from datetime import datetime
import requests

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# Create a dictionary to map month names to numerical representations
month_mapping = {
    "January": "00",
    "February": "01",
    "March": "02",
    "April": "03",
    "May": "04",
    "June": "05",
    "July": "06",
    "August": "07",
    "September": "08",
    "October": "09",
    "November": "10",
    "December": "11"
}

# Convert date to fit into urls
def convert_date(date):
    # Convert the date string to a datetime object
    datetime_date = datetime.strptime(date, "%Y-%m-%d")

    # Extract year, month, and day components
    year = datetime_date.year
    month = datetime_date.strftime("%B")  # Get the full month name
    day = datetime_date.day

    # Format the year and month to fit into the URL parameter format
    month_year = f"{month_mapping[month]}{year:04d}"  # Use the full year
    
    return day, month_year

# Define a function to extract the room data
def extract_room_data(room_element):
    room_name = room_element.find_element(By.CLASS_NAME, "d-flex.roomName").text
    room_price = room_element.find_element(By.CLASS_NAME, "price-wrapper").find_element(By.CLASS_NAME, "price").text
    return {"name": room_name, "price": room_price}

# Web scrape hotel info for avaliablity
def scape_hotel(num_adult, num_children, num_rooms, check_in_date, check_out_date):
    url = "https://www.ihg.com/crowneplaza/hotels/us/en/find-hotels/select-roomrate?fromRedirect=true&qSrt=sBR&qIta=99502222&icdv=99502222&qSlH=SINCP&qRms=6&qAdlt=2&qChld=1&qCiD=25&qCiMy=72023&qCoD=26&qCoMy=72023&qAAR=6CBARC&qRtP=6CBARC&setPMCookies=true&qSHBrC=CP&qDest=75%20Airport%20Boulevard%2001-01,%20Singapore,%20SG&srb_u=1"

    parsed_url = urlparse(url)
    query_parameters = parse_qs(parsed_url.query)

    # Retrieve Check in and out values
    check_in_day, check_in_month_year = convert_date(check_in_date)
    check_out_day, check_out_month_year = convert_date(check_out_date)

    # Update the values of the query parameters
    query_parameters['qAdlt'] = [num_adult]  # Number of adults
    query_parameters['qChld'] = [num_children]  # Number of children
    query_parameters['qRms'] = [num_rooms]   # Number of rooms
    query_parameters['qCiD'] = [check_in_day]  # Check-in day
    query_parameters['qCiMy'] = [check_in_month_year]  # Check-in month and year
    query_parameters['qCoD'] = [check_out_day]   # Check-out day
    query_parameters['qCoMy'] = [check_out_month_year]  # Check-out month and year

    # Construct the new URL with updated query parameters
    new_query = urlencode(query_parameters, doseq=True)
    new_url = urlunparse(parsed_url._replace(query=new_query))

    # Web scrape info 
    # Create a new instance of the Chrome browser
    driver = webdriver.Chrome()

    # Navigate to the URL
    driver.get(new_url)

    # Wait for the page to load (adjust the timeout as needed)
    wait = WebDriverWait(driver, 10)

    # Wait for room rate items to load
    room_rate_items = wait.until(EC.visibility_of_all_elements_located((By.CLASS_NAME, "room-rate-card")))

    # Extract data from room rate items
    rooms = [extract_room_data(room) for room in room_rate_items]

    # Close the browser window
    driver.quit()

    return rooms, new_url

