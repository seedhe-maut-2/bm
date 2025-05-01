from pyrogram import Client

api_id = 22625636
api_hash = "f71778a6e1e102f33ccc4aee3b5cc697"

app = Client("my_session", api_id, api_hash)

with app:
    msg = app.get_messages("hvuvvivkvmbihlhivticutxcy", 16)
    if msg.video:
        msg.download(file_name="video.mp4")
        print("वीडियो डाउनलोड हो गया!")
    else:
        print("वीडियो नहीं मिला")
