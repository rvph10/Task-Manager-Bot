import os
from bot.client import TaskBot

def main():    
    bot = TaskBot()
    print('Bot is running...')
    bot.run(os.getenv('DISCORD_TOKEN'))

if __name__ == "__main__":
    main()