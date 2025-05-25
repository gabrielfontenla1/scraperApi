# API Scraper for Dentists/Doctors

A Flask-based REST API that scrapes information about dentists and doctors from Google Local results using SerpAPI.

## Features

- Search for dentists/doctors by country and provinces
- Asynchronous processing with task status tracking
- Support for multiple Latin American countries and Spain
- Rate limiting with configurable delays
- JSON output with detailed business information

## Requirements

- Python 3.x
- Flask
- SerpAPI client

## Installation

```bash
pip install flask serpapi
```

## Usage

1. Start the server:
```bash
python app.py
```

2. Make a POST request to `/scrape` with configuration:
```json
{
    "apiKey": "your_serpapi_key",
    "query": "hospital",
    "provinces": ["Santiago Del Estero"],
    "delay": 1.5,
    "country": "Argentina"
}
```

3. Check task status at `/status/<task_id>`
4. Get results at `/results/<task_id>`

## API Endpoints

- `POST /scrape`: Start scraping
- `GET /status/<id>`: Check task status
- `GET /results/<id>`: Get task results
- `GET /results/<id>/download`: Download results as JSON
- `GET /tasks`: List all tasks
- `GET /countries`: List supported countries
- `GET /provinces/<country>`: List provinces for a country
- `GET /health`: Health check 