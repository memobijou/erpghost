import pytest
from selenium import webdriver
import os


class TestStockView:

    def test_stock_view(self):
        # Kemal has an excel sheet and wants to upload
        # so he goes on erpghost and clicks on stock menuitem
        browser = webdriver.Firefox()
        browser.get('http://127.0.0.1:8000/')
        assert "ERPGhost" in browser.title, "ERPGhost should be in title"

        menu_items = browser.find_element_by_id("myNavbar")
        menu_items = menu_items.find_elements_by_tag_name("li")

        item_names = []
        for item in menu_items:
            if item.text == "Inventar":
                inventar_item = item
            item_names.append(item.text)

        assert "Inventar" in item_names, "Inventar should be in menu items"

        inventar_item.click()

        assert "Inventar" in browser.title, "Invetar should be in title"

        bodyText = browser.find_element_by_tag_name('body').text

        if "Kein Eintrag vorhanden" in bodyText:
            assert "Kein Eintrag vorhanden" in bodyText, "Kein Eintrag should be in bodyText"

        inventar_btn = browser.find_element_by_id("btn_new_inventar")
        inventar_btn.click()

        assert "Neues Inventar" in browser.title, "'Neues Inventar' should be in title"

        # USE CASE 1:

        # he gets to the stock page and sees the table has no entries
        # now he wants to import his latest excel sheet into the system
        # so he clicks on a button 'Import CSV'

        # now he gets redirected to a new page
        # he sees a button 'Suche Datei' he clicks on it
        # and an file manager opens and he can select on excelfile
        browser.find_element_by_id("id_document").send_keys(os.getcwd() + "/documents/image.png")

        btn = browser.find_element_by_id("btn_upload")

        btn.click()

        assert "Detailansicht" in browser.title, "Should be Detailansicht in title"

# now he sees the select file with the filename

# MAIN USE CASE 1
# he sees the filename and it is the correct file to upload
# then he clicks on upload

# gets redirected to detail view
# sees notification

# USE CASE 1
# He sees the excelfile he uploaded and he can open it
# He sees delete button and can

# USE CASE 1
# DELETE THE WHOLE STOCK
# redirected to main view of stock

## MAIN USE CASE 2

# USE CASE 2
# click on back button and get 
# redirected to main view of stock
## MAIN USE CASE 2

# USE CASE 2
# not success marked red in box

# USE CASE 2
# He sees the filename but it is not the correct file
# he clicks on a button 'Clear' where he can delete the file

# MAIN USE CASE 2:
# he gets to the stock page and sees entries of stocks
