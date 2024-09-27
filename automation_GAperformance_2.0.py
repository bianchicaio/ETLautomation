import asyncio
import os
import re
import time
from datetime import datetime, timedelta
from playwright.async_api import async_playwright

async def download_data(page, download_path, start_date, end_date):
    # Navegando na página
    await page.frame_locator("#data-power-app iframe").get_by_role("tab", name="GA Performance").click()
    print("Selecionou a Tab GA Performance")

    await page.frame_locator("#data-power-app iframe").locator("div").filter(has_text=re.compile(r"^SiteMJR-MAK\(SSA\)$")).nth(3).click()
    time.sleep(7)
    await page.frame_locator("#data-power-app iframe").locator("label").filter(has_text="Select all").locator("div").click()
    time.sleep(4)
    await page.frame_locator("#data-power-app iframe").locator("label").filter(has_text="Select all").click()

    await page.frame_locator("#data-power-app iframe").get_by_placeholder("Search or enter options").click()
    await page.frame_locator("#data-power-app iframe").get_by_placeholder("Search or enter options").press("CapsLock")
    await page.frame_locator("#data-power-app iframe").get_by_placeholder("Search or enter options").fill("TP-LIS")
    print("Pesquisou por TP-LIS")

    await page.frame_locator("#data-power-app iframe").locator("label").filter(has_text=re.compile(r"^TP-LIS$")).locator("span").first.click()
    print("Selecionou Site TP Lis")

    # Selecionar o intervalo de datas usando Batch Date
    await page.frame_locator("#data-power-app iframe").get_by_text("Batch DateRecent 1 Custom").click()
    await page.frame_locator("#data-power-app iframe").get_by_role("tab", name="Fixed Date").click()

    # Preencher as datas com o formato correto
    await page.frame_locator("#data-power-app iframe").get_by_placeholder("Start date").click()
    await page.frame_locator("#data-power-app iframe").get_by_placeholder("Start date").fill(f"{start_date}")
    await page.frame_locator("#data-power-app iframe").get_by_placeholder("End date").click()
    await page.frame_locator("#data-power-app iframe").get_by_placeholder("End date").fill(f"{end_date}")
    print(f"Selecionou as datas {start_date} - {end_date}")
    print("Selecionou o Batch")

    await page.frame_locator("#data-power-app iframe").get_by_role("button", name="Query").click()
    print("Clicou em Query")

    # Faz o Scroll até a tabela
    x = 600  
    y = 600  
    await page.mouse.move(x, y)
    await page.mouse.wheel(0, 2000)
    print("Fez Scroll até a tabela Case Picker")
    
    time.sleep(4)

    await page.frame_locator("#data-power-app iframe").locator(".css-1m4zay6 > .css-ku4ifn > div:nth-child(3) > .css-xe7ikk > .css-13ynuro").click()
    await page.frame_locator("#data-power-app iframe").get_by_role("menuitem", name="Download").click()
    await page.frame_locator("#data-power-app iframe").get_by_text("UTF-8 encoded CSV(Max 1000k)").click()
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

async def process_download(start_date, end_date, download_path):
    # Cria um browser com os cookies de login
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="datapower_auth.json")
        page = await context.new_page()

        try:
            # Aumentando o timeout da página
            page.set_default_navigation_timeout(120000)
            await page.goto("https://datapower-va.bytelemon.com/bi/visit/7325384900452941829?immersive=1")
            # Realiza o download para o período especificado
            await download_data(page, download_path, start_date, end_date)

        except Exception as e:
            print(f"Erro ao processar a URL: {e}")
        finally:
            # Fecha o browser após o download
            await browser.close()
            print(f"Browser fechado após o download para o período: {start_date} - {end_date}")

async def main():
    download_path = os.path.join(os.path.expanduser('~'), 'Downloads')

    # Lógica para calcular as semanas com início no sábado e fim na sexta-feira
    today = datetime.today()

    # Ajuste para sempre capturar a semana passada de sábado a sexta-feira
    # Última sexta-feira
    last_friday = today - timedelta(days=today.weekday() + 3)
    last_saturday = last_friday - timedelta(days=6)

    # Semana anterior à semana passada
    previous_friday = last_friday - timedelta(days=7)
    previous_saturday = last_saturday - timedelta(days=7)

    # Faz o download da semana passada (de sábado a sexta-feira)
    start_date_last_week = last_saturday.strftime('%Y-%m-%d')
    end_date_last_week = last_friday.strftime('%Y-%m-%d')
    await process_download(start_date_last_week, end_date_last_week, download_path)

    # Faz o download da semana anterior à passada
    start_date_week_before_last = previous_saturday.strftime('%Y-%m-%d')
    end_date_week_before_last = previous_friday.strftime('%Y-%m-%d')
    await process_download(start_date_week_before_last, end_date_week_before_last, download_path)

if __name__ == "__main__":
    asyncio.run(main())
