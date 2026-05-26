# Trocas Din Din

Este projeto usa `web.py` como app Flask.

## Como rodar localmente
1. Ative seu ambiente Python.
2. Instale dependências:

```bash
pip install -r requirements.txt
```

3. Execute o servidor:

```bash
python web.py
```

4. Abra no navegador:

```bash
http://localhost:5000
```

## Como publicar no GitHub Pages
1. Gere o site estático no diretório `docs`:

```bash
python build_static_site.py
```

2. Faça commit de `docs/index.html`, `docs/uploads/` e todos os arquivos estáticos gerados.
3. No GitHub, vá em Settings → Pages.
4. Selecione a branch `main` e a pasta `/docs`.
5. Salve e aguarde a publicação.

## Como publicar no PythonAnywhere
1. Crie um web app no PythonAnywhere.
2. Aponte o diretório do seu projeto para a raiz do repositório, não para `docs`.
3. Use este arquivo WSGI como ponto de entrada:

```python
from web import app as application
```

4. Reinicie o web app.

A URL final será algo como `https://SEU_USUARIO.pythonanywhere.com`.

## Importante
- GitHub Pages **não pode** rodar `web.py` ou Flask.
- No PythonAnywhere, o app deve abrir a partir de `web.py`.
- Se você vir `docs/index.html` no navegador, a configuração do web app está apontando para a pasta errada.
