import asyncio
import os
import time
from datetime import datetime, timedelta
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import re
import win32com.client as win32

async def download_data(period, start_date, end_date, task_status, download_path, results, timeout_duration=60000):
    success = False
    error_message = ""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="datapower_auth.json")
        page = await context.new_page()

        try:
            await page.goto("https://datapower-va.bytelemon.com/bi/visit/6953507931698642950", timeout=timeout_duration)
            print(f"Página inicial carregada para {period} - {task_status}")

            await page.frame_locator("#data-power-app iframe").get_by_role("tab", name="Ads & Account Review").click(timeout=timeout_duration)
            print("Clicou na aba Ads & Account Review")

            await page.frame_locator("#data-power-app iframe").get_by_text("Ads Review PerfAccount Review").click(timeout=timeout_duration)
            print("Clicou em Ads Review PerfAccount Review")

            await page.frame_locator("#data-power-app iframe").locator("span").filter(has_text="Last 30 days (having data) (").first.click(timeout=timeout_duration)
            print("Selecionou Last 30 days")

            await page.frame_locator("#data-power-app iframe").get_by_text("Fixed Date").click()
            await page.frame_locator("#data-power-app iframe").get_by_placeholder("Start date").click()
            await page.frame_locator("#data-power-app iframe").get_by_placeholder("Start date").fill(start_date)
            print(f"Selecionou Start Date {start_date}")

            await page.frame_locator("#data-power-app iframe").get_by_placeholder("End date").click()
            await page.frame_locator("#data-power-app iframe").get_by_placeholder("End date").fill(end_date)
            print(f"Selecionou End Date {end_date}")

            # Seleciona filtro Auditor Site
            await page.frame_locator("#data-power-app iframe").get_by_text("Auditor SiteSelect").click()
            await page.frame_locator("#data-power-app iframe").get_by_text("LIS-TP").click()
            print("Selecionou Auditor Site")

            await page.frame_locator("#data-power-app iframe").locator(".report-filter-popover-close").click()

            await page.frame_locator("#data-power-app iframe").get_by_text("Task FlagExcludesimulation").click()
            print("Selecionou Task Flag Excludesimulation")

            # Clica duas vezes para garantir que "Select all" esteja desmarcado
            await page.frame_locator("#data-power-app iframe").locator("label").filter(has_text="Select all").locator("div").click()
            await page.frame_locator("#data-power-app iframe").locator("label").filter(has_text="Select all").locator("div").click()
            print("Certificou-se de que 'Select all' está desmarcado")

            # Verifica se "Exclude" está marcado e desmarca se necessário
            await page.frame_locator("#data-power-app iframe").locator("label").filter(has_text="Exclude").locator("div").click()
            print("Desmarcou 'Exclude'")

            await page.frame_locator("#data-power-app iframe").locator(".report-filter-popover-close").click(timeout=timeout_duration)
            print("Fechou o popover de filtro do relatório")

            await page.frame_locator("#data-power-app iframe").get_by_text("Affect ExperienceSelect").click()
            print("Selecionou Affect Experience")

            await page.frame_locator("#data-power-app iframe").locator("label").filter(has_text=re.compile(rf"^{task_status} Tasks$")).locator("div").first.click(timeout=timeout_duration)
            print(f"Selecionou {task_status} Tasks")

            await page.frame_locator("#data-power-app iframe").locator(".report-filter-popover-close > .arco-icon").click(timeout=timeout_duration)
            print("Fechou o popover de filtro do relatório")
            await page.wait_for_timeout(5000)
            # Mover o mouse para o centro da janela do navegador
            viewport_size = page.viewport_size
            center_x = viewport_size['width'] / 2
            center_y = viewport_size['height'] / 2
            await page.mouse.move(center_x, center_y)
            print("Moveu o mouse para o centro da janela do navegador")
            
            await page.frame_locator("#data-power-app iframe").locator(".css-1m4zay6 > .css-ku4ifn > div:nth-child(5) > .css-xe7ikk > .css-13ynuro > .guide-list-create").click()
            print("Clicou no menu de download")

            await page.frame_locator("#data-power-app iframe").get_by_role("menuitem", name="Download").click(timeout=timeout_duration) 
            print("Selecionou Download")

            await page.frame_locator("#data-power-app iframe").get_by_label("Download data").get_by_role("textbox").click(timeout=timeout_duration)
            print("Selecionou o campo para nomear o arquivo")
            
            # Adicionando um "_v" ao final do ficheiro para os "invalids" (necessário para script do ETL)
            if task_status == "invalid":
                filename = f"_Ads Review Raw Data - {period.lower().replace(' ', '_')}_{task_status.lower()}_v.csv"
            elif task_status == "Valid":
                filename = f"_Ads Review Raw Data - {period.lower().replace(' ', '_')}_{task_status.lower()}.csv"

            await page.frame_locator("#data-power-app iframe").get_by_label("Download data").get_by_role("textbox").fill(filename, timeout=timeout_duration)
            print(f"Nomeou o arquivo: {filename}")

            await page.wait_for_timeout(2000)
            await page.frame_locator("#data-power-app iframe").locator("label").filter(has_text="UTF-8 encoded CSV(Max 1000k)").locator("div").click(timeout=timeout_duration)
            print("Selecionou UTF-8 encoded CSV")

            await page.frame_locator("#data-power-app iframe").get_by_role("spinbutton").click(timeout=timeout_duration)
            await page.frame_locator("#data-power-app iframe").get_by_role("spinbutton").fill("1,000,000", timeout=timeout_duration)
            print("Preencheu o spinbutton com 1,000,000")

            async with page.expect_download(timeout=timeout_duration) as download_info:
                await page.frame_locator("#data-power-app iframe").get_by_role("button", name="Download").click()
                print("Iniciou o download")
                await page.wait_for_timeout(2000)

            download = await download_info.value
            await download.save_as(os.path.join(download_path, filename))
            print(f"Downloaded file saved to: {os.path.join(download_path, filename)}")
            

            success = True

        except PlaywrightTimeoutError as e:
            error_message = f"Erro de timeout: {e}"
            print(error_message)
        except Exception as e:
            error_message = f"Erro: {e}"
            print(error_message)

        finally:
            await context.close()
            await browser.close()

            # Registrar o resultado do download
            results.append((period, task_status, success, error_message))

async def main():
    download_path = os.path.join(os.path.expanduser('~'), 'Downloads')

    # Calcular datas de início e fim para as semanas anteriores (segunda a domingo)
    today = datetime.today()
    start_of_this_week = today - timedelta(days=today.weekday())

    last_week_start = (start_of_this_week - timedelta(weeks=1)).strftime('%Y-%m-%d')
    last_week_end = (start_of_this_week - timedelta(days=1)).strftime('%Y-%m-%d')

    week_before_last_start = (start_of_this_week - timedelta(weeks=2)).strftime('%Y-%m-%d')
    week_before_last_end = (start_of_this_week - timedelta(weeks=1, days=1)).strftime('%Y-%m-%d')

    periods = [
        ("Last week", last_week_start, last_week_end),
        ("Week before last", week_before_last_start, week_before_last_end)
    ]

    # Adicionar o período da semana atual se for quarta-feira ou posterior
    if today.weekday() >= 2:  # 2 representa quarta-feira (0 = segunda-feira)
        this_week_start = start_of_this_week.strftime('%Y-%m-%d')
        this_week_end = today.strftime('%Y-%m-%d')
        periods.append(("This week", this_week_start, this_week_end))

    task_statuses = ["Valid", "invalid"]

    results = []

    for period, start_date, end_date in periods:
        for task_status in task_statuses:
            await download_data(period, start_date, end_date, task_status, download_path, results)

    # Enviar email com o resumo dos resultados dos downloads
    send_email(results)

def send_email(results):
    try:
        outlook = win32.Dispatch("outlook.application")
        mail = outlook.CreateItem(0)
        mail.Subject = 'Relatório de Status dos Downloads'
        mail.To = 'caio.bechara@teleperformance.com'
        mail.CC = 'pedro.esteves@teleperformance.com'

        body = "Relatório de Status dos Downloads DATAPOWER ADS REVIEW:\n\n"
        for result in results:
            period, task_status, success, error_message = result
            if success:
                body += f"Download para {period} - {task_status}: SUCESSO\n"
            else:
                body += f"Download para {period} - {task_status}: FALHA\nErro: {error_message}\n"

        mail.Body = body

        mail.Send()
        print("E-mail enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

if __name__ == "__main__":
    asyncio.run(main())
