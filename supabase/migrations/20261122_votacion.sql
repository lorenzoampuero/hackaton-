-- Pulmón Urbano: votación vecinal (épocas de votación y votos anónimos).
-- Ejecútalo una vez en el SQL Editor de TU proyecto de Supabase (el mismo de SUPABASE_URL en .env).
-- La app usa la clave secreta desde el servidor; las tablas quedan cerradas al acceso público (RLS sin políticas).

create table if not exists public.votacion_periodos (
  id text primary key,
  comuna_slug text not null,
  nombre text not null,
  abre_en timestamptz not null,
  cierra_en timestamptz not null,
  cerrado_manual boolean not null default false,
  demo boolean not null default false,
  creado_en timestamptz not null default now(),
  check (cierra_en > abre_en)
);

create table if not exists public.votacion_votos (
  id text primary key,
  periodo_id text not null references public.votacion_periodos (id) on delete cascade,
  comuna_slug text not null,
  site_id text not null,
  opcion_id text not null,
  otro_texto text check (otro_texto is null or char_length(otro_texto) <= 280),
  edad_rango text check (edad_rango is null or edad_rango in ('menos_18', '18_29', '30_44', '45_59', '60_mas')),
  dispositivo_hash text not null,
  via_qr boolean not null default false,
  demo boolean not null default false,
  creado_en timestamptz not null default now(),
  unique (periodo_id, site_id, dispositivo_hash)
);

create index if not exists votacion_votos_periodo_sitio on public.votacion_votos (periodo_id, site_id);
create index if not exists votacion_periodos_comuna on public.votacion_periodos (comuna_slug, abre_en desc);

alter table public.votacion_periodos enable row level security;
alter table public.votacion_votos enable row level security;
-- Sin políticas: solo el servidor (clave secreta / service role) puede leer y escribir.
