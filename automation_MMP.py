import asyncio
import os
import re
from playwright.async_api import async_playwright
from datetime import datetime, timedelta
import time

#------------------week logic------------------------------

# Get today's date
today = datetime.today()
# Find the start of the current week (Monday)
start_of_current_week = today - timedelta(days=today.weekday())
# Find the end of the current week (Sunday)
end_of_current_week = start_of_current_week + timedelta(days=6)
# Find the start of the previous week
start_of_previous_week = start_of_current_week - timedelta(days=7)
# Find the end of the previous week
end_of_previous_week = end_of_current_week - timedelta(days=7)
# Format dates as -mm-dd strings
start_current_week = start_of_current_week.strftime("-%m-%d")
end_current_week = end_of_current_week.strftime("-%m-%d")
start_previous_week = start_of_previous_week.strftime("-%m-%d")
end_previous_week = end_of_previous_week.strftime("-%m-%d")
# Print or use the variables as needed
print(f"Current week: {start_current_week} to {end_current_week}")
print(f"Previous week: {start_previous_week} to {end_previous_week}")


#----------------------------------------------------------------------------
async def download_data(page, download_path, time_period):
    # Navegando na página
    await page.get_by_role("button", name="Data aggregation methodBy").click()
    await page.get_by_role("option", name="By employee").click()

    await page.get_by_role("button", name="More Filters").click()
    await page.get_by_role("button", name="DepartmentTP_LIS_TT-R1-PT-PT-").click()
  
    # Clicando na opção CSV para iniciar o download e guardar numa variável
    async with page.expect_download() as download_info:
        await page.frame_locator("#data-power-app iframe").get_by_role("button", name="Download").click()
        print(f"Fazendo Download para {time_period}")
    download = await download_info.value

    # Salvando o download no caminho especificado
    download_file_path = os.path.join(download_path, f"{time_period}_{download.suggested_filename}")
    await download.save_as(download_file_path)
    print(f"Download concluído para {time_period}. Arquivo salvo em: {download_file_path}")

async def main():
    # Cria um browser com os cookies de login
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=r"datapower_auth.json")
        page = await context.new_page()
        
        download_path = os.path.join(os.path.expanduser('~'), 'Downloads')

        try:
            # Aumentando o timeout da página
            page.set_default_navigation_timeout(120000)
            await page.goto("https://byteworks-va.bytelemon.com/v2/workhour/correct")
            page.get_by_role("button", name="Time Range").click()
            page.locator("div").filter(has_text=re.compile(r"^09:45$")).first.click()
            page.get_by_text("00", exact=True).nth(1).click()
            await page.pause()



        except Exception as e:
            print(f"Erro ao processar a URL: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
