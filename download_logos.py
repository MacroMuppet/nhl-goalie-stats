#!/usr/bin/env python3
import os
import aiohttp
import asyncio

# Create a list of NHL team shortcodes
TEAM_CODES = [
    'ANA', 'BOS', 'BUF', 'CAR', 'CBJ', 'CGY', 'CHI', 'COL',
    'DAL', 'DET', 'EDM', 'FLA', 'LAK', 'MIN', 'MTL', 'NJD',
    'NSH', 'NYI', 'NYR', 'OTT', 'PHI', 'PIT', 'SEA', 'SJS',
    'STL', 'TBL', 'TOR', 'VAN', 'VGK', 'WPG', 'WSH', 'ARI'
]

async def download_logo(session, team_code, logos_dir):
    url = f"https://assets.nhle.com/logos/nhl/svg/{team_code}_light.svg"
    filename = os.path.join(logos_dir, f"{team_code}_light.svg")
    
    try:
        async with session.get(url) as response:
            if response.status == 200:
                content = await response.read()
                with open(filename, 'wb') as f:
                    f.write(content)
                print(f"Successfully downloaded {team_code} logo")
            else:
                print(f"Failed to download {team_code} logo: Status {response.status}")
    except Exception as e:
        print(f"Error downloading {team_code} logo: {str(e)}")

async def main():
    # Create Logos directory if it doesn't exist
    logos_dir = "Logos"
    os.makedirs(logos_dir, exist_ok=True)
    
    print(f"Created directory: {logos_dir}")
    print("Starting logo downloads...")
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for team_code in TEAM_CODES:
            task = download_logo(session, team_code, logos_dir)
            tasks.append(task)
        
        await asyncio.gather(*tasks)
    
    print("\nDownload complete! Check the 'Logos' directory for the team logos.")

if __name__ == "__main__":
    asyncio.run(main()) 