import asyncio
import os
import re
import time
from datetime import datetime, timedelta
from playwright.async_api import async_playwright

def calculate_weeks():
    today = datetime.today()

    # Encontrar o último sábado (final da semana passada)
    last_saturday = today - timedelta(days=today.weekday() + 2)  # Sábado da semana passada
    last_sunday = last_saturday - timedelta(days=6)  # Domingo da semana passada

    # Encontrar o sábado anterior (final da semana retrasada)
    previous_saturday = last_sunday - timedelta(days=1)  # Sábado da semana retrasada
    previous_sunday = previous_saturday - timedelta(days=6)  # Domingo da semana retrasada

    # Obter o número da semana (semana do último domingo)
    current_week_number = last_sunday.isocalendar()[1]
    
    # Formatar as datas para o download
    last_week_start = last_sunday.strftime('%Y-%m-%d')
    last_week_end = last_saturday.strftime('%Y-%m-%d')

    week_before_last_start = previous_sunday.strftime('%Y-%m-%d')
    week_before_last_end = previous_saturday.strftime('%Y-%m-%d')

    return {
        "last_week": (last_week_start, last_week_end, current_week_number),
        "week_before_last": (week_before_last_start, week_before_last_end, current_week_number - 1)
    }

async def download_data(page, download_path, start_date, end_date, week_number):
    await page.frame_locator("#data-power-app iframe").get_by_role("tab", name="TCOR/CGVR").click()
    print("Clicou na Tab TCOR/CGVR")

    await page.frame_locator("#data-power-app iframe").locator("div").filter(has_text=re.compile(r"^TCOR$")).first.click()
    print("Selecionou TCOR")

    await page.frame_locator("#data-power-app iframe").get_by_text("SiteSelect").click()
    await page.frame_locator("#data-power-app iframe").get_by_placeholder("Search or enter options").fill("TP-LIS")
    await page.frame_locator("#data-power-app iframe").get_by_text("TP-LIS").click()
    print("Selecionou Site TP-LIS")

    await page.frame_locator("#data-power-app iframe").get_by_text("Moderation DateAdvanced (").click()
    await page.frame_locator("#data-power-app iframe").get_by_role("tab", name="Fixed Date").click()
    await page.frame_locator("#data-power-app iframe").get_by_placeholder("Start date").click()
    await page.frame_locator("#data-power-app iframe").get_by_placeholder("Start date").fill(f"{start_date} 00:00:00")
    await page.frame_locator("#data-power-app iframe").get_by_placeholder("End date").click()
    await page.frame_locator("#data-power-app iframe").get_by_placeholder("End date").fill(f"{end_date} 23:59:59")
    print(f"Selecionou a data {start_date} - {end_date}")

    await page.frame_locator("#data-power-app iframe").locator(".report-filter-popover-close > .arco-icon").click()

    # Faz o Scroll até a tabela
    x = 600  
    y = 600  
    await page.mouse.move(x, y)
    await page.mouse.wheel(0, 600)
    print("Fez Scroll até a tabela Case Picker")
    
    time.sleep(4)

    await page.frame_locator("#data-power-app iframe").locator(".css-1m4zay6 > .css-ku4ifn > div:nth-child(3) > .css-xe7ikk > .css-13ynuro").click()
    await page.frame_locator("#data-power-app iframe").get_by_role("menuitem", name="Download").click()
    await page.frame_locator("#data-power-app iframe").get_by_label("Download data").get_by_role("textbox").click()
    await page.frame_locator("#data-power-app iframe").get_by_label("Download data").get_by_role("textbox").fill(f"_TCOR Quality Case Picker  - 2024 W{week_number}")
    await page.frame_locator("#data-power-app iframe").locator("label").filter(has_text="UTF-8 encoded CSV(Max 1000k)").locator("div").click()
    await page.frame_locator("#data-power-app iframe").get_by_role("spinbutton").click()
    await page.frame_locator("#data-power-app iframe").get_by_role("spinbutton").fill("1,000,000")

    # Clicando na opção CSV para iniciar o download
    async with page.expect_download(timeout=120000) as download_info:
        await page.frame_locator("#data-power-app iframe").get_by_role("button", name="Download").click()
        print("Iniciou o download")
        await page.wait_for_timeout(5000)

    # Salvando o download no caminho especificado
    download = await download_info.value
    await download.save_as(os.path.join(download_path, download.suggested_filename))
    print(f"Downloaded file saved to: {os.path.join(download_path, download.suggested_filename)}")
    await page.wait_for_timeout(5000)

async def process_download(start_date, end_date, download_path, week_number):
    # Cria um browser com os cookies de login
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="datapower_auth.json")
        page = await context.new_page()

        try:
            # Aumentando o timeout da página
            page.set_default_navigation_timeout(120000)
            await page.goto("https://datapower-va.bytelemon.com/bi/visit/7325384900452941829?immersive=1")
            # Realiza o download para a data especificada
            await download_data(page, download_path, start_date, end_date, week_number)

        except Exception as e:
            print(f"Erro ao processar a URL: {e}")
        finally:
            # Fecha o browser após o download
            await browser.close()
            print(f"Browser fechado após o download para a data: {start_date} - {end_date}")

async def main():
    download_path = os.path.join(os.path.expanduser('~'), 'Downloads')

    # Calcula as semanas de domingo a sábado
    weeks = calculate_weeks()

    # Realizar o download da semana passada
    start_date_last_week, end_date_last_week, week_number_last_week = weeks["last_week"]
    await process_download(start_date_last_week, end_date_last_week, download_path, week_number_last_week)

    # Realizar o download da semana retrasada
    start_date_week_before_last, end_date_week_before_last, week_number_week_before_last = weeks["week_before_last"]
    await process_download(start_date_week_before_last, end_date_week_before_last, download_path, week_number_week_before_last)

if __name__ == "__main__":
    asyncio.run(main())
