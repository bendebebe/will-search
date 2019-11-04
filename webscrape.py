import ast, csv, json, os, re, sys, time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

#set up selenium webdriver to automate button clicks
options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument("--test-type")
path = os.path.join(os.getcwd(), 'chromedriver')
options.headless = False
browser = webdriver.Chrome(options=options, executable_path=path)
browser.get('http://www3.nccde.org/will/search/')

# find search input boxes
year = browser.find_element_by_id('ctl00_ctl00_ContentPlaceHolder1_ContentPlaceHolder1__TextBoxYear')
month = browser.find_element_by_id('ctl00_ctl00_ContentPlaceHolder1_ContentPlaceHolder1__TextBoxMonth')
day = browser.find_element_by_id('ctl00_ctl00_ContentPlaceHolder1_ContentPlaceHolder1__TextBoxDay')

# prompt use input for year month and day on the command line
input_year, input_month, input_day = None, None, None
while (True):
    input_year = raw_input('Type a year to search: ')
    if (input_year):
        break
    else:
        print('Error: A year is required to search, please try again.')

input_month = raw_input('Type a month (1-12) to search (press enter to leave blank): ')
if(input_month):
    input_day = raw_input('Type a day (1-31) to search (press enter to leave blank): ')

year.send_keys(input_year)
if (input_month): month.send_keys(input_month)
if (input_day): day.send_keys(input_day)
year.send_keys(Keys.ENTER)

src = browser.page_source

text_found = re.search(r'(There are).*(items matching your search criteria)', src)

if (text_found.group(0) == 'There are 0 items matching your search criteria'):
    print('Try again')

x = 1
data = []


table_len = len(browser.find_element_by_xpath("//table[@class='grid']").find_elements_by_xpath(".//tr"))

for r in range(1, table_len):
    table = browser.find_element_by_xpath("//table[@class='grid']")
    keys = ['Last', 'First', 'Middle']
    vals = []
    if (len(table.find_elements_by_xpath(".//tr")) <= 1):
        pass
    tds = table.find_elements_by_xpath(".//tr")[r].text.split(' ')
    for td in range(1, len(tds)-1):
        vals.append(tds[td])
    output_row = dict(zip(keys,vals))
    
    row = browser.find_element_by_xpath("//table[@class='grid']").find_elements_by_xpath(".//tr")[r]
    
    td = row.find_elements_by_xpath(".//td")[0]
    found_link = False
    try:
        details_btn = td.find_element_by_xpath(".//a")
        details_btn.click()
        found_link = True
    except:
        found_link = False
    if (found_link):
        # extract will info
        tables = browser.find_elements_by_xpath(".//table")
        for table in tables:
            for sub_row in table.find_elements_by_xpath(".//tr"):
                pairs = []
                cols = sub_row.find_elements_by_tag_name("td")
                for td in cols:
                    pairs.append(td.text)
                if len(pairs) == 2 and pairs[0] != "":
                    if pairs[0][-1] == ":":
                        output_row[pairs[0][:-1]] = pairs[1]
                    else:
                        output_row[pairs[0]] = pairs[1]
                elif len(pairs) > 2:
                    val = ''
                    for s in pairs[1:]:
                        val += (s + " ")
                    output_row['Personal Representatives Name'] = pairs[0]
                    output_row['Address'] = val
                elif len(pairs) == 1:
                    output_row['Attorney Info'] = pairs[0]
                else:
                    # implement "View Affadvit Details"
                    pass
        if browser.current_url !=  "http://www3.nccde.org/will/search/":       
            browser.execute_script("window.history.go(-1)")
    data.append(output_row)

browser.close()

filename = 'will-search_' + input_year
if (input_month): filename += '-' + input_month
if (input_day): filename += '-' + input_day

filename += '.csv'
with open(filename, mode='w') as file:
    fieldnames = ["Date of Death", "First", "Middle", "Last", "Will File #", "Inventory Due Date", "Date Inventory Filed", "Decedent Address", "Opening Deputy", "Closing Deputy", "Other Info", "Claims", "Personal Representatives Name", "Address", "Attorney Info"]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    for row in data:
        new_row = {k: v for k, v in row.items() if k in fieldnames}
        not_new_row = {k: v for k, v in row.items() if k not in fieldnames}
        writer.writerow(new_row)

print ('Scraping successfully outputed to file: %s') % filename