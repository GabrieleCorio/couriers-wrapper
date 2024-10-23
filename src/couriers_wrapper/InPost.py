import requests
import json
from bs4 import BeautifulSoup
import time

class InPostScraper:
    
    def __init__(self):
        self.tracking_url = "https://inpost.it/trova-il-tuo-pacco"
        self.session = requests.Session()  # Initialize session once

    def get_tracking(self, tracking_number):
        """Get tracking information including activities."""
        output = {'success': False, 'error': {'code': 0, 'message': 'Unknown error...'}}
        
        max_retries = 3
        retries = 0
        
        headers = {
            'Host': 'inpost.it',
            'User-Agent': 'RapidAPI/4.2.0 (Macintosh; OS X/14.6.1) GCDHTTPRequest',
            'x-requested-with': 'XMLHttpRequest',
        }
        
        while retries < max_retries:
            try:
                url = f'https://inpost.it/shipx-proxy/?number={tracking_number}&returnTranslations=true&language=it_IT'
                response = self.session.get(url, headers=headers)
                
                if response.status_code == 403:
                    print("Access denied (403). Retrying...")
                    retries += 1
                    time.sleep(2)
                    continue
                
                response.raise_for_status()  # Raise an error for other bad responses

                tracking_data = response.json()
                
                # Validate response structure
                if isinstance(tracking_data, list) and len(tracking_data) > 0:
                    activities = self._parse_tracking_activities(tracking_data[0])
                    shipment_details = self._extract_shipment_details(tracking_data[0])

                    return {'success': True, 'activities': activities, 'shipment_details': shipment_details}

                output['error'] = {'code': 404, 'message': 'Tracking information not found.'}
                break
            
            except requests.HTTPError as http_err:
                output['error']['message'] = str(http_err)
                break  # Stop retrying on HTTP errors other than 403
            except ValueError as json_err:
                output['error']['message'] = f"JSON decode error: {str(json_err)}"
                break  # Stop retrying if the JSON can't be decoded
            except Exception as err:
                output['error']['message'] = str(err)
                break  # Stop retrying for other exceptions

        return output

    def _parse_tracking_activities(self, data):
        """Extract tracking activities from the response data."""
        activities = []
        for event in data.get('events', []):
            activities.append({
                'date': event.get('timestamp'),
                'status': event.get('eventTitle'),
                'geolocation': {
                    'latitude': event.get('location', {}),
                    'longitude': event.get('location', {})
                }
            })
        return activities

    def _extract_shipment_details(self, data):
        """Extract shipment details from the response."""
        try:
            return {
                'main_tracking_number': data.get('mainTrackingNumber'),
                'destination': data.get('destination', {}).get('name'),
                'destination_address': {
                    'country': data.get('destination', {}).get('countryCode'),
                    'postal_code': data.get('destination', {}).get('postalCode'),
                    'city': data.get('destination', {}).get('city'),
                    'street': data.get('destination', {}).get('street'),
                }
            }
        except Exception:
            return None

    def close(self):
        """Close the session if it's open."""
        if self.session:
            self.session.close()
            self.session = None  # Prevent further use after closing
            print("Session closed.")
