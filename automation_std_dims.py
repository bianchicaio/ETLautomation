import asyncio
import os
from datetime import datetime, timedelta
import calendar
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import re
import time
import win32com.client as win32


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="wellness_auth.json")
        page = await context.new_page()
        download_path = os.path.join(os.path.expanduser('~'), 'Downloads')

        await page.goto("https://teleperformance.sharepoint.com/:x:/r/sites/S.DAF.Operations_Data_Analytics/_layouts/15/Doc.aspx?sourcedoc=%7B239593F6-9215-440A-A196-777F73C4952C%7D&file=STD_DIMS_TTOK%20new%20(Teams%20Edit).xlsx&action=default&mobileredirect=true&cid=232a65da-64a", timeout=360000)
        await page.wait_for_load_state('networkidle', timeout=360000)
        # await page.pause()
        time.sleep(30)
        await page.frame_locator("iframe[name=\"WacFrame_Excel_0\"]").get_by_role("button", name="File").click()
        print("Clicou em File")

        await page.frame_locator("iframe[name=\"WacFrame_Excel_0\"]").get_by_label("Save As").click()
        print("Selecionou Save As")

        # Inicia o download e espera que ele termine
        async with page.expect_download() as download_info:
            await page.frame_locator("iframe[name=\"WacFrame_Excel_0\"]").get_by_role("button", name="Download a Copy Download a").click()
            print("Iniciou o download")

        download = await download_info.value
        await download.save_as(os.path.join(download_path, download.suggested_filename))
        print(f"Arquivo baixado e salvo em: {os.path.join(download_path, download.suggested_filename)}")
        
        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())