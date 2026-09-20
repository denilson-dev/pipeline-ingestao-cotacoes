# 🚀 Cloud-Native Data Ingestion Pipeline

Pipeline de ingestão de cotações financeiras desenvolvido em Python, com PostgreSQL em Docker, execução em Linux/AWS EC2 e automação por cron.

O projeto foi estruturado para ser simples, reproduzível e seguro para portfólio: credenciais não ficam no código, falhas da API não geram dados fictícios e a gravação diária é idempotente por moeda.

## Arquitetura

```text
Exchange Rate API
        |
        v
   Python ETL
        |
        v
 PostgreSQL 16
   (Docker)
        ^
        |
 Linux Cron / execução manual
        |
      AWS EC2
```

## Tecnologias

- Python 3.12
- Requests
- Psycopg2
- PostgreSQL 16
- Docker / Docker Compose
- Linux Cron
- GitHub Actions
- Pytest
- Ruff
- AWS EC2

## Estrutura do repositório

```text
.
├── .env.example
├── .github/
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── cron/
│   └── pipeline.cron.example
├── sql/
│   └── init.sql
├── tests/
│   └── test_ingestao.py
├── Dockerfile
├── docker-compose.yml
├── ingestao.py
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## Segurança

As credenciais do PostgreSQL são carregadas por variáveis de ambiente. O arquivo real `.env` é ignorado pelo Git.

> Se uma senha real já tiver sido publicada anteriormente no histórico do repositório, ela deve ser trocada no PostgreSQL. Remover a senha do arquivo atual não elimina versões antigas do histórico Git.

## Como executar localmente

### 1. Clonar o projeto

```bash
git clone https://github.com/denilson-dev/pipeline-ingestao-cotacoes.git
cd pipeline-ingestao-cotacoes
```

### 2. Criar o arquivo de ambiente

```bash
cp .env.example .env
```

Edite `.env` e defina uma senha forte:

```dotenv
POSTGRES_DB=analytics_db
POSTGRES_USER=admin_dba
POSTGRES_PASSWORD=uma-senha-forte-aqui
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
```

### 3. Subir o PostgreSQL

```bash
docker compose up -d postgres
```

O banco é inicializado com `sql/init.sql`.

### 4. Executar o pipeline com Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python ingestao.py
```

Ou executar o pipeline em container:

```bash
docker compose --profile manual run --rm pipeline
```

## Comportamento em caso de falha da API

O pipeline faz novas tentativas de consulta à API. Se nenhuma tentativa retornar dados válidos, ele:

- registra o erro;
- encerra com código diferente de zero;
- não grava cotações inventadas no PostgreSQL.

Isso evita misturar dados simulados com dados reais.

## Idempotência

O schema cria um índice único para impedir mais de uma cotação da mesma moeda no mesmo dia UTC.

O comando de inserção usa:

```sql
ON CONFLICT DO NOTHING
```

Assim, uma execução repetida no mesmo dia não duplica registros.

## Automação com Cron

Há um exemplo em `cron/pipeline.cron.example`.

Exemplo:

```cron
0 6 * * * cd /opt/pipeline && /usr/bin/python3 ingestao.py >> /var/log/pipeline-ingestao.log 2>&1
```

Ajuste o diretório, o Python e o horário conforme a EC2.

## Testes e qualidade

Instale as dependências de desenvolvimento:

```bash
pip install -r requirements-dev.txt
```

Execute:

```bash
ruff check .
pytest -q
```

## CI/CD

O workflow `.github/workflows/ci.yml` executa automaticamente:

1. instalação das dependências;
2. validação de sintaxe Python;
3. Ruff;
4. Pytest;
5. validação do Docker Compose.

## Observação para banco já existente

O arquivo em `sql/init.sql` é executado automaticamente apenas quando o volume PostgreSQL é criado pela primeira vez.

Se já existir um banco/volume na EC2, revise os dados existentes antes de aplicar manualmente o novo índice de unicidade. Caso existam duas ou mais linhas da mesma moeda para o mesmo dia UTC, o índice não poderá ser criado até que essas duplicidades sejam tratadas.

## Próximas evoluções

- observabilidade com métricas e alertas;
- armazenamento histórico em camada analítica;
- Terraform para provisionamento da AWS;
- secrets manager;
- orquestração com Airflow ou Prefect;
- dashboard de acompanhamento das cotações.

## Objetivo do projeto

O objetivo é demonstrar, na prática, integração entre API externa, Python, PostgreSQL, Docker, Linux, automação, testes e infraestrutura em nuvem com foco em fundamentos de Engenharia de Dados.
