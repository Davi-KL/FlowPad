"""
core/reminder_scheduler.py
Agendador de lembretes.
Verifica periodicamente se há lembretes a disparar e exibe notificações nativas.
"""

import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta
from core.storage import Storage, Entry


class ReminderScheduler:
    """
    Roda no loop do Tkinter via `after()` — sem threads extras.
    Verifica lembretes a cada CHECK_INTERVAL_MS milissegundos.
    """

    CHECK_INTERVAL_MS = 60_000  # Checa a cada 1 minuto

    def __init__(self, root: tk.Tk, storage: Storage):
        self.root = root
        self.storage = storage
        self._running = False
        self._after_id = None
        self._notified_ids: set[str] = set()  # Evita notificar o mesmo lembrete 2x seguidas

    def start(self):
        self._running = True
        self._schedule_check()

    def stop(self):
        self._running = False
        if self._after_id:
            self.root.after_cancel(self._after_id)

    def _schedule_check(self):
        if not self._running:
            return
        self._check_reminders()
        self._after_id = self.root.after(self.CHECK_INTERVAL_MS, self._schedule_check)

    def _check_reminders(self):
        due = self.storage.get_reminders_due()
        for entry in due:
            if entry.id in self._notified_ids:
                continue
            self._fire_reminder(entry)
            self._notified_ids.add(entry.id)
            self._handle_repeat(entry)

    def _fire_reminder(self, entry: Entry):
        """Exibe uma notificação nativa do Windows."""
        title = entry.title or "Lembrete FlowPad"
        content = entry.content[:200]  # Limita tamanho da notificação
        try:
            # Usa toast do Windows via plyer se disponível
            from plyer import notification
            notification.notify(
                title=title,
                message=content,
                app_name="FlowPad",
                timeout=10,
            )
        except ImportError:
            # Fallback: messagebox do Tkinter
            messagebox.showinfo(f"⏰ {title}", content)

    def _handle_repeat(self, entry: Entry):
        """
        Se o lembrete tem intervalo de repetição, reagenda para o próximo disparo.
        Remove-o dos notificados para que possa disparar novamente.
        """
        if entry.reminder_interval_min and entry.reminder_interval_min > 0:
            next_time = datetime.now() + timedelta(minutes=entry.reminder_interval_min)
            entry.reminder_at = next_time.isoformat()
            self.storage.update(entry)
            # Remove do cache para disparar novamente no próximo ciclo correto
            self._notified_ids.discard(entry.id)
