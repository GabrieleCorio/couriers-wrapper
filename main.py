from src.couriers_wrapper.BRT import BRTScraper
from src.couriers_wrapper.InPost import InPostScraper

# brt = BRTScraper()
# print(brt.get_full_tracking(tracking_number='098166040512896', postal_code=20019))

scraper = InPostScraper()

tracking_info = scraper.get_tracking("71393229")
print(tracking_info)