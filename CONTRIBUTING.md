# Guia de Contribuição — FlowPad

Obrigado por considerar contribuir com o FlowPad! Este guia explica como configurar o ambiente, os padrões do projeto e o fluxo para abrir um PR.

---

## Setup do ambiente

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/flowpad.git
cd flowpad

# Crie e ative um ambiente virtual
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Linux/Mac

# Instale as dependências
pip install -r requirements.txt
```

## Rodando o app

```bash
python src/main.py
```

## Rodando os testes

```bash
pytest tests/ -v

# Com relatório de cobertura
pytest tests/ --cov=src --cov-report=html
```

## Formatação e linting

O projeto usa **black** para formatação e **ruff** para linting:

```bash
black src/ tests/
ruff check src/ tests/
```

---

## Estrutura do projeto

```
src/core/    → Lógica pura (storage, hotkeys, reminders, export)
src/ui/      → Janelas Tkinter (quick_capture, dashboard, settings)
src/utils/   → Configuração
tests/       → Testes unitários (sem UI)
assets/      → Ícones e imagens
docs/        → Documentação adicional
```

**Regra importante:** módulos em `core/` jamais importam nada de `ui/`. O acoplamento é unidirecional: `ui → core`.

---

## Fluxo para contribuir

1. Veja os [issues abertos](https://github.com/seu-usuario/flowpad/issues)
2. Comente no issue que vai trabalhar nele
3. Crie uma branch descritiva:
   ```bash
   git checkout -b feat/tag-filter
   git checkout -b fix/icon-not-loading
   ```
4. Escreva o código seguindo os padrões abaixo
5. Adicione ao menos um teste para qualquer nova funcionalidade
6. Abra um PR descrevendo **o quê** foi feito e **por quê**

---

## Padrões de código

- **PEP 8** — validado pelo ruff
- **Type hints** em todas as assinaturas de função
- **Docstrings** no topo de cada módulo novo e em métodos não-triviais
- Nomes de variáveis de domínio em português (`entry_type`, `lembrete`, `arquivar`)
- Nomes de infraestrutura em inglês (`callback`, `thread`, `listener`)

## Convenção de commits

```
feat: nova funcionalidade
fix: correção de bug
refactor: refatoração sem mudança de comportamento
test: adição ou correção de testes
docs: documentação
chore: manutenção (deps, config)
style: formatação, sem mudança lógica
```

---

## Dúvidas?

Abra uma [issue](https://github.com/seu-usuario/flowpad/issues) com a label `question`.
