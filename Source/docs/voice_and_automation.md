**Voice, Automation & Hooks**

- **Voice Support:** Add a TTS/STT layer. For local, use Vosk (STT) + Coqui/Flite (TTS) and pipe transcripts into the CLI/web interface. For cloud, use provider ASR/TTS with local privacy controls.
- **Automation Hooks:** Implement scheduled jobs (cron-like) to run analytics (monthly savings) and to send reminders. Add a worker queue (SQLite-based or Redis) and a scheduler component that triggers automations.
- **Example automation:** Expense reminder: schedule rule -> query expenses table for new uncategorized items -> send notification via local desktop notifier or email.
- **Security:** Ensure automation actions require authorization and audit logs.
