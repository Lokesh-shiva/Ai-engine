from instabot import Bot

def post_to_instagram(username, password, photo_path, caption):
    bot = Bot()
    bot.login(username=username, password=password)
    bot.upload_photo(photo_path, caption=caption)

if __name__ == "__main__":
    post_to_instagram("your_username", "your_password", "trend_video.jpg", "Check out the latest AI trends!")