-- Menus compartilhados: uma linha por menu_key (entidade 1000, Default) e dados de entidade em entity_menu_data.
-- entities.id: 1 = entity_number 1001 (Verbo Braga, legado); 2 = entity_number 1000 (DeixaEstarService, owner).
-- Rodar dentro de transacao; conferir os SELECTs de verificacao antes do COMMIT.

BEGIN;

CREATE TABLE IF NOT EXISTS entity_menu_data (
    entity_id INTEGER NOT NULL,
    menu_key VARCHAR(80) NOT NULL,
    data_key VARCHAR(80) NOT NULL,
    data TEXT,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (entity_id, menu_key, data_key)
);

-- 1) Perfis e funcoes de autorizacao: so para a entidade 1001 (id 1).
INSERT INTO entity_menu_data (entity_id, menu_key, data_key, data, updated_at)
SELECT 1, 'administrativo', k, (menu_config::jsonb -> k)::text, CURRENT_TIMESTAMP
FROM sidebar_menu_settings, unnest(ARRAY['authorization_functions', 'authorization_profile_fields']) AS k
WHERE lower(trim(menu_key)) = 'administrativo'
  AND entity_id = 1
  AND (menu_config::jsonb) ? k
ON CONFLICT (entity_id, menu_key, data_key) DO NOTHING;

-- 2) Remove os dados de entidade da linha compartilhada (entidade 2).
UPDATE sidebar_menu_settings
SET menu_config = ((menu_config::jsonb) - 'authorization_functions' - 'authorization_profile_fields')::text
WHERE lower(trim(menu_key)) = 'administrativo'
  AND entity_id = 2;

-- 3) Remove as copias da entidade 1 cujo menu tambem existe na entidade 2.
DELETE FROM sidebar_menu_settings s1
WHERE s1.entity_id = 1
  AND EXISTS (
      SELECT 1 FROM sidebar_menu_settings s2
      WHERE s2.entity_id = 2 AND s2.menu_key = s1.menu_key
  );

-- 4) Menus que existiam so na entidade 1 passam a ser Default da entidade 2.
UPDATE sidebar_menu_settings SET entity_id = 2 WHERE entity_id = 1;

-- Verificacao (esperado: 16 linhas, todas entity_id 2; entity_menu_data com 2 linhas para entity_id 1).
SELECT entity_id, count(*) AS menus FROM sidebar_menu_settings GROUP BY entity_id;
SELECT entity_id, menu_key, data_key FROM entity_menu_data ORDER BY 1, 2, 3;

COMMIT;
