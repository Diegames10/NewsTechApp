# Deploy do NewsTechApp no Render

## Problema Resolvido

O projeto estava configurado para salvar o banco de dados SQLite em um local temporário que não persiste entre reinicializações do container no Render. Esta configuração foi corrigida para usar o disco persistente do Render.

## Alterações Realizadas

### 1. Configuração do Banco de Dados
- **Arquivo**: `login_app/app.py`
- **Mudança**: Configurado para usar `/data/app.db` com criação automática do diretório
- **Benefício**: Dados persistem entre reinicializações do container

### 2. Dockerfile Atualizado
- **Arquivo**: `Dockerfile`
- **Mudanças**:
  - Criação do diretório `/data` no container
  - Adição de script de inicialização `start.sh`
  - Configuração adequada de permissões

### 3. Script de Inicialização
- **Arquivo**: `start.sh`
- **Função**: 
  - Verifica e cria o diretório `/data` se necessário
  - Inicializa o banco de dados na primeira execução
  - Inicia o servidor Gunicorn

### 4. Configuração do Render
- **Arquivo**: `render.yaml`
- **Configuração**:
  - Disco persistente de 1GB montado em `/data`
  - Variáveis de ambiente necessárias
  - Configuração de health check

## Como Fazer o Deploy

### Opção 1: Via Dashboard do Render

1. Acesse o [Render Dashboard](https://dashboard.render.com)
2. Clique em "New +" → "Web Service"
3. Conecte seu repositório GitHub
4. Configure:
   - **Environment**: Docker
   - **Dockerfile Path**: `./Dockerfile`
   - **Docker Context**: `.`
5. Na seção "Advanced":
   - Adicione um **Persistent Disk**:
     - Name: `newstech-data`
     - Mount Path: `/data`
     - Size: 1GB (ou mais conforme necessário)
6. Configure as variáveis de ambiente:
   - `SECRET_KEY`: (gere uma chave secreta)
   - `PYTHONUNBUFFERED`: `1`

### Opção 2: Via render.yaml (Recomendado)

1. Faça commit do arquivo `render.yaml` no seu repositório
2. No Render Dashboard, clique em "New +" → "Blueprint"
3. Conecte seu repositório e o Render detectará automaticamente o `render.yaml`

## Estrutura de Arquivos Atualizada

```
NewsTechApp/
├── Dockerfile                 # Container configuration
├── start.sh                  # Initialization script
├── render.yaml              # Render deployment config
├── README_RENDER.md         # This documentation
└── login_app/
    ├── app.py               # Updated with persistent storage
    ├── init_db.py          # Database initialization script
    └── ... (outros arquivos)
```

## Verificação Pós-Deploy

Após o deploy, você pode verificar se tudo está funcionando:

1. Acesse a URL fornecida pelo Render
2. Registre um novo usuário
3. Faça logout e login novamente
4. Reinicie o serviço no Render Dashboard
5. Verifique se o usuário ainda existe (dados persistiram)

## Monitoramento

- **Logs**: Disponíveis no Render Dashboard
- **Banco de dados**: Localizado em `/data/app.db` no container
- **Backup**: O Render faz backup automático dos discos persistentes

## Troubleshooting

### Problema: Banco de dados não persiste
- **Solução**: Verifique se o disco persistente está configurado corretamente em `/data`

### Problema: Erro de permissão
- **Solução**: O script `start.sh` já configura as permissões necessárias

### Problema: Aplicação não inicia
- **Solução**: Verifique os logs no Render Dashboard para identificar o erro específico

## Custos

- **Web Service**: Gratuito (com limitações) ou pago conforme o plano
- **Persistent Disk**: ~$0.25/GB/mês (1GB = ~$0.25/mês)

## Próximos Passos

1. Configure um domínio personalizado (opcional)
2. Configure SSL/TLS (automático no Render)
3. Configure monitoramento e alertas
4. Implemente backup adicional se necessário

