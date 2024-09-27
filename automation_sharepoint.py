import asyncio
import os
from playwright.async_api import async_playwright
import pandas as pd
import win32com.client as win32

async def download_files():
    # URLs das páginas a serem acessadas
    success_urls = []

    failure_urls = [
        "https://teleperformance.sharepoint.com/:x:/r/sites/S.DAF.Operations_Data_Analytics/_layouts/15/Doc.aspx?sourcedoc=%7B239593F6-9215-440A-A196-777F73C4952C%7D&file=STD_DIMS_TTOK%20new%20(Teams%20Edit).xlsx&action=default&mobileredirect=true&cid=232a65da-64a",
        "https://teleperformance.sharepoint.com/:x:/r/sites/TikTok212/_layouts/15/Doc.aspx?sourcedoc=%7B6BD41419-C2CF-4DA6-9A8D-A1B65E658FE1%7D&file=Live%20R1%20PBI%20data.xlsx&wdOrigin=TEAMS-MAGLEV.p2p_ns.rwc&action=default&mobileredirect=true",
        "https://teleperformance.sharepoint.com/:x:/r/sites/TikTok212/_layouts/15/Doc.aspx?sourcedoc=%7B663AAA6C-1F41-4018-AF34-19106FA5E504%7D&file=Ecolabeling%20Accuracy%20Individual.xlsx&wdOrigin=TEAMS-MAGLEV.p2p_ns.rwc&action=default&mobileredirect=true",
        "https://teleperformance.sharepoint.com/:x:/r/sites/TikTok212/_layouts/15/Doc.aspx?sourcedoc=%7BE2793DAA-20A0-43B8-8839-D73B0E5B2035%7D&file=Live%20R2%20-%20PBI.xlsx&wdOrigin=TEAMS-MAGLEV.p2p_ns.rwc&action=default&mobileredirect=true",
        "https://teleperformance.sharepoint.com/:x:/r/sites/TikTok212/_layouts/15/Doc.aspx?sourcedoc=%7B8F17E890-9130-4DCE-80BD-2BCA2EFAECA3%7D&file=Live%20R1%20R3%20-%20Quiz.xlsx&wdOrigin=TEAMS-MAGLEV.p2p_ns.rwc&action=default&mobileredirect=true",
        "https://teleperformance-my.sharepoint.com/:x:/r/personal/dijkstra_28_emea_teleperformance_com/_layouts/15/guestaccess.aspx?email=pedro.esteves%40teleperformance.com&e=4%3AGTDzi5&fromShare=true&at=9&CID=93410ac1-2838-1df0-cac8-9b2ccfaedfb8&share=ETb7JZ2sQ7RCsjFK6x6S7U4BVYn0WuL_eNkpaHbdnJ1VEw"
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        # Define o caminho de download padrão
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
                    page = await context.new_page()

                    # Abre o link
                    await page.goto(url)

                    await page.wait_for_load_state('networkidle', timeout=120000)  # Aumenta para 120 segundos

                    await page.frame_locator("iframe[name=\"WacFrame_Excel_0\"]").get_by_role("button", name="File").click()
                    print("Clicou no botão 'File'")

                    # Clica no botão "Save As"
                    await page.frame_locator("iframe[name=\"WacFrame_Excel_0\"]").get_by_label("Save As").click()
                    print("Clicou no botão 'Save As'")

                    async with page.expect_download() as download_info:
                        await page.frame_locator("iframe[name=\"WacFrame_Excel_0\"]").get_by_role("button", name="Download a Copy Download a").click()
                        print("Selecionou 'Download a Copy'")
                    download = await download_info.value

                    try:
                        await download.save_as(os.path.join(download_path, download.suggested_filename))
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