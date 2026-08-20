BEGIN;

CREATE TABLE IF NOT EXISTS voc_import_batch (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  batch_id varchar(255) NOT NULL,
  product_id varchar(255),
  market varchar(32) NOT NULL DEFAULT 'JP',
  coverage_status varchar(64) NOT NULL DEFAULT 'unverified',
  review_count integer NOT NULL DEFAULT 0,
  manifest_sha256 varchar(64),
  review_note text,
  _created_at TIMESTAMP(3) WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  _created_by user_profile DEFAULT (CASE WHEN current_setting('app.user_id', TRUE) = '' THEN NULL ELSE concat('(', current_setting('app.user_id', TRUE), ')')::user_profile END),
  _updated_at TIMESTAMP(3) WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  _updated_by user_profile DEFAULT (CASE WHEN current_setting('app.user_id', TRUE) = '' THEN NULL ELSE concat('(', current_setting('app.user_id', TRUE), ')')::user_profile END)
);
CREATE UNIQUE INDEX IF NOT EXISTS uk_voc_import_batch_batch_id ON voc_import_batch(batch_id);
ALTER TABLE voc_import_batch ENABLE ROW LEVEL SECURITY;
CREATE POLICY service_role_bypass_policy ON voc_import_batch TO service_role USING (true);
CREATE POLICY "修改全部数据" ON voc_import_batch AS PERMISSIVE FOR ALL TO authenticated USING (true);
CREATE POLICY "查看全部数据" ON voc_import_batch AS PERMISSIVE FOR SELECT TO authenticated, anon USING (true);
CREATE POLICY "修改本人数据" ON voc_import_batch AS PERMISSIVE FOR ALL TO authenticated USING ((current_setting('app.user_id'::text) = ANY (ARRAY[]::text[])) AND (current_setting('app.user_id'::text) = ((_created_by).user_id)::text));

CREATE TABLE IF NOT EXISTS voc_review (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  review_id varchar(255) NOT NULL,
  batch_id varchar(255), product_id varchar(255), source varchar(64), review_date date,
  rating numeric(3,1), sentiment varchar(64), title text, review_text text, source_url text,
  issues_json jsonb NOT NULL DEFAULT '[]'::jsonb, values_json jsonb NOT NULL DEFAULT '[]'::jsonb,
  scenarios_json jsonb NOT NULL DEFAULT '[]'::jsonb, responsibility_owner varchar(255),
  analysis_confidence varchar(32), manual_review_required boolean NOT NULL DEFAULT false,
  _created_at TIMESTAMP(3) WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  _created_by user_profile DEFAULT (CASE WHEN current_setting('app.user_id', TRUE) = '' THEN NULL ELSE concat('(', current_setting('app.user_id', TRUE), ')')::user_profile END),
  _updated_at TIMESTAMP(3) WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  _updated_by user_profile DEFAULT (CASE WHEN current_setting('app.user_id', TRUE) = '' THEN NULL ELSE concat('(', current_setting('app.user_id', TRUE), ')')::user_profile END)
);
COMMENT ON COLUMN voc_review.issues_json IS '@type string[]';
COMMENT ON COLUMN voc_review.values_json IS '@type string[]';
COMMENT ON COLUMN voc_review.scenarios_json IS '@type string[]';
CREATE UNIQUE INDEX IF NOT EXISTS uk_voc_review_review_id ON voc_review(review_id);
CREATE INDEX IF NOT EXISTS idx_voc_review_product_date ON voc_review(product_id, review_date);
ALTER TABLE voc_review ENABLE ROW LEVEL SECURITY;
CREATE POLICY service_role_bypass_policy ON voc_review TO service_role USING (true);
CREATE POLICY "修改全部数据" ON voc_review AS PERMISSIVE FOR ALL TO authenticated USING (true);
CREATE POLICY "查看全部数据" ON voc_review AS PERMISSIVE FOR SELECT TO authenticated, anon USING (true);
CREATE POLICY "修改本人数据" ON voc_review AS PERMISSIVE FOR ALL TO authenticated USING ((current_setting('app.user_id'::text) = ANY (ARRAY[]::text[])) AND (current_setting('app.user_id'::text) = ((_created_by).user_id)::text));

CREATE TABLE IF NOT EXISTS voc_issue (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  issue_key varchar(255) NOT NULL, batch_id varchar(255), product_id varchar(255), issue_name varchar(255),
  priority varchar(32), sample_count integer NOT NULL DEFAULT 0, denominator integer NOT NULL DEFAULT 0,
  negative_rate numeric(7,3), trend varchar(255), confidence varchar(32), evidence_review_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
  workflow_status varchar(64) NOT NULL DEFAULT 'new', owner user_profile, due_date date, review_note text,
  _created_at TIMESTAMP(3) WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  _created_by user_profile DEFAULT (CASE WHEN current_setting('app.user_id', TRUE) = '' THEN NULL ELSE concat('(', current_setting('app.user_id', TRUE), ')')::user_profile END),
  _updated_at TIMESTAMP(3) WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  _updated_by user_profile DEFAULT (CASE WHEN current_setting('app.user_id', TRUE) = '' THEN NULL ELSE concat('(', current_setting('app.user_id', TRUE), ')')::user_profile END)
);
COMMENT ON COLUMN voc_issue.evidence_review_ids IS '@type string[]';
CREATE UNIQUE INDEX IF NOT EXISTS uk_voc_issue_issue_key ON voc_issue(issue_key);
ALTER TABLE voc_issue ENABLE ROW LEVEL SECURITY;
CREATE POLICY service_role_bypass_policy ON voc_issue TO service_role USING (true);
CREATE POLICY "修改全部数据" ON voc_issue AS PERMISSIVE FOR ALL TO authenticated USING (true);
CREATE POLICY "查看全部数据" ON voc_issue AS PERMISSIVE FOR SELECT TO authenticated, anon USING (true);
CREATE POLICY "修改本人数据" ON voc_issue AS PERMISSIVE FOR ALL TO authenticated USING ((current_setting('app.user_id'::text) = ANY (ARRAY[]::text[])) AND (current_setting('app.user_id'::text) = ((_created_by).user_id)::text));

CREATE TABLE IF NOT EXISTS voc_action (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  action_key varchar(255) NOT NULL, batch_id varchar(255), product_id varchar(255), issue_key varchar(255),
  priority varchar(32), action_text text, evidence_text text, success_metric text,
  workflow_status varchar(64) NOT NULL DEFAULT 'new', owner user_profile, due_date date, validation_result text,
  _created_at TIMESTAMP(3) WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  _created_by user_profile DEFAULT (CASE WHEN current_setting('app.user_id', TRUE) = '' THEN NULL ELSE concat('(', current_setting('app.user_id', TRUE), ')')::user_profile END),
  _updated_at TIMESTAMP(3) WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  _updated_by user_profile DEFAULT (CASE WHEN current_setting('app.user_id', TRUE) = '' THEN NULL ELSE concat('(', current_setting('app.user_id', TRUE), ')')::user_profile END)
);
CREATE UNIQUE INDEX IF NOT EXISTS uk_voc_action_action_key ON voc_action(action_key);
ALTER TABLE voc_action ENABLE ROW LEVEL SECURITY;
CREATE POLICY service_role_bypass_policy ON voc_action TO service_role USING (true);
CREATE POLICY "修改全部数据" ON voc_action AS PERMISSIVE FOR ALL TO authenticated USING (true);
CREATE POLICY "查看全部数据" ON voc_action AS PERMISSIVE FOR SELECT TO authenticated, anon USING (true);
CREATE POLICY "修改本人数据" ON voc_action AS PERMISSIVE FOR ALL TO authenticated USING ((current_setting('app.user_id'::text) = ANY (ARRAY[]::text[])) AND (current_setting('app.user_id'::text) = ((_created_by).user_id)::text));

CREATE TABLE IF NOT EXISTS voc_marketing_insight (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  insight_key varchar(255) NOT NULL, batch_id varchar(255), product_id varchar(255), insight_type varchar(64),
  value_or_concern varchar(255), sample_count integer NOT NULL DEFAULT 0, denominator integer NOT NULL DEFAULT 0,
  recommended_message text, avoid_message text, channels text, confidence varchar(32), evidence_review_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
  workflow_status varchar(64) NOT NULL DEFAULT 'new', owner user_profile, experiment_result text,
  _created_at TIMESTAMP(3) WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  _created_by user_profile DEFAULT (CASE WHEN current_setting('app.user_id', TRUE) = '' THEN NULL ELSE concat('(', current_setting('app.user_id', TRUE), ')')::user_profile END),
  _updated_at TIMESTAMP(3) WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  _updated_by user_profile DEFAULT (CASE WHEN current_setting('app.user_id', TRUE) = '' THEN NULL ELSE concat('(', current_setting('app.user_id', TRUE), ')')::user_profile END)
);
COMMENT ON COLUMN voc_marketing_insight.evidence_review_ids IS '@type string[]';
CREATE UNIQUE INDEX IF NOT EXISTS uk_voc_marketing_insight_insight_key ON voc_marketing_insight(insight_key);
ALTER TABLE voc_marketing_insight ENABLE ROW LEVEL SECURITY;
CREATE POLICY service_role_bypass_policy ON voc_marketing_insight TO service_role USING (true);
CREATE POLICY "修改全部数据" ON voc_marketing_insight AS PERMISSIVE FOR ALL TO authenticated USING (true);
CREATE POLICY "查看全部数据" ON voc_marketing_insight AS PERMISSIVE FOR SELECT TO authenticated, anon USING (true);
CREATE POLICY "修改本人数据" ON voc_marketing_insight AS PERMISSIVE FOR ALL TO authenticated USING ((current_setting('app.user_id'::text) = ANY (ARRAY[]::text[])) AND (current_setting('app.user_id'::text) = ((_created_by).user_id)::text));

COMMIT;
