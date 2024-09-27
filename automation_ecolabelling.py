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
        context = await browser.new_context(storage_state="wellness_auth.json")
        page = await context.new_page()
        download_path = os.path.join(os.path.expanduser('~'), 'Downloads')

        await page.goto("https://teleperformance.sharepoint.com/sites/TikTok212/Shared%20Documents/Forms/AllItems.aspx?csf=1&web=1&e=Pe8zSi&CID=67a3b62f%2D3b2d%2D4a35%2D9077%2D9b06b0ce1e66&FolderCTID=0x012000B98B5AF80497F14392E44394E54AA19B&id=%2Fsites%2FTikTok212%2FShared%20Documents%2FData%20Analytics%2F1%2E%20Quality%20files%20for%20DA%20Team%20PBI%20reports&viewid=4d19ea0e%2D0774%2D4a0a%2D8fc4%2D204e3ee1184f")
        await page.get_by_role("link", name="ADSO").click()
        print("Clicou em ADSO")

        await page.get_by_role("checkbox", name="Ecolabeling Accuracy").click()
        print("Selecionou Ecolabelling")
        
        await page.get_by_role("button", name="Show more actions for this").click()

        # Inicia o download e espera que ele termine
        async with page.expect_download() as download_info:
            await page.get_by_label("Download").click()
            print("Iniciou o download")

        download = await download_info.value
        await download.save_as(os.path.join(download_path, download.suggested_filename))
        print(f"Arquivo baixado e salvo em: {os.path.join(download_path, download.suggested_filename)}")
        
        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())