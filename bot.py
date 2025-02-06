from bot.client import TaskBot
from config import DISCORD_TOKEN

def main():
    bot = TaskBot()
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()