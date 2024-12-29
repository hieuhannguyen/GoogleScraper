# Web-scraping modules
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
from datetime import datetime

# GPT querying modules
from openai import OpenAI
from token_count import TokenCount

# GUI modules
import tkinter as tk
from tkinter import font
from tkinter import filedialog
from tkinter import ttk
from tkinter import messagebox
from tkinter import simpledialog

from PIL import ImageTk, Image

# Data handling modules
import pandas as pd
import numpy as np
import sqlite3

## Quick actions

# Clear previous frames
def clear(frame):
    for widget in frame.winfo_children():
        widget.destroy()

# Load data from backup
def loadData():
    connection = sqlite3.connect("assets/data.db")
    df = pd.read_sql(sql = "SELECT * FROM backupData;", con=connection)
    connection.close()
    return df

# Update database
def updateBackup(df):
    connection = sqlite3.connect("assets/data.db")
    df.to_sql(name="backupData", con=connection, if_exists="replace", index=False)
    connection.close()

# Load failed scrapes
def loadFailed():
    connection = sqlite3.connect("assets/data.db")
    try:
        df = pd.read_sql(sql = "SELECT * FROM failedData;", con=connection)
        connection.close()
    except:
        errormessage=messagebox.showerror(
            title='No Data',
            message="""No failed scrapes found."""
        )
    else:
        updateBackup(df)
    finally:
        clear(analysisFrame)
        load_analysisFrame()

# Update failed scrapes
def updateFailed(df):
    connection = sqlite3.connect("assets/data.db")
    df.to_sql(name="failedData", con=connection, if_exists="replace", index=False)
    connection.close()

# Add a small space widget
def smallSpace(frame, size, **kw):
    space = tk.Label(
        frame,
        text = "",
        bg = bg,
        fg = bg,
        font = ("TkDefaultFont",size)
    ).pack(**kw)

## Defining key classes / engines

# Ratings Scraper Engine
class RatingsScraperEngine:
    def __init__(self, waitTime):
        self.waitTime = waitTime

    def scrape(self, name, loc):
        options=ChromeOptions()
        options.add_argument("--headless=new")
        driver=webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        driver.maximize_window()
            
        driver.get('https://www.google.com/maps')

        try:
            # Locate the Search Bar
            searchinput=WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//input[@class = 'fontBodyMedium searchboxinput xiQnY ']"))
                )

            # Search the Organization
            searchinput.send_keys(name+' '+loc)
            searchinput.send_keys(Keys.ENTER)
            time.sleep(self.waitTime)

            # Locate the Star Rating
            rating=WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.XPATH, "//div[@class = 'F7nice ']"))
                ).text

            # Extract the Average Star Rating and Number of Reviews
            rating=rating.split('\n')
            star=rating[0]
            numReview=rating[1].strip('()')

            # Get the Organization's Maps URL
            url=driver.current_url

            # Confirmation message for Terminal
            message = "Successfully scraped: "+ name

        except:
            # Replace target variables values as np.nan
            star=np.nan
            numReview=np.nan
            url=np.nan

            # Confirmation message for Terminal
            message = "Failed to scrape: "+ name
        
        # Quit driver
        driver.quit()

        # Print message
        print(message)

        # Return results
        return star, numReview, url
    
# Review Scraper Engine
class ReviewsScraperEngine:
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

                message = "Successfully scraped: " + name

            except:
                message = "Failed to scrape: " + name
                review_text = np.nan


            # Print message to terminal
            print(message)
            
            # Quit the driver
            driver.quit()

        return review_text

# S2 Prompter
class s2Prompter:
    def __init__(self, model, tokenLimit, apikey):
        self.tokenLimit = tokenLimit
        self.model = model
        self.apikey = apikey

    def prompting(self, name, reviewList):
        prompt = f"The business is '{name}' and the following Python list include\
              the business's reviews from customers: {reviewList}\
              \n Without including proper nouns, replace '[string]' in the following \
              sentence with specific information from the reviews: 'With customers who \
              rave about [string], I am sure you receive many emails per week asking to \
              buy [business name].' Make sure the output sentence is grammatically correct and professional."
        
        tc = TokenCount(model_name= self.model)
        tokens = tc.num_tokens_from_string(prompt)
        if tokens>=7000:
            warningbox=messagebox.askokcancel(
                title="High Token Count",
                message=f"The total token count for {name} will exceed {tokens} tokens. Continue?"
            )
            if warningbox:
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
            print(f"Error querying for: {name}")
            target = np.nan
        else:
            print(f"Successfully queried for: {name}")
            print(f"Token usage: {response.usage.total_tokens}")
            sentence = response.choices[0].message.content.strip()

            startInd = sentence.find('about') + 6
            endInd = sentence.find(', I')
            target = sentence[startInd:endInd].strip()

            # Handles "their"
            if target.find('their') != -1:
                target = target.replace('their', 'the')
            # Handles mentioning of company names
            if target.find(name) != -1:
                target = target.replace(name, 'your company')
        return target

# Settings Class/Engine
class Settings:
    def __init__(self):
        connection = sqlite3.connect("assets/data.db")
        self.settingsTable = pd.read_sql(sql = "SELECT * FROM Settings;", con=connection)
        connection.close()

        self.waitTime = self.settingsTable['waitTime'][0]
        self.scrollLimit = self.settingsTable['scrollLimit'][0]
        self.tokenLimit = self.settingsTable['tokenLimit'][0]
        self.model = self.settingsTable['model'][0]
        self.apikey = self.settingsTable['apiKey'][0]

    def changeSettings(self, settingItem, newSetting):
        connection = sqlite3.connect("assets/data.db")
        cur = connection.cursor()
        if type(newSetting)==str:
            cur.execute(f"UPDATE Settings SET {settingItem} = '{newSetting}';")
        else:
            cur.execute(f"UPDATE Settings SET {settingItem} = {newSetting};")
        connection.commit()
        connection.close()
    
    def defaultSettings(self):
        connection = sqlite3.connect("assets/data.db")
        cur = connection.cursor()
        cur.execute(f"DELETE FROM Settings;")
        cur.execute(f"INSERT INTO Settings SELECT * FROM defaultSettings;")
        connection.commit()
        connection.close()

    def keepAPI(self):
        connection = sqlite3.connect("assets/data.db")
        cur = connection.cursor()
        cur.execute(f"DELETE FROM Settings;")
        cur.execute(f"INSERT INTO Settings SELECT * FROM defaultSettings;")
        cur.execute(f"UPDATE Settings SET apiKey = {self.apikey};")
        connection.commit()
        connection.close()


## Defining functionalities

# Uploading files
def fileUpload():

    #Select files
    file_path = filedialog.askopenfilename(
            title="Select a .csv or .xlsx file",
            filetypes=[("CSV or XLSX files", ".csv .xlsx")]
        )

    #Handling for excel
    if file_path.find('.xlsx') != -1:
            try:
                df = pd.read_excel(file_path)
            except:
                messagebox.showerror(
                    parent = root, 
                    title="File Read Unsuccessul", 
                    message = 'Failed to read your file. Please try again.')
                load_menuFrame()
            else:
                updateBackup(df)
                load_analysisFrame()
    #Handling for csv
    elif file_path.find('.csv') != -1:
            try:
                df = pd.read_csv(file_path)
            except:
                messagebox.showerror(
                    parent=root, 
                    title="File Read Unsuccessul", 
                    message='Failed to read your file. Please try again.')
                load_menuFrame()
            else:
                updateBackup(df)
                load_analysisFrame()
    else:
        messagebox.showinfo(
            parent=root, 
            title="No File Selected", 
            message="You didn't select a file.")
        load_menuFrame()

# Changing columns in database then return to a certain frame/execute a certain function
def changeColumn(column, item, returnfunc):
    df = loadData()
    df = df.rename(columns = {column:item})
    updateBackup(df)
    returnfunc()

# Prep Columns for Rating Scraper 
def prep_ratingScraper():
    # Data Handling
    df = loadData()
    if 'Firm Name' not in list(df.columns): 
        load_columnFrame('Firm Name', list(df.columns), prep_ratingScraper)
    elif 'Location' not in list(df.columns):
        load_columnFrame('Location', list(df.columns), prep_ratingScraper)
    else:
        load_scraperFrame("scraping ratings")

# Activate Rating Scraper
def load_RatingScraper():

    setting=Settings()
    
    df = loadData()

    notice=messagebox.showinfo(
            parent=root,
            title='Process Start',
            message='''
Scraping has begun.

The program might appear frozen. Avoid
terminating the program to not lose progress.

If you ran this program through an interpreter, 
open your terminal to see progress.''')

    # Initialize scraper
    scraper = RatingsScraperEngine(setting.waitTime)

    # Scrape
    results = df.apply(lambda row: scraper.scrape(row['Firm Name'], row['Location']), axis=1)
    cols = ['Star Ratings', 'Number of Reviews', 'Google Maps URL']
    for i in range(len(cols)):
        rowList = []
        for row in results:
            rowList.append(row[i])
        df = pd.concat([df, pd.Series(rowList, name= cols[i])], axis=1)
    updateBackup(df)

    # Extract organizations
    extraction(df, 'ratings')

# Prep Columns for Reviews Scraper 
def prep_reviewScraper():

    # Data Handling
    df = loadData()

    # Check for appropriate columns
    if 'Firm Name' not in list(df.columns): 
        load_columnFrame('Firm Name', list(df.columns), prep_reviewScraper)
    elif 'Google Maps URL' not in list(df.columns):
        load_columnFrame('Google Maps URL', list(df.columns), prep_reviewScraper)
    else:
        load_scraperFrame("scraping reviews")

# Activate Rating Scraper
def load_ReviewScraper():

    setting=Settings()

    # Load in the data
    df=loadData()

    # Notify user of scraping process
    notice=messagebox.showinfo(
            parent=root,
            title='Process Start',
            message='''
Scraping has begun.

The program might appear frozen. Do not
terminate the program to avoid losing progress.

If you ran this program through an interpreter, 
open your terminal to see progress.''')

    # Initialize scraper
    scraper=ReviewsScraperEngine(setting.waitTime, setting.scrollLimit)

    # Scrape
    df['Reviews']=df.apply(lambda row: scraper.scrape(row['Firm Name'], row['Google Maps URL']), axis=1)
    df=df.astype({'Reviews': str})
    updateBackup(df)

    # Extract organizations
    extraction(df, 'reviews')

# Prepping data for S2 Prompter
def prep_S2Prompter():
    # Data Handling
    df = loadData()

    # Check for appropriate columns
    if 'Firm Name' not in list(df.columns): 
        load_columnFrame('Firm Name', list(df.columns), prep_S2Prompter)
    elif 'Reviews' not in list(df.columns):
        load_columnFrame('Reviews', list(df.columns), prep_S2Prompter)
    else:
        load_scraperFrame("conducting sentiment analysis")

def load_S2Prompter():
    setting=Settings()
    # Load in the data
    df=loadData()
    prompter=s2Prompter(model=setting.model, apikey=setting.apikey, tokenLimit=setting.tokenLimit)

        # Notify user of scraping process
    notice=messagebox.showinfo(
            parent=root,
            title='Process Start',
            message=f'''
Prompting {setting.model}.

The program might appear frozen. Do not 
terminate the program to avoid losing progress.

If you ran this program through an interpreter, 
open your terminal to see progress.''')

    # Prompt
    df['Email Phrase']=df.apply(lambda row: prompter.prompting(row['Firm Name'], row['Reviews']), axis=1)

    if (df["Email Phrase"].isna()).all():
        error=messagebox.showerror(title='Prompting Failed',
        message="""
There has been an error with the AI model.
Please check your API Key and model name
in Settings.""")
        load_menuFrame()
    else:
        updateBackup(df)
        # Extract organizations
        extraction(df, 'emailPhrases')

# mini extraction:
def extraction_mini(df):
    version=datetime.now().strftime("%m%d%H%M")
    path=filedialog.askdirectory()
    df.to_csv(path+'/'+f'recovered_{version}', index=False)
    success=messagebox.showinfo(
            parent=root,
            title='Success',
            message=f'Successful extraction. Your file name is: receovered_{version}.csv'
        )


# Extraction Logic
def extraction(df, process):

    # Ask if user wants to extract successful scrapes
    choice=messagebox.askyesno(
        parent=root,
        title='Extract to csv?',
        message='Do you want to extract successfully scraped information to a csv file?'
    )

    # Extract if yes
    if choice:
        version=datetime.now().strftime("%m%d%H%M")
        outputName=process+'_'+version+'.csv'
        path=filedialog.askdirectory()
        df.to_csv(path+'/'+outputName, index=False)
        success=messagebox.showinfo(
            parent=root,
            title='Success',
            message=f'Successful extraction. Your file name is: {outputName}'
        )
        
    # Check for np.nan values in the dataset 
    if df.isna().any(axis=1).sum() != 0:

        #Collect failed scrapes and add to backup database
        failed=df[df.isna().any(axis=1)]
        updateFailed(failed)

        # Ask if users want to extract failed scrapes
        choice=messagebox.askyesno(
            parent=root,
            title='Extract failed to csv?',
            message='''
Do you want to extract UNsuccessfully scraped information to a csv file? 
You can also recover these organizations in the analysis page.'''
        )
        # Extract failed scrapes
        if choice:
            version=datetime.now().strftime("%m%d%H%M")
            outputName='failed'+process.title()+'_'+version+'.csv'
            path=filedialog.askdirectory()
            failed.to_csv(path+'/'+outputName, index=False)
            messageBox=messagebox.showinfo(
                parent=root,
                title='Failed Scrapes Extracted',
                message=f'Extracted failed scrapes as {outputName}.'
            )

    load_analysisFrame()

## Defining frames

# Main Menu
def load_menuFrame():

    clear(analysisFrame)
    clear(columnFrame)
    clear(scraperFrame)
    clear(settingsFrame)
    menuFrame.tkraise()
    menuFrame.pack_propagate(False)
    menuFrame.grid_propagate(False)

    # small space
    smallSpace(menuFrame, 18)

    # heading
    heading = tk.Label(
        menuFrame,
        text="Main Menu",
        bg=bg,
        fg="white",
        font=headingFont
    ).pack()

    # main text
    userManual = tk.Label(
        menuFrame,
        text ="""
    Version: 3.5.00    
    Last update: 12/28/2024

    Thanks for downloading this program! 
    Contact me at nguyenhieuhannah@gmail.com  
    for improvement ideas or bug reports.

    Visit the program's github page for a 
    detailed description of utilities and 
    licensure. 
    """,
        font = normalFont,
        justify="left",
        anchor = "w",
        bg = "white",
        fg = "black"
    ).pack(pady = 20, fill="both")


    # upload button
    uploadButton = tk.Button(
        menuFrame,
        width= 7,
        height = 1,
        text = "Upload",
        font = buttonFont,
        background = button_bg,
        fg = "white",
        cursor = "hand2",
        activebackground=buttonHover_bg,
        activeforeground="black",
        command = lambda: fileUpload()
    ).pack(padx=20, pady=5)

    # recover button
    recoverButton = tk.Button(
        menuFrame,
        width= 7,
        height = 1,
        text = "Recover",
        font = buttonFont,
        background = button_bg,
        fg = "white",
        cursor = "hand2",
        activebackground=buttonHover_bg,
        activeforeground="black",
        command = lambda: load_analysisFrame()
    ).pack(padx=20, pady=5)

    # setting button
    settingButton = tk.Button(
        menuFrame,
        width = 7,
        height = 1,
        text = "Settings",
        font = buttonFont,
        background = button_bg,
        fg = "white",
        cursor = "hand2",
        activebackground=buttonHover_bg,
        activeforeground="black",
        command = lambda: load_settingsFrame()
    ).pack(pady=5)

    smallSpace(menuFrame, 5, side=tk.BOTTOM)

# Main Analysis Tools
def load_analysisFrame():

    # Clear frames
    clear(menuFrame)
    clear(analysisFrame)
    clear(columnFrame)
    clear(scraperFrame)
    analysisFrame.tkraise()

    # Load the data
    df = loadData()

    # small space
    smallSpace(analysisFrame, 18)

    # Heading
    heading = tk.Label(
        analysisFrame, 
        text = "Analysis Tools",
        bg = bg,
        fg = "white",
        font = headingFont
    ).pack()

    smallSpace(analysisFrame, 10)

    # Preview text
    preview = tk.Label(
        analysisFrame, 
        text = "  Preview of loaded data:",
        bg = bg,
        fg = "white",
        font = boldFont,
        anchor = "w",
        justify="left"
    ).pack(fill ="both", pady=10)

    # Preview table that truncates the middle columns if df has more than 5 columns
    temp = df.copy()

    # Add an empty column to temp if df has more than 5 columns
    if df.shape[1] >5:
        temp.insert(2,"..",[".." for i in range(df.shape[0])])
        displayColumns = [0,1,2,df.shape[1]-1, df.shape[1]]
    else:
        displayColumns="#all"

    # Initializing the tree with temp
    tree = ttk.Treeview(
        analysisFrame, 
        columns=list(temp.columns), 
        show='headings',
        displaycolumns=displayColumns,
        height=5 if temp.shape[0] > 5 else temp.shape[0],
        selectmode='none'
        )
    
    # Creating the columns
    for col in temp.columns:
        tree.heading(col, text=col)
        tree.column(col, width=100, anchor='center')
    
    # Shrink the empty column 
    if df.shape[1] >5:
        tree.column('..', width=20, anchor='center')

    # Insert data into the Treeview
    for index, row in temp.iterrows():
        tree.insert("", tk.END, values=list(row))

    # Add a horizontal scrollbar
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    hsb.pack(side='bottom', fill='x')
    tree.configure(xscrollcommand=hsb.set)

    # Pack the Treeview widget
    tree.pack(fill="both")

    smallSpace(analysisFrame, 10)

    # Options text
    options = tk.Label(
        analysisFrame, 
        text = "  Options:",
        bg = bg,
        fg = "white",
        font = boldFont,
        anchor = "w",
        justify="left"
    ).pack(fill ="both",pady=10)

    option1=tk.Button(
        analysisFrame,
        text='  Step 1: Scrape Google Maps Ratings and URL',
        font=normalFont,
        background="white",
        fg="black",
        cursor="hand2",
        anchor="w",
        justify="left",
        activebackground=buttonHover_bg,
        bd=0,
        command=lambda: prep_ratingScraper()
    ).pack(fill='both', pady=0)

    # Option Review Scraper
    option2=tk.Button(
        analysisFrame,
        text='  Step 2: Scrape Google Reviews',
        font=normalFont,
        background="white",
        fg="black",
        cursor="hand2",
        anchor="w",
        justify="left",
        activebackground=buttonHover_bg,
        bd=0,
        command=lambda: prep_reviewScraper()
    ).pack(fill='both', pady=0)

    # prompt gpt-4o
    option3=tk.Button(
        analysisFrame,
        text='  Step 3: Conduct sentiment analysis with GPT-4o',
        font=normalFont,
        background="white",
        fg="black",
        cursor="hand2",
        anchor="w",
        justify="left",
        activebackground=buttonHover_bg,
        bd=0,
        command=lambda: prep_S2Prompter()
    ).pack(fill='both', pady=0)

    # extract the file to csv
    option4=tk.Button(
        analysisFrame,
        text='  Extract the current file to csv',
        font=normalFont,
        background="white",
        fg="black",
        cursor="hand2",
        anchor="w",
        justify="left",
        activebackground=buttonHover_bg,
        bd=0,
        command=lambda: extraction_mini(df)
    ).pack(fill='both', pady=0)

        # Option Rating Scraper
    option5=tk.Button(
        analysisFrame,
        text='  Recover the last batch of unsuccessful scrapes',
        font=normalFont,
        background="white",
        fg="black",
        cursor="hand2",
        anchor="w",
        justify="left",
        activebackground=buttonHover_bg,
        bd=0,
        command=lambda: loadFailed()
    ).pack(fill='both', pady=0)

    NoteMessage = tk.Label(
        analysisFrame, 
        text = "  Visit the program's github page for detailed \n  descriptions of each step.",
        bg = bg,
        fg = "white",
        font = boldFont,
        anchor = "w",
        justify="left"
    ).pack(fill ="both",pady=10)

    # go Back button
    goBack=tk.Button(
        analysisFrame,
        width=7,
        height=1,
        text="Go Back",
        font=buttonFont,
        background=button_bg,
        fg="white",
        cursor="hand2",
        activebackground=buttonHover_bg,
        activeforeground="black",
        command=lambda: load_menuFrame()
    ).pack(pady=10)

# Select column frame
def load_columnFrame(item, columns, returnfunc):
    clear(analysisFrame)
    clear(columnFrame)
    columnFrame.tkraise()

    #small space
    smallSpace(columnFrame, 18)

    # Heading
    heading = tk.Label(
        columnFrame, 
        text = "Column Select",
        bg = bg,
        fg = "white",
        font = headingFont
    ).pack()

    question = tk.Label(
        columnFrame, 
        text = f"\nWhich column contains the {item} \nof the interested organizations?\n",
        bg = bg,
        fg = "white",
        font = boldFont,        
        anchor = "center",
        justify="center"
        ).pack(fill ="both", pady=10)
    
    for column in columns:
        colButton = tk.Button(
                columnFrame,
                text=column,
                font=normalFont,
                background="white",
                fg="black",
                cursor="hand2",
                activebackground=buttonHover_bg,
                activeforeground="black",
                bd=0,
                command=lambda column=column: changeColumn(column, item, returnfunc)
            ).pack(fill='both', pady=0)

    goBack = tk.Button(
        columnFrame,
        width = 7,
        height = 1,
        text = "Go Back",
        font = buttonFont,
        background = button_bg,
        fg = "white",
        cursor = "hand2",
        activebackground=buttonHover_bg,
        activeforeground="black",
        command = lambda: load_analysisFrame()
    ).pack(side=tk.BOTTOM, pady=20)

def load_scraperFrame(process):

    # Initialize the frame
    clear(scraperFrame)
    clear(analysisFrame)
    clear(columnFrame)
    scraperFrame.tkraise()

    # Space
    smallSpace(scraperFrame, 18)

    # Heading
    heading=tk.Label(
        scraperFrame,
        text='   Processing...',
        bg=bg,
        fg="white",
        font=headingFont
    ).pack()
    
    smallSpace(scraperFrame, 10)
    
    # Warning
    warning = tk.Label(
        scraperFrame,
        text="""
    While processing, the program might appear
    frozen. You can minimize this window but do
    not terminate the program to not lose
    progress.

    If you ran the program in an interpreter, 
    open your terminal to see progress.
    """,
        font=normalFont,
        background="white",
        fg="black",
        anchor="w",
        justify="left"
    ).pack(fill='both', pady=0)

    smallSpace(scraperFrame, 10)

    # Please wait photo
    waitingPic = Image.open("assets/pleasewait.jpg")
    resized = waitingPic.resize((200, 300), Image.LANCZOS)
    waitingPic_resized = ImageTk.PhotoImage(resized)
    waitingPic_widget = tk.Label(
        scraperFrame, 
        image=waitingPic_resized, 
        bg=bg)
    waitingPic_widget.image = waitingPic_resized
    waitingPic_widget.pack(side=tk.TOP)

    smallSpace(scraperFrame,20)

    # Select next step
    if process == "scraping ratings":
        load_RatingScraper()
    elif process == "scraping reviews":
        load_ReviewScraper()
    elif process == "conducting sentiment analysis":
        load_S2Prompter()
    else:
        messagebox.showerror(
            title="Error",
            message="An error has occured. Please try again."
        )
        load_menuFrame()

# SettingsFrame
def load_settingsFrame():
    # Initialize the frame
    clear(menuFrame)
    clear(settingsFrame)
    setting=Settings()
    settingsFrame.tkraise()

        # small space
    smallSpace(settingsFrame, 18)

    # heading
    heading = tk.Label(
        settingsFrame,
        text = "Settings",
        bg = bg,
        fg = "white",
        font = headingFont
    ).pack()

    # Prints current settings
    preview = tk.Label(
        settingsFrame, 
        text = "  Current Settings:",
        bg = bg,
        fg = "white",
        font = boldFont,
        anchor = "w",
        justify="left"
    ).pack(fill ="both", pady=10)

    setting1=tk.Label(
        settingsFrame,
        text=f'  Wait Time: {setting.waitTime} seconds',
        font=normalFont,
        background="white",
        fg="black",
        anchor="w",
        justify="left"
    ).pack(fill='both', pady=0)

    setting2=tk.Label(
        settingsFrame,
        text=f'  Collection Limit: {setting.scrollLimit*10} reviews',
        font=normalFont,
        background="white",
        fg="black",
        anchor="w",
        justify="left"
    ).pack(fill='both', pady=0)

    setting3=tk.Label(
        settingsFrame,
        text=f'  Token Limit: {setting.tokenLimit} tokens',
        font=normalFont,
        background="white",
        fg="black",
        anchor="w",
        justify="left"
    ).pack(fill='both', pady=0)

    setting4=tk.Label(
        settingsFrame,
        text=f'  GPT Model: {setting.model}',
        font=normalFont,
        background="white",
        fg="black",
        anchor="w",
        justify="left"
    ).pack(fill='both', pady=0)

    setting4=tk.Label(
        settingsFrame,
        text=f'  API Key: {setting.apikey}',
        font=normalFont,
        background="white",
        fg="black",
        anchor="w",
        justify="left"
    ).pack(fill='both', pady=0)

    smallSpace(settingsFrame, 10)

    # Options text
    options = tk.Label(
        settingsFrame, 
        text = "  Options:",
        bg = bg,
        fg = "white",
        font = boldFont,
        anchor = "w",
        justify="left"
    ).pack(fill ="both",pady=10)

    option1=tk.Button(
        settingsFrame,
        text='  Change Wait Time',
        font=normalFont,
        background="white",
        fg="black",
        cursor="hand2",
        anchor="w",
        justify="left",
        activebackground=buttonHover_bg,
        bd=0,
        command=lambda: load_settingsChange('waitTime')
    ).pack(fill='both', pady=0)

    option2=tk.Button(
        settingsFrame,
        text='  Change Collection Limit',
        font=normalFont,
        background="white",
        fg="black",
        cursor="hand2",
        anchor="w",
        justify="left",
        activebackground=buttonHover_bg,
        bd=0,
        command=lambda: load_settingsChange('scrollLimit')
    ).pack(fill='both', pady=0)

    option3=tk.Button(
        settingsFrame,
        text='  Change Token Limit',
        font=normalFont,
        background="white",
        fg="black",
        cursor="hand2",
        anchor="w",
        justify="left",
        activebackground=buttonHover_bg,
        bd=0,
        command=lambda: load_settingsChange('tokenLimit')
    ).pack(fill='both', pady=0)

    option4=tk.Button(
        settingsFrame,
        text='  Change GPT Model',
        font=normalFont,
        background="white",
        fg="black",
        cursor="hand2",
        anchor="w",
        justify="left",
        activebackground=buttonHover_bg,
        bd=0,
        command=lambda: load_settingsChange('model')
    ).pack(fill='both', pady=0)

    option5=tk.Button(
        settingsFrame,
        text='  Change API Key',
        font=normalFont,
        background="white",
        fg="black",
        cursor="hand2",
        anchor="w",
        justify="left",
        activebackground=buttonHover_bg,
        bd=0,
        command=lambda: load_settingsChange('apiKey')
    ).pack(fill='both', pady=0)

    option4=tk.Button(
        settingsFrame,
        text='  Load Default Settings',
        font=normalFont,
        background="white",
        fg="black",
        cursor="hand2",
        anchor="w",
        justify="left",
        activebackground=buttonHover_bg,
        bd=0,
        command=lambda: load_default()
    ).pack(fill='both', pady=0)

    smallSpace(settingsFrame, 10)

    # go Back button
    goBack=tk.Button(
        settingsFrame,
        width=7,
        height=1,
        text="Go Back",
        font=buttonFont,
        background=button_bg,
        fg="white",
        cursor="hand2",
        activebackground=buttonHover_bg,
        activeforeground="black",
        command=lambda: load_menuFrame()
    ).pack(pady=10)

# Settings Change Frame
def load_settingsChange(settingOption):
    setting=Settings()
    while True:
        if settingOption in {'waitTime','scrollLimit', 'tokenLimit'}:
            user_input=simpledialog.askstring(title='Setting Change', prompt=\
f"""
Your input must be a numerical value.
For collection limit, the program will automatically convert your number
to an appropriate integer.

What do you want to set {var_to_str[settingOption]} to?
""")
            try:
                user_input = float(user_input)
            except:
                notice=messagebox.showerror(title='Input Error',message='Please only enter numerical values.')
                continue
            else:
                if (user_input > 20 and settingOption == 'waitTime') or (user_input > 500 and settingOption == 'scrollLimit'):
                    answer=messagebox.askyesno(title='Long Wait Time', message='This setting will result in long scraping time. Continue?')
                    if answer:
                        break
                    else:
                        continue
                elif user_input > 7000 and settingOption == 'tokenLimit':
                    answer=messagebox.askyesno(title='Costly Operation', message='This setting will result in potentially high prompting costs. Continue?')
                    if answer:
                        break
                    else:
                        continue
                else:
                    break
        elif settingOption == 'model':
            user_input=simpledialog.askstring(title='Setting Change', prompt= \
f"""
Your input must adhere to OpenAI's syntax found in this link: https://platform.openai.com/docs/models/gp (updates regularly).
Wrong syntax will result in errors while prompting.

Syntax for models relevant to this program:
- GPT-4o: 'gpt-4o'
- GPT-4o mini: 'gpt-4o-mini'
- GPT-3.5 turbo: 'gpt-3.5-turbo'

What do you want to set {var_to_str[settingOption]} to?
""")
            user_input = str(user_input).lower()
            break
        else:
            user_input=simpledialog.askstring(title='Setting Change', prompt= f"Input your API Key as is. \t\t\t\t")
            break
    if settingOption == 'scrollLimit':
        user_input /= 10
        user_input = int(user_input)
    setting.changeSettings(settingOption, user_input)
    clear(settingsFrame)
    load_settingsFrame()

# load default settings
def load_default():
    setting=Settings()
    setting.defaultSettings()
    clear(settingsFrame)
    load_settingsFrame()


## Execution of the app

# Creating root window
root = tk.Tk()
root.title('Reviews Scraper and Analysis Tool')
root.resizable(0, 0)
root.eval("tk::PlaceWindow . center")

# Initialize settings
var_to_str = {
    'waitTime': 'wait time',
    'scrollLimit': 'collection limit',
    'tokenLimit' : 'token limit',
    'model' : 'model',
    'apiKey': 'API key'
}

# Design specs
bg="#123a63"
button_bg="#6394c7"
buttonHover_bg="#b4cde5"
headingFont=font.Font(family='Open Sans', size=36, weight="bold")
buttonFont=font.Font(family='Open Sans', size=23, weight="bold")
normalFont=font.Font(family='Open Sans', size=18)
boldFont=font.Font(family='Open Sans', size=18, weight="bold")
tinyFont=font.Font(family='Open Sans', size=12)

# Calling the frames
menuFrame=tk.Frame(root, bg=bg, height=700, width=550)
analysisFrame=tk.Frame(root, bg=bg)
columnFrame=tk.Frame(root, bg=bg)
scraperFrame=tk.Frame(root, bg=bg)
settingsFrame=tk.Frame(root, bg=bg)

menuFrame.grid(row=0,column=0,sticky='nesw')
menuFrame.grid_propagate(0)
menuFrame.pack_propagate(0)

# Initialize the frames
for frame in (analysisFrame, columnFrame, scraperFrame, settingsFrame):
    frame.grid(row=0, column=0, sticky='nesw')

#start the program
load_menuFrame()

#run the app
root.mainloop()