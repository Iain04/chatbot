from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from datetime import datetime

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
    room_price = room_element.find_element(By.CLASS_NAME, "cash").text
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

    # Define the User-Agent header to mimic a web browser
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.9999.99 Safari/537.36"

    # Web scrape info
    # Chrome options 
    options = Options()
    options.headless = True  # Enable headless mode
    options.add_argument(f"user-agent={user_agent}")

    # Create a new instance of the Chrome browser
    driver = webdriver.Chrome(options=options)

    # Navigate to the URL
    driver.get(new_url)

    # Wait for the page to load (adjust the timeout as needed)
    wait = WebDriverWait(driver, 10)

    # Initialize values outside the try-except block
    room_rate_items = None
    rooms = None
    data_dict = {}

    print("Is page loaded?", driver.execute_script("return document.readyState") == "complete")

    # Wait for room rate items to load
    try:
        room_rate_items = wait.until(EC.visibility_of_all_elements_located((By.CLASS_NAME, "room-rate-card")))
    except Exception as e:
        print("Exception:", e)

    # Extract room data
    try:
        rooms = [extract_room_data(room) for room in room_rate_items]
        print(rooms)

    except Exception as e:
        print("Exception:", e)
        rooms = None

    # Extract values to display
    try:
        
        # Wait for the elements to become visible (adjust timeout as needed)
        date_element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="crr-bc-wrapper"]/search-header/div/div[1]/div[1]'))
        )
        guest_count_element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="crr-bc-wrapper"]/search-header/div/div[1]/div[2]/span[1]'))
        )
        room_count_element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="crr-bc-wrapper"]/search-header/div/div[1]/div[2]/span[2]'))
        )
    
        # Extract data from the elements
        data_dict['date_range'] = date_element.text
        data_dict['guest_count'] = int(guest_count_element.text.split()[0])
        data_dict['room_count'] = int(room_count_element.text.split()[0])
        print(data_dict)
    
    except Exception as e:
        print("Exception:", e)
        data_dict = None

    # Close the browser window
    driver.quit()

    return rooms, new_url, data_dict

