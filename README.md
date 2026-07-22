# Auditor de Acessos v1.0

Bot corporativo para automatizar a auditoria de acessos, construído com o
ecossistema BotCity (Maestro, DataPool e Credentials Vault).

## Estrutura

```
auditor_acessos_bot/
├── .env                # modelo de variáveis de ambiente (copie para .env)
├── config.py           # configuração central (paths, flags, labels)
├── logger.py           # logging padronizado (arquivo + console)
├── maestro_client.py   # wrapper de integração com o Maestro (com modo offline)
├── bot.py              # regras de negócio: validação + simulação do ERP
├── dispatcher.py       # Etapa A: lê o CSV e popula o DataPool
├── main.py             # Etapa B: consome o DataPool e audita (Performer)
├── dados_entrada/
│   └── usuarios_auditoria.csv   # dados de exemplo (item 3 tem CPF em branco de propósito)
└── logs/
    └── execucao.log     # gerado em tempo de execução
```

## Como rodar

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar o ambiente
```bash
cp .env
```
Edite o `.env` com os dados do seu Maestro quando quiser rodar integrado (veja
abaixo o modo offline para testar sem servidor).

### 3. No painel do BotCity Maestro
- Crie o DataPool com o label configurado em `DATAPOOL_LABEL` (padrão: `FilaAuditoriaRH`).
- Crie a credencial no Vault com o label configurado em `CREDENTIAL_LABEL`
  (padrão: `credencial_erp`), com as chaves `username` e `password`.

### 4. Rodar o Dispatcher (Etapa A — popula a fila)
```bash
python dispatcher.py
```

### 5. Rodar o Bot Principal (Etapa B — consome a fila e audita)
```bash
python main.py
```

## Modo offline (testar sem Maestro real)

Com `MAESTRO_ENABLED=false` e `VAULT_ENABLED=false` no `.env` (valores padrão
do `.env.example`), o bot roda 100% localmente:
- O DataPool é simulado em `logs/datapool_<label>.json`.
- A credencial retorna um usuário/senha fictícios (a senha nunca é logada).
- Alertas e artefatos são apenas registrados no log local.

Isso permite validar toda a lógica de negócio e resiliência — inclusive o
comportamento do item 3 (CPF em branco) — antes de conectar ao Maestro real.
Para rodar de fato integrado ao Maestro, basta trocar as duas flags para
`true` e preencher `MAESTRO_SERVER`, `MAESTRO_LOGIN` e `MAESTRO_KEY`.

## Requisitos atendidos

- **Estrutura modular**: `main.py`, `config.py`, `bot.py`, `dispatcher.py`,
  `maestro_client.py`, `logger.py` — cada um com responsabilidade única.
- **Sem hardcoding**: todos os paths e labels vêm do `.env` via `config.py`.
- **Logs padronizados**: `logs/execucao.log` com timestamp, nível (INFO/WARNING/ERROR) e mensagem.
- **Fail Fast**: se `dados_entrada/` não existir, o bot emite um alerta no
  Maestro e encerra imediatamente com código de saída 1 (testado tanto no
  Dispatcher quanto no Performer).
- **`ExecutionResult`**: classe em `main.py` que padroniza o resumo da
  execução (sucessos, erros, duração) e é postada como artefato JSON no Maestro.
- **DataPool**: Dispatcher (`dispatcher.py`) alimenta a fila; Performer
  (`main.py`) consome em loop `while`.
- **Resiliência de item**: CPF em branco levanta `ValidationError`, o item é
  marcado como erro no DataPool e o loop continua para o próximo item.
- **Credentials Vault**: usuário/senha do "ERP" vêm exclusivamente do Vault
  em tempo de execução (`maestro_client.get_credential`); a senha nunca é
  impressa ou logada — apenas `"Acessando sistema com o usuário: ..."`.
