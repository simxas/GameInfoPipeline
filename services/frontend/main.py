from flask import Flask, jsonify, request, render_template
import os
import logging
import requests

from monitoring.metrics import (
    register_metrics,
    metrics_blueprint,
    EXTERNAL_API_LATENCY
)


app = Flask(__name__)

# --- Connect the Monitoring ---
# 1. Register the before/teardown request hooks
register_metrics(app)

# 2. Register the /metrics endpoint Blueprint
app.register_blueprint(metrics_blueprint)

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOCAL_API_BASE_URL = 'http://backend-service:8000'
RAWG_API_BASE_URL = 'https://api.rawg.io/api'
RAWG_API_KEY = os.getenv('RAWG_API_KEY')
REQUEST_TIMEOUT = 30


def handle_api_error(response, api_name):
    """Helper function to handle API errors consistently"""
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f'{api_name} API error: {response.status_code} - {response.text}')
        return None


def get_model_response(endpoint, method='POST', data=None):
    """
    Call local LLM API running on port 8000
    """
    url = f'{LOCAL_API_BASE_URL}{endpoint}'
    data_to_sent = {
        'prompt': f"I need a very short review in English of game called {data['gameName']} which was released for {data['platform']}"
    }
    try:
        if method.upper() == 'POST':
            with EXTERNAL_API_LATENCY.labels(api_name='fastapi_backend').time():
                response = requests.post(url, json=data_to_sent)
        else:
            return {'error': 'Unsuported HTTP method'}
        return handle_api_error(response, 'Local')

    except requests.exceptions.ConnectionError:
        logger.error(f'Failed to connect to local API at {url}')
        return {'error': 'Local API connection failed'}
    except requests.exceptions.Timeout:
        logger.error(f'Local API request timeout for {url}')
        return {'error': 'Local API timeout'}
    except requests.exceptions.RequestException as e:
        logger.error(f'Local API request failed: {str(e)}')
        return {'error': f'Local API error: {str(e)}'}


def get_platform_id(platform_name):
    """
    Map platform names from your HTML form to RAWG platform IDs
    Based on the actual RAWG API response data
    """
    platform_mapping = {
        # Modern Platforms
        'PC': '4',
        'PlayStation 5': '187',
        'PlayStation 4': '18',
        'Xbox Series X/S': '186',  # RAWG calls it "Xbox Series S/X"
        'Xbox One': '1',
        'Nintendo Switch': '7',
        'Mobile (iOS)': '3',  # RAWG calls it "iOS"
        'Mobile (Android)': '21',  # RAWG calls it "Android"
        'Mac': '5',  # RAWG calls it "macOS"
        'Linux': '6',
        
        # Retro Consoles
        'Nintendo Entertainment System (NES)': '49',  # RAWG calls it "NES"
        'Super Nintendo (SNES)': '79',  # RAWG calls it "SNES"
        'Nintendo 64': '83',
        'GameCube': '105',
        'Wii': '11',
        'Wii U': '10',
        'Game Boy': '26',
        'Game Boy Color': '43',
        'Game Boy Advance': '24',
        'Nintendo DS': '9',
        'Nintendo 3DS': '8',
        'PlayStation 1': '27',  # RAWG calls it "PlayStation"
        'PlayStation 2': '15',
        'PlayStation 3': '16',
        'PlayStation Portable (PSP)': '17',  # RAWG calls it "PSP"
        'PlayStation Vita': '19',  # RAWG calls it "PS Vita"
        'Original Xbox': '80',  # RAWG calls it "Xbox"
        'Xbox 360': '14',
        'Sega Genesis (Mega Drive)': '167',  # RAWG calls it "Genesis"
        'Sega Saturn': '107',  # RAWG calls it "SEGA Saturn"
        'Sega Dreamcast': '106',  # RAWG calls it "Dreamcast"
        'Atari 2600': '23',
        'Atari 7800': '28',
        'Neo Geo': '12',
        'Game Gear': '77',
        'Nintendo DSi': '13',
        'Classic Macintosh': '55',
        'Apple II': '41',
        'Commodore / Amiga': '166',
        'Atari 5200': '31',
        'Atari Flashback': '22',
        'Atari 8-bit': '25',
        'Atari ST': '34',
        'Atari Lynx': '46',
        'Atari XEGS': '50',
        'SEGA CD': '119',
        'SEGA 32X': '117',
        'SEGA Master System': '74',
        '3DO': '111',
        'Jaguar': '112'
    }
    
    return platform_mapping.get(platform_name)


def get_game_by_name(game_name, platform):
    """
    Search game by the name and return best match
    """
    params = {
        'search': game_name,
        'page_size': 1, # get only top result
        'search_exact': 'true' # for more precise matching
    }

    if platform and platform != 'Other':
        platform_id = get_platform_id(platform)
        if platform_id:
            params['platforms'] = platform_id

    result = call_rawg_api('/games', params)

    if result and result.get('results'):
        return result['results'][0]
    
    return None

def get_full_game_info(game_name, platform):
    """
    First search game by the name and then get full details
    """
    searched_game = get_game_by_name(game_name, platform)

    if not searched_game:
        return None

    game_slug = searched_game.get('slug')

    detailed_game_info = call_rawg_api(f'/games/{game_slug}')

    return detailed_game_info



def call_rawg_api(endpoint, params=None):
    """
    Call RAWG.io external API
    """
    url = f'{RAWG_API_BASE_URL}{endpoint}'

    # API key
    if params == None:
        params = {}
    params['key'] = RAWG_API_KEY

    try:
        with EXTERNAL_API_LATENCY.labels(api_name='rawg_io').time():
            rawg_response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            return handle_api_error(rawg_response, 'RAWG')
    except requests.exceptions.ConnectionError:
        logger.error(f'Failed to connect to RAWG API at {url}')
        return {'error': 'RAWG API connection failed'}
    except requests.exceptions.Timeout:
        logger.error(f'RAWG API request timeout for {url}')
        return {'error': 'RAWG API timeout'}
    except requests.exceptions.RequestException as e:
        logger.error(f'RAWG API request failed: {str(e)}')
        return {'error': f'RAWG API error: {str(e)}'}



@app.route('/')
def home():
    # This route will now be automatically monitored by our setup
    return render_template('home.html')

@app.post('/input')
def user_input():
    form_data = {
        'gameName': request.form['gameName'],
        'platform': request.form['platform']
    }

    rawg_info = get_full_game_info(form_data['gameName'], form_data['platform'])
    print(rawg_info['background_image'])
    review_obj = get_model_response('/predict', method='POST', data=form_data)
    # print(review_obj['response'])



    return render_template(
        'answer.html', 
        game_name=form_data['gameName'], 
        platform=form_data['platform'],
        release_date=rawg_info['released'],
        rating=rawg_info['rating'],
        game_cover_art=rawg_info['background_image'],
        review_text=review_obj['response']
    )
