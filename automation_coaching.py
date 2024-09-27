import asyncio
import os
from datetime import datetime, timedelta
import calendar
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import re
import win32com.client as win32


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="lark_auth.json")
        page = await context.new_page()
        download_path = os.path.join(os.path.expanduser('~'), 'Downloads')

        await page.goto("https://teleperformance.larksuite.com/sheets/shtusIaUugKkg91iq4IA1YP2wgd")

        await page.locator("div").filter(has_text=re.compile(r"^0 collaborator in total\+0Share0$")).get_by_role("button").nth(1).click()
        print("Clicou em menu")
        await page.get_by_text("Download As").click()
        print("Clicou em Download As")

        # Inicia o download e espera que ele termine
        async with page.expect_download() as download_info:
            await page.get_by_role("menuitem", name="Excel (.xlsx)").locator("span").nth(1).click()
            print("Iniciou o download Excel")

        download = await download_info.value
        await download.save_as(os.path.join(download_path, download.suggested_filename))
        print(f"Arquivo baixado e salvo em: {os.path.join(download_path, download.suggested_filename)}")
        
        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())