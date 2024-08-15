import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import time
import numpy as np
import sys
from datetime import datetime
from openai import OpenAI
from token_count import TokenCount


def clear():
    os.system('cls' if os.name=='nt' else 'clear')

def goBack():
    temp = input("\nPress Enter to continue.")

def intCheck(optionList):
    while True:
        inputStr = input('Your choice: ').strip()
        try:
            inputStr = int(inputStr)
        except:
            print('Only numbers accepted. Try again.\n')
            continue
        else:
            if inputStr not in optionList:
                print(f'Invalid input. Choose one option among {str(optionList)}. Try again.\n')
            else:
                break
    return inputStr

def fileSelect():
    while True:
        clear()
        files = [f for f in os.listdir('./input')]
        print('\nDetected the following files in the "input" folder.')
        print('What do you want to do?')
        for i in range(len(files)):
            optionsInd = i+1
            print(f'{optionsInd}. Upload {files[i]}')
        print(f'{len(files)+1}. Go back to the main menu\n')
        userChoice = intCheck([i for i in range(1, len(files)+2)])
        if userChoice == len(files) + 1:
            clear()
            sys.exit(0)
        else:
            userChoice -=1
            fileName = files[userChoice]
        
        if fileName.find('.xlsx') != -1:
            try:
                organizations = pd.read_excel('./input/'+fileName)
            except:
                print('\nFailed to read in your input. Please check the file before trying again.\n')
                goBack()
                continue
            else:
                clear()
                print('\nFile Upload Successful.\n')
                break
        elif fileName.find('.csv') != -1:
            try:
                organizations = pd.read_csv('./input/'+fileName)
            except:
                print('\nFailed to read in your input. Please check the file before trying again.\n')
                goBack()
                continue
            else:
                clear()
                print('\nFile Upload Successful.\n')
                break
        else:
            print('\nInvalid upload: This program only accepts .csv or .xlsx files. Try again.\n')
            goBack()
            continue
    return organizations

def selectColumn(organizationDF, targetColumns):
    clear()
    print('These are the names of the columns in your file: ')
    colIndex = 1
    for col in organizationDF.columns:
        print(f'{colIndex}. {col}')
        colIndex+=1
    for i in targetColumns:
        print(f'\nWhich column contains the {i} of the target organizations?')
        colInd = intCheck([i for i in range(1, len(organizationDF.columns)+1)])
        colInd -=1
        colName = organizationDF.columns[colInd]
        organizationDF = organizationDF.rename(columns = {colName:i})
    print('\nTarget Columns Successfully Identified. Please wait as the program is loading the next step.\n')
    return organizationDF

def mainMenu():
    while True:
        print("""MAIN MENU
1. Upload a file for analysis
2. Quit the program
              """)
        choice = intCheck([1,2])
        if choice == 1:
            clear()
            try: 
                file = fileSelect()
            except:
                continue
            else:
                break
        elif choice == 2:
            clear()
            exit()
        else:
            print('Invalid input. Please try again.\n')
    return file


class RatingsScraper:
    def __init__(self, waitTime):
        self.waitTime = waitTime

    def scrape(self, name, loc):
        options = ChromeOptions()
        options.add_argument("--headless=new")
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        driver.maximize_window()
        driver.get('https://www.google.com/maps')

        try:
            # Locate the Search Bar
            searchinput = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//input[@class = 'fontBodyMedium searchboxinput xiQnY ']"))
                )

            # Search the Organization
            searchinput.send_keys(name+' '+loc)
            searchinput.send_keys(Keys.ENTER)
            time.sleep(self.waitTime)

            # Locate the Star Rating
            rating = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.XPATH, "//div[@class = 'F7nice ']"))
                ).text

            # Extract the Average Star Rating and Number of Reviews
            rating = rating.split('\n')
            star = rating[0]
            numReview = rating[1].strip('()')

            # Get the Organization's Maps URL
            url = driver.current_url

            # Confirmation
            message = 'Successfully Scraped: ' + name

        except:
            message = 'Failed to Scrape: ' + name
            star = np.nan
            numReview = np.nan
            url = np.nan
    
        # Quit driver
        driver.quit()

        # Print Confirmation
        print(message)

        # Return results
        return star, numReview, url
    
class ReviewsScraper:
    def __init__(self, waitTime, scrollLimit):
        self.waitTime = waitTime
        self.scrollLimit = scrollLimit

    def scrape(self, name, url):
        # Initialize the driver
        options = ChromeOptions()
        options.add_argument("--headless=new")
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        driver.maximize_window()
        try:
            driver.get(url)

        except:
            print('Cannot access URL. Cannot scrape: '+name)
            review_text = np.nan

        else:

            # Locate the review
            try:

                reviewButton = WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.XPATH, "//button[@class = 'hh2c6 ']"))
                        )
                reviewButton.click()

                # While-loop for scrolling
                end_search = False
                scroll = 0

                # Determine an appropriate scroll limit
                scroll_limit = self.scrollLimit

                try:
                    last_height = WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@class = 'm6QErb XiKgde ']"))
                        ).size['height']
                except:
                    end_search = True

                while not end_search:

                    #Starts Scrolling
                    driver.find_element(By.XPATH, "//div[@class = 'm6QErb DxyBCb kA9KIf dS8AEf XiKgde ']").send_keys(Keys.END)
                    time.sleep(random.uniform(4,8))

                    #Scroll count
                    scroll += 1

                    #Get new height:
                    new_height = WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@class = 'm6QErb XiKgde ']"))
                        ).size['height']

                    #While-loop argument:
                    if new_height == last_height or scroll == scroll_limit:
                        end_search = True
                    else:
                        last_height = new_height

                # Opening reviews to full text
                reviewButtons = driver.find_elements(By.XPATH, "//button[@class = 'w8nwRe kyuRq']")
                for button in reviewButtons:
                    button.click()
                time.sleep(self.waitTime)

                # Scraping all reviews
                review_text = []
                reviews = driver.find_elements(By.XPATH, "//span[@class='wiI7pd']")
                for r in reviews:
                    review_text.append(r.text)

                message = 'Successfully Scraped: ' + name

            except:
                review_text = np.nan
                message = 'Failed to Scrape: ' + name

            # Print Confirmation
            print(message)

            # Quit the driver
            driver.quit()

        return review_text

class s2Prompter:
    def __init__(self, tokenLimit, apikey):
        self.tokenLimit = tokenLimit
        self.model = 'gpt-4o'
        self.apikey = apikey
        if self.apikey == "":
            self.apikey = input("Enter your API key: ").strip()

    def prompting(self, name, reviewList):

        # generate the prompt
        prompt = f"The business is '{name}' and the following Python list include\
              the business's reviews from customers: {reviewList}\
                \n Without using proper nons, replace '[string]' in the following sentence \
                with specific information from the reviews: 'With customers who rave about \
                [string], I am sure you receive many emails per week asking to \
                buy [business name].' Refrain from including proper nouns in [string].\
                Make sure the output sentence is grammatically correct and professional. \
                Once again, exclude proper nouns from [string]."
        
        # get the input token count
        tc = TokenCount(model_name= self.model)
        tokens = tc.num_tokens_from_string(prompt)
        if tokens >= 7000:
            print(f"""\nThe token count for {name} will exceed {tokens} tokens. Continue?
1. Yes
2. No. Please skip this organization.\n""")
            userchoice = intCheck([1,2])

            if userchoice == 1:
                pass
            else:
                return np.nan
        try:
            client = OpenAI(api_key = self.apikey)
            response = client.chat.completions.create(
            model= self.model,
            messages = [
                {
                    "role":"user",
                    "content": prompt
                }
            ],
            max_tokens=self.tokenLimit
            )
        except:
            print(f'Error querying for: {name}\n')
            target=np.nan
        else:
            print(f'Successfully queried for: {name}\n')
            print(f'Token usage: {response.usage.total_tokens}\n')
            sentence=response.choices[0].message.content.strip()

            startInd=sentence.find('about') + 6
            endInd=sentence.find(', I')
            target=sentence[startInd:endInd].strip()

            # Handles "their"
            if target.find('their') != -1:
                target=target.replace('their', 'the')

            # Handles mentioning of company's name
            if target.find(name) != -1:
                target=target.replace(name,'your team')

        return target

class Settings:
    def __init__(self):
        file = open("settings.txt", "r")
        self.settingList = file.read()
        self.settingList = self.settingList.split(",")
        file.close()
        self.waitTime = int(self.settingList[0])
        self.scrollLimit = int(self.settingList[1])
        self.tokenLimit = int(self.settingList[2])
        self.apikey = self.settingList[3]
    def changeWaitTime(self,newWaitTime):
        self.waitTime = newWaitTime
        file = open("settings.txt", "w")
        file.write(f"{self.waitTime},{self.scrollLimit},{self.tokenLimit},{self.apikey}")
        file.close()
    def changeScrollLimit(self, newLimit):
        self.scrollLimit = newLimit
        file = open("settings.txt", "w")
        file.write(f"{self.waitTime},{self.scrollLimit},{self.tokenLimit},{self.apikey}")
        file.close()
    def changeTokens(self, newLimit):
        self.tokenLimit = newLimit
        file = open("settings.txt", "w")
        file.write(f"{self.waitTime},{self.scrollLimit},{self.tokenLimit},{self.apikey}")
        file.close()
    def changeAPI(self, newAPI):
        self.apikey = newAPI
        file = open("settings.txt", "w")
        file.write(f"{self.waitTime},{self.scrollLimit},{self.tokenLimit},{self.apikey}")
        file.close()

def inputStr(settingOption):
    clear()
    print('ONLY ENTER VALID INTERGERS\n')
    while True:
        inputStr = input(f'New {settingOption}: ').strip()
        try:
            inputStr = int(inputStr)
        except:
            print('\nOnly enter intergers. Try again.')
        else:
            if inputStr <= 0:
                print('\nImpossible input. Try again.')
            else:
                break
    return inputStr

def concatDF(organizationDF, results, cols):
    for i in range(len(cols)):
        rowList = []
        for row in results:
            rowList.append(row[i])
        organizationDF = pd.concat([organizationDF, pd.Series(rowList, name= cols[i])], axis=1)

    return organizationDF

def extraction(organizationDF, process):
    clear()
    if process=="ratings":
        failed=organizationDF[organizationDF['Google Maps URL'].isna()]
    elif process=="reviews":
        failed=organizationDF[organizationDF['Reviews'].isna()]
    else:
        failed=organizationDF[organizationDF['Email Phrases'].isna()]
    if failed.empty:
        pass
    else:
        organizationDF=pd.merge(organizationDF, failed, indicator=True, how='outer').query('_merge=="left_only"').drop('_merge', axis=1)
    print("Scrape Complete.\n")
    print("Scraped file preview:")
    print(organizationDF.head(5))
    version = datetime.now().strftime("%m%d%H%M")
    outputName = process+'_'+version+'.csv'
    organizationDF.to_csv('./output/'+outputName, index=False)
    print('\nExtracted to csv: ', outputName)
    if failed.empty:
        pass
    else:
        outputName = 'failed'+process.title()+'_'+version+'.csv'
        failed.to_csv('./output/'+outputName, index=False)
        print('\nFailed organizations extracted in output folder: ', outputName)
    temp = input('\nPress Enter to go back to analysis options.')
    return organizationDF

def mainActions(organizationDF):
    setting = Settings()
    while True:
        clear()
        print('Preview: ')
        print(organizationDF.head(5))
        print('''\nWhat do you want to do with this file?
1. Step 1: Scrape Google Maps Ratings and URL
2. Step 2: Scrape Google Reviews (file must contain google Maps URLs)
3. Step 3: Conduct sentiment analysis with GPT-4o (file must contain scraped Google reviews)
4. Change settings
5. Go back to main menu
              ''')
        choice = intCheck([1,2,3,4,5])
        if choice == 1:
            scraper = RatingsScraper(setting.waitTime)
            try:
                organizationDF[['Firm Name', 'Location']].isnull()
            except:
                try:
                    organizationDF = selectColumn(organizationDF,['Firm Name', 'Location'])
                except:
                    break
                else:
                    pass
            else:
                pass
            finally:
                clear()
                results = organizationDF.apply(lambda row: scraper.scrape(row['Firm Name'], row['Location']), axis=1)
                cols = ['Star Ratings', 'Number of Reviews', 'Google Maps URL']
                organizationDF = concatDF(organizationDF, results, cols)
                organizationDF = extraction(organizationDF, 'ratings')
        elif choice ==2:
            try:
                organizationDF[['Firm Name', 'Google Maps URL']].isnull()
            except:
                try:
                    organizationDF = selectColumn(organizationDF,['Firm Name', 'Google Maps URL'])
                except:
                    break
                else:
                    pass
            else:
                pass
            finally:
                clear()
                scraper = ReviewsScraper(setting.waitTime, setting.scrollLimit)
                organizationDF['Reviews'] = organizationDF.apply(lambda row: scraper.scrape(row['Firm Name'], row['Google Maps URL']), axis=1)
                organizationDF = extraction(organizationDF, 'reviews')
        elif choice == 3:
            clear()
            try:
                organizationDF[['Firm Name', 'Reviews']].isnull()
            except:
                try:
                    organizationDF = selectColumn(organizationDF,['Firm Name', 'Reviews'])
                except:
                    break
                else:
                    pass
            else:
                pass
            finally:
                clear()
                prompter = s2Prompter(setting.tokenLimit, setting.apikey)
                clear()
                print('Please wait to initialize sentiment analysis...\n')
                organizationDF['Email Phrases'] = organizationDF.apply(lambda row: prompter.prompting(row['Firm Name'], row['Reviews']), axis=1)
                organizationDF = extraction(organizationDF,'sentiment')
        elif choice == 4:
            while True:
                    clear()
                    print("Current settings:\n")
                    print('Wait time (in seconds) for scrapers: ', setting.waitTime)
                    print('Maximum numbers of reviews to collect per organization: ', setting.scrollLimit*10)
                    print('Maximum output tokens for GPT models: ', setting.tokenLimit)
                    print('Your API key: ', setting.apikey)
                    print("""\nWhat do you want to do?
1. Change wait time
2. Change maximum number of reviews
3. Change GPT's output token limit
4. Add API key                        
5. Go back
                            """)
                    choice = intCheck([1,2,3,4,5])
                    if choice == 1:
                        newSetting = inputStr('wait time to scrape one review')
                        setting.changeWaitTime(newSetting)
                    elif choice == 2:
                        newSetting = round((inputStr('maximum number of reviews to collect when scraping one organization')/10))
                        setting.changeScrollLimit(newSetting)
                    elif choice == 3:
                        newSetting = inputStr('maximum output tokens for GPT models')
                        setting.changeTokens(newSetting)
                    elif choice == 4:
                        clear()
                        newSetting = input("Enter your API key: ").strip()
                        setting.changeAPI(newSetting)
                    else:
                        clear()
                        break
        else:
            clear()
            sys.exit(0)