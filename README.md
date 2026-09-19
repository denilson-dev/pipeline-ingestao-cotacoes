# 🚀 Cloud-Native Secure Data Ingestion Pipeline

Pipeline de dados automatizado, seguro e escalável desenvolvido para ingestão, tratamento e armazenamento de dados em nuvem, utilizando boas práticas de infraestrutura, containerização e automação.

---

## 🏗️ Arquitetura do Projeto

O projeto foi desenhado focando na segurança e isolamento dos componentes, simulando um ambiente de produção real:

1. **Infraestrutura em Nuvem (AWS EC2):** Instância Ubuntu rodando em ambiente isolado com regras restritas de firewall (Security Groups).
2. **Containerização (Docker):** O banco de dados PostgreSQL roda encapsulado em um container Docker, garantindo portabilidade, facilidade de deploy e isolamento de recursos.
3. **Extração e Transformação (Python):** Script em Python responsável por consumir dados de API externa, realizar limpeza e tratamento estrutural com `pandas`, e persistir no banco.
4. **Automação (Linux Cron):** Rotina agendada no sistema operacional para execução autônoma diária do pipeline.

---

## 🛠️ Tecnologias Utilizadas

* **Cloud:** AWS EC2 (Linux Ubuntu)
* **Banco de Dados:** PostgreSQL (via Docker)
* **Linguagem:** Python 3.x (`requests`, `pandas`, `psycopg2`)
* **Containerização:** Docker & Docker Compose
* **Automação:** Linux Cron Jobs
* **Versionamento:** Git & GitHub

---

## 📂 Estrutura de Diretórios

```text
pipeline_ingestao/
├── Dockerfile              # Configuração do ambiente do script
├── docker-compose.yml      # Orquestração do banco PostgreSQL
├── main.py                 # Script principal de ETL (Python)
├── requirements.txt        # Dependências do projeto Python
├── .env                    # Variáveis de ambiente sensíveis (credenciais)
└── README.md               # Documentação oficial do projeto
