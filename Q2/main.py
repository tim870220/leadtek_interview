from bs4 import BeautifulSoup
import csv
import datetime
import mariadb
from mariadb import Error
import asyncio
import time
import logging
from pyppeteer import launch


class GpuScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        self.log_file = 'scraper.log'
        logging.basicConfig(filename=self.log_file, level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')
        self.conn = mariadb.connect(
            user="root",
            password="00000000",
            host="localhost",
            port=3306,
            database="leadtek"
        )
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        try:
            self.cursor.execute(
                "CREATE TABLE IF NOT EXISTS gpu (SID INT AUTO_INCREMENT PRIMARY KEY, DATETIME DATETIME, ITEM VARCHAR(255), PRICE INT)")
            logging.info("MariaDB table created successfully!")
        except mariadb.Error as error:
            logging.error(f"Error creating MariaDB table: {error}")

    def run(self,page_text, product_name):
        soup = BeautifulSoup(page_text, 'html.parser')
        gpu_list = soup.find_all('dl', class_='col3f')
        print('gpu_list',len(gpu_list))
        for gpu in gpu_list:
            name = gpu.find('h5')
            if name and product_name in name.text:
                price = gpu.find('span', class_='value')
                if price:
                    self.write_to_csv(name.text, price.text)
                    self.write_to_database(name.text, int(price.text))
                    logging.info(f"{name.text}: {price.text}")

    def write_to_csv(self, item, price):
        with open('gpu_prices.csv', mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), item, price])
            logging.info("Data written to CSV successfully!")

    def write_to_database(self, item, price):
        try:
            self.cursor.execute(
                f"INSERT INTO gpu (DATETIME, ITEM, PRICE) VALUES ('{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}', '{item}', {price});")
            self.conn.commit()
            logging.info("Data written to MariaDB successfully!")
        except mariadb.Error as error:
            self.conn.rollback()
            logging.error(f"Error writing data to MariaDB: {error}")
        
    def __del__(self):
        self.cursor.close()
        self.conn.close()

async def main():
    url = 'https://ecshweb.pchome.com.tw/search/v3.3/?q=RTX%204080&scope=all'
    product_name = '4080'
    browser = await launch(headless = True)
    page = await browser.newPage()
    await page.goto(url)
    time.sleep(1)
    page_text = await page.content()
    # print(page_text)
    await browser.close()
    scraper = GpuScraper()
    scraper.run(page_text, product_name)
    

asyncio.run(main())
