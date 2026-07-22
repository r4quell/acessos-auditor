# Auditor de Acessos v1.0

Bot corporativo desenvolvido para automatizar o processo de auditoria de acessos, utilizando o ecossistema **BotCity Maestro**, **DataPool** e **Credentials Vault**.

O projeto simula um cenário corporativo de validação de usuários, processamento de filas, integração segura com credenciais e tratamento de exceções, seguindo boas práticas de desenvolvimento RPA.

---

## Tecnologias utilizadas

- Python
- BotCity Maestro
- BotCity DataPool
- BotCity Credentials Vault
- CSV para entrada de dados
- Logging estruturado
- Variáveis de ambiente com `.env`

---

## Estrutura do projeto

```text
auditor_acessos_bot/
├── .env                      # variáveis de ambiente e configurações do bot
├── config.py                 # configuração central do projeto
├── logger.py                 # logging em arquivo e console
├── maestro_client.py         # integração com BotCity Maestro/Vault
├── bot.py                    # regras de negócio e validações
├── dispatcher.py             # Etapa A: alimentação do DataPool
├── main.py                   # Etapa B: execução do Performer
├── requirements.txt          # dependências do projeto
├── dados_entrada/
│   └── usuarios_auditoria.csv # massa de dados para auditoria
└── logs/
    └── execucao.log          # logs gerados durante execução
```

---

## Como executar

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar ambiente

Configure o arquivo `.env` com as variáveis necessárias para execução do bot.

Exemplo de configuração offline:

```env
MAESTRO_ENABLED=false
VAULT_ENABLED=false
```

Para executar integrado ao BotCity Maestro, preencha também as configurações do servidor, login e chave de acesso.

---

## Configuração do BotCity Maestro

No painel do BotCity Maestro:

1. Criar um **DataPool** com o label configurado em `DATAPOOL_LABEL`.

Exemplo:

```text
FilaAuditoriaRH
```

2. Criar uma credencial no **Credentials Vault** com o label configurado em `CREDENTIAL_LABEL`.

Chaves esperadas:

```text
username
password
```

---

## Execução do fluxo

### Etapa A - Dispatcher

Responsável por ler o arquivo CSV e inserir os itens no DataPool.

```bash
python dispatcher.py
```

### Etapa B - Performer

Responsável por consumir os itens da fila e executar a auditoria.

```bash
python main.py
```

---

## Modo offline

O projeto possui modo offline para testes sem conexão com o Maestro.

No arquivo `.env`:

```env
MAESTRO_ENABLED=false
VAULT_ENABLED=false
```

Nesse modo:

- O DataPool é simulado localmente.
- As credenciais são fictícias.
- Senhas nunca são exibidas nos logs.
- Alertas e resultados ficam registrados localmente.

Esse modo permite validar toda a lógica do bot antes da integração com ambiente corporativo.

---

## Funcionalidades implementadas

### Estrutura modular

Cada módulo possui uma responsabilidade única:

- `main.py` → execução principal do bot.
- `dispatcher.py` → envio de dados para fila.
- `bot.py` → regras de auditoria.
- `config.py` → configurações centralizadas.
- `logger.py` → gerenciamento de logs.
- `maestro_client.py` → integração Maestro e Vault.

### Segurança

- Credenciais protegidas através do `.env`.
- Integração com Credentials Vault.
- Senhas nunca são armazenadas em código ou exibidas nos logs.

### Tratamento de erros

- Validação de dados de entrada.
- Estratégia Fail Fast para falhas críticas.
- Continuidade da execução mesmo quando um item apresenta erro.

Exemplo:

- Usuário com CPF vazio gera erro de validação.
- Item é marcado como erro.
- Próximo usuário continua sendo processado.

---

## Requisitos atendidos

✅ Automação corporativa utilizando BotCity Maestro.  
✅ Processamento de fila com DataPool.  
✅ Uso de Credentials Vault para credenciais sensíveis.  
✅ Arquitetura modular e organizada.  
✅ Configurações externas via `.env`.  
✅ Logs padronizados com timestamp, nível e mensagem.  
✅ Classe `ExecutionResult` para resumo da execução.  
✅ Tratamento de exceções e resiliência por item.  

---

## Exemplo de log

```text
INFO - Iniciando auditoria de acessos
INFO - Acessando sistema com o usuário: usuario_teste
WARNING - CPF inválido ou ausente para usuário 003
INFO - Execução finalizada
```

---
