# Changelog

Todas as mudanças relevantes do FlowPad são documentadas aqui.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).

---

## [0.2.0] — 2026-06-05 — Sprint 1: Qualidade e UX

### Adicionado
- Campo de tags na janela de captura rápida (formato: `python, ideia, trabalho`)
- Filtro por tag no dashboard
- Exportação de entradas para `.md`, `.txt` e `.json`
- Tela de configurações de hotkeys (sem editar JSON manualmente)
- Ícone `.ico` real com múltiplas resoluções (16, 32, 48, 64, 128, 256px)
- `CONTRIBUTING.md` com guia completo para contribuidores
- `pytest.ini` para configuração dos testes
- Testes unitários para o módulo `Exporter`

---

## [0.1.0] — 2024-01-01 — Sprint 0: MVP Base

### Adicionado
- Janela de captura rápida com dark theme e navegação 100% pelo teclado
- Dashboard com busca em tempo real e filtro por tipo de entrada
- 5 tipos de entrada: Insight, Lembrete, Clipboard, Tarefa, Nota
- Hotkeys globais configuráveis (`Ctrl+Shift+Space`, `Ctrl+Shift+F`)
- System tray com menu de contexto
- Lembretes com notificações nativas e suporte a repetição
- Persistência em JSON local (`%APPDATA%\FlowPad\entries.json` no Windows)
- Configuração do usuário em JSON com merge profundo para compatibilidade
- Testes unitários para `Storage` e `Config`
- Suporte a PyInstaller para geração de `.exe` standalone
