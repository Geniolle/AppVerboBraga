# VS Code - Configuração Profissional do AppVerboBraga

Este documento registra as principais configurações do VS Code utilizadas no projeto AppVerboBraga.

## Perfil utilizado

Perfil do VS Code:

```text
AppVerboBraga - Profissional
```

## Extensões recomendadas

As extensões recomendadas do projeto estão em:

```text
.vscode/extensions.json
```

Principais extensões:

- Python
- Pylance
- Ruff
- Docker
- GitLens
- Prettier
- EditorConfig
- Material Icon Theme
- YAML
- DotENV
- Error Lens

## Atalhos configurados

| Atalho | Função |
|---|---|
| `Ctrl + Alt + V` | Validar Python |
| `Ctrl + Alt + G` | Git Status |
| `Ctrl + Alt + D` | Docker Restart |
| `Ctrl + Alt + H` | Teste HTTP |
| `Ctrl + Alt + L` | Logs Docker Web |
| `Ctrl + Alt + C` | Validação Completa Local |
| `Ctrl + Alt + R` | Reiniciar e Testar Docker |

## Tarefas principais

As tarefas estão configuradas em:

```text
.vscode/tasks.json
```

### Validação completa local

Executa em sequência:

```text
AppVerboBraga: Validar Python
AppVerboBraga: Git Diff Check
AppVerboBraga: Git Diff Resumo
AppVerboBraga: Git Status
```

Atalho:

```text
Ctrl + Alt + C
```

### Reiniciar e testar Docker

Executa em sequência:

```text
AppVerboBraga: Docker Restart
AppVerboBraga: Teste HTTP
AppVerboBraga: Logs Docker Web
```

Atalho:

```text
Ctrl + Alt + R
```

## Configurações criadas no projeto

Foram criados ou ajustados estes ficheiros:

```text
.vscode/extensions.json
.vscode/launch.json
.vscode/settings.json
.vscode/tasks.json
.prettierignore
.prettierrc.json
pyproject.toml
.gitattributes
.gitignore
```

## Observações sobre CRLF/LF

O projeto utiliza `LF` para ficheiros de código e configuração.

O PowerShell continua com `CRLF`:

```text
*.ps1 text eol=crlf
```

Os warnings atuais de CRLF em ficheiros já modificados são esperados e não representam erro funcional.

## Atalhos úteis do VS Code

| Atalho | Função |
|---|---|
| `Ctrl + Shift + P` | Abrir Command Palette |
| `Ctrl + Shift + V` | Abrir Preview de Markdown |
| `Ctrl + B` | Mostrar/ocultar barra lateral |
| `Ctrl + aspas invertida` | Mostrar/ocultar terminal |
| `Ctrl + S` | Guardar ficheiro |

## Fluxo recomendado de trabalho

Antes de finalizar alterações no projeto, executar:

```text
Ctrl + Alt + C
```

Para validar:

```text
Python compileall
Git diff check
Git diff resumo
Git status
```

Quando precisar reiniciar e testar o Docker:

```text
Ctrl + Alt + R
```

Esse atalho executa:

```text
Docker restart
Teste HTTP com espera automática
Logs recentes do container web
```
