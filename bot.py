import os
from bot.client import TaskBot
from dotenv import load_dotenv

def main():
    if os.getenv('DEV'):
        load_dotenv('.env.dev')
    else:
        load_dotenv('.env.dev')
        
    bot = TaskBot()
    print('Bot is running...')
    bot.run(os.getenv('DISCORD_TOKEN'))

if __name__ == "__main__":
    main()