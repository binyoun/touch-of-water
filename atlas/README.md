# Water Atlas

The participant layer of Touch of Water. Anyone sends a photo of a water they remember, the place it comes from, and a sentence in English and their own language (the same fields a workshop team gives in `teams.json`). Each one becomes a dot on a shared map across Jakarta, Kuala Lumpur and Ho Chi Minh City, in the colour of its photo.

- **Page:** `atlas.html`, live at https://binyoun.github.io/touch-of-water/atlas.html
- **Receiver:** `atlas/Code.gs`, a Google Apps Script web app in the project's Google account. Photos go to a Drive folder, one row per contribution goes to a Sheet.

## What happens to a photo

1. On the phone: the photo is redrawn at most 1600 px on its longest side as a JPEG. This drops its EXIF, GPS included.
2. On the phone, then again on the receiver: the place is rounded to 0.01° (about 1.1 km).
3. The receiver saves the photo privately in Drive and adds a row with status `pending`.
4. Nothing is public until you change the status to `approved`. Photos are shared by link only if the contributor chose "Photo and words".

## Setup (once, about 10 minutes)

1. In the project Google account, create a Google Sheet called **Water Atlas** and a Drive folder called **Water Atlas photos**. Keep both private.
2. Open the Sheet, then **Extensions → Apps Script**. Replace the editor's contents with `atlas/Code.gs`.
3. Paste the Sheet ID and the folder ID into `SHEET_ID` and `FOLDER_ID` at the top.
4. Choose `setup` in the function menu and click **Run**. Approve the permissions (Sheets and Drive).
5. **Deploy → New deployment → Web app.** Execute as: *Me*. Who has access: *Anyone*. Copy the web app URL.
6. Paste the URL into `ATLAS_ENDPOINT` near the top of the script in `atlas.html`, then push to main.

Until step 6, the page runs in test mode: it reads the photo but sends nothing (the payload is printed in the browser console).

After editing `Code.gs`, use **Deploy → Manage deployments → Edit → New version**, so the URL stays the same.

## Moderation

- Check new rows in the Sheet. Open the photo from `photo_file` (a Drive file ID) and check it shows no faces or house numbers.
- Set `status` to `approved` or `rejected`. Approved rows appear on the map within a minute.
- **To remove a contribution** (contributors email their code, the `id` column): set it to `rejected` and delete the photo from the Drive folder.
- `archive` says whether the contributor agreed to keeping it after the exhibition. Delete the `no` rows and their photos when the exhibition closes.

## QR codes

Add `?src=` to record where a contribution came from. It ends up in the `source` column, for example:

- `https://binyoun.github.io/touch-of-water/atlas.html?src=petua-air`
- `https://binyoun.github.io/touch-of-water/atlas.html?src=mmu-2026`

## Reading the Atlas

`GET` on the web app URL returns the approved contributions as JSON:
`{ entries: [{ id, lat, lng, colour, place?, textEn?, textNative?, lang?, credit?, photo? }] }`.
