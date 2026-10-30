-- Water Atlas receiver on Supabase. Paste the whole file into the project's
-- SQL Editor and click Run, once. Setup and moderation: atlas/README.md.
--
-- Visitors (the anon key in atlas.html) can do three things and nothing else:
--   1. upload one new JPEG to the private bucket "atlas", under in/<uuid>.jpg
--   2. call atlas_submit() to add a row, which always starts as "pending"
--   3. call atlas_entries() to read approved rows, shaped by what each person chose to show
-- The table itself has no policies, so only you, in the dashboard, can read or change it.

create type public.atlas_status as enum ('pending', 'approved', 'rejected');

create table public.atlas (
  id          text primary key default substr(replace(gen_random_uuid()::text, '-', ''), 1, 8),
  received    timestamptz not null default now(),
  status      public.atlas_status not null default 'pending',
  city        text,
  place       text,
  lat         numeric(5, 2) not null,
  lng         numeric(5, 2) not null,
  text_en     text,
  text_native text,
  lang        text,
  credit      text,
  show        text not null default 'dot' check (show in ('photo', 'words', 'dot')),
  archive     boolean not null default false,
  colour      text not null default '#7fa6c8',
  photo_path  text not null unique,
  source      text not null default 'web'
);

alter table public.atlas enable row level security;
revoke all on public.atlas from anon, authenticated;

-- Plain one-line text, cut to length; empty becomes null.
create function public.atlas_text_(v jsonb, max int) returns text
language sql immutable set search_path = '' as $$
  select nullif(left(trim(regexp_replace(coalesce(v #>> '{}', ''), '[[:cntrl:]]', ' ', 'g')), max), '')
$$;

-- One contribution from atlas.html. The photo is uploaded first; this checks it is
-- there and unused, then adds the row as pending.
create function public.atlas_submit(d jsonb) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  p_lat numeric;
  p_lng numeric;
  path text := d ->> 'photoPath';
  new_id text;
begin
  if coalesce(d ->> 'website', '') <> '' then
    return jsonb_build_object('ok', true, 'id', 'thanks'); -- honeypot: only bots fill it
  end if;

  begin
    p_lat := (d ->> 'lat')::numeric;
    p_lng := (d ->> 'lng')::numeric;
  exception when others then
    return jsonb_build_object('ok', false, 'error', 'place');
  end;
  if p_lat is null or p_lng is null or abs(p_lat) > 90 or abs(p_lng) > 180 then
    return jsonb_build_object('ok', false, 'error', 'place');
  end if;

  if (d -> 'consent') is distinct from 'true'::jsonb then
    return jsonb_build_object('ok', false, 'error', 'consent');
  end if;

  if path is null or path !~ '^in/[0-9a-f-]{36}\.jpg$'
     or not exists (select 1 from storage.objects o where o.bucket_id = 'atlas' and o.name = path)
     or exists (select 1 from public.atlas a where a.photo_path = path) then
    return jsonb_build_object('ok', false, 'error', 'photo');
  end if;

  insert into public.atlas (city, place, lat, lng, text_en, text_native, lang, credit,
                            show, archive, colour, photo_path, source)
  values (
    public.atlas_text_(d -> 'city', 20),
    public.atlas_text_(d -> 'place', 80),
    -- Rounded again here: the page already rounds, but the database never trusts the page.
    round(p_lat, 2),
    round(p_lng, 2),
    public.atlas_text_(d -> 'textEn', 280),
    public.atlas_text_(d -> 'textNative', 280),
    public.atlas_text_(d -> 'lang', 30),
    public.atlas_text_(d -> 'credit', 60),
    case when d ->> 'show' in ('photo', 'words', 'dot') then d ->> 'show' else 'dot' end,
    (d -> 'archive') = 'true'::jsonb,
    case when d ->> 'colour' ~* '^#[0-9a-f]{6}$' then d ->> 'colour' else '#7fa6c8' end,
    path,
    case when d ->> 'source' ~ '^[a-z0-9-]{1,32}$' then d ->> 'source' else 'web' end
  )
  returning id into new_id;

  return jsonb_build_object('ok', true, 'id', new_id);
end
$$;

-- Approved contributions for the map. Words only if the person chose "words" or
-- "photo"; the photo's path only if they chose "photo".
create function public.atlas_entries() returns jsonb
language sql stable security definer set search_path = '' as $$
  select coalesce(jsonb_agg(jsonb_strip_nulls(jsonb_build_object(
    'id', a.id, 'lat', a.lat, 'lng', a.lng, 'colour', a.colour,
    'place',      case when a.show <> 'dot' then a.place end,
    'textEn',     case when a.show <> 'dot' then a.text_en end,
    'textNative', case when a.show <> 'dot' then a.text_native end,
    'lang',       case when a.show <> 'dot' then a.lang end,
    'credit',     case when a.show <> 'dot' then a.credit end,
    'photoPath',  case when a.show = 'photo' then a.photo_path end
  )) order by a.received), '[]'::jsonb)
  from public.atlas a
  where a.status = 'approved'
$$;

-- Whether a stored photo may be shown: approved, and its owner chose "photo".
create function public.atlas_photo_public(path text) returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (select 1 from public.atlas a
                 where a.photo_path = path and a.status = 'approved' and a.show = 'photo')
$$;

revoke execute on function public.atlas_text_(jsonb, int), public.atlas_submit(jsonb),
  public.atlas_entries(), public.atlas_photo_public(text) from public, anon, authenticated;
grant execute on function public.atlas_submit(jsonb), public.atlas_entries(),
  public.atlas_photo_public(text) to anon, authenticated;

-- Photos: a private bucket. Visitors may add new JPEGs up to 4 MB but never list,
-- replace or delete them, and may open one only once it is approved for showing.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('atlas', 'atlas', false, 4194304, array['image/jpeg']);

create policy "atlas: visitors add new photos" on storage.objects
  for insert to anon, authenticated
  with check (bucket_id = 'atlas' and name ~ '^in/[0-9a-f-]{36}\.jpg$');

create policy "atlas: approved photos can be opened" on storage.objects
  for select to anon, authenticated
  using (bucket_id = 'atlas' and public.atlas_photo_public(name));
