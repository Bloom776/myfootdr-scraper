## Introduction

This project scrapes archived clinic data from the MyFootDr website. It addresses the need to extract and store historical clinic information, which is no longer directly accessible through the live website.

This scraper provides a structured dataset of clinic details, enabling data analysis and historical trend identification. You can use the extracted data for research, reporting, or to populate other systems.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Features

*   Scrape archived clinic data from MyFootDr's website.
*   Extract clinic details, including address, phone number, and operating hours.
*   Store scraped data in a structured format.
    *   Output data as a CSV file.
    *   Optionally save data to a SQLite database.
*   Configure the scraping process via command-line arguments.
    *   Specify the target URL.
    *   Define the output file path.
*   Handle pagination to retrieve data from multiple pages.
*   Implement error handling to manage potential scraping issues.

## Tech Stack

This project leverages the following technologies:

*   **Language:** Python
*   **Web Scraping:** Beautiful Soup 4
*   **HTTP Client:** requests
*   **Data Handling:** pandas

## Prerequisites

To successfully run this project, ensure the following prerequisites are met:

**Required:**

*   **Python:** Version 3.8 or higher. Verify your Python version using:

    ```bash
    python --version
    ```

*   **Pip:** Python's package installer. Pip is typically installed with Python. Confirm its availability with:

    ```bash
    pip --version
    ```

*   **Required Python Packages:** Install the necessary Python packages using `pip`:

    ```bash
    pip install beautifulsoup4 requests
    ```

**Optional:**

*   **Virtual Environment (Recommended):** Create and activate a virtual environment to manage project dependencies. Navigate to the project directory and execute:

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Linux/macOS
## Installation

To install and configure the `myfootdr-scraper` project, follow these steps:

1.  **Clone the Repository:** Clone the project repository to your local machine using the provided Git URL.

    ```bash
    git clone https://github.com/Bloom776/myfootdr-scraper.git
    ```

2.  **Navigate to the Project Directory:** Change your current directory to the newly cloned project directory.

    ```bash
    cd myfootdr-scraper
    ```

3.  **Install Python Dependencies:** Install the required Python packages using `pip`. Ensure you have Python 3.7 or later installed.

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up Environment Variables:** Create a `.env` file in the project's root directory to store your environment variables. Define the necessary variables as shown in the example below. Replace the placeholder values with your actual credentials.

    ```
## Usage

To run the scraper, execute the `myfootdr_scraper.py` script.

```bash
python myfootdr_scraper.py
```

This command initiates the web scraping process, extracting clinic information from the archived MyFootDr clinics page and saving the results to `myfootdr_clinics.csv`.

## Contributing

This project welcomes contributions. Please review the following guidelines before submitting issues or pull requests.

## License

This project is not licensed.

Without a license, you are not granted any rights to use, modify, or distribute this software. All rights are reserved.