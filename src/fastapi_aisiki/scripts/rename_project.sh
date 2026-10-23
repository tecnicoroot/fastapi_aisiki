#!/usr/bin/env bash
# Renomeia o template fastapi-aisiki para um projeto novo.
# Uso: ./scripts/rename_project.sh loja-api
set -euo pipefail

OLD_NAME="fastapi-aisiki"
OLD_PKG="fastapi_aisiki"

NEW_NAME="${1:-}"
if [[ ! "$NEW_NAME" =~ ^[a-z][a-z0-9-]*[a-z0-9]$ ]]; then
    echo "Uso: $0 <nome-do-projeto>   (minúsculas, números e hífen; ex.: loja-api)" >&2
    exit 1
fi
NEW_PKG="${NEW_NAME//-/_}"

if [[ ! -d "src/$OLD_PKG" ]]; then
    echo "Erro: rode na raiz do template (src/$OLD_PKG não encontrado)." >&2
    exit 1
fi

echo "Renomeando $OLD_NAME -> $NEW_NAME (pacote $OLD_PKG -> $NEW_PKG)"

# 1. Move o pacote Python
git mv "src/$OLD_PKG" "src/$NEW_PKG" 2>/dev/null || mv "src/$OLD_PKG" "src/$NEW_PKG"

# 2. Substitui os nomes em todos os arquivos de texto do projeto
#    (perl -pi funciona igual no Linux e no macOS, diferente do sed -i)
grep -rIl --exclude-dir={.git,.venv,__pycache__,.mypy_cache,.ruff_cache,.pytest_cache} \
    --exclude=uv.lock --exclude="$(basename "$0")" \
    -e "$OLD_PKG" -e "$OLD_NAME" -e "fastapi-pro" . \
| xargs -r perl -pi -e "s/\Q$OLD_PKG\E/$NEW_PKG/g; s/\Q$OLD_NAME\E/$NEW_NAME/g; s/fastapi-pro/$NEW_NAME/g"

# 3. Recria o uv.lock e reinstala o pacote com o novo nome
uv sync

# 4. Cria o .env a partir do modelo, já com uma SECRET_KEY nova
if [[ ! -f .env ]]; then
    cp .env.example .env
    KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')"
    perl -pi -e "s/^SECRET_KEY=.*/SECRET_KEY=$KEY/" .env
    echo ".env criado com SECRET_KEY nova."
fi

echo
echo "Pronto. Restam: revisar description/authors no pyproject.toml e o README.md,"
echo "ajustar FIRST_SUPERUSER_* no .env e rodar: make up && make check"