-- Reference DDL r4: validate in-memory only during specs. No user database created.
PRAGMA foreign_keys=ON;
CREATE TABLE company (
 id TEXT PRIMARY KEY, name TEXT NOT NULL CHECK(length(trim(name))>0), notes TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL, archived_at TEXT
);
CREATE TABLE contact (
 id TEXT PRIMARY KEY, company_id TEXT NOT NULL REFERENCES company(id) ON DELETE RESTRICT,
 name TEXT NOT NULL DEFAULT '', email TEXT NOT NULL, email_key TEXT NOT NULL CHECK(length(email_key)>0),
 created_at TEXT NOT NULL, archived_at TEXT, UNIQUE(company_id,email_key)
);
CREATE TABLE campaign (
 id TEXT PRIMARY KEY, title TEXT NOT NULL, topic TEXT NOT NULL, objective TEXT NOT NULL,
 audience_segment TEXT NOT NULL, tone TEXT NOT NULL, formats_json TEXT NOT NULL,
 config_revision INTEGER NOT NULL DEFAULT 1 CHECK(config_revision>0), created_at TEXT NOT NULL, archived_at TEXT
);
CREATE TABLE campaign_recipient (
 id TEXT PRIMARY KEY, campaign_id TEXT NOT NULL REFERENCES campaign(id) ON DELETE RESTRICT,
 contact_id TEXT NOT NULL REFERENCES contact(id) ON DELETE RESTRICT, email_key TEXT NOT NULL,
 snapshot_json TEXT NOT NULL, selected_at TEXT NOT NULL, archived_at TEXT,
 UNIQUE(campaign_id,email_key), UNIQUE(id,campaign_id)
);
CREATE TABLE generation_run (
 id TEXT PRIMARY KEY, campaign_id TEXT NOT NULL REFERENCES campaign(id) ON DELETE RESTRICT,
 status TEXT NOT NULL CHECK(status IN ('prepared','running','waiting_input','needs_review','finished','failed','cancelled')),
 step TEXT NOT NULL, config_revision INTEGER NOT NULL, config_json TEXT NOT NULL, sources_json TEXT NOT NULL,
 context_json TEXT NOT NULL, metrics_json TEXT NOT NULL DEFAULT '{}', error_json TEXT,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL, UNIQUE(id,campaign_id)
);
CREATE TABLE content_version (
 id TEXT PRIMARY KEY, campaign_id TEXT NOT NULL REFERENCES campaign(id) ON DELETE RESTRICT,
 run_id TEXT, format TEXT NOT NULL CHECK(format IN ('linkedin','email','article','ad')),
 variant TEXT NOT NULL DEFAULT '', revision_no INTEGER NOT NULL CHECK(revision_no>0),
 body TEXT NOT NULL, content_hash TEXT NOT NULL CHECK(length(content_hash)=64),
 origin TEXT NOT NULL CHECK(origin IN ('generated','human_edit','manual_external')),
 parent_version_id TEXT, created_at TEXT NOT NULL,
 UNIQUE(id,campaign_id), UNIQUE(campaign_id,format,variant,revision_no),
 FOREIGN KEY(run_id,campaign_id) REFERENCES generation_run(id,campaign_id) ON DELETE RESTRICT,
 FOREIGN KEY(parent_version_id,campaign_id) REFERENCES content_version(id,campaign_id) ON DELETE RESTRICT
);
CREATE TABLE approval (
 id TEXT PRIMARY KEY, campaign_id TEXT NOT NULL REFERENCES campaign(id) ON DELETE RESTRICT,
 run_id TEXT, config_revision INTEGER NOT NULL, version_manifest_json TEXT NOT NULL,
 source_hash TEXT NOT NULL CHECK(length(source_hash)=64), context_hash TEXT NOT NULL CHECK(length(context_hash)=64),
 revision_hash TEXT NOT NULL CHECK(length(revision_hash)=64), actor TEXT NOT NULL, approved_at TEXT NOT NULL,
 UNIQUE(id,campaign_id), FOREIGN KEY(run_id,campaign_id) REFERENCES generation_run(id,campaign_id) ON DELETE RESTRICT
);
CREATE TABLE export_record (
 id TEXT PRIMARY KEY, campaign_id TEXT NOT NULL REFERENCES campaign(id) ON DELETE RESTRICT,
 approval_id TEXT NOT NULL, operation_id TEXT NOT NULL UNIQUE, payload_hash TEXT NOT NULL,
 files_manifest_json TEXT NOT NULL, occurred_at TEXT NOT NULL,
 FOREIGN KEY(approval_id,campaign_id) REFERENCES approval(id,campaign_id) ON DELETE RESTRICT
);
CREATE TABLE distribution_record (
 id TEXT PRIMARY KEY, campaign_id TEXT NOT NULL REFERENCES campaign(id) ON DELETE RESTRICT,
 content_version_id TEXT NOT NULL, campaign_recipient_id TEXT,
 kind TEXT NOT NULL CHECK(kind IN ('email_sent','publication')),
 channel TEXT NOT NULL CHECK(channel IN ('email','linkedin','web','ad','other_public')),
 occurred_at TEXT NOT NULL, recorded_at TEXT NOT NULL, actor TEXT NOT NULL,
 destination_snapshot_json TEXT NOT NULL, public_url TEXT, batch_id TEXT,
 operation_id TEXT NOT NULL, operation_item_key TEXT NOT NULL UNIQUE, payload_hash TEXT NOT NULL,
 batch_size INTEGER NOT NULL DEFAULT 1 CHECK(batch_size>0), repeat_reason TEXT,
 supersedes_id TEXT UNIQUE, correction_reason TEXT,
 UNIQUE(id,campaign_id),
 CHECK((kind='email_sent' AND channel='email' AND campaign_recipient_id IS NOT NULL AND public_url IS NULL)
    OR (kind='publication' AND channel<>'email' AND campaign_recipient_id IS NULL)),
 CHECK(supersedes_id IS NULL OR (supersedes_id<>id AND correction_reason IS NOT NULL AND length(trim(correction_reason))>0)),
 FOREIGN KEY(content_version_id,campaign_id) REFERENCES content_version(id,campaign_id) ON DELETE RESTRICT,
 FOREIGN KEY(campaign_recipient_id,campaign_id) REFERENCES campaign_recipient(id,campaign_id) ON DELETE RESTRICT,
 FOREIGN KEY(supersedes_id,campaign_id) REFERENCES distribution_record(id,campaign_id) ON DELETE RESTRICT
);
CREATE TABLE followup_event (
 id TEXT PRIMARY KEY, campaign_id TEXT NOT NULL REFERENCES campaign(id) ON DELETE RESTRICT,
 campaign_recipient_id TEXT, distribution_id TEXT,
 kind TEXT NOT NULL CHECK(kind IN ('response','note','next_step')), body TEXT NOT NULL CHECK(length(trim(body))>0),
 occurred_at TEXT NOT NULL, recorded_at TEXT NOT NULL, due_at TEXT, actor TEXT NOT NULL,
 supersedes_id TEXT UNIQUE, correction_reason TEXT, UNIQUE(id,campaign_id),
 CHECK(supersedes_id IS NULL OR (supersedes_id<>id AND correction_reason IS NOT NULL AND length(trim(correction_reason))>0)),
 FOREIGN KEY(campaign_recipient_id,campaign_id) REFERENCES campaign_recipient(id,campaign_id) ON DELETE RESTRICT,
 FOREIGN KEY(distribution_id,campaign_id) REFERENCES distribution_record(id,campaign_id) ON DELETE RESTRICT,
 FOREIGN KEY(supersedes_id,campaign_id) REFERENCES followup_event(id,campaign_id) ON DELETE RESTRICT
);
CREATE TABLE operator_credentials (
 id INTEGER PRIMARY KEY CHECK(id=1), encoded_password_hash TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE INDEX idx_run_campaign ON generation_run(campaign_id,created_at);
CREATE INDEX idx_content_campaign ON content_version(campaign_id,format,created_at);
CREATE INDEX idx_dist_recipient ON distribution_record(campaign_id,campaign_recipient_id,content_version_id);
CREATE INDEX idx_followup_recipient ON followup_event(campaign_id,campaign_recipient_id,occurred_at);
-- JSON DTO structure, approval manifest membership/hash, logical-piece parent match,
-- same-recipient followup consistency, email-format send check, and idempotent batch
-- payload agreement are SERVICE invariants tested separately; DDL alone is insufficient.
CREATE TRIGGER immutable_content_version_update BEFORE UPDATE ON content_version BEGIN SELECT RAISE(ABORT,'immutable record; append a new revision/event'); END;
CREATE TRIGGER immutable_content_version_delete BEFORE DELETE ON content_version BEGIN SELECT RAISE(ABORT,'immutable record; append a new revision/event'); END;
CREATE TRIGGER immutable_approval_update BEFORE UPDATE ON approval BEGIN SELECT RAISE(ABORT,'immutable record; append a new revision/event'); END;
CREATE TRIGGER immutable_approval_delete BEFORE DELETE ON approval BEGIN SELECT RAISE(ABORT,'immutable record; append a new revision/event'); END;
CREATE TRIGGER immutable_export_record_update BEFORE UPDATE ON export_record BEGIN SELECT RAISE(ABORT,'immutable record; append a new revision/event'); END;
CREATE TRIGGER immutable_export_record_delete BEFORE DELETE ON export_record BEGIN SELECT RAISE(ABORT,'immutable record; append a new revision/event'); END;
CREATE TRIGGER immutable_distribution_record_update BEFORE UPDATE ON distribution_record BEGIN SELECT RAISE(ABORT,'immutable record; append a new revision/event'); END;
CREATE TRIGGER immutable_distribution_record_delete BEFORE DELETE ON distribution_record BEGIN SELECT RAISE(ABORT,'immutable record; append a new revision/event'); END;
CREATE TRIGGER immutable_followup_event_update BEFORE UPDATE ON followup_event BEGIN SELECT RAISE(ABORT,'immutable record; append a new revision/event'); END;
CREATE TRIGGER immutable_followup_event_delete BEFORE DELETE ON followup_event BEGIN SELECT RAISE(ABORT,'immutable record; append a new revision/event'); END;
