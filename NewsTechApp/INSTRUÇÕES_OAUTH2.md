# Instruções para Configurar OAuth2

## Problemas Corrigidos

1. **Links OAuth2 no template**: Corrigidos de `/login/google` e `/login/github` para `/oauth2/login/google` e `/oauth2/login/github`
2. **Configuração dos blueprints**: Removidos `redirect_url` fixos e ajustados `redirect_to` para as funções corretas
3. **Rotas de inicialização**: Criadas rotas específicas para iniciar o processo OAuth2

## Configuração no Google Cloud Console

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Vá para "APIs & Services" > "Credentials"
3. Crie ou edite suas credenciais OAuth 2.0
4. Adicione as seguintes URLs autorizadas de redirecionamento:
   - Para desenvolvimento local: `http://localhost:5000/oauth2/login/google/authorized`
   - Para produção no Render: `https://SEU_DOMINIO_RENDER.onrender.com/oauth2/login/google/authorized`

## Configuração no GitHub

1. Acesse [GitHub Developer Settings](https://github.com/settings/developers)
2. Vá para "OAuth Apps" e crie ou edite sua aplicação
3. Configure as seguintes URLs:
   - Homepage URL: `https://SEU_DOMINIO_RENDER.onrender.com`
   - Authorization callback URL: `https://SEU_DOMINIO_RENDER.onrender.com/oauth2/login/github/authorized`

## Variáveis de Ambiente no Render

Configure as seguintes variáveis de ambiente no painel do Render:

```
GOOGLE_CLIENT_ID=seu_google_client_id
GOOGLE_CLIENT_SECRET=seu_google_client_secret
GITHUB_CLIENT_ID=seu_github_client_id
GITHUB_CLIENT_SECRET=seu_github_client_secret
SECRET_KEY=uma_chave_secreta_forte
```

## Fluxo OAuth2 Corrigido

1. Usuário clica em "Google" ou "GitHub" no formulário de login
2. É redirecionado para `/oauth2/login/google` ou `/oauth2/login/github`
3. Essas rotas redirecionam para o provedor OAuth2 (Google/GitHub)
4. Após autorização, o usuário retorna para `/oauth2/login/google/authorized` ou `/oauth2/login/github/authorized`
5. A aplicação processa a resposta e faz login do usuário

## Teste Local

Para testar localmente:

1. Crie um arquivo `.env` com suas credenciais
2. Configure URLs de callback para `localhost:5000`
3. Execute a aplicação e teste os logins OAuth2

