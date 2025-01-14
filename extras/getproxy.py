import re, threading
from libs.mbrowser import mBrowser
from utils.utils import printf, die
from cores.actions import fread, fwrite
from utils.progressbar import progress_bar
import data

try:
	from Queue import Queue
except ImportError:
	from queue import Queue
"""
support url:
https://free-proxy-list.net/
"""

ROOT_FOLDER = data.__path__[0]
PROXY_PATH = "%s%s" %(ROOT_FOLDER, "/listproxy.txt")
LIVE_PATH = "%s%s" %(ROOT_FOLDER, "/liveproxy.txt")

def livelist():
	return fread(LIVE_PATH).split("\n")

def getlist():
	return fread(PROXY_PATH).split("\n")

def getnew(options):
	def parse_proxy(response):
		try:
			re_ip = r"\b(?:\d{1,3}\.){3}\d{1,3}\b<\/td><td>\d{1,5}"
			result = re.findall(re_ip, response, re.MULTILINE)
			result = [element.replace("</td><td>", ":") for element in result]
			return result
		except Exception as error:
			die("[x] GetProxy: Error while parsing proxies.", error)
			
	def checkProxyConnProvider(url = "https://free-proxy-list.net/"):
		try:
			printf("[+] Getting proxy list from %s" %(url))

			getproxy = mBrowser()

			getproxy.open(url)
			printf("[*] Gathering proxies completed.", "good")
			return getproxy.get_resp()

		except Exception as error:
			die("[x] GetProxy: Error while connecting to proxy server!", error)
		finally:
			getproxy.close()
			

	try:
		listproxy = parse_proxy(checkProxyConnProvider())
	except Exception as error:
		printf("[x] Getproxy.getnew: %s" %(error))
		listproxy = ""
	finally:
		try:
			listproxy = "\n".join(listproxy)
			printf("[*] Get %s proxies." %(len(listproxy)), "good")
			printf("[+] Saving to %s" %(PROXY_PATH))
			fwrite(PROXY_PATH, listproxy)
			printf("[*] Data saved!", "good")

		except Exception as error:
			die("[x] GetProxy: Error while writting data", error)


def check(options):
	
	def run_threads(threads, sending, completed, total):
		# Run threads
		for thread in threads:
			sending += 1 # Sending
			progress_bar(sending, completed, total)
			thread.start()

		# Wait for threads completed
		for thread in threads:
			completed += 1
			progress_bar(sending, completed, total)
			thread.join()
		
		return sending, completed

	def checProxyConn(proxyAddr, target, result, verbose):
		try:
			proxyTest = mBrowser()
			proxyTest.setproxy(proxyAddr)

			if verbose:
				printf("[+] Trying: %s" %(proxyAddr))

			proxyTest.open(options.url)

			if verbose:
				printf("[*] Success: %s" %(proxyAddr), "good")
			result.put(proxyAddr)

		except Exception as error:
			if verbose:
				printf("[x] %s %s" %(proxyAddr, error), "bad")
		finally:
			try:
				proxyTest.close()
			except:
				pass
	try:
		proxylist = fread(PROXY_PATH).split("\n")
				
		workers, result = [], Queue()
		trying, completed, total = 0, 0, len(proxylist)

		for tryProxy in proxylist:
			if len(workers) == options.threads:
				trying, completed = run_threads(workers, trying, completed, total)
				del workers[:]
			
			worker = threading.Thread(
				target = checProxyConn,
				args = (tryProxy, options.url, result, options.verbose)
			)

			worker.daemon = True
			workers.append(worker)
			
		trying, completed = run_threads(workers, trying, completed, total)
		del workers[:]

	except KeyboardInterrupt as error:
		printf("[x] Terminated by user!", "bad")
		import os
		os._exit(0)
	
	except Exception as error:
		die("[x] GetProxy: Error while checking proxy connection to target", error)

	finally:
		try:
			_data = "\n".join(list(result.queue))
			printf("[*] %s proxies worked." %(len(_data)), "good")
			printf("[+] Write working proxies")
			fwrite(LIVE_PATH, _data)
			printf("[*] Write working proxies completed", "good")
		except Exception as err:
			die("[x] GetProxy: Error while writing result", err)