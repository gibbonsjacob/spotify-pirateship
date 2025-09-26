

CREATE TABLE fact_batch_execution (
    batch_id TEXT PRIMARY KEY,            -- unique ID for the run
    batch_start_ts TEXT NOT NULL,         -- ISO8601 timestamp when batch started
    batch_end_ts TEXT,                    -- ISO8601 timestamp when batch finished
    input_count INTEGER NOT NULL,         -- number of tracks picked up for this run
    success_count INTEGER DEFAULT 0,      -- number of tracks successfully downloaded
    error_count INTEGER DEFAULT 0,        -- number of tracks that failed
    runtime_host TEXT,                    -- optional: machine name / env
    triggered_by TEXT,                    -- optional: user / process trigger
    insert_date                 TEXT DEFAULT (datetime('now'))

);