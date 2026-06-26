import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient

# 1. Setup Structured Ingestion Logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename=f"logs/scraping_{datetime.now().strftime('%Y%m%d')}.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 2. Extract Infrastructure Credentials
load_dotenv()
API_ID = os.getenv("TG_API_ID")
API_HASH = os.getenv("TG_API_HASH")
PHONE = os.getenv("TG_PHONE")

if not API_ID or not API_HASH:
    logger.critical("Initialization Failed: Missing TG_API_ID or TG_API_HASH in .env")
    raise ValueError("API credentials missing inside the root .env file configuration.")

# Exact verified public Telegram handles for the targeted Ethiopian medical businesses
CHANNELS = ["CheMed123", "lobelia4cosmetics", "tikvahpharma"]

async def scrape_channel(client, channel_username, limit=1000):
    """
    Extracts high-volume historical message records and associated media assets 
    from a public channel, appending directly into a partitioned raw Data Lake.
    """
    logger.info(f"Initiating extraction sequence for: {channel_username}")
    print(f"\n🚀 Scraping Channel: {channel_username} (Targeting up to {limit} messages)")
    
    scraped_count = 0
    
    try:
        # Resolve target channel entity via public handle
        entity = await client.get_entity(channel_username)
        
        async for message in client.iter_messages(entity, limit=limit):
            msg_date = message.date if message.date else datetime.now()
            date_str = msg_date.strftime("%Y-%m-%d")
            
            image_path = None
            has_media = False
            
            # Extract and store uncompressed visual assets for downstream YOLO validation
            if message.photo:
                has_media = True
                img_dir = f"data/raw/images/{channel_username}"
                os.makedirs(img_dir, exist_ok=True)
                image_path = f"{img_dir}/{message.id}.jpg"
                
                # Deduplication check to optimize bandwidth usage
                if not os.path.exists(image_path):
                    await client.download_media(message.photo, file=image_path)
                    logger.debug(f"Media downloaded successfully for msg_id: {message.id}")

            # Mapping structure adhering strictly to analytical pipeline requirements
            record = {
                "message_id": message.id,
                "channel_name": channel_username,
                "message_date": msg_date.isoformat(),
                "message_text": message.text if message.text else "",
                "has_media": has_media,
                "image_path": image_path,
                "views": message.views if message.views else 0,
                "forwards": message.forwards if message.forwards else 0
            }
            
            # Define Data Lake partition pathway (YYYY-MM-DD hierarchy)
            lake_dir = f"data/raw/telegram_messages/{date_str}"
            os.makedirs(lake_dir, exist_ok=True)
            lake_file = f"{lake_dir}/{channel_username}.json"
            
            # Atomic Read-and-Append block to safely merge data falling on identical dates
            current_day_data = []
            if os.path.exists(lake_file):
                try:
                    with open(lake_file, "r", encoding="utf-8") as rf:
                        current_day_data = json.load(rf)
                        # Avoid duplicating identical message IDs during backfills
                        if any(item['message_id'] == message.id for item in current_day_data):
                            continue
                except json.JSONDecodeError:
                    current_day_data = []
            
            current_day_data.append(record)
            
            with open(lake_file, "w", encoding="utf-8") as wf:
                json.dump(current_day_data, wf, ensure_ascii=False, indent=4)
                
            scraped_count += 1
            if scraped_count % 100 == 0:
                print(f"   ↳ Progress status: Cached {scraped_count} records...")

        logger.info(f"Extraction successful: Parsed {scraped_count} records from {channel_username}.")
        print(f"✅ Success! Collected {scraped_count} entries from {channel_username}.")

    except Exception as e:
        logger.error(f"Incomplete extraction for handle '{channel_username}': {str(e)}")
        print(f"❌ Failed to extract '{channel_username}'. Review logs directory for raw exception logs.")

async def main():
    # Construct authenticated client session architecture
    client = TelegramClient('kara_scraper_session', int(API_ID), API_HASH)
    await client.start(phone=PHONE)
    
    print("====== Kara Solutions: Processing Data Lake Raw Ingestion Layer ======")
    for channel in CHANNELS:
        await scrape_channel(client, channel, limit=1000)
        
    await client.disconnect()
    print("\n🏁 Data collection complete. Multi-channel raw data lake partition initialized.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())