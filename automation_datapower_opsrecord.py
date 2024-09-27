import asyncio
import os
from datetime import datetime, timedelta
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import re
import win32com.client as win32

async def download_data(start_date, end_date, download_path, results, timeout_duration=60000):
    success = False
    error_message = ""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="datapower_auth.json")
        page = await context.new_page()

        try:
            await page.goto("https://datapower-va.bytelemon.com/bi/visit/7361807889996120069", timeout=timeout_duration)
            await page.wait_for_selector("#data-power-app iframe")  # Esperar o iframe carregar
            await page.frame_locator("#data-power-app iframe").get_by_text("Moderation Date").click()
            print(f"Clicou no filtro de datas e vai selecionar {start_date} e {end_date}")
            
            await page.frame_locator("#data-power-app iframe").get_by_role("tab", name="Fixed Date").click()
            print("Selecionou Fixed Date")

            # Preencher a data de fim primeiro
            await page.frame_locator("#data-power-app iframe").get_by_placeholder("End date").click()
            await page.frame_locator("#data-power-app iframe").get_by_placeholder("End date").fill(end_date)
            
            # Preencher a data de início
            await page.frame_locator("#data-power-app iframe").get_by_placeholder("Start date").click()
            await page.frame_locator("#data-power-app iframe").get_by_placeholder("Start date").fill(start_date)
            
            # Clicar em "Query"
            await page.frame_locator("#data-power-app iframe").get_by_role("button", name="Query").click()
            print("Clicou em Query")
            
            # Esperar os resultados da query aparecerem
            await page.frame_locator("#data-power-app iframe").locator("div").filter(has_text=re.compile(r"^Ops Record$")).first.click()
            print("Selecionou Tab Ops Record")

            # Mover o mouse para a parte inferior da janela do navegador
            viewport_size = page.viewport_size
            bottom_x = viewport_size['width'] / 2
            bottom_y = viewport_size['height'] - 13  # Perto da parte inferior
            await page.mouse.move(bottom_x, bottom_y)
            print("Moveu o mouse para a parte inferior da janela do navegador")
            
            await page.frame_locator("#data-power-app iframe").locator(".css-1m4zay6 > .css-ku4ifn > div:nth-child(3) > .css-xe7ikk > .css-13ynuro > .guide-list-create").click()
            await page.frame_locator("#data-power-app iframe").get_by_role("menuitem", name="Download").click()
            
            # Selecionar UTF-8 CSV e definir limite de linhas
            await page.frame_locator("#data-power-app iframe").locator("label").filter(has_text="UTF-8 encoded CSV(Max 1000k)").locator("div").click()
            await page.frame_locator("#data-power-app iframe").get_by_role("spinbutton").click()
            await page.frame_locator("#data-power-app iframe").get_by_role("spinbutton").fill("1,000,000")

            # Iniciar o download
            async with page.expect_download(timeout=timeout_duration) as download_info:
                await page.frame_locator("#data-power-app iframe").get_by_role("button", name="Download").click()
                print("Iniciou o download")

            download = await download_info.value
            file_path = os.path.join(download_path, download.suggested_filename)
            await download.save_as(file_path)
            print(f"Downloaded file saved to: {file_path}")

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
            results.append((f"{start_date} to {end_date}", success, error_message))

async def main():
    download_path = os.path.join(os.path.expanduser('~'), 'Downloads')

    # Calcular datas de início e fim para as últimas quatro semanas (de segunda a domingo)
    today = datetime.today()
    
    # Encontre a última segunda-feira
    last_monday = today - timedelta(days=today.weekday() + 7)  # Segunda-feira da semana passada
    
    start_dates = [(last_monday - timedelta(weeks=i)).strftime('%Y-%m-%d') for i in range(4)]
    end_dates = [(last_monday + timedelta(days=6) - timedelta(weeks=i)).strftime('%Y-%m-%d') for i in range(4)]

    results = []

    # Executa o download para cada semana (da mais recente para a mais antiga)
    for start_date, end_date in zip(start_dates, end_dates):
        await download_data(start_date, end_date, download_path, results)

    # Enviar email com o resumo dos resultados dos downloads
    send_email(results)

def send_email(results):
    try:
        outlook = win32.Dispatch("outlook.application")
        mail = outlook.CreateItem(0)
        mail.Subject = 'Relatório de Status dos Downloads'
        mail.To = 'caio.bechara@teleperformance.com'
        
        body = "Relatório de Status dos Downloads DATAPOWER OPS_RECORD:\n\n"
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

if __name__ == "__main__":
    asyncio.run(main())
