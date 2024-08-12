# GOOGLE SCRAPER
## Version: 1.4.0
This Python program scrapes Google reviews of interested businesses then query GPT-4o's engine to complete the following sentence: "With customers who rave about {...}, I am sure you receive many emails per week asking to buy your business." 

### Lastest update
- Tried different organizational schemes
- Removed max tries
- Allowed the program to save settings locally
- Added a setting option to save user's API key locally

### Prerequisites
- Python
- A Python interpreter (VSCode, Anaconda, etc.)
- Once download, make sure to $ pip install -r requirements.txt

### User guide
The program opens the input folder and asks the user to upload a .csv or .xlsx file. This file contains the list of interested organizations and at the very least must have two columns:
- One containing the names of interested organizations
- One containing the locations of interested organizations
The program allows user to scrape Google ratings, reviews, and then conduct sentiment analysis with GPT-4o to generate a phrase that completes the sentence above. You must have an OpenAI's API Key ready before running the querying option. 
The program's functionalities are dependent upon one another:
- You can scrape Google ratings and URL only if you provide the Names and Locations of interested organizations.
- You can scrape Google reviews only if you provide the Names and Google URLs of interested organizations.
- You can appropriately query GPT 4-o only if you provide the Names and Google Reviews of interested organizations.

### Settings guide
The program allows you to customize the scrapers' and prompters' settings to specialize your operations. These settings apply until you change them again. The following settings are customizable:
1. Scrapers' wait time to access one organization: For many actions that the scrapers take to access the organization's Google Maps site, it will wait for a specific time before moving on to the next action. This ensures that the website properly loads before the scraper can access information. Increasing wait time is recommended if your internet is not stable and you have less than 10 organizations you want to scrape.
2. Max reviews to collect per organization: When the scraper access an organization's Google review page, it enacts scrolling to unhide old reviews. However, some organizations have thousands of review that scrolling to the end would take too much time. The scraper currently only collects up to a specified number of reviews. You can increase this number if you wish but keep in mind that not all reviews contain actual comments made by customers and the more you collect, the more irrelevance you introduce to the reviews dataset (old reviews, short and uninformative comments, etc.)
3. Max output tokens: This setting controls the word limit that GPT-4o can produce to respond to your prompt. Most of the time, output is only a few hundreds tokens. The higher the limit, the greater the risk that GPT-4o will produce a long and costly response. The lower the limit, it is very likely that GPT-4o will fail to produce the desired phrase/sentence.
4. Your API key: You can have the program save your API key to its local txt file. This way, you won't have to keep entering your key in future scrapes.