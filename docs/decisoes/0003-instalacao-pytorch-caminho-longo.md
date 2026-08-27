# ADR 0003 — Instalação do PyTorch com caminho de projeto longo (Windows)

## Contexto

O diretório do projeto vive dentro do OneDrive, com um caminho longo e
com espaços (`C:\Users\...\OneDrive - CTG Brasil\CTG Br\02 - PYTHON\Mancal_Analisys`).
O pacote `torch` (CPU, wheel oficial `download.pytorch.org/whl/cpu`,
compatível com Python 3.14 — ver ADR 0001) inclui uma árvore de arquivos
de licença de terceiros muito profunda
(`torch-2.13.0+cpu.dist-info/licenses/third_party/kineto/libkineto/...`).
Ao instalar normalmente dentro de `.venv\Lib\site-packages\`, o caminho
completo de alguns desses arquivos ultrapassa o limite de 260 caracteres
do Windows (`MAX_PATH`), causando `OSError [WinError 206]`.

A correção padrão (habilitar `LongPathsEnabled` no registro do Windows)
exige privilégio de administrador, que o ambiente não tem. `subst`
(mapear a pasta a uma letra de unidade) também não funcionou neste
ambiente (retornou "parâmetro inválido" mesmo para pastas fora do
OneDrive).

## Decisão

Instalar o `torch` isoladamente em um diretório de caminho curto fora do
projeto, e registrá-lo no `.venv` do projeto via um arquivo `.pth`
(mecanismo padrão do `site` do Python, que adiciona o caminho ao
`sys.path` na inicialização do interpretador):

```powershell
.\.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu --target "C:\tmp\pylibs" --no-deps
echo C:\tmp\pylibs > .venv\Lib\site-packages\_torch_external.pth
```

As dependências do `torch` (sympy, networkx, jinja2, fsspec, filelock,
mpmath, setuptools) são instaladas normalmente dentro do `.venv` — apenas
o pacote `torch` em si tem a árvore de arquivos problemática.

## Consequência

- `import torch` funciona normalmente a partir do `.venv` do projeto;
  `pip freeze` reconhece a versão corretamente (`torch==2.13.0+cpu`).
- **Quem for reproduzir o ambiente em outra máquina Windows com o mesmo
  problema de caminho precisa repetir os dois comandos acima
  manualmente** — `pip install -r backend/requirements.txt` sozinho
  tentará instalar `torch` no local padrão e pode falhar com o mesmo
  erro se o caminho do projeto também for longo. Documentado aqui e no
  `README.md`.
- Se o projeto for movido para um caminho mais curto (fora do OneDrive,
  ou com `LongPathsEnabled` ativado por um administrador), essa
  contorção deixa de ser necessária — pode-se reinstalar normalmente e
  remover `_torch_external.pth`.
