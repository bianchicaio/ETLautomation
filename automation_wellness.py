import asyncio
import os
import time
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="wellness_auth.json")
        page = await context.new_page()
        download_path = os.path.join(os.path.expanduser('~'), 'Downloads')

        try:
            # Acessa a URL
            await page.goto("https://teleperformance-my.sharepoint.com/:x:/p/dijkstra_28_emea/ETb7JZ2sQ7RCsjFK6x6S7U4BVYn0WuL_eNkpaHbdnJ1VEw?email=pedro.esteves%40teleperformance.com&e=4%3AGTDzi5&fromShare=true&at=9&CID=93410ac1-2838-1df0-cac8-9b2ccfaedfb8")
            
            # Espera de 15 segundos para garantir o carregamento completo do conteúdo
            print("Esperando 15 segundos para o carregamento completo das tabelas...")
            await asyncio.sleep(30)  # Aguarda 15 segundos

            # Tentativa de clicar no botão "File"
            retries = 15
            clicked = False
            while not clicked and retries > 0:
                try:
                    await page.frame_locator("iframe[name=\"WacFrame_Excel_0\"]").get_by_role("button", name="File").click()
                    print("Clicou em File")
                    await page.frame_locator("iframe[name=\"WacFrame_Excel_0\"]").get_by_label("Save As").click()
                    print("Clicou em Save As")
                    clicked = True
                except Exception as e:
                    print(f"Tentativa de clicar em 'File' falhou: {e}")
                    retries -= 1
                    await asyncio.sleep(2)  # Espera 2 segundos antes de tentar novamente

            # Inicia o download e espera que ele termine
            async with page.expect_download() as download_info:
                await page.frame_locator("iframe[name=\"WacFrame_Excel_0\"]").get_by_role("button", name="Download a Copy Download a").click()
                print("Iniciou o download")

            download = await download_info.value
            await download.save_as(os.path.join(download_path, download.suggested_filename))
            print(f"Arquivo baixado e salvo em: {os.path.join(download_path, download.suggested_filename)}")

        except Exception as e:
            print(f"Ocorreu um erro durante a execução: {e}")
        finally:
            # Fechando o contexto e o navegador corretamente
            await context.close()
            await browser.close()
            print("Navegador fechado")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Erro na execução do asyncio: {e}")
