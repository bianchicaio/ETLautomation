import asyncio
import os
import time
import re
import shutil   
from playwright.async_api import async_playwright
import win32com.client as win32

async def download_files():

    success_urls = []

    # URLs das páginas a serem acessadas
    failure_urls = url = ['https://teleperformance.larksuite.com/sheets/shtusjLubYGiKkRYwhqySE39Hgg?sheet=XhmUPq',#GA 1.0 PT TTR1
       'https://teleperfomance.larksuite.com/sheets/shtusIbCsBcNIGhr9EsqGg4FHte?sheet=PRHk1L',#GA 1.0 FI TTR1
       'https://teleperformance.larksuite.com/sheets/shtusJDpWNWcJc7esxbFcKHqowe?sheet=ZzgRZL',#UA TTR1
       'https://teleperformance.larksuite.com/sheets/shtusiIjVTZVpOHItQzXmSvYr0g?sheet=ILdzs7',#HB TTR1
       'https://teleperformance.larksuite.com/sheets/MciUsGYmHh3iOFtJHSxum0uFswb?sheet=ECWE7s',#PT TTR2
       'https://teleperformance.larksuite.com/sheets/Ufkqsy2WuhHIrHtdzfmuGlEWsEf?sheet=thvKHO',#UA TTR2
       'https://teleperformance.larksuite.com/sheets/shtusRvfqaTzYkEzWeBeeCXNl4c?sheet=sbfUJT',#FR TTR1
       'https://teleperformance.larksuite.com/sheets/shtus1Juf67YEF9ZXlx0jjVSJ2d?sheet=HnwcUG',#Creator FR TTR1
       'https://teleperformance.larksuite.com/sheets/shtus7tLBP6YaA73FmeLO7aGnTh?sheet=Kh9ZTH',#NL TTR1
       'https://teleperformance.larksuite.com/sheets/shtusbL94YqOzSPResz49UNwHYM?sheet=scRTg8',#ES TTR1
       'https://teleperformance.larksuite.com/sheets/WeuXsloKmh7g1ati1dbuyyVOs2g?sheet=bUgE81',#FR TTR2
       'https://teleperformance.larksuite.com/sheets/BMmGs7rfghlgehtMwHMuMTkMsCf?sheet=EfOtFR',#NL SPS TTR1
       'https://teleperformance.larksuite.com/sheets/BMmGs7rfghlgehtMwHMuMTkMsCf?sheet=RAS00L',#FR SPS TTR1
       'https://teleperformance.larksuite.com/sheets/BMmGs7rfghlgehtMwHMuMTkMsCf?sheet=f910b9',#IT SPS TTR1
       'https://teleperformance.larksuite.com/sheets/GR5zsTOhYhlcCetrj2auysbRsff?sheet=tux0nD',#GA2.0 IT TTR1
       'https://teleperformance.larksuite.com/sheets/HUnHsthM3hFsPvt90U2u2S4zsvg?sheet=d55kza'#GA2.0 IT TTR2
       
      ]

    # Cria um browser com os cookies de login
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=r"\\emea.tpg.ads\\portugal\\Departments\\ITDEV\\PowerBI\\accounting\\business analysts\\01 - ba\\02 - projects\\tiktok\\10. Python scripts\NEW ETL\Aux Scripts\\ETL_Bots\\lark_auth2.json")
        page = await context.new_page()
       
        download_path = os.path.join(os.path.expanduser('~'), 'Downloads')
 
        # Criando um dicionário para rastrear as tentativas de cada URL
        attempt_count = {url: 0 for url in failure_urls}
        max_attempts = 3
 
        while failure_urls:
            for url in failure_urls[:]:
                if attempt_count[url] >= 3:
                    print(f"Máximo de tentativas atingido para a URL: {url}")
                    failure_urls.remove(url)
                    continue
               
                try:
                    print(f"Acessando a URL: {url}")
                    page.set_default_navigation_timeout(60000) # Aumentando o timeout da pagina
                    await page.goto(url)
 
                    print("Carregar a página")
 
                    # Tempo extra de carregamento
                    await asyncio.sleep(5)
                    print("Carregamento concluído")
 
                    # Clique em "More" e depois em "Filter"
                    print("Tentando clicar em 'More'")
                    await page.locator("#sheet-fold").get_by_text("More").click()
                    print("Clicou em 'More'")
                    print("Tentando clicar em 'Filter'")
                    await page.locator("#sheet-filter").get_by_text("Filter").click()
                    print("Clicou em 'Filter'")
                   
                    # Se houver a opcao Remove Filter, clicar para remover.
                    remove_filter_element = await page.query_selector('text=Remove Filter')
                    if remove_filter_element:
                        await remove_filter_element.click()
                        print("Clicou em 'Remove Filter'")
                    else:
                        print("Remove Filter não encontrado")
 
                    # Clique no terceiro botão após filtrar os colaboradores
                    print("Tentando clicar nos 3 pontinhos")
                    await page.locator(".suite-more-menu").click()
                    print("Clicou nos 3 pontinhos")
 
                    # Clique em "Download As"
                    print("Tentando clicar em 'Download As'")
                    await page.get_by_text("Download As").click()
                    print("Clicou em 'Download As'")
 
                    # Clicando na opcao CSV para iniciar o download e guardar numa variavel
                    async with page.expect_download() as download_info:
                        await page.get_by_text("CSV (.csv)").click()
                        print("Selecionou 'CSV (.csv)'")
                    download = await download_info.value
 
                    # Aguarda o início do download
                    print("Esperando o início do download")
 
                    # Verificando se o download foi salvo
                    try:
                        download_file_path = os.path.join(download_path, download.suggested_filename)
                        await download.save_as(download_file_path)
                        print("Download Salvo")
                        success_urls.append(url)
                        failure_urls.remove(url)
                        print("Itens na lista de bem sucedido:", len(success_urls), " Itens na lista de fail:", len(failure_urls))
                    except Exception as e:
                        print(f"Erro ao salvar o download: {str(e)}")
 
                    # Aguarda um pouco antes de prosseguir para a próxima URL
                    await page.wait_for_timeout(5000)
 
                except Exception as e:
                    print(f"Erro ao processar a URL {url}: {str(e)}")
               
                # Incrementa o contador de tentativas
                attempt_count[url] += 1
                print(f"Tentativa {attempt_count[url]} para a URL {url}")
 
        await browser.close()
 
        return success_urls, [url for url in attempt_count if attempt_count[url] >= max_attempts and url not in success_urls]
 
def send_email(success_urls, failure_urls):
    try:
        outlook = win32.Dispatch("outlook.application")
        mail = outlook.CreateItem(0)
        mail.Subject = 'Relatório de Status dos Downloads'
        mail.To = 'caio.bechara@teleperformance.com'
        mail.CC = 'pedro.esteves@teleperformance.com'
        if failure_urls:
            mail.Body = "Os seguintes downloads falharam após 3 tentativas:\n\n" + "\n".join(failure_urls)
        else:
            mail.Body = "Todos os downloads foram bem-sucedidos.\n\nObrigado."
        mail.Send()
        print("E-mail enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {str(e)}")
 
if __name__ == "__main__":
    success_urls, failure_urls = asyncio.run(download_files())
    send_email(success_urls, failure_urls)
#------------------------------------------------------------------Move Files----------------------------------------------------------------
#THE CODE SHOULD SHOW YOUR NAME:
username = os.getlogin()
print('Your username:'+ username)
#IF YOU DONT USE YOUR DOWNLOAD FOLDER CHANGE THE BELOW STRING TO YOUR FOLDER:
folder="Downloads"
downloads_folder_path = fr"C:\\Users\\{username}\\{folder}"
#THIS CODE WILL READ THE DOWNLOADED FILES:
GP_PT_TTR1=fr"C:\Users\\{username}\\{folder}\PT TTR1 Glidepath & Action Tracker - GA Review (100).csv"
GP_FI_TTR1=fr"C:\Users\\{username}\\{folder}\FI TTR1 Glidepath & Action Tracker - GA Review (100).csv"
GP_UA_TTR1=fr"C:\Users\\{username}\\{folder}\UA TTR1 Glidepath & Action Tracker - GA Review (100).csv"
GP_HB_TTR1=fr"C:\Users\\{username}\\{folder}\HB TTR1 Glidepath & Action Tracker - GA Review (100).csv"
GP_PT_TTR2=fr"C:\Users\\{username}\\{folder}\TTR2 - GA - PT Masterfile 2024 - GA Review (100).csv"
GP_UA_TTR2=fr"C:\Users\\{username}\\{folder}\UA TTR2 Glidepath & Action Tracker - GA Review (100).csv"
UNO_GA_IT_TTR2= fr"C:\Users\\{username}\\{folder}\TTR2 - UNO Project - Masterfile - GA Review (100) GA 2.0.csv"
UNO_GA_IT_TTR1= fr"C:\Users\\{username}\\{folder}\TTR1 - UNO Project - Masterfile - GA Review (100) GA 2.0.csv"
UNO_GA_TTR1FR= fr"C:\Users\\{username}\\{folder}\FR TTR1 Glidepath & Action Tracker - GA Review (100) GA 2.0.csv"
UNO_GA_CreatorFR= fr"C:\Users\\{username}\\{folder}\Glidepath Creator TTR1 FR - GA Review (100) GA 2.0.csv"
UNO_GA_TTR1ES= fr"C:\Users\\{username}\\{folder}\ES TTR1 Glidepath & Action Tracker - GA Review (100) GA 2.0.csv"
UNO_GA_TTR1= fr"C:\Users\\{username}\\{folder}\NL TTR1 Glidepath & Action Tracker - GA Review (100) GA 2.0.csv"
Uno_GA_TTR2 = fr"C:\Users\\{username}\\{folder}\TTR2 - GA - FR Masterfile  - GA Review (100) GA 2.0.csv"
Uno_GA_SPS_IT =fr"C:\Users\\{username}\\{folder}\SPS GA Masterfile - IT GA Review (100) GA 2.0.csv"
Uno_GA_SPS_FR = fr"C:\Users\\{username}\\{folder}\SPS GA Masterfile - FR GA Review (100) GA 2.0.csv"
Uno_GA_SPS_NL = fr"C:\Users\\{username}\\{folder}\SPS GA Masterfile - NL GA Review (100) GA 2.0.csv"

#DESTINATION FOLDER:
GP_TTR1_EMEA=r"\\emea.tpg.ads\portugal\Departments\ITDEV\PowerBI\accounting\business analysts\01 - ba\02 - projects\tiktok\4. Raw Data and Aux Files\9. Quality Data\TTR1 GA Glidepath"
GP_TTR2_EMEA=r"\\emea.tpg.ads\portugal\Departments\ITDEV\PowerBI\accounting\business analysts\01 - ba\02 - projects\tiktok\4. Raw Data and Aux Files\9. Quality Data\TTR2 GA Glidepath"
UNO_Glidepath_location=r"\\emea.tpg.ads\portugal\Departments\ITDEV\PowerBI\accounting\business analysts\01 - ba\02 - projects\tiktok\4. Raw Data and Aux Files\9. Quality Data\UNO Project\Glidepath files"


#THIS WILL MOVE ALL THE ABOVE FILES, IF THE FILE IS NOT DOWNLOAED THE CODE WILL NOT RUN:
file_paths = [
    (GP_PT_TTR1, GP_TTR1_EMEA),
    (GP_FI_TTR1, GP_TTR1_EMEA),
    (GP_UA_TTR1, GP_TTR1_EMEA),
    (GP_HB_TTR1, GP_TTR1_EMEA),
    (GP_PT_TTR2, GP_TTR2_EMEA),
    (GP_UA_TTR2, GP_TTR2_EMEA),
    (UNO_GA_IT_TTR2, UNO_Glidepath_location),
    (UNO_GA_IT_TTR1, UNO_Glidepath_location),
    (UNO_GA_TTR1FR, UNO_Glidepath_location),
    (UNO_GA_CreatorFR, UNO_Glidepath_location),
    (UNO_GA_TTR1ES, UNO_Glidepath_location),
    (UNO_GA_TTR1, UNO_Glidepath_location),
    (Uno_GA_TTR2, UNO_Glidepath_location),
    (Uno_GA_SPS_IT, UNO_Glidepath_location),
    (Uno_GA_SPS_FR, UNO_Glidepath_location),
    (Uno_GA_SPS_NL, UNO_Glidepath_location)
]

try:
    for source, destination in file_paths:
        try:
            shutil.copy(source, destination)
            print(f"Moved file: {source} ")
        except FileNotFoundError:
            continue  # If file is missing, continue to the next one
    print("Files moved with success.")
except Exception as e:
    print("Fails", e)