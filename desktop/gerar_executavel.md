# Gerar Executável

Instruções para gerar o executável do APP_AUTOMATION usando PyInstaller.

## Windows

Requisitos:
- Python instalado com o launcher `py`
- PyInstaller (`pip install pyinstaller`)
- UPX em `C:/upx-4.2.4-win64` (opcional, para compressão)

Comando:

```bat
py -m PyInstaller --onefile --windowed --icon=icons/esse.ico --name=APP_AUTOMATION_4.1V --strip --upx-dir=C:/upx-4.2.4-win64 --noconfirm --add-data "icons/Altaia.png;icons" --add-data "icons/esse.ico;icons" --paths=. app.py
```

## Linux

Requisitos:
- Python 3 (`python3`)
- PyInstaller (`pip3 install pyinstaller`)
- UPX instalado (`sudo apt install upx-ucl`)

Observação: o binário gerado é um executável **ELF para Linux**, não um `.exe` para Windows. Para gerar um `.exe`, compile diretamente no Windows.

Diferenças em relação ao comando do Windows:
- `py` → `python3`
- Separador do `--add-data`: `;` → `:`
- `--upx-dir` aponta para o diretório do UPX no Linux (ex.: `/usr/bin`)

Comando:

```bash
python3 -m PyInstaller --onefile --windowed --icon=icons/esse.ico --name=APP_AUTOMATION_4.1V --strip --upx-dir=/usr/bin --noconfirm --add-data "icons/Altaia.png:icons" --add-data "icons/esse.ico:icons" --paths=. app.py
```

## GitHub Actions (gerar .exe sem precisar de Windows local)

Útil quando você só tem Python no WSL/Linux. O workflow [`.github/workflows/build-desktop.yml`](../.github/workflows/build-desktop.yml) compila o `.exe` em um runner `windows-latest`.

Repositório de destino: [github.com/sandesrafael/APP_Automation](https://github.com/sandesrafael/APP_Automation)

### Setup inicial (uma vez)

Se a pasta local ainda não é um repositório git, inicialize e aponte para o repo existente no GitHub:

```bash
cd APP_Automation-main
git init
git add .
git commit -m "ci: build desktop exe"
git branch -M main
git remote add origin https://github.com/sandesrafael/APP_Automation.git
git push -u origin main
```

Se o repositório remoto já tem commits, faça `git pull --rebase origin main` antes do `push`.

### Como acionar:

1. **Push de uma tag** começando com `v` (ex.: `v4.1`, `v4.1.1`):
   ```bash
   git tag v4.1
   git push origin v4.1
   ```
   Além de gerar o artifact, anexa o `.exe` automaticamente a um Release no GitHub.

2. **Manual** pela aba *Actions* → *Build Desktop Executable (Windows)* → *Run workflow*.

3. **Automático** em push para arquivos dentro de `desktop/` ou o próprio workflow.

Após o job concluir, o `.exe` fica disponível em:
- *Artifacts* (sempre) — `APP_AUTOMATION_4.1V-windows.zip` na página da execução.
- *Releases* (apenas em push de tag `v*`).
