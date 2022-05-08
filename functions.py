from datetime import datetime
import os, json, asyncio, re, time
from random import randint
from sqlite3 import connect
import pyrogram
from requests import get
from pyrogram import *
from apscheduler.schedulers.asyncio import AsyncIOScheduler as AIS


months = re.findall("(\w+)", "Ocak Şubat Mart Nisan Mayıs Haziran Temmuz Ağustos Eylül Ekim Kasım Aralık")

con = connect("courses.db", check_same_thread=0)
cursor = con.cursor()


class Config:
    def __init__(self, session_name: str = "CourseBot", api_id: int = None, api_hash: str = None, bot_token: str = None, start_scheme: str = None, credit_channel: str = "herkesicinudemy", tzinfo: str = "Europe/Istanbul") -> pyrogram.Client:
        self.name = session_name
        self.api_id = api_id
        self.api_hash = api_hash
        self.token = bot_token
        self.check_every_minute = 15
        self.send_every_hour = 5
        self.timezone = tzinfo
        self.start_scheme = f"Selam, ücretsiz kurslara erişmek için ```/get``` komutunu kullanmalısınız.\n\nEğer csv veya json formatında çıktı isterseniz:\n\n```/get json``` veya ```/get csv``` komutunu verebilirsiniz.\n\nGeri bildirim için **[buradan](https://t.me/theliec)** iletişime geçebilirsiniz. "
        self.credit_channel = credit_channel
    def setclient(self):
        return pyrogram.Client(name=self.name, api_id=self.api_id, api_hash=self.api_hash, bot_token=self.token)


class Courses:
    def __init__(self, id: int = 0, urls:list[str] = [], course_content: str = "", csv_content:str = "", json_content:str = "", date: str = "", timestamp: int = 0) -> None:
        self.id = id
        self.urls = urls
        self.course_content = course_content
        self.csv_content = csv_content
        self.json_content = json_content
        self.date = date
        self.timestamp = timestamp
    
    def __create__(self, status: bool = True):
        cursor.execute("CREATE TABLE IF NOT EXISTS courses (id int, urls text, course_content text, csv_content text, json_content text, date text, timestamp int) ")
    def __add__(self):
        urls = str(self.urls).replace("'", '"')
        csv_content = str(self.csv_content).replace("'", '"')
        json_content = str(self.json_content).replace("'", '"')
        course_content = str(self.course_content).replace("'", '"')
        cursor.execute(f"INSERT INTO courses VALUES ({self.id}, '{urls}', '{course_content}','{csv_content}', '{json_content}', '{self.date}', {self.timestamp} )")
        con.commit()
    def __get__(self):
        try:
            args = cursor.execute("SELECT * from courses ORDER BY timestamp").fetchall()[-1]
            return Courses(*args)
        except:
            return False
    
    def __delete__(all: bool = False):
        cursor.execute(f"DELETE FROM courses where timestamp < {time.time() - 7200}")
        con.commit()


def get_courses(start=1, stop=3, config: Config = None):
    all_content = ""

    for i in range(start, stop):
        main = str(get(f"https://www.discudemy.com/language/english/{i}").content)
        all_content += main

    courses = [course for course in re.findall(
        'class="card-header"[ ?\W?]{1,}href="(.*?)"', all_content
    )]

    links = []
    for course in courses:
        alias = re.split("/", course)[-1]
        request = re.findall('<a id="couponLink" href="(.*?)"',str(get(f"https://discudemy.com/go/{alias.lower().strip()}").content))
        if len(request) > 0:
            if "couponCode" in request[0]:
                credit = config.credit_channel if config else "herkesicinudemy"
                link = str(request[0]).replace("?", f"?via=@{credit.lower()}&")
                links.append(link)
    
    return links



def get_informations(url, *args, options=0):
    ### PAGE SOURCE ###
    stack = str(get(url).content)
    
    ### DEFINES FOR PARSED ELEMENTS ###
    title = re.findall('data-purpose="lead-title">(.*?)</h1>', stack)[0]
    desc = re.findall('data-purpose="lead-headline">(.*?)</div>', stack)[0]
    rating = re.findall('data-purpose="rating-number">(.*?)</span>', stack)[0]
    rating = re.findall("(\d)[\.\,]?", rating)[0]
    instructor = re.findall("""<div class="udlite-heading-lg udlite-link-underline instructor--instructor__title--34ItB"><a href=".*?">(.*?)</a></div>""", stack)[0]
    instructor = instructor[:instructor.find("(")].strip()
    
    variables = [(title, "title"), (desc, "desc"), (rating, "rating"), (instructor, "instructor")]

    if options:
        return [arg[0] for arg in variables if arg[1] in args]
    return [title, desc, url, rating, instructor]

def pattern_creator(title, description, rate, url, language):
      return   f"""💫 **{title}**\n\n📝 __{description}__\n\n🔗 **{url}**\n\n✨ __Puan: {rate}/5 \n\n🌎 Dil: {language}\n\n[Altyazı Yöntemleri](https://t.me/herkesicinudemy/556)\n\n**@herkesicinudemy | @herkesicinegitim**"""

def add_courses(chat: str = "herkesicinudemy", bot: str = "herkesicinudemy_bot"):
    csv_fn = f"courses.csv"
    json_fn = f"courses.json"
    if os.path.isfile(csv_fn): os.remove(csv_fn)
    if os.path.isfile(json_fn): os.remove(json_fn)
    links = get_courses(stop=4)
    data = dict()
    json_content = ""
    csv_content = ""
    csv_content += "title, description, url, rating, instructor\n"
    for link in links:
        csv_content += "'{}','{}','{}',{},'{}'".format(*get_informations(link))
        csv_content += '\n'
    
    for i, link in enumerate(links):
        title, description, url, rating, instructor = get_informations(link)
        data[f'{i}'] = {"title":title, "description":description, "url": url, "rating":int(rating), "instructor":instructor}

    json_content += str(json.dumps(data))

    scheme = ""
    for i, link in enumerate(links):
        title, description, url, rating, instructor = get_informations(link)
        scheme += f"**[{i+1}. {title}]({link})**\n\n"
    scheme += f"__Made with Python by @theliec__\n\n@{chat.lower()}\n@{bot.lower()}"
    
    base = Courses(id=randint(10000, 999999), urls=links, course_content=scheme, csv_content=csv_content, json_content=json_content, date=datetime.now(), timestamp=time.time())
    base.__add__()



def course_sender(app: pyrogram.Client, chat: str = "herkesicinudemy", bot: str = "herkesicinudemy_bot", links: list = None, return_scheme: bool = False):
        if not links:
            links = get_courses()
        
        with app:
            date = datetime.now()
            start_message = f"{date.day} {months[date.month-1]} {date.year} tarihine ait ücretsiz eğitimler birazdan paylaşılmaya başlanacaktır.\n\nKurslardan bazıları ücretli olabilir, kontrol edin.\n\n**@herkesicinudemy | @herkesicinegitim**"
            app.send_message(chat, text=start_message)
            time.sleep(15)
            
            for link in links:
                time.sleep(2)
                desen = pattern_creator(*get_informations(link, "title", "desc", "rating", options=1), url=link, language="İngilizce")
                app.send_message(chat, text=desen)
                time.sleep(4)
        if return_scheme:
            scheme = ""
            for i, link in enumerate(links):
                title, description, url, rating, instructor = get_informations(link)
                scheme += f"**[{i+1}. {title}]({link})**\n\n"
            scheme += f"__Made with Python by @theliec__\n\n@{chat}\n@{bot}"

            return scheme

def delete(base: Courses = Courses()):
    base.__delete__()
    
