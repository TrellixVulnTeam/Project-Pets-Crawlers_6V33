"""
Module containing the spiders for http://www.tiendapet.cl
"""
from datetime import datetime
import scrapy
from project_pets.items import ProjectPetsItem
from project_pets.spiders.utils import parse_price, parse_name


class TiendapetDogFoodSpider(scrapy.Spider):
    """ Spider only for the dog food pages """
    name = 'tiendapet_dog_food'
    allowed_domains = ['https://www.tiendapet.cl']

    start_urls = ['https://www.tiendapet.cl/catalogo/perro/alimentos']
    # start_urls = ['http://daymascotas.cl/categoria-producto/alimentos-perro/page/%s/' % page for page in range(1, 9)]

    def parse(self, response):
        for product in response.selector.css('div.block-producto'):
            scraped_product = Product()
            scraped_product.name = parse_name(product.css('h5::text').extract()[0])
            scraped_product.href = product.css('a.catalogo_click_detail::attr(href)').extract()[0]
            scraped_product.price = product.css('table').extract()[0]
            scraped_product.image_href = product.css('img::attr(src)').extract()[0]
            scraped_product.category = "food"
            scraped_product.animal = "dog"

            product_list = parse_price_table(scraped_product)

            for final_product in product_list:
                item = ProjectPetsItem()
                item['name'] = final_product.name
                item['href'] = final_product.href
                item['price'] = final_product.price
                item['image_href'] = final_product.image_href
                item['store'] = final_product.store
                item['category'] = final_product.category
                item['animal'] = final_product.animal
                item['date'] = final_product.date
                item['date_str'] = final_product.date_str

                yield item

        # next_page = response.css('.next::attr(href)').extract_first()
        # if next_page is not None:
        #     yield response.follow(next_page, callback=self.parse)


# Create a helper class to manipulate extracted data
class Product(object):
    """ Helper class to transform scraped objects """
    def __init__(self, name="", href="", price="", image_href="", category="", animal=""):
        self.name = name
        self.href = href
        self.price = price
        self.image_href = image_href
        self.store = "Tienda Pet"
        self.category = category
        self.animal = animal
        self.date = datetime.today()
        self.date_str = datetime.today().strftime('%Y-%m-%d')      

def parse_price_table(scraped_product):
    """ Transform one scraped product into as many new objectes as necessary
        depending on how many prices their table has.
        Returns an array of objects """
    # create an array to hold the new objects
    product_list = []
    # get the html contained in the price property
    html_table = scraped_product.price

    # find out how many rows the table data has
    rows = html_table.count('<tr>')
    # print(rows)
    # find out how many data points the table has.
    # If it has just one, it means the product its out of stock
    table_data_count = html_table.count('<td>')
    # print(table_data_count)
    # If it has just one data_point don't save the product and skip it.
    if table_data_count != 1:
        # iterate over the table rows to create new objects(products)
        while rows > 0:
            # print(html_table)
            # print(type(html_table))
            # locate the span tags that indicate a discount
            try:
                span_start = html_table.index('<span>')
            except ValueError:
                span_start = 0
            # span_end = html_table.index('</span>')

            # locate the first set of table data elements containing the
            # end of the product name
            start_td_name = html_table.index('<td>')
            end_td_name = html_table.index('</td>')
            # if a span exists, find out if the span belongs to the current row
            end_td_name = span_start if span_start > 0 and span_start < end_td_name else end_td_name

            # get the end part (string) of the name from the table
            name_end = html_table[start_td_name + len('<td>'):end_td_name]
            # join the main product name and the end of it
            new_name = scraped_product.name.replace('/n', '').strip() + ' ' + name_end.replace('\\n', '').strip()

            # extract the second set of td elements containing the price
            # using the end td point of the name found before
            start_td_price = html_table.index('<td>', end_td_name)
            end_td_price = html_table.index('</td>', start_td_price)
            new_price = html_table[start_td_price + len('<td>'):end_td_price]
            new_price = parse_price(new_price)

            # create the new product
            new_product = Product(new_name, scraped_product.href, new_price, scraped_product.image_href, scraped_product.category, scraped_product.animal)

            # truncate the string removing the row
            row_end = html_table.index('</tr>')
            html_table = html_table[row_end + len('</tr>'):len(html_table)]

            # save the new product and start again
            product_list.append(new_product)
            rows -= 1
            # fruit = 'Apple'
            # isApple = True if fruit == 'Apple' else False
    return product_list
    