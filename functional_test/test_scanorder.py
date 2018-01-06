import pytest
import re
from selenium import webdriver
from mixer.backend.django import mixer
pytestmark = pytest.mark.django_db  # verhindert das nix in datenbank geschrieben wird
class TestScanOrderView:
	#Warehousemaster gets delivery and wants to scan them
	#to a specific order
	def test_scan_order(self):
		#Warehousemaster opens webpage and clicks on order
		browser = webdriver.Firefox()
		browser.get('http://127.0.0.1:8000/order/')
		# He now clicks on 'Bestellung anlegen' 
		#because he wants to create a new order
		btns = browser.find_elements_by_tag_name("a")

		for btn in btns:
			if btn.text == "Bestellung anlegen":
				btn.click()
				break


		# Now he has to login
		# fakeuser = mixer.blend("auth.User")
		if "login" in browser.current_url:

			user_field = browser.find_element_by_id("id_username")
			password_field = browser.find_element_by_id("id_password")

			if user_field and password_field:
				user_field.send_keys("mbijou")
				password_field.send_keys("erpghost")

				inputs = browser.find_elements_by_tag_name("input")

				for input_ in inputs:
					if input_.get_attribute("type") == "submit":
						login_btn = input_
						login_btn.click()
						break


		# # Warehousemaster opens webpage of specific order
		# browser = webdriver.Firefox()
		# browser.get('http://127.0.0.1:8000/order/2')
		# assert 'ERPGhost' in browser.title, "Should be ERPGhost in title"
		# # Warehousemaster clicks on Scan Button to start scanning products
		# # and gets redirected to Scanning Page
		# button = browser.find_element_by_id('scan_btn')
		# button.click()

		# scan_page_url = browser.current_url
		# REGEX = re.search('scan/$', scan_page_url)
		# assert REGEX != None , "Should append scan to url"

		# # warehousemaster looking for input field to scan product
		# # inputfield should be already focused onload
		# # he scans a product, product appears in input field
		# test_value = "1234"
		# body = browser.find_element_by_tag_name('body')
		# match_product_input = browser.find_element_by_id("product_match")
		# body.send_keys(test_value)
		# match_product_value = match_product_input.get_attribute('value')
		# assert test_value == match_product_value, "Should be same value as in Input"

		# # product typed in not matched
		# # sees exception "Eine EAN ist 13-Stellig"
		# assert "Eine EAN ist 13-Stellig" in browser.page_source, "Should be true"

		# # clears field because he typed in wrong input by cicking on clear button
		# button = browser.find_element_by_id('clearMatchField')
		# button.click()

		# # now he looks in a table for the rows to match that ean which are not confirmed
		# tbody = browser.find_element_by_tag_name('tbody')
		# trs = tbody.find_elements_by_tag_name('tr')
		# assert trs != None, "Should not be None"
		# confirmation = None
		# for r in trs:
		# 	# if it is None he scans the product
		# 	confirmed_td = r.find_elements_by_tag_name("td")[2]
		# 	product_td = r.find_elements_by_tag_name("td")[0]
		# 	if confirmed_td.text == 'None':
		# 		confirmation = confirmed_td.text
		# 		# now he scans the product in the row
		# 		body.send_keys(product_td.text)
		# 		assert "Eine EAN ist 13-Stellig" not in browser.page_source, "This error message should not be on page"

		# # He sees a product that is not confirmed
		# if confirmation:

		# 	# now he gets a match and clicks on YES and checks if first
		# 	# product is confirmed or not and he sees that is not confirmed
		# 	# assert td.text == 'None', "Should be None it should not be confirmed"

		# 	# now he clicks on yes to confirm that product
		# 	buttons = body.find_elements_by_tag_name("button")
		# 	confirm_btn = None
		# 	for button in buttons:
		# 		if button.get_attribute('innerHTML') == "Ja":
		# 			confirm_btn = button
		# 	confirm_btn.click()

		# 	# SEITE WIRD NEU GELADEN

		# 	tbody = browser.find_element_by_tag_name("tbody")
		# 	trs = tbody.find_elements_by_tag_name("tr")
			
		# 	new_confirmation = None

		# 	for tr in trs:
		# 		td_confirmation = tr.find_elements_by_tag_name("td")[2]

		# 	new_confirmation = td_confirmation
		# 	# VERGLEICHEN OB EIN NONE BESTÄTIGT WURDE		
		# 	assert new_confirmation != 'None', "confirmed should be now confirmed or not confirmed"
		# # He sees all products confirmed
		# else: # neue Bestellung erzeugen und scannen
		# 	pass
