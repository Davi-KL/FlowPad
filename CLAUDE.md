[# CLAUDE.md — FlowPad

> **Este arquivo é o guia principal para o Claude Code trabalhar neste projeto.**
> Ele deve ser lido integralmente antes de qualquer ação.
> **Regra obrigatória:** Este arquivo deve ser atualizado ao final de cada sprint e sempre que uma decisão ou alteração relevante for tomada.

---

## 📌 Visão Geral do Projeto

**FlowPad** é um aplicativo desktop open source para Windows (compatível com Linux/Mac) que resolve um problema específico de desenvolvedores e pessoas criativas em estado de _flow_: capturar ideias, insights, lembretes e informações de forma extremamente rápida — sem quebrar o fluxo de trabalho.

- **Problema:** Sair do contexto atual para anotar algo quebra o estado de concentração.
- **Solução:** Um app que roda em background, ativado por hotkeys globais, com UI minimalista e navegação 100% pelo teclado.
- **Público-alvo:** Desenvolvedores, designers, escritores, qualquer pessoa que trabalha com foco intenso.

---

## 🏗️ Arquitetura do Projeto

```
flowpad/
├── src/
│   ├── main.py                  # Ponto de entrada
│   ├── core/
│   │   ├── app.py               # Controlador central (orquestra tudo)
│   │   ├── storage.py           # Persistência JSON (CRUD de entradas)
│   │   ├── hotkey_manager.py    # Hotkeys globais via pynput
│   │   └── reminder_scheduler.py # Agendador de lembretes
│   ├── ui/
│   │   ├── tray_icon.py         # Ícone da bandeja do sistema
│   │   ├── quick_capture.py     # Janela popup de captura rápida ⭐
│   │   ├── dashboard.py         # Hub de abas (orquestra as 5 visões)
│   │   ├── view_insights.py     # Aba: cards de insights FILO
│   │   ├── view_reminders.py    # Aba: lembretes por proximidade
│   │   ├── view_clipboard.py    # Aba: clipboard FILO + Ctrl+Shift+C
│   │   ├── view_tasks.py        # Aba: to-do com toggle de conclusão
│   │   └── view_notes.py        # Aba: lista de títulos + painel de conteúdo
│   └── utils/
│       └── config.py            # Configurações do usuário (JSON)
├── tests/
│   ├── test_storage.py
│   └── test_config.py
├── docs/
│   └── (gerado nas sprints)
├── assets/
│   └── (ícones, imagens)
├── requirements.txt
├── flowpad.spec                 # PyInstaller — gera o .exe
└── CLAUDE.md                   # Este arquivo
```

### Fluxo de dados

```
Hotkey pressionada
    → HotkeyManager detecta (thread pynput)
    → Chama root.after() [thread safety]
    → FlowPadApp.open_quick_capture()
    → QuickCaptureWindow abre
    → Usuário preenche e pressiona Ctrl+Enter
    → Entry criada → Storage.save() → JSON gravado em disco
    → Janela fecha com flash de confirmação
```

---

## 🛠️ Stack Tecnológica

| Tecnologia | Versão | Por quê |
|---|---|---|
| **Python** | 3.11+ | Ecossistema rico, baixa barreira de entrada para contribuidores open source |
| **Tkinter** | built-in | Sem dependências externas de UI, disponível em qualquer Python, suficiente para o MVP |
| **pynput** | 1.7.6 | Hotkeys globais confiáveis em Windows/Linux/Mac |
| **pystray** | 0.19.5 | System tray nativo multiplataforma |
| **Pillow** | 10.3.0 | Geração do ícone do tray programaticamente |
| **plyer** | 2.1.0 | Notificações nativas do SO |
| **PyInstaller** | 6.6.0 | Geração do `.exe` standalone sem precisar do Python instalado |
| **pytest** | 8.2.0 | Testes unitários |
| **ruff + black** | latest | Linting e formatação consistente |

### Por que JSON e não SQLite?

Escolha intencional para o MVP:
- **Portabilidade:** O arquivo de dados pode ser aberto, editado, versionado e compartilhado por qualquer pessoa.
- **Contribuição open source:** Contribuidores não precisam conhecer SQL para entender o modelo de dados.
- **Debugging:** Fácil inspecionar o estado da aplicação sem ferramentas externas.
- **Migração futura:** Quando necessário, a camada `Storage` pode ser reimplementada com SQLite sem mudar nenhuma outra parte do código.

### Por que Tkinter e não CustomTkinter/PyQt?

- Tkinter é **built-in** — zero instalação extra para quem clonar o projeto.
- Para o MVP, a funcionalidade supera a estética.
- Sprint 3 já prevê migração para **CustomTkinter** para melhorar a UI sem mudar a lógica.

---

## ⌨️ Atalhos de Teclado

### Globais (funcionam em qualquer app)

| Atalho | Ação |
|---|---|
| `Ctrl + Shift + Space` | Abre janela de captura rápida |
| `Ctrl + Shift + F` | Abre o dashboard |

### Na janela de captura rápida

| Atalho | Ação |
|---|---|
| `1` – `5` | Trocar tipo em modo seleção |
| `Enter` | Confirmar tipo e abrir campos |
| `Escape` | Fechar sem salvar |
| `Enter` | Salvar (campo único: insight, clipboard, tarefa) |
| `Shift + Enter` | Nova linha (campo único) |
| `Ctrl + Enter` | Salvar (Lembrete e Nota, de qualquer campo) |
| `Tab` / `Enter` | Avançar campo (Lembrete: texto → hora → data) |
| `Enter` no título | Mover foco ao conteúdo (Nota) |

### No dashboard — Menu principal

| Atalho | Ação |
|---|---|
| `↑ / ↓` | Navegar entre cards |
| `Enter` | Abrir visão do card selecionado |
| `I` / `L` / `C` / `T` / `N` | Abrir Insights / Lembretes / Clipboard / Tarefas / Notas |
| `Escape` | Fechar o dashboard |

### No dashboard — Dentro de uma visão

| Atalho | Ação |
|---|---|
| `↑ / ↓` | Navegar pelos itens da lista |
| `Enter` | Ação primária (copiar ou marcar tarefa) |
| `Space` | Marcar / desmarcar tarefa |
| `C` | Copiar item selecionado |
| `A` | Arquivar item selecionado |
| `Delete` | Deletar item selecionado |
| `N` | Nova captura no tipo atual |
| `F5` | Atualizar lista |
| `1` / `2` / `3` | Filtrar tarefas: Todas / Pendentes / Concluídas |
| `Escape` | Voltar ao menu principal |

---

## 📦 Tipos de Entrada

| Chave | Label | Cor | Uso |
|---|---|---|---|
| `insight` | 💡 Insight | Amarelo `#F4C542` | Ideias criativas, percepções |
| `reminder` | ⏰ Lembrete | Vermelho `#E05C5C` | Coisas para fazer com prazo |
| `clipboard` | 📋 Clipboard | Azul `#5CB8E0` | Textos, links, trechos de código |
| `task` | ✅ Tarefa | Verde `#5CE07A` | Ações concretas a executar |
| `note` | 📝 Nota | Roxo `#A07AE0` | Notas livres, referências |

---

## 🚀 Como Rodar

### Instalação

```bash
# Clone o repositório
git clone https://github.com/Davi-KL/FlowPad.git
cd flowpad

# Crie um ambiente virtual (recomendado)
python -m venv .venv
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # Linux/Mac

# Instale as dependências
pip install -r requirements.txt
```

### Executar em modo desenvolvimento

```bash
python src/main.py
```

### Rodar os testes

```bash
pytest tests/ -v
pytest tests/ --cov=src --cov-report=html  # Com cobertura
```

### Gerar o .exe

```bash
pyinstaller flowpad.spec
# O executável estará em dist/FlowPad.exe
```

---

## 📋 Roadmap de Sprints

### ✅ Sprint 4 — UX Polish & Navegação por Teclado (concluída)

**Objetivo:** Redesenhar o dashboard como menu de cards, adicionar navegação completa por teclado nas visões e reformular a captura rápida com layout multi-campo para Lembrete e Nota.

**O que foi entregue:**
- [x] **[REFACTOR] `ui/dashboard.py`** — reescrito como máquina de estados `menu` | `view`; menu com 5 cards estilizados (barra colorida por tipo, contagem de entradas, atalhos de letra I/L/C/T/N, navegação ↑↓/Enter)
- [x] **[FEAT] Navegação por teclado nas visões** — auto-seleção do primeiro item ao abrir; ↑↓ navegam a lista; Enter executa ação primária; C/A/Del funcionam em todas as visões; 1/2/3 filtram tarefas
- [x] **[FEAT] `select_first()` e `_nav()`** — adicionados aos 5 views para suportar navegação do dashboard
- [x] **[REFACTOR] `ui/quick_capture.py`** — Lembrete com 3 campos simultâneos (texto + hora HH:MM + data DD/MM); Nota com título + conteúdo lado a lado; máscara automática insere `:` e `/` após 2 dígitos e avança o foco
- [x] **[FIX] Modo seleção preservado na captura rápida** — janela ainda abre pedindo confirmação com Enter antes de exibir os campos

**Decisões técnicas desta sprint:**
- Todos os key bindings de visão centralizados no `DashboardWindow` (CTkToplevel) — `CTkFrame` não recebe foco de teclado, portanto bindings em frames filhos não disparavam; solução: métodos `_view_nav/copy/archive/delete/filter` no dashboard delegam para a visão ativa via `_active_key`
- `_nav(direction)` com índice circular e busca por ID — robusto a re-renders que destroem e recriam widgets
- Máscara de entrada implementada via `<KeyPress>` binding com `return "break"` — controla inserção manualmente sem `validatecommand`, mais previsível em Tkinter nativo
- `_editing` flag na quick_capture separa modo seleção (só visual, 1–5 trocam tipo) de modo edição (campos ativos, 1–5 não interferem)
- `select_first()` chamado pelo dashboard após `view.refresh()` toda vez que uma visão é aberta

---

### ✅ Sprint 3 — Polish Visual (concluída)

**Objetivo:** Migrar para CustomTkinter, widgets modernos, suporte a tema dark/light e fade-in na captura rápida.

**O que foi entregue:**
- [x] **[DEPS] `customtkinter==5.2.2`** — adicionado ao requirements.txt
- [x] **[FEAT] `ui/colors.py`** — paleta centralizada com tuplas `(light, dark)` para troca automática de tema
- [x] **[REFACTOR] `src/main.py`** — inicializa `ctk.set_appearance_mode("dark")` e color theme
- [x] **[REFACTOR] `core/app.py`** — root window migrada de `tk.Tk` para `ctk.CTk`
- [x] **[REFACTOR] Todos os 5 views** — `tk.Listbox` substituído por `ctk.CTkScrollableFrame` com cards clicáveis; seleção por ID em vez de índice
- [x] **[REFACTOR] `ui/dashboard.py`** — migrado para `ctk.CTkToplevel`; toggle Dark/Light com `CTkSegmentedButton` no header
- [x] **[REFACTOR] `ui/quick_capture.py`** — migrado para `ctk.CTkToplevel`; animação de fade-in (~160ms, 60fps)
- [x] **[REFACTOR] `ui/settings.py`** — migrado para `ctk.CTkToplevel`; seletor de tema visual com preview em tempo real

**Decisões técnicas desta sprint:**
- `text_widget` na quick_capture mantido como `tk.Text` nativo — garante bindings de teclado precisos sem depender das APIs internas do CTkTextbox
- Cards usam `fg_color` como tupla `(light, dark)` para suporte automático ao appearance_mode
- Fade-in via `wm_attributes("-alpha")` incrementado de 0→1 em steps de 0.1 a cada 16ms (≈60fps)
- Seleção de item nos views armazenada por `entry.id` (string UUID) em vez de índice — robusta a re-renders

---

### ✅ Sprint 2 — Visões por Tipo (concluída)

**Objetivo:** Dashboard por abas com visão especializada para cada tipo de entrada; captura multi-passo para Lembrete e Nota; captura automática de clipboard.

**O que foi entregue:**
- [x] **[FEAT] `Entry.completed` + `Storage.toggle_completed()`** — campo booleano para tarefas, toggle atômico no JSON
- [x] **[FEAT] `ui/view_tasks.py`** — lista To-Do com filtros Todas/Pendentes/Concluídas, Space para toggle
- [x] **[FEAT] `ui/view_insights.py`** — cards FILO com painel de detalhe, ações copiar/arquivar/deletar
- [x] **[FEAT] `ui/view_clipboard.py`** — cards FILO, hint de Ctrl+Shift+C, ações por item
- [x] **[FEAT] `ui/view_reminders.py`** — ordenado por proximidade, vencidos em vermelho, próximos em verde
- [x] **[FEAT] `ui/view_notes.py`** — painel bipartido: lista de títulos (esquerda) + conteúdo completo (direita)
- [x] **[REFACTOR] `ui/dashboard.py`** — reescrito como hub de abas (sem busca global); cada aba carrega sua visão
- [x] **[FEAT] `ui/quick_capture.py`** — 5 tipos (adicionado Nota 📝); máquina de estados multi-passo para Lembrete (3 passos) e Nota (2 passos)
- [x] **[FEAT] Ctrl+Shift+C** — hotkey global captura área de transferência diretamente, exibe toast e salva como Clipboard
- [x] **[TEST] 4 testes novos** em `test_storage.py` para `completed` e `toggle_completed`

**Decisões técnicas desta sprint:**
- Visões são `tk.Frame` embarcados no dashboard — evita janelas separadas, simplifica lifecycle
- `_switch_tab()` usa `pack`/`pack_forget` em vez de `grid` — mais simples e suficiente para 5 abas
- Captura multi-passo: state machine `_step` + `_step_data` em `QuickCaptureWindow`; `date` é o único campo que aceita vazio (= hoje)
- Toast de clipboard: `Toplevel` com `overrideredirect(True)` no canto inferior direito, auto-destrói em 1,4s
- Ctrl+Shift+C lê clipboard via `root.clipboard_get()` na thread principal (chamado por `root.after(0, ...)` do callback pynput)

---

### ✅ Sprint 1 — Qualidade e UX (concluída)

**Objetivo:** Robustez, testes e polish da UX.

**O que foi entregue:**
- [x] **[FEAT] Janela de captura rápida redesenhada** — fluxo em dois modos (seleção → escrita), fundo colorido por tipo, modal com grab_set(), ativação com delay para garantir foco no Windows
- [x] **[FEAT] Tags nas entradas** — campo de tags no dashboard com filtro em tempo real
- [x] **[FEAT] Exportação de entradas** — botão "📤 Exportar" no dashboard, gera `.md`, `.txt` ou `.json`
- [x] **[FEAT] Tela de configurações de hotkeys** — `ui/settings.py` com validação de formato, reload sem reiniciar
- [x] **[FIX] Ícone .ico real** — 6 resoluções (16→256px) em `assets/icon.ico`, fallback programático em `tray_icon.py`
- [x] **[TEST] Testes do Exporter** — 12 testes unitários, lógica pura sem UI
- [x] **[DOCS] CONTRIBUTING.md** — guia completo para contribuidores
- [x] **[DOCS] CHANGELOG.md** — histórico de versões no formato Keep a Changelog

**Decisões técnicas desta sprint:**
- `grab_set()` com `after(50ms)` para garantir foco no Windows (focus-stealing prevention)
- `<Shift-Return>` registrado antes de `<Return>` + checagem de `event.state & 0x1` para quebra de linha sem salvar
- Teclas 1–4 ficam em modo seleção (não entram no modo escrita) — Enter confirma o tipo
- Exportação usa importação lazy de `filedialog` para não poluir testes
- `_get_asset_path()` com `sys._MEIPASS` para compatibilidade com PyInstaller

---

### ✅ Sprint 0 — MVP Base (concluída)

**Objetivo:** Estrutura completa funcional do zero.

**O que foi entregue:**
- [x] Estrutura de diretórios do projeto
- [x] `core/storage.py` — CRUD completo em JSON com Entry model
- [x] `core/hotkey_manager.py` — Hotkeys globais via pynput
- [x] `core/reminder_scheduler.py` — Agendador de lembretes com repetição
- [x] `core/app.py` — Controlador central orquestrando todos os módulos
- [x] `ui/tray_icon.py` — System tray com menu de contexto
- [x] `ui/quick_capture.py` — Janela popup com dark theme e navegação por teclado
- [x] `ui/dashboard.py` — Dashboard completo com busca, filtro e ações
- [x] `utils/config.py` — Sistema de configuração com defaults e merge profundo
- [x] `requirements.txt` e `flowpad.spec`
- [x] `tests/test_storage.py` e `tests/test_config.py`
- [x] `CLAUDE.md` inicial

**Decisões técnicas desta sprint:**
- JSON sobre SQLite (ver seção "Stack Tecnológica")
- Tkinter puro para o MVP (sem CustomTkinter ainda)
- Janela root oculta como base para todas as Toplevel (padrão Tkinter)
- `root.after()` para thread safety entre pynput e Tkinter

---

---

### 🔮 Sprint 2 — Polish Visual

**Objetivo:** Migrar para CustomTkinter, adicionar temas, melhorar animações.

- [ ] **[REFACTOR] Migrar para CustomTkinter** — Widgets modernos mantendo toda a lógica atual
- [ ] **[FEAT] Múltiplos temas** — Dark, Light, Dracula, Solarized
- [ ] **[FEAT] Animação de abertura** — Fade-in na janela de captura rápida
- [ ] **[FEAT] Histórico de clipboard** — Ver as últimas N entradas do tipo clipboard numa floating window

---

### 🔮 Sprint 3 — Recursos Avançados

**Objetivo:** Funcionalidades para usuários avançados e power users.

- [ ] **[FEAT] Modo de edição inline no dashboard** — Editar entrada sem abrir nova janela
- [ ] **[FEAT] Atalho para tipos específicos** — `Ctrl+Shift+R` abre captura já no modo Reminder
- [ ] **[FEAT] Busca fuzzy** — Busca tolerante a erros de digitação
- [ ] **[FEAT] Sincronização via arquivo** — Opção de salvar em pasta do OneDrive/Dropbox
- [ ] **[FEAT] Plugin system** — API para contribuidores adicionarem tipos customizados

---

## 🤝 Regras para o Claude Code

### Comportamento obrigatório

1. **Explicação didática ao final de cada tarefa/sprint:**
   > Após concluir qualquer implementação relevante, o Claude Code deve escrever um bloco explicando:
   > - O que foi feito
   > - Por que a abordagem foi escolhida
   > - Como isso beneficia o usuário final
   > - Como isso facilita contribuições open source

2. **Atualizar este CLAUDE.md:**
   > - Ao finalizar cada sprint: mover os itens para "concluída" e registrar decisões
   > - Ao tomar qualquer decisão arquitetural relevante: documentar na seção correspondente
   > - Ao adicionar nova dependência: atualizar a tabela de stack com justificativa
   > - Ao mudar um atalho de teclado: atualizar a tabela de atalhos

3. **Documentação completa:**
   > Todo módulo novo deve ter:
   > - Docstring no topo do arquivo explicando propósito e responsabilidade
   > - Docstrings em métodos não-triviais
   > - Comentários em linhas de código não-óbvias

4. **Padrões de código:**
   > - Seguir PEP 8 (validado por ruff)
   > - Formatação com black
   > - Type hints em assinaturas de função
   > - Nomes em português para variáveis de domínio (entry_type, lembrete) e inglês para infraestrutura (callback, thread, listener)

5. **Testes antes de PR:**
   > Qualquer nova feature deve ter pelo menos um teste unitário.
   > Bugs corrigidos devem ter um teste de regressão.

6. **Convenção de commits:**
   ```
   feat: nova funcionalidade
   fix: correção de bug
   refactor: refatoração sem mudança de comportamento
   test: adição ou correção de testes
   docs: documentação
   chore: tarefas de manutenção (deps, config)
   style: formatação, sem mudança lógica
   ```

### O que NÃO fazer

- ❌ Não remover comentários de arquivos existentes sem justificativa
- ❌ Não mudar a estrutura de diretórios sem atualizar este arquivo
- ❌ Não adicionar dependências sem documentar na tabela de stack
- ❌ Não fazer commits grandes com múltiplas features — preferir commits atômicos
- ❌ Não usar `global` em Python sem necessidade explícita

---

## 📁 Dados e Configuração

### Localização dos arquivos (Windows)

```
%APPDATA%\FlowPad\
├── config.json     # Preferências do usuário
└── entries.json    # Todas as entradas salvas
```

### Localização (Linux/Mac)

```
~/.flowpad/
├── config.json
└── entries.json
```

### Formato de uma entrada (entries.json)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "content": "Implementar cache LRU no módulo de storage",
  "title": "Ideia de otimização",
  "entry_type": "insight",
  "tags": ["performance", "storage"],
  "reminder_at": null,
  "reminder_interval_min": null,
  "created_at": "2024-01-15T14:32:10.123456",
  "archived": false,
  "completed": false
}
```

---

## 🐛 Problemas Conhecidos (MVP)

| # | Descrição | Impacto | Previsto para |
|---|---|---|---|
| 1 | Ícone gerado programaticamente é simples | Estético | Sprint 1 |
| 2 | Tela de configurações ainda não existe | Médio | Sprint 1 |
| 3 | `plyer` pode falhar silenciosamente em algumas configs do Windows | Baixo | Sprint 1 |
| 4 | Sem teste de UI (apenas testes de lógica) | Médio | Sprint 1 |

---

## 🌐 Open Source

**Licença:** MIT — qualquer pessoa pode usar, modificar e distribuir.

**Como contribuir:**
1. Fork o repositório
2. Crie uma branch: `git checkout -b feat/minha-feature`
3. Siga as regras de código acima
4. Abra um PR descrevendo o que foi feito e por quê

**Estrutura pensada para contribuidores:**
- Cada módulo tem uma única responsabilidade clara
- Zero acoplamento entre `core/` e `ui/` — os módulos de core não importam nada de ui
- `Storage` e `Config` são completamente testáveis sem precisar de Tkinter

---

*Última atualização: Sprint 4 — UX Polish & Navegação por Teclado*
*Próxima atualização prevista: ao finalizar Sprint 5 (Recursos Avançados)*
