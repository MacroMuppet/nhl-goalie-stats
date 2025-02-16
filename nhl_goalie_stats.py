#!/usr/bin/env python3
import pandas as pd
import asyncio
import aiohttp
import json
import svgwrite
from svgwrite import cm, mm
import base64
from PIL import Image
import io

# Add team secondary colors dictionary
TEAM_COLORS = {
    'WPG': '#7B303E',  # Dark Red
    'WSH': '#C8102E',  # Red
    'LAK': '#A2AAAD',  # Silver
    'TBL': '#00205B',  # Dark Blue
    'COL': '#236192',  # Steel Blue
    'SEA': '#99D9D9',  # Ice Blue
    'OTT': '#C69214',  # Gold
    'ANA': '#B5985A',  # Vegas Gold
    'MIN': '#C51230',  # Red
    'CGY': '#F1BE48'   # Gold
}

async def get_nhl_data():
    # NHL Stats API endpoint for goalie stats
    url = "https://api.nhle.com/stats/rest/en/goalie/summary"
    params = {
        "isAggregate": "false",
        "isGame": "false",
        "sort": "[{\"property\":\"savePct\",\"direction\":\"DESC\"}]",
        "start": 0,
        "limit": 50,
        "factCayenneExp": "gamesPlayed>=19",
        "cayenneExp": "gameTypeId=2 and seasonId=20242025"
    }
    
    print("Fetching data from NHL API...")
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                
                if 'data' not in data:
                    print("Warning: Unexpected API response format")
                    print("Response:", data)
                    return pd.DataFrame()
                
                # Convert to DataFrame
                df = pd.DataFrame(data['data'])
                
                if df.empty:
                    print("Warning: No data returned from API")
                    return df
                
                # Print column names for debugging
                print("\nAvailable columns:", df.columns.tolist())
                
                # Rename columns (using actual column names from the API)
                df = df.rename(columns={
                    'goalieFullName': 'Full_Name',
                    'lastName': 'Last_Name',
                    'gamesPlayed': 'Games_Played',
                    'savePct': 'Save_Percentage',
                    'teamAbbrevs': 'Team'
                })
                
                # Create formatted name (First initial + Last name)
                df['Name'] = df['Full_Name'].apply(lambda x: f"{x.split()[0][0]}. {x.split()[-1]}")
                
                # For players with multiple teams, use their current team (last one in the list)
                df['Current_Team'] = df['Team'].apply(lambda x: x.split(',')[-1].strip())
                
                # Select only the columns we need
                df = df[['Name', 'Games_Played', 'Save_Percentage', 'Team', 'Current_Team']]
                
                print(f"\nSuccessfully retrieved data for {len(df)} goalies")
                
                # Print first few rows for verification
                print("\nFirst few rows of data:")
                print(df.head().to_string())
                
                return df
            else:
                print(f"Error: API returned status code {response.status}")
                return pd.DataFrame()

def get_team_logo_base64(team_code, background_color):
    """Load team logo and convert to base64 for SVG embedding with specified background color"""
    jpg_path = f"Logos_JPG/{team_code}_light.jpg"
    try:
        with Image.open(jpg_path) as img:
            # Convert to RGBA to handle transparency
            img = img.convert('RGBA')
            
            # Create a new image with the specified background color
            background = Image.new('RGBA', img.size, background_color)
            
            # Convert white and near-white pixels to transparent
            data = img.getdata()
            new_data = []
            for item in data:
                # If pixel is white or very close to white, make it transparent
                if item[0] > 240 and item[1] > 240 and item[2] > 240:
                    new_data.append((0, 0, 0, 0))  # Transparent
                else:
                    new_data.append(item)
            
            img.putdata(new_data)
            
            # Composite the logo onto the colored background
            composite = Image.alpha_composite(background, img)
            
            # Convert back to RGB for JPEG
            final_img = composite.convert('RGB')
            
            # Save to bytes
            buffer = io.BytesIO()
            final_img.save(buffer, format='JPEG', quality=95)
            return base64.b64encode(buffer.getvalue()).decode()
    except Exception as e:
        print(f"Error loading logo for {team_code}: {str(e)}")
        return None

def create_save_percentage_graph(df):
    # Get top 10 goalies by save percentage
    top_10 = df.nlargest(10, 'Save_Percentage')
    
    # Convert save percentages to actual percentages for display
    save_pcts_pct = top_10['Save_Percentage'] * 100
    
    # SVG dimensions and margins
    width = 1200
    height = 600
    margin = {'top': 60, 'right': 40, 'bottom': 100, 'left': 60}
    
    # Calculate plot area dimensions
    plot_width = width - margin['left'] - margin['right']
    plot_height = height - margin['top'] - margin['bottom']
    
    # Create SVG document
    dwg = svgwrite.Drawing('nhl_goalie_save_percentages.svg', size=(width, height))
    
    # Add white background
    dwg.add(dwg.rect(insert=(0, 0), size=(width, height), fill='white'))
    
    # Calculate scales
    bar_width = plot_width / len(top_10) * 0.8
    x_spacing = plot_width / len(top_10)
    
    min_save = min(save_pcts_pct)
    max_save = max(save_pcts_pct)
    y_scale = plot_height / (max_save - min_save + 0.4)  # Add padding
    
    # Add title
    dwg.add(dwg.text('Top 10 NHL Goalies by Save Percentage (2024-25 Season)',
                     insert=(width/2, margin['top']/2),
                     text_anchor='middle',
                     font_size=20,
                     font_family='Arial'))
    dwg.add(dwg.text('Min 19 Games',
                     insert=(width/2, margin['top']/2 + 25),
                     text_anchor='middle',
                     font_size=16,
                     font_family='Arial'))
    
    # Add y-axis
    dwg.add(dwg.line(start=(margin['left'], margin['top']),
                     end=(margin['left'], height-margin['bottom']),
                     stroke='black',
                     stroke_width=1))
    
    # Add y-axis labels and grid lines
    y_ticks = 5
    for i in range(y_ticks + 1):
        y_val = min_save - 0.2 + (max_save - min_save + 0.4) * i / y_ticks
        y_pos = height - margin['bottom'] - (y_val - (min_save - 0.2)) * y_scale
        
        # Grid line
        dwg.add(dwg.line(start=(margin['left'], y_pos),
                        end=(width-margin['right'], y_pos),
                        stroke='lightgray',
                        stroke_width=1,
                        stroke_dasharray='5,5'))
        
        # Y-axis label
        dwg.add(dwg.text(f'{y_val:.2f}%',
                        insert=(margin['left'] - 10, y_pos),
                        text_anchor='end',
                        dominant_baseline='middle',
                        font_size=12,
                        font_family='Arial'))
    
    # Add bars with team logos
    for i, (_, row) in enumerate(top_10.iterrows()):
        x = margin['left'] + i * x_spacing + (x_spacing - bar_width) / 2
        y_val = row['Save_Percentage'] * 100
        bar_height = (y_val - (min_save - 0.2)) * y_scale
        y = height - margin['bottom'] - bar_height
        
        team_code = row['Current_Team']
        team_color = TEAM_COLORS.get(team_code, '#808080')  # Default to gray if color not found
        
        # Convert hex color to RGB tuple for PIL
        hex_color = team_color.lstrip('#')
        rgb_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4)) + (255,)  # Add alpha channel
        
        # Create pattern with team logo
        logo_base64 = get_team_logo_base64(team_code, rgb_color)
        if logo_base64:
            pattern = dwg.pattern(id=f'logo-{i}',
                                insert=(x, y),
                                size=(bar_width, bar_height),
                                patternUnits="userSpaceOnUse")
            
            # Add colored background to pattern with 100% opacity
            pattern.add(dwg.rect(insert=(0, 0),
                               size=(bar_width, bar_height),
                               fill=team_color,
                               fill_opacity=1.0))  # Changed from 0.8 to 1.0
            
            # Add logo on top of background
            pattern.add(dwg.image(f'data:image/jpeg;base64,{logo_base64}',
                                insert=(0, 0),
                                size=(bar_width, bar_height)))
            dwg.defs.add(pattern)
            
            # Add bar with pattern fill
            dwg.add(dwg.rect(insert=(x, y),
                           size=(bar_width, bar_height),
                           fill=f'url(#logo-{i})',
                           stroke='gray',
                           stroke_width=1))
        
        # Add value label
        dwg.add(dwg.text(f'{y_val:.2f}%',
                        insert=(x + bar_width/2, y - 5),
                        text_anchor='middle',
                        font_size=12,
                        font_family='Arial'))
        
        # Add x-axis label (goalie name)
        dwg.add(dwg.text(row['Name'],
                        insert=(x + bar_width/2, height-margin['bottom'] + 35),
                        text_anchor='end',
                        transform=f'rotate(-45, {x + bar_width/2}, {height-margin["bottom"] + 35})',
                        font_size=12,
                        font_family='Arial'))
    
    # Save the SVG
    dwg.save()
    print("\nGraph has been saved as 'nhl_goalie_save_percentages.svg'")
    
    # Print the data
    print("\nTop 10 Goalies by Save Percentage:")
    print(top_10[['Name', 'Team', 'Save_Percentage', 'Games_Played']].to_string(index=False))

async def main():
    try:
        # Get and process the data
        df = await get_nhl_data()
        
        if df.empty:
            print("No data was found. Please check if the API is accessible.")
            return
        
        # Create and save the graph
        print("\nCreating visualization...")
        create_save_percentage_graph(df)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 