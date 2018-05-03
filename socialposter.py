#!/usr/bin/python
#-*- coding:utf-8 -*-

import os,sys,time,random,getopt

from selenium import webdriver

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains    

from selenium.common.exceptions import TimeoutException

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

try:
	from twisted.python import log
except:
	class Log(object):
		def msg(self,arg):
			pass
		def err(self):
			pass

	log = Log()

class Poster(object):
	def usage(self):
		pass

	def login(self):
		pass

	def parse_opt(self,argv):
		pass
		
	def check_before_post(self):
		pass

	def publish(self):
		pass

	def get_pic_element(self):
		pass
	
	def get_text_element(self):
		pass		


PICTURE_FILE_EXTS = ["jpg","jpeg","png","gif","bmp"]

class SocialPoster(Poster):

	#social media user name
	_user = None

	#social media user password
	_passwd = None

	#content to be posted
	_content = None

	#pictures dir to be load from your computer
	_picdir = None
	
	#how many pictures to be posted
	_picnum = 0

	_headless = 1

	_options = None

	#browser type
	_type = "chrome"

	_driver = None

	_userdatadir = None

	_display = None

	def __init__(self,argv):

		#argv can be a string, such as "ls -al *.txt"
		if type(argv) in [ type(""),type(u"")]:
			argv = argv.split("")
		
		self._parse_opt(argv)

	def _load_content_from_file(self,filename):
		import codecs
		f = codecs.open(filename,'r','utf-8')
		self._content = f.readlines()
		f.close()

	def _parse_opt(self,argv):

		shortargs = 'u:p:c:t:f:b:r:j:n:hw'
		
		longargs = ['name=', 'password=', 'file=','picdir=','picnum=',
					'browser=','user-data-dir=','content=','tag=','help','window']
		
		opts,args= getopt.getopt( argv, shortargs, longargs)

		for opt,arg in opts:
			
			#print "OPT:",opt
			#print "ARG:",arg

			if opt in ('-h','--help'):
				self.usage()
			
			elif opt in ('-w','--window'):
				#start x windows mode
				self._headless = 0
			
			elif opt in ('-u','--name'):
				#login user name
				self._user = arg
			
			elif opt in ('-p','--password'):
				#login user password
				self._passwd = arg
			
			elif opt in ('-c','--content'):
				#content to be posted
				if type(arg) != type(u""):
					arg = arg.decode("utf-8")
				
				#也许参数中存有'\n'这种字符，非转义字符
				arg = arg.replace("\\n","\n")

				#convert to list
				self._content = arg.split("\n")
			
			elif opt in ('-r','-user-data-dir'):
				#set browser data directory
				self._userdatadir = arg
			
			elif opt in ('-f','--file'):
				#load conent from a file
				if self._content is None:
					self._load_content_from_file(arg)
			
			elif opt in ('-j','--picdir'):
				#picture directory
				self._picdir = arg

			elif opt in ('-n','--picnum'):
				self._picnum = int(arg)

			elif opt in ('-b','--browser'):
				#browser type
				self._type = arg

			else:
				self.parse_opt(argv)

	def _open(self):
		
		assert ( self._type in ['firefox','chrome'] )

		if self._type == "chrome":
			options = webdriver.ChromeOptions()
		else:
			options = webdriver.FirefoxOptions()

		if self._headless:

			from pyvirtualdisplay import Display

			#start virutal display
			self._display = Display(visible=0, size=(800, 800))  
			self._display.start()
			
			options.add_argument('--headless')
			options.add_argument('--disable-gpu')

			if self._type == "chrome":
				options.add_argument('--no-sandbox')
		

		if self._type == "chrome":
			
			if self._userdatadir is None:
				#default user data dir is $HOME/.config/google-chrome
				self._userdatadir =  os.path.join(os.environ['HOME'],
					".config","google-chrome")
			
			options.add_argument('--use-data-dir=%s' % self._userdatadir)

			self._driver = webdriver.Chrome(chrome_options = options)
		
		else:
			
			if self._userdatadir == None:

				import ConfigParser

				profileini = os.path.join(os.environ['HOME'],
					".mozilla/firefox/profiles.ini")

				iniparser = ConfigParser.ConfigParser()
				iniparser.read(profileini)

				path = iniparser.get("Profile0","Path")

				if path and len(path)>0:
					self._userdatadir = os.path.join(os.environ['HOME'],
						".mozilla/firefox",path)

					print("set user data dir to default dir : [%s]" % self._userdatadir)

			if self._userdatadir:		
				fp = webdriver.FirefoxProfile(self._userdatadir)
				self._driver = webdriver.Firefox(fp,firefox_options = options)
			else:
				self._driver = webdriver.Firefox(firefox_options = options)


		return self._driver


	def _check(self):
		assert( self._content != None)
		self.check_before_post()

	def _post_pictures(self,element):

		if self._picdir == None or len(self._picdir) == 0:
			return


		import re

		#picdir can be "dir1|dir2|dir3"
		picdirs = self._picdir.split("|")

		files = []

		#load original picture files 
		for picdir in picdirs:
			
			picfiles = None

			try:
				tempfiles = os.listdir(picdir)

				temppicfiles = []

				for filename in tempfiles:
					filename = filename.strip()

					extension = re.findall("\.(\w+)$",filename)
					
					if(len(extension) == 1) and (extension[0] in PICTURE_FILE_EXTS):
						temppicfiles.append(filename)

				if len(temppicfiles) > 0:
					#files must be the absolute file 
					picfiles = map(lambda val : os.path.join(picdir,val) , temppicfiles)
			
			except:
				log.err()
			else:
				if picfiles: files.extend(picfiles)

		#随机冲洗几次，以保证图片的随机性
		shuffleno = 3
		for i in range(shuffleno):
			random.shuffle(files)

		#随机抽取其中几张，最多是maxpicsinapost张
		maxpicsinapost = 9
		if self._picnum > 0:
			maxpicsinapost = min(maxpicsinapost, self._picnum)

		#sample from picture files	
		picfiles = random.sample(files, min(len(files),maxpicsinapost ) )

		index = 1

		#add pictures to html element
		for picfilename in picfiles:
			element.send_keys(picfilename)
			
			print("add picture[%d]:%s" % (index,picfilename))
			index += 1

			#for uploading
			time.sleep(3)
		
		#waiting for all pictures have been uploaded.
		secondsforuploading = len(picfiles) * 3
		print("waiting for %d seconds to upload..." % secondsforuploading)
		time.sleep(secondsforuploading )

	def _post_content(self,element):

		print "add text:",
		
		for content in self._content:
			
			if len(content) > 0:
				element.send_keys(content)
				print content
			else:
				element.send_keys(Keys.ENTER)


	def _close(self):

		if self._driver:
			self._driver.close()
			print("browser driver closed.")

		if self._display:
			self._display.stop()
			print("virutal display closed")

	def login_and_post(self):

		self._check()

		isok = False
		
		try:
			#启动浏览器
			print('starting browser %s' % self._type)
			self._open()
			print('started browser.')

			#登陆社交平台
			self.login()

			#发布文字
			textelm = self.get_text_element()
			self._post_content(textelm)

			#发布图片
			picelm = self.get_pic_element()
			self._post_pictures(picelm)

			#发布完成后处理
			self.publish()
			print "posted a message:%s" % self._content

			time.sleep(3)

			isok = True

		except:
			log.err()

		finally:
			self._close()
			return isok



class WeiboPoster(SocialPoster):
	
	__website = "https://www.weibo.com"
	
	_type = "firefox"

	_max_trying_num = 3

	def usage(self):
		print "Usage:%s -c content -t tag" % sys.argv[0]
		print "\t-content xxxxx -tag  xxxxx"
		sys.exit(1)

	def get_pic_element(self):
		return self._driver.find_element_by_xpath("//input[@name='pic1' and @type='file']")

	def get_text_element(self):
		return self._driver.find_element_by_css_selector("textarea.W_input")

	def login(self):
		
		tryagain = 0
		
		while tryagain < self._max_trying_num:
		
			try: 		
		
				print("open website [%s]." % self.__website)
				self._driver.get(self.__website)
				print("opened, now the url is [%s]" % self._driver.current_url)

				#check we are in and if the web contains a form to be posted.
				WebDriverWait(self._driver, 10).until(lambda driver: 
					driver.find_element_by_css_selector("textarea.W_input"))

				break

			except:
				tryagain += 1
				print("try to login again,num=%d" % tryagain)
				log.err()
		
	def publish(self):
		self._driver.find_element_by_css_selector(".W_btn_a.btn_30px").click()


class ToutiaoPoster(SocialPoster):
	
	_max_trying_num = 3
	_web_site = "https://www.toutiao.com"

	def check_before_post(self):
		assert(self._user is not None)
		assert(self._passwd is not None)


	def _login_with_user_passwd(self):
		print("login qq with user(%s)..." % (self._user))

		#input user name
		self._driver.find_element_by_xpath("//input[@id='u' and @type='text']").clear()
		userelm = self._driver.find_element_by_xpath("//input[@id='u' and @type='text']")
		
		for ch in self._user:
			userelm.send_keys(ch)
			time.sleep( random.random() / 2)

		time.sleep(2)

		#input user password
		self._driver.find_element_by_xpath("//input[@id='p' and @type='password']").clear()
		passwdelm = self._driver.find_element_by_xpath("//input[@id='p' and @type='password']")
		
		for ch in self._passwd:
			passwdelm.send_keys(ch)
			time.sleep( random.random() / 2)

		time.sleep(2)

		#login toutiao with the QQ
		self._driver.find_element_by_xpath("//div[@id='go']").click()


	def login(self):
		
		tryagain = 0
		
		while tryagain < self._max_trying_num:
		
			try:
				
				print("try to get web:%s" % self._web_site)
				self._driver.get(self._web_site)
				print("got web,url is [%s]" % self._driver.current_url)

				print("try to find qq login entry...")
				self._driver.find_element_by_xpath("//li[@class='sns qq']").click()
				print("we found qq entry and try to login with qq...")

				WebDriverWait(self._driver, 10).until(lambda driver: driver.find_element_by_id("u"))
				print("qq login url is %s" % self._driver.current_url)

				self._login_with_user_passwd()

				#waiting for the direction to toutiao website
				waitseconds = 60
				print("login to qq for %d seconds..." % waitseconds)
				
				WebDriverWait(self._driver, waitseconds).until(
					EC.presence_of_element_located((By.XPATH,"//a[@class='tb-link']")))

				print("toutiao login is ok, url is %s" % self._driver.current_url)

				#open the toutiao post window
				self._driver.find_element_by_xpath("//a[@class='tb-link']").click()

				time.sleep(3)

				#jump to poster window
				self._driver.switch_to_window(self._driver.window_handles[1])

				WebDriverWait(self._driver, 10).until(
					EC.presence_of_element_located((By.XPATH,"//*[@name='title']")))

				#we are in,all is ok!
				break

			except:
				log.err()
				tryagain += 1
				print("try again,num:%d" % tryagain)

	
	def get_text_element(self):
		return self._driver.find_element_by_xpath("//*[@name='title']")

	def get_pic_element(self):
		return self._driver.find_element_by_id('fileElem')

	def publish(self):
		self._driver.find_element_by_xpath("//a[@class='upload-publish active']").click()


def post_weibo(argv):
	weibo = WeiboPoster(argv)
	weibo.login_and_post()

def post_toutiao(argv):
	toutiao = ToutiaoPoster(argv)
	toutiao.login_and_post()


if __name__ == "__main__":

	try:
		from twisted.python import log
		log.startLogging(sys.stdout)
	except:
		pass

	media = sys.argv[1]
	assert(media in ("weibo","toutiao"))

	argv = sys.argv[2:]

	if media == "weibo":
		post_weibo(argv)
	else:
		post_toutiao(argv)
