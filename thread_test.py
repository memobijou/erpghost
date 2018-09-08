import threading
import time

class EbayThread(threading.Thread):
	def __init__(self, seconds):
		super().__init__()
		self.seconds = seconds
	def run(self):
		print("Ebay Task Running")
		time.sleep(self.seconds)
		print("Ebay Task Ending")

class AmazonThread(threading.Thread):
	def __init__(self, seconds):
		super().__init__()
		self.seconds = seconds
	def run(self):
		print("Amazon Task Running")
		time.sleep(self.seconds)
		print("Amazon Task Ending")

amazon_thread, ebay_thread = AmazonThread(30), EbayThread(20)
threads = [amazon_thread, ebay_thread]

amazon_thread.start()
ebay_thread.start()

# wait for all threads to complete
for t in threads:
	t.join()
print("Finished allllll")

