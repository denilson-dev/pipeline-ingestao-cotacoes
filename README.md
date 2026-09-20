# 🚀 Data Ingestion Pipeline — Projeto de Estudo

Projeto de estudo desenvolvido para colocar em prática conceitos de Engenharia de Dados por meio da ingestão automatizada de cotações financeiras.

A implementação utiliza Python, PostgreSQL em Docker, Linux/AWS EC2 e automação com cron. O objetivo é consolidar conhecimentos estudados na teoria por meio de uma aplicação prática, simples e reproduzível, aplicando também boas práticas básicas de segurança, modelagem de dados, automação, testes e versionamento.

## Objetivos de aprendizado

Neste projeto, busquei praticar:

- consumo de uma API externa com Python;
- tratamento e validação de dados antes da persistência;
- modelagem de dados para representar a taxa de câmbio de forma explícita;
- gravação e atualização idempotente de dados em PostgreSQL;
- uso de Docker para o banco de dados;
- execução em Linux/AWS EC2;
- automação de tarefas com cron;
- uso de variáveis de ambiente para credenciais;
- testes automatizados com Pytest;
- análise estática com Ruff;
- integração contínua com GitHub Actions;
- versionamento e documentação com Git/GitHub.

## Arquitetura utilizada no estudo

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

## Modelo de dados

A tabela principal utiliza os seguintes campos:

| Campo | Finalidade |
| --- | --- |
| `id` | identificador interno do registro |
| `moeda` | moeda cuja cotação está sendo registrada, como USD ou EUR |
| `taxa_brl` | quantidade de reais correspondente a uma unidade da moeda |
| `data_referencia` | data à qual a cotação se refere |
| `data_ingestao` | momento em que o dado foi gravado no banco |

Essa separação evita tratar uma taxa de câmbio como se fossem preços distintos de compra e venda e também diferencia a data do dado da data em que ele entrou no pipeline.

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
│   ├── migrations/
│   │   └── 002_normalize_cotacoes.sql
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

## Boas práticas de segurança aplicadas

As credenciais do PostgreSQL são carregadas por variáveis de ambiente. O arquivo real `.env` é ignorado pelo Git.

Também foi removido o uso de credenciais fixas diretamente no código.

> Observação: se uma senha real já tiver sido publicada anteriormente no histórico do repositório, ela deve ser trocada no PostgreSQL. Remover a senha do arquivo atual não elimina versões antigas do histórico Git.

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

Edite `.env` e defina uma senha própria:

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

## Tratamento de falhas da API

O pipeline realiza novas tentativas de consulta à API. Se nenhuma tentativa retornar dados válidos, ele:

- registra o erro;
- encerra com código diferente de zero;
- não grava cotações fictícias no PostgreSQL.

Esse comportamento evita misturar dados de simulação com os dados obtidos da API.

## Idempotência

A combinação `(moeda, data_referencia)` é única no banco.

Quando o pipeline encontra novamente a mesma moeda para a mesma data, utiliza `ON CONFLICT ... DO UPDATE` para atualizar a taxa e o horário de ingestão em vez de criar uma duplicidade.

## Migração do modelo anterior

O primeiro modelo utilizava `valor_compra`, `valor_venda` e `data_cotacao`. Para bancos já existentes, o arquivo:

```text
sql/migrations/002_normalize_cotacoes.sql
```

faz a migração para o modelo atual.

A migração:

1. renomeia a tabela antiga para `cotacoes_diarias_legacy`;
2. cria a nova tabela normalizada;
3. migra uma cotação por moeda e dia, escolhendo o registro mais recente quando houver duplicidade;
4. mantém todos os registros originais na tabela `cotacoes_diarias_legacy` como cópia de segurança.

Por segurança, a tabela legada não é apagada automaticamente.

> Em um ambiente já existente, aplique a migração antes de executar a nova versão do `ingestao.py`.

## Automação com Cron

Há um exemplo em `cron/pipeline.cron.example`.

O exemplo carrega as variáveis do arquivo `.env` antes de executar o Python. Em um servidor, mantenha esse arquivo com permissões restritas, por exemplo:

```bash
chmod 600 .env
```

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

## Integração Contínua (CI)

O workflow `.github/workflows/ci.yml` executa automaticamente:

1. instalação das dependências;
2. validação de sintaxe Python;
3. análise com Ruff;
4. testes com Pytest;
5. validação do Docker Compose;
6. inicialização de um PostgreSQL temporário para validar o schema.

Essa automação é utilizada para praticar conceitos de integração contínua e manter verificações básicas do projeto a cada alteração.

## Próximos estudos

Alguns temas que pretendo explorar futuramente:

- observabilidade com métricas e alertas;
- armazenamento histórico em camada analítica;
- Terraform para provisionamento de infraestrutura;
- gerenciamento de segredos;
- orquestração com Airflow ou Prefect;
- dashboard para acompanhamento dos dados.

## Sobre o projeto

Este repositório registra uma etapa do meu processo de aprendizado em Engenharia de Dados.

A proposta não é representar experiência profissional na área, mas demonstrar o contato prático com tecnologias e conceitos estudados, documentando o que foi implementado, testado e aprendido ao longo do projeto.
