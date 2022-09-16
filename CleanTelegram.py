import os
from time                                    import sleep
from selenium                                import webdriver
from selenium.webdriver.common.by            import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui           import WebDriverWait
from selenium.webdriver.common.keys          import Keys
from selenium.webdriver.support              import expected_conditions as ec

def anonym_browser(save_cookies=False):
    # Setting up browser, cookie saving, reducing bot detection.
    options = webdriver.ChromeOptions()
    dir_path = os.getcwd()

    if save_cookies:
        
        profile = os.path.join(dir_path, "profile", "TelegramBotProfile")

        options.add_argument(
            r'user-data-dir={}'.format(profile))

    options.add_argument("window-size=1280,720")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/99.0.4844.84 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_experimental_option('useAutomationExtension', False)

    browser = webdriver.Chrome(options=options, executable_path="driver/chromedriver.exe")
    browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    
    "source": """

    Object.defineProperty(navigator, 'webdriver', {

    get: () => undefined

    })

    """

    })

    browser.execute_cdp_cmd('Network.setUserAgentOverride',
                            {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, '
                             'like Gecko) Chrome/83.0.4103.53 Safari/537.36'})

    return browser

div_dict =     {"search"          :'//input[contains(@class, "input-field-input")]'                   ,
                "contact"         :'//a[contains(@class, "chatlist-chat rp")]'                       ,
                "data_id"         :"data-mid"                                                         ,
                "messages_div"    :"//div[contains(@class, 'bubble-content')]/parent::div/parent::div",
                "forward_search"  :'//input[contains(@class, "selector-search-input i18n")]'          ,
                "forward_contact" :"//div[contains(@class, 'sidebar-left-section-content')]/ul/a"    ,
                "hide"            :'//*[@id="column-center"]/div/div[2]/div[4]/div/div[1]/div/div[2]/div[2]/form[1]/div[2]',
                "send_button"     :'//*[@id="column-center"]/div[1]/div[2]/div[4]/div/div[5]/button'  ,
                "arrow_class"     :"bubble-beside-button.forward"                                     ,
                "forward_contacts":'chatlist-chat'}


class TelegramBot():

    def __init__(self, input_contact, output_contact, cookies):

        self.browser            = anonym_browser(save_cookies=cookies)
        self.input_contact      = input_contact
        self.output_contact      = output_contact
        self.wait               = WebDriverWait(self.browser, 10)
        self.chain              = ActionChains(self.browser)
        self.key                = Keys()
        self.last_output_id = ""
        self.last_input_id  = ""
        self.paths = div_dict
    
    def run(self):
        self.connect()
        while True:
            self.listening()
            self.send_new_msgs()

    def connect(self):
        telegram_connected = False
        self.browser.get("https://web.telegram.org/k")

        print("Waiting Conection, please scan QR CODE\n")

        while not telegram_connected:
            try:
                self.wait.until(ec.visibility_of_element_located((By.XPATH, self.paths["search"])))
                telegram_connected = True
                print("Connected to Telegram.\n")
            except:
                print("Not possible to stablish a connection, trying again.\n")
                continue

    def search_contact(self, contact_to_search):
        sleep(0.5)
        print(f"Searching for: {contact_to_search} in contact list\n")
        while True:
            try:
                # Search contact in the search box.
                searcher_box = self.browser.find_element(by = By.XPATH, value = self.paths["search"])
                searcher_box.clear()
                searcher_box.send_keys(contact_to_search)
                
                sleep(1)
                # Waiting for all the contact divs to show up.
                self.wait.until(ec.presence_of_all_elements_located((By.XPATH, self.paths["contact"])))

                # Using a method to return a list with all contacts rectangles divs.
                resultant_contacts_divs = self.find_contacts_divs()

                # Iterating through list and veryfing contact.
                for contact_object in resultant_contacts_divs:

                    if contact_to_search in contact_object.text:
                        print("Found contact! Returning it\n")

                        return contact_object
            except:
                print("Found no contact with the specified name, trying again.\n")


    def find_contacts_divs(self):
        self.wait.until(ec.presence_of_all_elements_located((     By.XPATH, self.paths["contact"])))
        contacts_div_list = self.browser.find_elements(by = By.XPATH, value = self.paths["contact"])
        
        return contacts_div_list


    def listening(self):
        sleep(0.5)

        self.search_click(self.input_contact)

        print("Waiting for new messages on the input contact.\n")

        sleep(1)

        last_div           = self.find_text_divs()
        self.last_input_id = last_div.get_attribute(self.paths["data_id"])

        while self.last_input_id == self.last_output_id:

            last_div              = self.find_text_divs()
            self.last_input_id    = last_div.get_attribute(self.paths["data_id"])

        print("Found a new message\n"                             )
        print(f"Last id sent from the input: {self.last_input_id}")
        print(f"Last id sent to the output:\n {self.last_output_id}")

    def search_click(self, contact_name):
        contact_to_click = self.search_contact(contact_name)
        contact_to_click.click()

    def send_new_msgs(self):

        '''if self.last_output_id == "":
            self.last_output_id = self.last_input_id
            print("First message ignored\n")
            return'''

        print("Sending new message\n")
        
        last_div            = self.find_text_divs()

        self.last_output_id = last_div.get_attribute(self.paths["data_id"])

        self.forward_message(last_div)


    def find_text_divs(self):
        self.wait.until(ec.presence_of_all_elements_located((      By.XPATH, self.paths["messages_div"])))
        messages_div_list  = self.browser.find_elements(by = By.XPATH, value = self.paths["messages_div"])

        # Since we need to check the new messages first, the list needs to be flipped.

        return messages_div_list[-1]


    def forward_message(self, text_div):

        self.hover_and_execute(text_div)

        search_box = self.browser.find_element(by = By.XPATH, value = self.paths["forward_search"])
        self.wait.until(ec.visibility_of(search_box))
        search_box.send_keys(self.output_contact)

        sleep(1)
        contact_button = self.browser.find_element(by = By.XPATH, value = self.paths["forward_contact"])
        self.chain.move_to_element(contact_button).perform()
        self.chain.click       (on_element = None).perform()

        sleep(2)
        text_box = self.browser.find_element(by = By.XPATH, value = '//*[@id="column-center"]/div/div[2]/div[4]/div/div[1]/div/div[2]/div[1]/div[2]')
        self.chain.move_to_element(text_box).perform()
        self.wait.until(ec.presence_of_element_located((By.CLASS_NAME, "btn-menu.active")))

        self.wait = WebDriverWait(self.browser, 2)
        
        hide = self.browser.find_element(by = By.XPATH, value = self.paths["hide"])
        self.wait.until(ec.visibility_of(hide))
        hide.click()

        self.wait    = WebDriverWait(self.browser, 10)
        send_button  = self.browser.find_element(by = By.XPATH, value = self.paths["send_button"])
        send_button.click()


    def hover_and_execute(self, text_div):

        self.chain.move_to_element(text_div).perform()
        arrow_button = text_div.find_element(by=By.CLASS_NAME, value = self.paths["arrow_class"])
        arrow_button.click()
        self.wait.until(ec.presence_of_all_elements_located((By.CLASS_NAME, self.paths["forward_contacts"])))

