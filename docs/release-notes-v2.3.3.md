**What's Changed**

**Download Queue and Shutdown Reliability**

Fixed an issue where quickly pausing and resuming a download could leave it waiting indefinitely. The latest resume request is now preserved until the previous worker releases the task.

Paused workers are now awakened during shutdown. Workers retiring after a concurrency change remain tracked, and window closure waits for download workers to stop.

Failed file deletions now keep the task in the list so users can retry.

**Cookie and Saved Data Handling**

Empty or malformed saved cookie files are now removed before downloading or analyzing playlists. Unreadable files are skipped, and cookie deletion failures no longer interrupt downloads. Videos requiring authentication may require signing in again.

Invalid settings file encoding now falls back to default settings, and malformed download folder values fall back to an alternative download folder.

Malformed saved task records and duplicate task IDs are skipped so valid tasks can still be restored.

**Development and Testing**

Removed unused metadata preflight code, legacy download wrappers, obsolete quality helpers, unused worker state, and the unused non-strict binary update checker.

Added regression coverage for cookie validation, saved data recovery, rapid pause/resume, worker shutdown, and failed file deletion.

Updated the application version to **v2.3.3**.
