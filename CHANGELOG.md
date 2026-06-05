# Changelog

Todas as mudanças relevantes do FlowPad são documentadas aqui.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).

---

## [0.7.0] — 2026-06-05 — Monitoramento de Clipboard e Correções

### Adicionado
- Monitoramento automático de clipboard: qualquer `Ctrl+C` salva no histórico sem precisar de hotkey manual (polling a cada 1s via `root.after`, sem nova dependência)
- Toggle "Monitorar clipboard automaticamente" nas configurações (efeito imediato, sem reiniciar)
- Migração automática de dados ao trocar pasta: diálogo pergunta se quer copiar o `entries.json` atual; se a pasta de destino já tiver arquivo, oferece sobrescrever ou manter o existente
- Botão "Restaurar padrões" na seção de hotkeys das configurações

### Alterado
- `Ctrl+Shift+C` (captura manual de clipboard) removido — substituído pelo monitoramento automático
- `Ctrl+Shift+R` migrado para `Ctrl+Alt+R` para evitar conflito com hard-reload do Chrome
- Migração silenciosa no `config.json`: ao iniciar o app, valores antigos (`ctrl+shift+c`, `ctrl+shift+r`) são substituídos automaticamente se o usuário não tiver customizado

### Corrigido
- Hotkeys `Ctrl+Shift+C` e `Ctrl+Shift+R` conflitavam com DevTools e hard-reload do Chrome porque o pynput não suprime eventos — resolvido trocando os padrões para `Ctrl+Alt`

---

## [0.6.0] — 2026-06-05 — Sprint 5: Recursos Avançados

### Adicionado
- **Busca fuzzy em todas as 5 visões**: campo `🔍 Buscar...` em cada visão, filtragem em tempo real com tolerância a erros de digitação (`difflib.SequenceMatcher`, sem nova dependência); `Ctrl+F` foca o campo; `Escape` limpa a busca
- **Edição inline no dashboard**: tecla `E` abre editor no próprio card sem nova janela; `Ctrl+Enter` salva, `Escape` cancela; Notas editam título + conteúdo no painel direito
- **`Storage.update_entry()`**: patch parcial de campos — atualiza apenas os campos passados, preserva os demais
- **`utils/fuzzy.py`**: estratégia tripla — substring exata → similaridade palavra-a-palavra (ratio > 0.7) → similaridade global (ratio > 0.6)
- **Atalho `Ctrl+Alt+R` — Lembrete Direto**: abre quick_capture já em modo Lembrete com campos visíveis imediatamente (parâmetro `start_editing: bool` no `QuickCaptureWindow`)
- **Pasta de dados customizável**: OneDrive, Dropbox ou qualquer pasta local; configurável nas Settings; requer reinício para aplicar
- **Plugin system (base)**: `PluginManager` carrega `.py` de `src/plugins/`; cada plugin expõe `register(app) -> dict` com `types` e `hotkeys`; `example_plugin.py` demonstra tipo "🔖 Favorito"
- Guard `_is_text_focused()` no dashboard: evita disparar atalhos de letra (C, A, E, N) enquanto o campo de busca está focado
- Testes: `tests/test_utils.py` com 8 casos para `fuzzy_match`; `tests/test_storage.py` com 4 casos para `update_entry`

### Alterado
- Settings redesenhada: campo para hotkey do Lembrete Direto; nova seção "Dados & Sincronização"; corrigido bug que apagava `clipboard_capture` ao salvar
- Todas as 5 visões mantêm `_filtered: list[Entry]` — `_nav()`, `select_first()` e `_get_selected()` operam sobre a lista filtrada, compondo busca e filtros existentes

---

## [0.5.0] — 2026-06-05 — Sprint 4: UX Polish e Navegação por Teclado

### Adicionado
- **Dashboard redesenhado** como máquina de estados `menu | view`: 5 cards estilizados por tipo com barra colorida lateral, contagem de entradas e atalhos de letra (`I L C T N`)
- **Navegação por teclado completa nas visões**: `↑↓` navegam a lista; `Enter` executa ação primária; `C` copia; `A` arquiva; `Delete` deleta; `N` nova entrada; `F5` atualiza; `1/2/3` filtram tarefas
- **`select_first()` e `_nav(direction)`** em todos os 5 views para suporte à navegação do dashboard
- **Quick capture reformulada**: Lembrete com 3 campos simultâneos (texto + hora HH:MM + data DD/MM); Nota com título + conteúdo; máscara automática insere `:` e `/` após 2 dígitos e avança o foco

### Corrigido
- Key bindings de visão centralizados no `DashboardWindow` (CTkToplevel) — CTkFrame não recebe foco de teclado, bindings em frames filhos não disparavam

---

## [0.4.0] — 2026-06-05 — Sprint 3: Polish Visual

### Adicionado
- **CustomTkinter 5.2.2**: widgets modernos com suporte a tema dark/light
- **`ui/colors.py`**: paleta centralizada com tuplas `(light, dark)` para troca automática de tema
- Toggle Dark/Light no header do dashboard via `CTkSegmentedButton`
- Animação de fade-in na quick capture (~160ms, 60fps via `wm_attributes("-alpha")`)

### Alterado
- Todos os 5 views migrados de `tk.Listbox` para `ctk.CTkScrollableFrame` com cards clicáveis
- Seleção de item por `entry.id` (UUID) em vez de índice — robusta a re-renders
- Dashboard, quick capture e settings migrados para `ctk.CTkToplevel`
- Root window migrada de `tk.Tk` para `ctk.CTk`

---

## [0.3.0] — 2026-06-05 — Sprint 2: Visões por Tipo

### Adicionado
- **`Entry.completed` + `Storage.toggle_completed()`**: campo booleano para tarefas com toggle atômico no JSON
- **`ui/view_tasks.py`**: lista To-Do com filtros Todas/Pendentes/Concluídas e `Space` para toggle
- **`ui/view_insights.py`**: cards FILO com painel de detalhe e ações copiar/arquivar/deletar
- **`ui/view_clipboard.py`**: cards FILO com ações por item
- **`ui/view_reminders.py`**: ordenado por proximidade; vencidos em vermelho, próximos em verde
- **`ui/view_notes.py`**: painel bipartido — lista de títulos (esquerda) + conteúdo completo (direita)
- Hotkey `Ctrl+Shift+C` para captura direta do clipboard com toast de confirmação
- Quick capture com 5 tipos e máquina de estados multi-passo para Lembrete (texto → hora → data) e Nota (título → conteúdo)
- 4 testes para `completed` e `toggle_completed`

### Alterado
- Dashboard reescrito como hub de abas com `pack/pack_forget`

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
