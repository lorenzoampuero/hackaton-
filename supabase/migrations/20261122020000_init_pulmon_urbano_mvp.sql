-- Migración inicial Pulmón Urbano v5 (Supabase Project: fommievafrgbyjuvnauy)
CREATE TABLE IF NOT EXISTS public.perfiles_planes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email text UNIQUE NOT NULL,
  nombre text NOT NULL DEFAULT 'Usuario Demo',
  organizacion text NOT NULL DEFAULT 'Municipalidad / Consultora',
  rol text NOT NULL DEFAULT 'Evaluador Territorial',
  plan_id text NOT NULL DEFAULT 'gratis',
  plan_nombre text NOT NULL DEFAULT 'Gratis (Demo / Público)',
  modalidad text NOT NULL DEFAULT 'mensual',
  precio_uf numeric NOT NULL DEFAULT 0,
  precio_clp integer NOT NULL DEFAULT 0,
  exportaciones_usadas integer NOT NULL DEFAULT 0,
  exportaciones_limite integer NOT NULL DEFAULT 2,
  informes_ia_usados integer NOT NULL DEFAULT 0,
  informes_ia_limite integer NOT NULL DEFAULT 0,
  estado text NOT NULL DEFAULT 'activo',
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.casos_guardados (
  id text PRIMARY KEY,
  user_email text NOT NULL DEFAULT 'demo@pulmonurbano.cl',
  comuna_slug text NOT NULL,
  site_id text,
  titulo text NOT NULL,
  tipo_label text NOT NULL DEFAULT 'Caso con IA',
  nota text NOT NULL DEFAULT '',
  foto_data_url text,
  pregunta_ia text,
  respuesta_ia text,
  confianza_pct integer NOT NULL DEFAULT 92,
  paquete jsonb,
  informe jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.consultas_ia (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_email text NOT NULL DEFAULT 'demo@pulmonurbano.cl',
  comuna_slug text,
  site_id text,
  caso_id text,
  pregunta text NOT NULL,
  tiene_imagen boolean NOT NULL DEFAULT false,
  respuesta text NOT NULL,
  modelo text,
  created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.perfiles_planes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.casos_guardados ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.consultas_ia ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "mvp_all_perfiles_planes" ON public.perfiles_planes;
CREATE POLICY "mvp_all_perfiles_planes" ON public.perfiles_planes
  FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "mvp_all_casos_guardados" ON public.casos_guardados;
CREATE POLICY "mvp_all_casos_guardados" ON public.casos_guardados
  FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "mvp_all_consultas_ia" ON public.consultas_ia;
CREATE POLICY "mvp_all_consultas_ia" ON public.consultas_ia
  FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);

INSERT INTO public.perfiles_planes (
  email, nombre, organizacion, rol, plan_id, plan_nombre, modalidad, precio_uf, precio_clp,
  exportaciones_usadas, exportaciones_limite, informes_ia_usados, informes_ia_limite, estado
)
VALUES (
  'demo@pulmonurbano.cl', 'Equipo Evaluador', 'Municipalidad Demo', 'Planificación Urbana',
  'gratis', 'Gratis (Demo / Público)', 'mensual', 0, 0,
  0, 2, 0, 0, 'activo'
)
ON CONFLICT (email) DO NOTHING;
