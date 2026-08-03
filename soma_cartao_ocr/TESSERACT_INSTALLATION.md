# 🔧 Guia de Instalação do Tesseract OCR

## Windows (Recomendado)

### Passo 1: Download

1. Acesse: https://github.com/UB-Mannheim/tesseract/wiki
2. Procure a seção "Downloads"
3. Baixe a **versão mais recente** (ex: `tesseract-ocr-w64-setup-v5.3.0.exe`)
4. Salve em um local de fácil acesso (ex: Downloads)

### Passo 2: Executar Instalador

1. **Duplo clique** no arquivo .exe
2. Na primeira tela, clique **"Next"**
3. Na tela de "License", selecione **"I Agree"** e clique **"Next"**
4. Na tela de "Choose Install Location", **NÃO MUDE** o caminho:
   - Deve estar: `C:\Program Files\Tesseract-OCR`
   - Clique **"Next"**

### Passo 3: Selecionar Idiomas (IMPORTANTE!)

Na tela "Choose Components":
- ✅ Marque: **English**
- ✅ Marque: **Portuguese**
- Deixe desmarcadas: Outros idiomas (opcional)
- Clique **"Next"**

### Passo 4: Concluir Instalação

1. Clique **"Install"** (vai levar 2-3 minutos)
2. Quando terminar, clique **"Finish"**
3. **Reinicie o terminal/PowerShell** (importante!)

### Passo 5: Verificar Instalação

Abra o **PowerShell** e execute:

```powershell
tesseract --version
```

**Resultado esperado:**
```
tesseract 5.3.0
  leptonica-1.82.0
  libgif 5.2.1 : libjpeg 9e (libjpeg-turbo 2.1.3) : libpng 1.6.37 : libtiff 4.5.0 : zlib 1.2.13
  Found AVX2
  Found AVX
  Found SSE
```

✅ Se vir a versão = Tesseract instalado com sucesso!

---

## Linux (Ubuntu/Debian)

```bash
# Instalar Tesseract
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install libtesseract-dev

# Instalar Python bindings
pip install pytesseract

# Verificar
tesseract --version
```

---

## macOS

```bash
# Instalar com Homebrew
brew install tesseract

# Instalar Python bindings
pip install pytesseract

# Verificar
tesseract --version
```

---

## Verificação do pytesseract

```python
import pytesseract
pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Testar
from PIL import Image
text = pytesseract.image_to_string(Image.open('test.png'))
print(text)
```

---

## Solução de Problemas

### ❌ "tesseract is not installed or it's not in your PATH"

**Solução 1: Adicionar ao PATH (Windows)**

1. Abra "Editar as variáveis de ambiente do sistema"
   - Pressione `Win + X` → "Sistema"
   - Clique "Informações avançadas do sistema"
   - Clique "Variáveis de Ambiente"

2. Sob "Variáveis do sistema", clique "Novo"
   - Nome: `Path`
   - Valor: `C:\Program Files\Tesseract-OCR`
   - Clique "OK"

3. **Reinicie o PowerShell**

4. Teste: `tesseract --version`

**Solução 2: Configurar em Python (ocr_hybrid.py)**

```python
import pytesseract
pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### ❌ "No tessdata file found"

**Solução:**

1. Desinstale Tesseract completamente
2. Reinstale do zero, **marcando os idiomas necessários**
3. Localize a pasta: `C:\Program Files\Tesseract-OCR\tessdata`
   - Deve conter: `eng.traineddata`, `por.traineddata`

### ❌ Python não encontra Tesseract

**Solução:**

```python
import pytesseract
import os

# Adicionar ao PATH dinamicamente
os.environ['PATH'] += os.pathsep + r'C:\Program Files\Tesseract-OCR'

# Ou configurar diretamente
pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

---

## ✅ Após Instalar

Execute:

```bash
# Verificar Tesseract
python verify_tesseract.py

# Se tudo OK, testar OCR Híbrido
python test_hybrid_ocr.py

# Se números são capturados, executar main.py
python main.py
```

---

## 🎯 Verificação de Sucesso

Você saberá que funcionou quando:

1. ✅ `tesseract --version` funciona no terminal
2. ✅ `python verify_tesseract.py` mostra "✅ TESSERACT PRONTO"
3. ✅ `python test_hybrid_ocr.py` captura números em `temp_cleaned_digits.jpg`
4. ✅ `python main.py` executa sem erros de Tesseract
5. ✅ `investigate_line11.py` mostra `débito_eur: "1,99"` (não vazio!)

---

## 📝 Tempo Estimado

- Download: 2 minutos
- Instalação: 3 minutos
- Configuração: 2 minutos
- **Total: ~7 minutos**

---

**Próximo passo após instalar:**

1. Abra PowerShell em: `C:\workspace\soma_cartao_ocr`
2. Execute: `python verify_tesseract.py`
3. Se ✅, execute: `python test_hybrid_ocr.py`
4. Se capturar números, me avisa para integrar em main.py!
