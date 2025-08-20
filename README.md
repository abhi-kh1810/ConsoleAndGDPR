# Console Error Scraper

A Python script that automatically navigates to a website, handles cookie consent, and captures JavaScript console errors.

## Features

- **Automatic Cookie Consent**: Automatically finds and clicks "Accept All" cookie buttons regardless of their position
- **GDPR Compliance Tracking**: Detects and reports the presence of GDPR/cookie consent banners
- **Console Error Capture**: Captures JavaScript console errors, warnings, and page errors
- **Flexible URL Configuration**: Uses .env file for easy URL management
- **Structured Output**: Saves errors as JSON files in organized directory structure
- **Comprehensive Error Detection**: Captures various types of console messages and page errors

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Create a Virtual Environment

It's recommended to use a virtual environment to avoid conflicts with other Python projects.

#### For Mac/Linux:
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

#### For Windows:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Command Prompt)
venv\Scripts\activate

# Or for PowerShell
venv\Scripts\Activate.ps1
```

**Note**: You'll see `(venv)` in your terminal prompt when the virtual environment is active.


## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Playwright Browsers**:
   ```bash
   playwright install chromium
   ```

3. **Configure Site URL**:
   Copy this file to .env and update the values:
   ```
   SITE_URL=https://your-target-website.com
   ```

## Usage

Run the script:
```bash
python console_error_scraper.py
```

The script will:
1. Load the site URL from the `.env` file
2. Navigate to the website
3. Automatically detect and click any "Accept All" cookie buttons
4. Track GDPR/cookie consent banner presence
5. Capture console errors during page loading and interaction
6. Save results to `console_error/site_url/<domain>.json`

## Output Structure

The script creates a directory structure:
```
console_error/
└── site_url/
    └── <domain>.json
```

The JSON file contains:
- Site URL and domain information
- Timestamp of when the scraping occurred
- GDPR compliance status (whether a cookie consent banner was found)
- Total count of errors
- Detailed error information including:
  - Error type (error, warning, page_error)
  - Error message
  - Timestamp
  - Location information (if available)
