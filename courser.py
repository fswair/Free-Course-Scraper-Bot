from datetime import datetime
import os, json, asyncio, re, time
from pyrogram import *
from functions import *
from apscheduler.schedulers.asyncio import AsyncIOScheduler as AIS

### SESSION AREA - BEGIN ###
session="CourseBot"
api_hash="your api_hash"
api_id=123456 # your api_id
config = Config(api_hash=api_hash, api_id=api_id, bot_token="your_token")
app: Client = config.setclient()

base = Courses()
base.__create__()
### SESSION AREA - END  ###

if not base.__get__():
    print("Database have no data. Courses are fetching..")
    add_courses()
print("All courses saved to database. Client starting...")


@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    start_text = config.start_scheme
    print(f"{message.from_user.first_name} started the bot...")
    await asyncio.sleep(2)
    await app.send_message(message.chat.id, text=start_text, reply_to_message_id=message.id, disable_web_page_preview=1)
@app.on_message(filters.command("get") & filters.private)
async def getcourses(client, message):
    print(f'{message.from_user.first_name} ({message.from_user.username or message.from_user.id}) gave "{message.text}" command..')
    base = Courses().__get__()
    plaintext = ""
    id, urls, course_content, csv_content, json_content, date, timestamp  = base.id, base.urls, base.course_content, base.csv_content, base.json_content, base.date, base.timestamp
    if len(message.command) > 1:
        with open(f"{message.from_user.id}.csv", "w", encoding="utf8") as csv:
            csv.write(str(csv_content))
        with open(f"{message.from_user.id}.json", "w", encoding="utf8") as json:
            json.write(str(json_content))
        with open(f"{message.from_user.id}.txt", "w", encoding="utf8") as plain:
            for x in list(eval(urls)):
                plaintext += f'{x}\n'
            plain.write(plaintext)
        
        await asyncio.sleep(2)

        if re.match(f"^[\W]get (json)$", message.text):
            await app.send_document(message.chat.id, document=f"{message.from_user.id}.json", file_name="courses.json", caption=f"@{config.credit_channel}")
        elif re.match(f"^[\W]get (csv)$", message.text):
            await app.send_document(message.chat.id, document=f"{message.from_user.id}.csv", file_name="courses.csv", caption=f"@{config.credit_channel}")
        elif re.match(f"^[\W]get (txt)$", message.text):
            await app.send_document(message.chat.id, document=f"{message.from_user.id}.txt", file_name="courses.txt", caption=f"@{config.credit_channel}")

        os.remove(f"{message.from_user.id}.csv")
        os.remove(f"{message.from_user.id}.json")
        os.remove(f"{message.from_user.id}.txt")
    else:
        await asyncio.sleep(1)
        await app.send_message(message.chat.id, text=course_content, reply_to_message_id=message.id)




scheduler = AIS(timezone=config.timezone)
scheduler.add_job(func=lambda: course_sender(app=app), trigger="interval", hours=config.send_every_hour)
scheduler.start()

update_scheduler = AIS(timezone="Europe/Istanbul")
update_scheduler.add_job(func=add_courses, trigger="interval", minutes=config.check_every_minute)
update_scheduler.start()

trash_scheduler = AIS(timezone="Europe/Istanbul")
trash_scheduler.add_job(func=lambda: delete(base=base), trigger="interval", minutes=config.check_every_minute)
trash_scheduler.start()
app.run()
