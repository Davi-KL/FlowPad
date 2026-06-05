# FlowPad ✏️

> Capture ideias, insights e lembretes em milissegundos — sem quebrar seu fluxo de trabalho.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-5CE07A)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Mac-blue)
![Status](https://img.shields.io/badge/Status-MVP-F4C542)

---

## O Problema

Você está no meio de uma sessão de código, completamente focado. De repente tem uma ideia brilhante, percebe uma tarefa futura ou quer salvar um trecho de um artigo.

O que acontece? Você para, abre outro app, organiza tudo bonitinho e... perdeu o estado mental de flow.

## A Solução

**FlowPad** roda silenciosamente em background. Quando precisar capturar algo:

1. Pressione **`Ctrl + Shift + Space`**
2. Digite sua ideia (ou cole um texto)
3. **`Ctrl + Enter`** para salvar

Pronto. Em menos de 3 segundos você está de volta ao que estava fazendo.

---

## Funcionalidades

- 🚀 **Captura em < 3 segundos** — janela popup instantânea via hotkey
- ⌨️ **100% pelo teclado** — mouse é opcional, nunca obrigatório
- 🗂️ **5 tipos de entrada** — Insight, Lembrete, Clipboard, Tarefa, Nota
- ⏰ **Lembretes automáticos** — notificações nativas com frequência configurável
- 🔍 **Dashboard com busca** — encontre qualquer entrada em segundos
- 🎨 **Dark theme** — projetado para longas sessões de trabalho
- 💾 **Dados locais em JSON** — seus dados são seus, sem nuvem, sem login
- 🔓 **Open source MIT** — use, modifique, contribua

---

## Instalação

### Opção 1: Executável (.exe) — recomendado para usuários Windows

Baixe o `FlowPad.exe` na página de [Releases](https://github.com/seu-usuario/flowpad/releases).

Sem instalação, sem dependências. Execute e comece a usar.

### Opção 2: Do código fonte

```bash
git clone https://github.com/seu-usuario/flowpad.git
cd flowpad
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
python src/main.py
```

---

## Atalhos de Teclado

### Globais

| Atalho | Ação |
|---|---|
| `Ctrl + Shift + Space` | Captura rápida |
| `Ctrl + Shift + F` | Abrir dashboard |

### Na captura rápida

| Atalho | Ação |
|---|---|
| `Ctrl + Enter` | Salvar |
| `Escape` | Cancelar |
| `Ctrl + 1` a `5` | Mudar tipo de entrada |

### No dashboard

| Atalho | Ação |
|---|---|
| `N` | Nova captura |
| `C` | Copiar selecionado |
| `A` | Arquivar selecionado |
| `Delete` | Deletar selecionado |

---

## Arquitetura

O FlowPad foi projetado com separação clara de responsabilidades para facilitar contribuições:

```
core/       → Lógica pura (sem UI), 100% testável
ui/         → Janelas e componentes visuais
utils/      → Configuração e utilitários
```

Para entender a arquitetura completa, decisões técnicas e roadmap detalhado, consulte o [CLAUDE.md](./CLAUDE.md).

---

## Contribuindo

Contribuições são muito bem-vindas!

1. Veja os [issues abertos](https://github.com/seu-usuario/flowpad/issues)
2. Fork e crie uma branch: `git checkout -b feat/sua-feature`
3. Leia o [CLAUDE.md](./CLAUDE.md) para entender os padrões do projeto
4. Abra um PR descrevendo sua mudança

---

## Licença

MIT © 2024 — Faça o que quiser, só não remova os créditos 🙂
