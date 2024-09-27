import asyncio
import os
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
import re
import pandas as pd
import win32com.client as win32

async def download_fixed_date(page, start_date, end_date, description):
    await page.frame_locator("#data-power-app iframe").get_by_text("1st Round Resolve TimeThis").click()
    print("Clicou no botão para selecionar data")
    await page.frame_locator("#data-power-app iframe").get_by_role("tab", name="Fixed Date").click()
    print("Selecionou Fixed Date")
    
    await page.frame_locator("#data-power-app iframe").get_by_placeholder("Start date").click()
    await page.frame_locator("#data-power-app iframe").get_by_placeholder("Start date").fill(start_date)
    print(f"Preencheu Start date com {start_date}")
    
    await page.frame_locator("#data-power-app iframe").get_by_placeholder("End date").click()
    await page.frame_locator("#data-power-app iframe").get_by_placeholder("End date").fill(end_date)
    print(f"Preencheu End date com {end_date}")

    await page.frame_locator("#data-power-app iframe").get_by_text("Site NameSelect").click()
    await page.frame_locator("#data-power-app iframe").locator("label").filter(has_text="LIS-TP").locator("div").first.click()
    
    await page.frame_locator("#data-power-app iframe").get_by_text("resolve_date").click()
    print("Arrumou filtro Date Scale")

    await page.frame_locator("#data-power-app iframe").locator("div:nth-child(3) > .filter-tensile-box > .css-j6rygn > .bi-filter-box > .css-1emh8f9 > .css-vdkatv > .css-1pkcfmb > .css-13z34rs > .css-1pfvgnk").click()


    #await page.frame_locator("#data-power-app iframe").locator("div").filter(has_text=re.compile(r"^Moderator InfoEmptyModerator$")).nth(3).click()
    print("Clicou em Empty para Dynamic dimensions")

    #await page.frame_locator("#data-power-app iframe").get_by_text("project_title").click()
    print("Escolher Moderator em Moderator info")

    await page.frame_locator("#data-power-app iframe").get_by_text("department").nth(1).click()
    print("Selecionou department na Dynamic dimension 2")

    await page.frame_locator("#data-power-app iframe").get_by_text("mode_name").click()
    print("Selecionou mode name")

    await page.frame_locator("#data-power-app iframe").get_by_text("labeling_method").click()
    print("Selecionou labeling method")
    
    #await page.pause()

    await page.frame_locator("#data-power-app iframe").locator("div:nth-child(3) > .css-xe7ikk > .css-13ynuro").click()
    print("Clicou no menu")

    await page.frame_locator("#data-power-app iframe").get_by_role("menuitem", name="Download").click()
    print("Selecionou Download")

    await page.frame_locator("#data-power-app iframe").locator("label").filter(has_text="UTF-8 encoded CSV(Max 1000k)").locator("div").click()
    print("Selecionou UTF-8")
    
    async with page.expect_download() as download_info:
        await page.frame_locator("#data-power-app iframe").get_by_role("button", name="Download").click()
    
    download = await download_info.value
    download_path = os.path.join(os.path.expanduser('~'), 'Downloads', download.suggested_filename)
    await download.save_as(download_path)
    print(f"Fez o download e salvou em: {download_path}")
    
    return download_path

async def download_with_retries(browser_context, start_date, end_date, description, max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Tentativa {attempt} para {description}")
            
            # Cria uma nova página em um novo contexto do navegador
            page = await browser_context.new_page()
            await page.goto("https://datapower-va.bytelemon.com/bi/visit/6982209149375414277?immersive=1")
            print("Acessou a página")

            download_path = await download_fixed_date(page, start_date, end_date, description)
            await page.close()
            return True
        except Exception as e:
            print(f"Erro na tentativa {attempt} para {description}: {e}")
            if attempt < max_retries:
                print("Tentando novamente após 5 segundos...")
                await asyncio.sleep(5)
            else:
                print(f"Falha após {max_retries} tentativas para {description}")
            await page.close()
    return False

def send_email(success):
    try:
        outlook = win32.Dispatch("outlook.application")
        mail = outlook.CreateItem(0)
        mail.Subject = 'Relatório de Status dos Downloads'
        mail.To = 'caio.bechara@teleperformance.com'
        #mail.CC = 'pedro.esteves@teleperformance.com'

        if success:
            mail.Body = "Todos os downloads do arquivo MI Labeling foram bem-sucedidos.\n\nObrigado."
        else:
            mail.Body = "Houve problemas na realização dos downloads do arquivo MI Labeling.\n\nPor favor, verifique."

        mail.Send()
        print("E-mail enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

async def main():
    today = datetime.today()
    first_day_this_month = today.replace(day=1).strftime('%Y-%m-%d')
    end_date_this_month = today.strftime('%Y-%m-%d')
    
    first_day_last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1).strftime('%Y-%m-%d')
    last_day_last_month = (today.replace(day=1) - timedelta(days=1)).strftime('%Y-%m-%d')

    success = True
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        for period, start_date, end_date in [("this_month", first_day_this_month, end_date_this_month),
                                             ("last_month", first_day_last_month, last_day_last_month)]:
            if period == "last_month" and today.day >= 15:
                continue
            
            context = await browser.new_context(storage_state="mi_auth.json")
            result = await download_with_retries(context, start_date, end_date, period)
            await context.close()
            
            if not result:
                success = False
        
        await browser.close()
    
    # Envia o email com o resultado dos downloads
    send_email(success)

if __name__ == "__main__":
    asyncio.run(main())
