# Hikvision ISUP Bridge

Ponte entre terminais biométricos Hikvision (DS-K1T342MFWX) e a plataforma Exousia School.

## Como funciona

1. O terminal Hikvision conecta via **ISUP (EHome)** neste servidor na porta `7660`
2. Quando um aluno encosta o dedo, o terminal envia um evento de acesso
3. Este serviço traduz o evento e encaminha para a API Exousia (`POST /attendance`)

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/health` | Status do serviço |
| `POST` | `/simulate/event` | Simular evento biométrico (teste) |
| `POST` | `/users/sync` | Cadastrar aluno no terminal |
| `POST` | `/users/capture-fingerprint` | Iniciar captura de digital |
| `DELETE` | `/users/{employee_no}` | Remover aluno do terminal |

## Variáveis de Ambiente

```env
ISUP_LISTEN_PORT=7660
EXOUSIA_API_URL=https://exousia-school-backend.vpcxvl.easypanel.host/api/v1
BRIDGE_PORT=9500
```

## Rodar localmente

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 9500 --reload
```

## Docker

```bash
docker build -t hikvision-bridge .
docker run -p 9500:9500 -p 7660:7660 hikvision-bridge
```
