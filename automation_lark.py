import asyncio
import os
import time
import re
from playwright.async_api import async_playwright
import win32com.client as win32

async def download_files():

    success_urls = []

    # URLs das páginas a serem acessadas
    failure_urls = ['https://teleperformance.larksuite.com/sheets/MciUsGYmHh3iOFtJHSxum0uFswb?sheet=ECWE7s',
                'https://teleperformance.larksuite.com/sheets/shtusbL94YqOzSPResz49UNwHYM?sheet=scRTg8',
                'https://teleperformance.larksuite.com/sheets/shtusjLubYGiKkRYwhqySE39Hgg?sheet=XhmUPq',
                'https://teleperformance.larksuite.com/sheets/shtus7tLBP6YaA73FmeLO7aGnTh?sheet=Kh9ZTH',
                'https://teleperformance.larksuite.com/sheets/shtusIbCsBcNIGhr9EsqGg4FHte?sheet=PRHk1L',
                'https://teleperformance.larksuite.com/sheets/shtusJDpWNWcJc7esxbFcKHqowe?sheet=ZzgRZL',
                'https://teleperformance.larksuite.com/sheets/shtusiIjVTZVpOHItQzXmSvYr0g?sheet=ILdzs7',
                'https://teleperformance.larksuite.com/sheets/shtusRvfqaTzYkEzWeBeeCXNl4c?sheet=qjSPUH',
                'https://teleperformance.larksuite.com/sheets/WeuXsloKmh7g1ati1dbuyyVOs2g?sheet=EZ4gyX&table=tblsfbOK4WUfmytg&view=vewc8Ue4n0',
                'https://teleperformance.larksuite.com/sheets/Ufkqsy2WuhHIrHtdzfmuGlEWsEf?sheet=thvKHO'
                ]

    # Cria um browser com os cookies de login
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="lark_auth.json")
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