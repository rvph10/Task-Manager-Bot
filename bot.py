import os
import time
import discord
from discord.errors import DiscordServerError, HTTPException
from bot.client import TaskBot

async def run_with_retry(bot: TaskBot, token: str, max_retries: int = 5, delay: int = 5):
    """Run the bot with retry logic for handling Discord server errors"""
    for attempt in range(max_retries):
        try:
            await bot.start(token)
            break
        except DiscordServerError as e:
            if attempt < max_retries - 1:
                print(f"Discord servers unavailable (attempt {attempt + 1}/{max_retries})")
                print(f"Error: {e}")
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("Maximum retry attempts reached. Please try again later.")
                raise
        except HTTPException as e:
            print(f"HTTP Error occurred: {e}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise

def main():
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        raise ValueError("DISCORD_TOKEN environment variable not set")
        
    bot = TaskBot()
    print('Bot is starting...')
    
    try:
        import asyncio
        asyncio.run(run_with_retry(bot, token))
    except KeyboardInterrupt:
        print("\nBot shutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()