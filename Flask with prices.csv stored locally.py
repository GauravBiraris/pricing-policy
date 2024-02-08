import csv
import requests
from requests.exceptions import HTTPError, ConnectionError
import json
import random
import string
from datetime import datetime
import statistics
from google.cloud import storage
import flask
from jsonschema import validate
import logging

app = flask.Flask(__name__)
logging.basicConfig(level=logging.INFO) 

def generate_id():
  return ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))

def build_search_body(product_name, product_desc, additional_info, gps, message_id, transaction_id, tenant):
  
  search_body = {
    'context': {
      'domain': tenant[0]['domain'],
      'country': tenant[0]['country'],
      'city': tenant[0]['city'],
      'action': 'search',
      'core_version': '1.0.0',
      'bap_id': tenant[0]['bap_id'],
      'bap_uri': tenant[0]['bap_uri'],
      'transaction_id': transaction_id,
      'message_id': message_id,
      'timestamp': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
      'ttl': 'PT30S',
      'key': tenant[0]['key'],
    },
    'message': {
      'intent': {
        'item': {
          'descriptor': {
            'name': product_name,
            'short_desc': product_desc,
            'long_desc': additional_info,
          }
        },
        'fulfillment': {
          'end': {
            'location': {
              'gps': gps
            }
          }
        }
      }
    }
  }
  
  return search_body

def send_search_request(search_body):

  url = 'https://example.com/search'
  try:
    response = requests.post(url, json=search_body)
    response.raise_for_status()
    return response
  except HTTPError as http_err:
    raise Exception(f"HTTP error: {http_err}") 
  except ConnectionError as conn_err:
    raise Exception(f"Connection error: {conn_err}")  
  
def get_on_search_responses(message_id):

  # Stub response
  return [
    {
      'context': {'message_id': message_id},
      'message': {
        'catalog': {
          'bpp': {
            'providers': [
              {'items': [{'price': {'listed_value': '150'}}]}
            ]
          }
        }
      }
    },
    {
      'context': {'message_id': message_id},
      'message': {
        'catalog': {
          'bpp': {
            'providers': [
              {'items': [{'price': {'listed_value': '200'}}]}
            ]
          }
        }  
      }
    }
  ]
  
def extract_prices(on_search_body, product_name):
  
  prices = []
  
  for provider in on_search_body['message']['catalog']['bpp']['providers']:
  
    for item in provider['items']:
    
      if item['descriptor']['name'] == product_name:
      
        prices.append(float(item['price']['listed_value']))
        
  return prices
  
def calc_stats(prices):

  if prices:
    mean = statistics.mean(prices) 
    median = statistics.median(prices)
    mode = statistics.mode(prices)
    min_price = min(prices)
    max_price = max(prices)
    return [mean, median, mode, max_price, min_price]
  else:
    return []

# Main function  

def process_calls():

  logging.info("Starting processing")
  
  # Initialize Storage client
  storage_client = storage.Client()

  # Download input CSVs from bucket
  bucket = storage_client.get_bucket('my-bucket')
  blob = bucket.blob('calls.csv')
  calls_string = blob.download_as_string()
  calls = list(csv.DictReader(calls_string.splitlines()))

  blob = bucket.blob('tenant.csv')
  tenant_string = blob.download_as_string()
  tenant = list(csv.DictReader(tenant_string.splitlines()))

  # Load API specs
  with open('ONDC_API_specs.json', 'r') as f:
    specs = json.load(f)

  # Create output files  
  prices_csv = open('prices.csv', 'w', newline='') 
  writer = csv.writer(prices_csv)
  writer.writerow(['product_name', 'mean', 'median', 'mode', 'max', 'min'])
  
  tenant_csv = open('tenantR.csv', 'w', newline='')
  writer = csv.writer(tenant_csv)
  writer.writerow(['key', 'value'])

  # Iterate through each call
  for call in calls:

    try:  
      product_name = call['product_name']
      product_desc = call['product_description']
      additional_info = call['additional_info']
      gps = call['Gps']

      # Generate IDs
      message_id = generate_id()
      transaction_id = generate_id()

      # Build search body
      search_body = build_search_body(product_name, product_desc, 
                                      additional_info, gps, message_id, 
                                      transaction_id, tenant)

      # Send search request
      response = send_search_request(search_body)
      response.raise_for_status()

      # Get on_search responses
      on_search_bodies = get_on_search_responses(message_id)

      # Process each response  
      prices = []
      for body in on_search_bodies:
      
        validate(body, specs['on_search_schema'])
        
        prices.extend(extract_prices(body, product_name))
        
      # Calculate stats
      stats = calc_stats(prices)
      
      # Append to CSV
      writer.writerow([product_name, *stats])
      
    except Exception as e:
      logging.error("Error processing %s: %s", product_name, e)

  # Upload output CSVs to bucket  
  output_csv_string = open('prices.csv', 'r').read()
  blob = bucket.blob('prices.csv')
  blob.upload_from_string(output_csv_string)

  logging.info("Processing complete!")


@app.route('/on_search') 
def on_search():
  pass

if __name__ == '__main__':
  process_calls()
  app.run()