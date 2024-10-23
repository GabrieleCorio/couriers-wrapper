import requests
from bs4 import BeautifulSoup

class BRTScraper:
    
    def __init__(self):
        self.search_url = "https://www.mybrt.it/it/mybrt/my-parcels/incoming"
        self.details_url = "https://www.mybrt.it/it/mybrt/my-parcels/details/protection"

    def _get_csrf_token(self, session):
        """Fetch CSRF token from the main page."""
        response = session.get(self.search_url)
        response.raise_for_status()  # Raises an HTTPError if the request returned an unsuccessful status code
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_meta = soup.find('meta', {'name': '_csrf'})
        if csrf_meta:
            return csrf_meta['content']
        raise ValueError("CSRF token not found.")
    
    def _get_tracking_activities(self, soup):
        """Extract tracking activities from the page."""
        parcel_status_div = soup.find('div', class_='parcelStatus')
        if not parcel_status_div:
            return None
        
        rows = parcel_status_div.find_all('div', class_='row')
        activities = [
            {
                'date': row.find('div', class_='col-xs-5').find('span').text,
                'status': row.find('div', class_='col-xs-7').find('span').text
            }
            for row in rows
        ]
        return activities

    def get_tracking(self, tracking_number):
        """Get basic tracking information."""
        output = {'success': False, 'error': {'code': 0, 'message': 'Unknown error...'}}
        
        session = requests.Session()
        try:
            csrf_token = self._get_csrf_token(session)
            data = {'_csrf': csrf_token, 'value': tracking_number}
            response = session.post(self.search_url.replace('incoming', 'search'), data=data)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            activities = self._get_tracking_activities(soup)
            
            if activities:
                return {'success': True, 'activities': activities}
            return {'success': False, 'error': {'code': 404, 'message': 'Tracking information not found.'}}
        
        except (requests.HTTPError, ValueError) as e:
            output['error']['message'] = str(e)
        
        return output

    def get_full_tracking(self, tracking_number, postal_code):
        """Get full tracking information including sender and recipient details."""
        output = {'success': False, 'error': {'code': 0, 'message': 'Unknown error...'}}
        
        session = requests.Session()
        try:
            csrf_token = self._get_csrf_token(session)
            
            # Step 1: Basic search
            data = {'_csrf': csrf_token, 'value': tracking_number}
            response = session.post(self.search_url.replace('incoming', 'search'), data=data)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            activities = self._get_tracking_activities(soup)
            if not activities:
                return {'success': False, 'error': {'code': 404, 'message': 'Tracking information not found.'}}
            
            # Step 2: Full details
            data = {
                '_csrf': csrf_token,
                'parcelType': 'INCOMING',
                'verificationCode': postal_code,
                'number': tracking_number,
                'shipmentType': 'PARCEL_DETAILS',
                'validate': 'Conferma'
            }
            response = session.post(self.details_url, data=data, )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            shipment_details = self._extract_shipment_details(soup)
            
            if shipment_details:
                return {'success': True, 'activities': activities, 'shipment_details': shipment_details}
            return {'success': False, 'error': {'code': 404, 'message': 'Shipment details not found.'}}
        
        except (requests.HTTPError, ValueError) as e:
            output['error']['message'] = str(e)
        
        return output

    def _extract_shipment_details(self, soup):
        """Extract sender, recipient, and shipment information."""
        try:
            shipment_number = soup.find('div', class_='box-1').find_all('p')[1].get_text(strip=True)
            brt_code = soup.find('div', class_='box-1').find_all('p')[3].get_text(strip=True)

            sender_info = [p.get_text(strip=True) for p in soup.find('div', class_='box-2').find_all('p')]
            recipient_info = [p.get_text(strip=True) for p in soup.find('div', class_='box-4').find_all('p')]

            return {
                'shipment_number': shipment_number,
                'brt_code': brt_code,
                'sender': {
                    'name': sender_info[1],
                    'address': sender_info[2:5]
                },
                'recipient': {
                    'name': recipient_info[1],
                    'address': recipient_info[2:5],
                    'contact_info': recipient_info[5:]
                }
            }
        except (IndexError, AttributeError):
            return None
