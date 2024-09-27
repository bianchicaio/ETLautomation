import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import re
import win32com.client as win32

async def download_data(page, download_path, timeout_duration=60000):
    success = False
    error_message = ""
    filename = "TP-LIS - RCA - 2nd Round QA_BS SR Qs Performance_SR LIS.csv"

    try:
        # Navega para a página e realiza as ações necessárias
        await page.goto("https://bytedance.sg.larkoffice.com/base/GHoXboG1YaWmigsDvKLlO8KzgFe?table=tblPELwHGA3cbJe5&view=veweOl34mL", timeout=timeout_duration)
        print("Página carregada")

        #await page.get_by_text("BS SR Qs Performance").click(timeout=timeout_duration)
        #print("Clicou em 'BS SR Qs Performance'")
        #await page.pause()
        await page.locator(".suite-more-menu").click()
        print("Clicou no botão de opções")

        await page.get_by_role("menuitem", name="Export").click(timeout=timeout_duration)
        print("Selecionou 'Export'")

        await page.get_by_role("menuitem", name="Excel/CSV").click(timeout=timeout_duration)
        print("Selecionou 'Excel/CSV'")

        await page.get_by_label("CSV").check(timeout=timeout_duration)
        print("Selecionou 'CSV'")

        await page.get_by_role("dialog").get_by_role("img").nth(2).click(timeout=timeout_duration)
        await page.locator("div").filter(has_text=re.compile(r"^SR LISDownload all data from the current view$")).nth(1).click(timeout=timeout_duration)
        
        print("Selecionou 'Download all data from the current view'")

        # Inicia o download e espera que ele termine
        async with page.expect_download(timeout=timeout_duration) as download_info:
            await page.get_by_role("button", name="Download").click()
            print("Iniciou o download")
        
        download = await download_info.value
        await download.save_as(os.path.join(download_path, filename))
        print(f"Arquivo baixado e salvo em: {os.path.join(download_path, filename)}")

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
    period = "BS SR Qs Performance"
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="mi_qa_auth.json")
        page = await context.new_page()

        success, error_message = await download_data(page, download_path)
        results.append((period, success, error_message))

        await context.close()
        await browser.close()

    #send_email(results)

if __name__ == "__main__":
    asyncio.run(main())
