
# START


# IMPORTS

# For Selenium:
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
# For Scrapy:
import scrapy
from scrapy import Selector
# For making a CSV File:
import csv
# For making the Process WAIT:
import time

# Global Variable Definitions:
search_query = dict()
search_query['link'] = 'https://www.federalreserve.gov/start-job-search.htm'
chrome_path = 'emptor\\chromedriver.exe'
job_categories = ["All", "Accounting", "Administrative", "Architecture/Engineering", "EEO", 
                  "Attorney", "Bank Examiner", "Business Analyst", "Computer Professional",
                  "Economist", "Computer Support", "Editors/Writers", "Financial Analyst",
                  "Governors", "Graphic Design", "Health Services", "Human Resources",
                  "Interns", "Mail Services and Supply", "Other Clerical-Acctg/Payroll",
                  "Other Clerical-Administration", "Other Clerical-Bldg Services", 
                  "Other Clerical-ComputerSupport", "Other Clerical-Finance/Bus An",
                  "Other Clerical Food Services", "Other Clerical-Graphics", "Other Clerical-HR",
                  "Other Clerical-Mail Svc/Supply", "Other Clerical-Other", "Other Clerical-PR/Writ/Edit",
                  "Other Clerical-Purchasing", "Other Clerical-Training", "Other Professional",
                  "Public Relations", "Purchasing", "Research Assistant", "Security Administration",
                  "Security Escort", "Secrtry/Steno/Clerk Typ/Recept", "Security Admin Support",
                  "Security", "Trade/Crafts-Eng/Plant", "Trade/Crafts-Food Service", "Trade/Crafts-Maintenance",
                  "Trade/Crafts-Other", "Trade/Crafts-Print/Litho", "Trade/Crafts-Postal/Supply", "Training" 
                  ]

# Function which will fill the form using the keywords and category passed and submit it in selenium:
def fill_form(data, driver):
	WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "advancedSearchInterface.keywordInput"))).send_keys(data['keywords'])
	select = Select(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "advancedSearchInterface.jobfield1L1"))))
	select.select_by_visible_text(data['category'])
	WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "advancedSearchFooterInterface.searchAction"))).click()

# Function which will parse through the HTML and Extract the required information:
def get_output(page_src, n, driver):
	for_name = "requisitionListInterface.reqTitleLinkAction.row"
	for_cnv = "requisitionListInterface.reqContestNumberValue.row"
	for_location = "requisitionListInterface.reqBasicLocation.row"
	for_date = "requisitionListInterface.reqPostingDate.row"
	name = []
	cnv = []
	dates = []
	location = []
	for i in range(1,n+1):
		name.append(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, for_name+str(i)))).text)
		cnv.append(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, for_cnv+str(i)))).text)
		dates.append(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, for_date+str(i)))).text)
		location.append(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, for_location+str(i)))).text)

	return name,cnv,dates,location

# Spider Defenition:
class fed_reserve_jobs(scrapy.Spider):
    # Name of the Spider:
    name = "fed_reserve_jobs" 

    # Spider's Initialization Function:
    def __init__(self,category='',keywords='', *args,**kwargs):
    	
    	# In order to change the values of the global variables:
    	global search_query
    	global job_categories

    	super(fed_reserve_jobs, self).__init__(*args, **kwargs)
    	self.kw = keywords
    	self.jc = category
    	search_query['keywords'] = self.kw
    	search_query['category'] = self.jc

    	# Checking if the job category given as input exists [ Will EXIT if the Job Category does not exist]:
    	temp = 1
    	if search_query['category'] == "":
    		search_query['category'] = "All"
    	for i in range(len(job_categories)):
    		if search_query['category'] == job_categories[i]:
    			temp=2
    			break
    	if temp ==1:
    		print("\n job category does not exist")
    		exit()

    	# Saves the Search Query in a .TXT file:
    	f = open("search_queries.txt","w+")
    	f.write("\n Keywords: " + search_query['keywords'] + "\n Job Category: " + search_query['category'] + "\n Link Scraped: " + search_query['link'])
    	f.close()

    # Spider's Start Requestion function:
    def start_requests(self):
    	global search_query
    	yield scrapy.Request(url=search_query['link'], callback=self.parse)

    # Spider's Parse Function:
    def parse(self, response):
    	
    	# In Order to Use the value of the global variable:
    	global chrome_path

    	page = response.url.split("/")[-2]

    	# Extracts the second url present in the iframe element:
    	iframe_url = response.css('iframe').xpath('@src').extract()[0]

    	# Need to now open selenium with the iframe_url = "https://frbog.taleo.net/careersection/1/moresearch.ftl?lang=en&portal=101430233":
    	driver = webdriver.Chrome(chrome_path)
    	driver.get(iframe_url)
    	data = { 'keywords': search_query['keywords'], 'category': search_query['category'] }
    	fill_form(data,driver)

    	# To ensure that the page loads fully before we extract the required information:
    	time.sleep(5)

    	# Stores the Page_source of the page in a .HTML File:
    	f = open("iframe_src.html","w+")
    	f.write(driver.page_source)
    	f.close()

    	# TO Find the Number of Results:
    	n_results = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "requisitionListInterface.ID3798"))).text
    	temp1 = n_results.split('(')
    	if n_results == temp1[0]: # When Number of Results (Jobs Found) = 0
    		number_of_results = 0
    		n_results = "Search Results : No Jobs Found with the given criteria"
    	else: # When Number of Results (Jobs Found) > 0
    		temp2 = temp1[1].split(' ')
    		number_of_results = int(temp2[0])

    	# To Find The Required Information, Call the Get_output() function:
    	name,cnv,posted_date,location = get_output(driver.page_source, number_of_results, driver)

    	# Closes the Webpage and The Driver is Shut Down:
    	driver.quit()

    	# Writes the reulsts line in the search_queries.txt File:
    	f = open("search_queries.txt", "a")
    	f.write("\n\n " + n_results)
    	f.close()

    	# To create a .TXT File with the Required Extracted Data:
    	f = open("output_data.txt", "w+")
    	f.write("\nNumber of Jobs Found: " + str(number_of_results))
    	for i in range(number_of_results):
    		f.write("\n" + str(i+1) + "\n Job Description: " + str(name[i]) + "\n Contest Number Value: " + str(cnv[i]) + "\n Posted on Date: " + str(posted_date[i]) + "\n location: "+ str(location[i]) + str("\n"))
    	f.close()

# END