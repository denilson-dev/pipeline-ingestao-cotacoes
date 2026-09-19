# 🚀 Pipeline de Ingestão Diária de Cotações Financeiras

Pipeline automatizado para extração, tratamento e armazenamento de dados de cotações de moedas em tempo real, utilizando **Python**, **PostgreSQL**, **Docker** e hospedado em infraestrutura de nuvem na **AWS (EC2)**.

---

## 🏗️ Arquitetura da Solução

```text
[ API AwesomeAPI ] ──> [ Script Python (ETL) ] ──> [ PostgreSQL (Container Docker) ]
                                │
                        [ Agendamento Crontab ]
