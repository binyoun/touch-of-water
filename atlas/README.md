# Water Atlas

The participant layer of Touch of Water. Anyone sends a photo of a water they remember, the place it comes from, and a sentence in English and their own language (the same fields a workshop team gives in `teams.json`). Each one becomes a dot on a shared map across Jakarta, Kuala Lumpur and Ho Chi Minh City, in the colour of its photo.

- **Page:** `atlas.html`, live at https://binyoun.github.io/touch-of-water/atlas.html
- **Receiver:** a free Supabase project, set up by `atlas/supabase.sql`. Photos go to a private storage bucket, one row per contribution goes to the `atlas` table.

## What happens to a photo

1. On the phone: the photo is redrawn at most 1600 px on its longest side as a JPEG. This drops its EXIF, GPS included.
2. On the phone, then again in the database: the place is rounded to 0.01° (about 1.1 km).
3. The photo is saved in the private bucket `atlas` under a random name, and a row is added with status `pending`.
4. Nothing is public until you change the status to `approved`. Even then, the photo can be opened only if the contributor chose "Photo and words", and only through a link that expires after an hour.

## Setup (once, about 10 minutes)

1. Sign up at [supabase.com](https://supabase.com) (Continue with GitHub is quickest) and click **New project**. Name it `water-atlas`, choose the **Singapore** region, and save the database password somewhere safe. Wait a minute or two while it starts.
2. Open **SQL Editor** in the left bar, paste the whole of `atlas/supabase.sql`, and click **Run**. It should say "Success. No rows returned".
3. Open **Project Settings → API Keys** (or **Connect**). Copy the **Project URL** and the **publishable key** (or the legacy **anon** key). Never use the secret or `service_role` key here.
4. Paste them into `SUPABASE_URL` and `SUPABASE_KEY` near the top of the script in `atlas.html`, then push to main.

Until step 4, the page runs in test mode: it reads the photo but sends nothing (the payload is printed in the browser console).

The publishable key is meant to be public. The database only lets it upload a new photo, add a pending row, and read approved rows; the table itself has no access rules for visitors at all.

## Moderation

- **Table Editor → atlas** lists every contribution. `photo_path` is where its photo is: **Storage → atlas → in**, then the file with that name. Check it shows no faces or house numbers.
- Set `status` to `approved` or `rejected` from the dropdown. Approved rows appear on the map the next time the page loads.
- **To remove a contribution** (contributors email their code, the `id` column): delete the row, and delete its photo from **Storage → atlas → in**.
- `archive` says whether the contributor agreed to keeping it after the exhibition. Delete the `false` rows and their photos when the exhibition closes.
- A free project pauses after a week with no visits. If the page stops sending, open the project in the dashboard and click **Restore**.

## QR codes

Add `?src=` to record where a contribution came from. It ends up in the `source` column, for example:

- `https://binyoun.github.io/touch-of-water/atlas.html?src=petua-air`
- `https://binyoun.github.io/touch-of-water/atlas.html?src=mmu-2026`

## Reading the Atlas

`POST {SUPABASE_URL}/rest/v1/rpc/atlas_entries` with the publishable key in the `apikey` header returns the approved contributions as JSON:
`[{ id, lat, lng, colour, place?, textEn?, textNative?, lang?, credit?, photoPath? }]`.
