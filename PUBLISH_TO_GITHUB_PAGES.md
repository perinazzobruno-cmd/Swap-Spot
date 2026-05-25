Guia rápido para publicar no GitHub Pages

1) O repositório inclui um gerador estático `build_static_site.py` que cria um site estático na pasta `docs/`.

2) Como gerar o site localmente:

   - Tenha Python instalado.
   - No terminal, rode:

```powershell
python build_static_site.py
```

   - Isso criará `docs/index.html` e copiará imagens para `docs/uploads/`.

3) Publicar no GitHub Pages (opção simples):

   - Faça commit e push das mudanças para o branch `main`.
   - No GitHub, vá em Settings → Pages.
   - Em 'Source', selecione `main` branch e a pasta `/docs`.
   - Salve — o site será publicado em alguns minutos.

4) Para atualizações automáticas: rode o `build_static_site.py` localmente sempre que os dados mudarem e faça commit das mudanças em `docs/`.

Observações:
- GitHub Pages só serve arquivos estáticos — o `web.py` (Flask) não roda no Pages.
- Se preferir deploy automatizado, posso adicionar uma GitHub Action que executa o gerador e publica automaticamente.
