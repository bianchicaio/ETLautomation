import asyncio
import os
from datetime import datetime, timedelta
import calendar
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import re
import win32com.client as win32

def get_month_date_range(year, month):
    first_day = datetime(year, month, 1)
    last_day = datetime(year, month, calendar.monthrange(year, month)[1])
    return first_day.strftime('%Y-%m-%d'), last_day.strftime('%Y-%m-%d')

async def download_data(page, download_path, start_date, end_date, timeout_duration=60000):
    success = False
    error_message = ""

    try:
        # Navega para a página e realiza as ações necessárias
        await page.goto("https://datapower-va.bytelemon.com/bi/visit/6953507931698642950?immersive=1", timeout=timeout_duration)
        print("Página carregada")

        await page.get_by_role("menuitem", name="Dashboard", exact=True).click()
        await page.get_by_role("menuitem", name="All Dashboard").click()

        # Espera pela abertura de uma nova página ao clicar no item do grid
        async with page.expect_popup() as page1_info:
            await page.get_by_text("Site Moderation Report").click()

        page1 = await page1_info.value  # Aqui garantimos que a nova página foi obtida antes de continuar

        # Interações na nova página
        await page1.frame_locator("#data-power-app iframe").get_by_role("tab", name="QA from new dataset").click()
        await page1.frame_locator("#data-power-app iframe").locator("div").filter(has_text=re.compile(r"^Raw Data Export$")).first.click()
        #await page.pause()
        await page1.frame_locator("#data-power-app iframe").locator("#stick-element-wrapper").get_by_text("QA1 Date").click()
        await page1.frame_locator("#data-power-app iframe").get_by_role("tab", name="Fixed Date").click()

        # Preencher as datas de início e término
        await page1.frame_locator("#data-power-app iframe").get_by_placeholder("Start date").click()
        await page1.frame_locator("#data-power-app iframe").get_by_placeholder("Start date").fill(start_date)
        await page1.frame_locator("#data-power-app iframe").get_by_placeholder("End date").click()
        await page1.frame_locator("#data-power-app iframe").get_by_placeholder("End date").fill(end_date)
        
        print(f"Selecionou 'Download all data from the current view' para o período de {start_date} a {end_date}")

        await page1.frame_locator("#data-power-app iframe").locator("div").filter(has_text=re.compile(r"^QA Mode - RAW data - task level$")).first.hover()
        await page1.frame_locator("#data-power-app iframe").locator(".css-1m4zay6 > .css-ku4ifn > div:nth-child(4) > .css-xe7ikk > .css-13ynuro").click()
        await page1.frame_locator("#data-power-app iframe").get_by_role("menuitem", name="Download").click()
        await page1.frame_locator("#data-power-app iframe").get_by_text("UTF-8 encoded CSV(Max 1000k)").click()
        await page1.frame_locator("#data-power-app iframe").get_by_role("spinbutton").click()
        await page1.frame_locator("#data-power-app iframe").get_by_role("spinbutton").fill("1,000,000")

        # Inicia o download e espera que ele termine
        async with page1.expect_download(timeout=timeout_duration) as download_info:
            await page1.frame_locator("#data-power-app iframe").get_by_role("button", name="Download").click()
            print("Iniciou o download")

        download = await download_info.value
        await download.save_as(os.path.join(download_path, download.suggested_filename))
        print(f"Arquivo baixado e salvo em: {os.path.join(download_path, download.suggested_filename)}")

        success = True

    except PlaywrightTimeoutError as e:
        error_message = f"Erro de timeout: {e}"
        print(error_message)
    except Exception as e:
        error_message = f"Erro: {e}"
        print(error_message)

    return success, error_message

def send_email(results):
    try:
        outlook = win32.Dispatch("outlook.application")
        mail = outlook.CreateItem(0)
        mail.Subject = 'Relatório de Status dos Downloads'
        mail.To = 'caio.bechara@teleperformance.com'

        body = "Relatório de Status dos Downloads:\n\n"
        for result in results:
            period, success, error_message = result
            if success:
                body += f"Download para {period}: SUCESSO\n"
            else:
                body += f"Download para {period}: FALHA\nErro: {error_message}\n"

        mail.Body = body
        mail.Send()
        print("E-mail enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

async def main():
    download_path = os.path.join(os.path.expanduser('~'), 'Downloads')
    results = []

    # Obter o ano e mês atual
    now = datetime.now()
    current_year = now.year
    current_month = now.month

    # Definir as datas para o mês atual
    current_start_date, current_end_date = get_month_date_range(current_year, current_month)
    
    # Definir as datas para o mês anterior
    previous_month = current_month - 1 if current_month > 1 else 12
    previous_year = current_year if current_month > 1 else current_year - 1
    previous_start_date, previous_end_date = get_month_date_range(previous_year, previous_month)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="mi_auth.json")
        page = await context.new_page()

        # Fazer o download para o mês atual
        success, error_message = await download_data(page, download_path, current_start_date, current_end_date)
        results.append((f"{current_year}-{current_month}", success, error_message))

        # Fazer o download para o mês anterior
        success, error_message = await download_data(page, download_path, previous_start_date, previous_end_date)
        results.append((f"{previous_year}-{previous_month}", success, error_message))

        await context.close()
        await browser.close()

    send_email(results)

if __name__ == "__main__":
    asyncio.run(main())
