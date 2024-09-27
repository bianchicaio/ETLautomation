import asyncio
import os
import re
from datetime import datetime, timedelta
from playwright.async_api import async_playwright

async def download_data(page, download_path, time_period, start_date=None, end_date=None):
    # Navegando na página
    await page.frame_locator("#data-power-app iframe").get_by_role("tab", name="Productivity").click()
    await page.frame_locator("#data-power-app iframe").locator("#stick-element-wrapper").get_by_text("Date").click()

    if time_period:
        await page.frame_locator("#data-power-app iframe").get_by_text(time_period).click()
    else:
        await page.frame_locator("#data-power-app iframe").get_by_text("Fixed Date").click()
        await page.frame_locator("#data-power-app iframe").get_by_placeholder("Start date").click()
        await page.frame_locator("#data-power-app iframe").get_by_placeholder("Start date").fill(start_date)
        await page.frame_locator("#data-power-app iframe").get_by_placeholder("End date").click()
        await page.frame_locator("#data-power-app iframe").get_by_placeholder("End date").fill(end_date)

    await page.frame_locator("#data-power-app iframe").locator("#stick-element-wrapper").get_by_text("Date").click()
    await page.frame_locator("#data-power-app iframe").locator("div").filter(has_text=re.compile(r"^Raw Data$")).first.click()
    # Faz o Scroll até a tabela certo
    x = 600  
    y = 600  
    await page.mouse.move(x, y)
    await page.mouse.wheel(0, 500)

    # Move o mouse pra baixo da tela  
    x = 500 
    y = 700  
    await page.mouse.move(x, y)


    await page.frame_locator("#data-power-app iframe").locator(".css-1m4zay6 > .css-ku4ifn > div:nth-child(3) > .css-xe7ikk > .css-13ynuro").click()
    await page.frame_locator("#data-power-app iframe").get_by_role("menuitem", name="Download").click()
    await page.frame_locator("#data-power-app iframe").locator("label").filter(has_text="UTF-8 encoded CSV(Max 1000k)").locator("div").click()
    await page.frame_locator("#data-power-app iframe").get_by_role("spinbutton").fill("1,000,000")

    # Clicando na opção CSV para iniciar o download e guardar numa variável
    async with page.expect_download(timeout=120000) as download_info:
        await page.frame_locator("#data-power-app iframe").get_by_role("button", name="Download").click()
        print("Iniciou o download")
        await page.wait_for_timeout(5000)

    # Salvando o download no caminho especificado
    download = await download_info.value
    await download.save_as(os.path.join(download_path, download.suggested_filename))
    print(f"Downloaded file saved to: {os.path.join(download_path, download.suggested_filename)}")
    await page.wait_for_timeout(5000)

async def main():
    # Cria um browser com os cookies de login
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="datapower_auth.json")
        page = await context.new_page()
        
        download_path = os.path.join(os.path.expanduser('~'), 'Downloads')

        try:
            # Aumentando o timeout da página
            page.set_default_navigation_timeout(120000)
            await page.goto("https://datapower-va.bytelemon.com/bi/visit/6953507931698642950?immersive=1")

            # Download para "Last week"
            await download_data(page, download_path, "Last week")

            # Download para "This week"
            await download_data(page, download_path, "This week")

            # Calcular datas para a semana anterior à "Last week"
            today = datetime.today()
            start_of_this_week = today - timedelta(days=today.weekday())
            start_of_last_week = start_of_this_week - timedelta(weeks=1)
            start_of_week_before_last = start_of_this_week - timedelta(weeks=2)

            start_date = start_of_week_before_last.strftime('%Y-%m-%d')
            end_date = (start_of_last_week - timedelta(days=1)).strftime('%Y-%m-%d')

            # Download para "Last week -1"
            await download_data(page, download_path, None, start_date, end_date)

        except Exception as e:
            print(f"Erro ao processar a URL: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
