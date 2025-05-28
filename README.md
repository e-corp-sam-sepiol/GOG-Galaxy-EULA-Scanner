![GOG Galaxy Logo](https://cdn2.steamgriddb.com/icon/a928731e103dfc64c0027fa84709689e/32/256x256.png)

# GOG Galaxy EULA Privacy Scanner

This Python script helps you find, collect, and review the End User License Agreements (EULAs) and similar legal documents for all your installed GOG Galaxy games. It’s designed for privacy-conscious gamers, researchers, and anyone who wants to know exactly what legal terms and privacy policies come with the games they own.

## What Does It Do?

- **Scans your GOG Galaxy folders** and finds every game you have installed.
- **Searches each game’s folder (and subfolders)** for EULA, license, and legal files—covering TXT, PDF, DOCX, RTF, and HTML formats.
- **Matches EULAs to each game** by looking for the game’s name in the file name or inside the document itself, so you don’t end up with unrelated third-party licenses.
- **Optionally analyzes each EULA for privacy concerns** using OpenAI, if you provide an API key.
- **Outputs a CSV report** summarizing what was found for each game, and a clean, readable text dump of all EULAs for manual review.

## Why Use This?

Modern PC games often come bundled with a maze of legal documents—not just for the game itself, but also for middleware, anti-cheat, and other third-party components. If you care about privacy, data collection, or just want to know what you’re agreeing to, finding the actual EULA for each game can be a pain.

This script automates the process, helping you:

- **Quickly see which games have EULAs or privacy policies.**
- **Spot games that may have invasive terms or require extra scrutiny.**
- **Keep a personal archive of all the legal documents attached to your game library.**

## How To Use

1. **Install the required dependencies** (the script will tell you if you’re missing any).
2. **Set your GOG Galaxy install path** in the script if it’s not the default.
3. *(Optional)* Set your OpenAI API key as an environment variable or in the script if you want privacy analysis.
4. **Run the script:**  
```
python gog_eula_privacy_scanner.py
```
5. **Check the output:**
- `gog_eula_privacy_report.csv` — summary for each game.
- `gog_eula_dump.txt` — all EULA/legal text, cleaned up and separated by game.

## Notes

- If you don’t set an OpenAI API key, the script will still collect and organize all EULAs, but won’t perform automated privacy analysis.
- The script tries to be smart about only including relevant EULAs, but some generic or third-party licenses may still show up, especially if a game uses a very generic filename for its EULA.
- This tool is for informational and research purposes only. It does not constitute legal advice.
