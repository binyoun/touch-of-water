/**
 * Water Atlas receiver: a Google Apps Script web app owned by the project's Google
 * account. The upload page (atlas.html) POSTs one contribution as JSON; this saves the
 * photo to a Drive folder and a row to a Sheet with status "pending". The artist
 * changes status to "approved" by hand. GET returns approved contributions only,
 * shaped by what each contributor chose to show. Setup and moderation: atlas/README.md.
 */

const SHEET_ID = 'PASTE_SHEET_ID';   // from the Sheet's URL: /spreadsheets/d/<this>/edit
const FOLDER_ID = 'PASTE_FOLDER_ID'; // from the Drive folder's URL: /folders/<this>
const SHEET_NAME = 'Atlas';

const HEADERS = ['received', 'id', 'status', 'city', 'place', 'lat', 'lng', 'text_en', 'text_native', 'lang',
  'credit', 'show', 'archive', 'colour', 'photo_file', 'source', 'shared'];
const COL = Object.fromEntries(HEADERS.map((h, i) => [h, i]));
const SHOWS = ['photo', 'words', 'dot'];
const MAX_PHOTO_BYTES = 4 * 1024 * 1024;
const CACHE_SECONDS = 60;

/** Run once from the editor: writes the header row and the status dropdown. */
function setup() {
  const sh = sheet_();
  sh.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]).setFontWeight('bold');
  sh.setFrozenRows(1);
  const rule = SpreadsheetApp.newDataValidation()
    .requireValueInList(['pending', 'approved', 'rejected'], true).build();
  sh.getRange(2, COL.status + 1, sh.getMaxRows() - 1, 1).setDataValidation(rule);
  DriveApp.getFolderById(FOLDER_ID); // fails here, not on the first visitor, if the ID is wrong
}

function doPost(e) {
  let d;
  try { d = JSON.parse(e.postData.contents); } catch (err) { return json_({ ok: false, error: 'bad request' }); }
  if (d.website) return json_({ ok: true, id: 'thanks' }); // honeypot: only bots fill it

  const lat = Number(d.lat), lng = Number(d.lng);
  if (!isFinite(lat) || !isFinite(lng) || Math.abs(lat) > 90 || Math.abs(lng) > 180) return json_({ ok: false, error: 'place' });
  if (d.consent !== true) return json_({ ok: false, error: 'consent' });
  if (typeof d.photo !== 'string' || d.photo.length > MAX_PHOTO_BYTES * 1.4) return json_({ ok: false, error: 'photo' });

  const bytes = Utilities.base64Decode(d.photo);
  if (bytes.length > MAX_PHOTO_BYTES || bytes[0] !== -1 || bytes[1] !== -40) return json_({ ok: false, error: 'photo' }); // JPEG starts FF D8

  const id = Utilities.getUuid().slice(0, 8);
  const file = DriveApp.getFolderById(FOLDER_ID).createFile(Utilities.newBlob(bytes, 'image/jpeg', 'atlas-' + id + '.jpg'));

  const row = [];
  row[COL.received] = new Date();
  row[COL.id] = id;
  row[COL.status] = 'pending';
  row[COL.city] = text_(d.city, 20);
  row[COL.place] = text_(d.place, 80);
  // Rounded again here: the page already rounds, but the sheet never trusts the page.
  row[COL.lat] = Math.round(lat * 100) / 100;
  row[COL.lng] = Math.round(lng * 100) / 100;
  row[COL.text_en] = text_(d.textEn, 280);
  row[COL.text_native] = text_(d.textNative, 280);
  row[COL.lang] = text_(d.lang, 30);
  row[COL.credit] = text_(d.credit, 60);
  row[COL.show] = SHOWS.indexOf(d.show) >= 0 ? d.show : 'dot';
  row[COL.archive] = d.archive === true ? 'yes' : 'no';
  row[COL.colour] = /^#[0-9a-f]{6}$/i.test(d.colour) ? d.colour : '#7fa6c8';
  row[COL.photo_file] = file.getId();
  row[COL.source] = /^[a-z0-9-]{1,32}$/.test(d.source) ? d.source : 'web';
  row[COL.shared] = 'no';

  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try { sheet_().appendRow(row); } finally { lock.releaseLock(); }
  return json_({ ok: true, id: id });
}

/** Approved contributions for the map, cached for a minute. */
function doGet() {
  const cache = CacheService.getScriptCache();
  const hit = cache.get('entries');
  if (hit) return ContentService.createTextOutput(hit).setMimeType(ContentService.MimeType.JSON);

  const sh = sheet_();
  const rows = sh.getDataRange().getValues();
  const entries = [];
  for (let i = 1; i < rows.length; i++) {
    const r = rows[i];
    if (r[COL.status] !== 'approved') continue;
    const e = { id: r[COL.id], lat: r[COL.lat], lng: r[COL.lng], colour: r[COL.colour] };
    if (r[COL.show] === 'photo' || r[COL.show] === 'words') {
      e.place = r[COL.place]; e.textEn = r[COL.text_en]; e.textNative = r[COL.text_native]; e.lang = r[COL.lang]; e.credit = r[COL.credit];
    }
    if (r[COL.show] === 'photo') {
      // A photo is shared by link only once it is approved and its owner chose to show it.
      if (r[COL.shared] !== 'yes') {
        DriveApp.getFileById(r[COL.photo_file]).setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
        sh.getRange(i + 1, COL.shared + 1).setValue('yes');
      }
      e.photo = 'https://drive.google.com/thumbnail?id=' + r[COL.photo_file] + '&sz=w800';
    }
    entries.push(e);
  }
  const out = JSON.stringify({ entries: entries });
  cache.put('entries', out, CACHE_SECONDS);
  return ContentService.createTextOutput(out).setMimeType(ContentService.MimeType.JSON);
}

function sheet_() {
  const ss = SpreadsheetApp.openById(SHEET_ID);
  return ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);
}

// Plain one-line text, cut to length. A leading = + - @ would run as a formula in the sheet.
function text_(v, max) {
  const s = String(v == null ? '' : v).replace(/[\u0000-\u001f\u007f]/g, ' ').trim().slice(0, max);
  return /^[=+\-@]/.test(s) ? "'" + s : s;
}

function json_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}
