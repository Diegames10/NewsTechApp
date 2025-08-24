# Demo – Login com três métodos (Local, Google, GitHub)

Esta é uma implementação **simplificada** para demonstrar o diagrama de casos de uso do *Sistema de Autenticação*.
Ela oferece três formas de login: **usuário/senha**, **Google** e **GitHub**.

> ⚠️ Os logins com Google e GitHub funcionam em **modo de simulação por padrão**. Para torná-los reais, veja a seção **Habilitar OAuth de verdade**.

## Estrutura
```
login-multimetodos/
├─ index.html
├─ styles.css
├─ app.js
└─ callback.html
```

## Como rodar
Abra o `index.html` em um servidor estático (ex.: extensão *Live Server* do VS Code ou `python -m http.server 5500`) e acesse:
```
http://localhost:5500/index.html
```

### Login e Senha (simulado)
- Sucesso se **usuário = `teste`** e **senha = `123`**.
- Caso contrário, uma mensagem de erro é exibida.

### Login com Google / GitHub
- Por padrão, o **Modo simulação** fica ativado (expandir *Configurações* na página).
- Você verá mensagens de sucesso simuladas.
- Para executar o fluxo real, desmarque *Modo simulação* e informe os `CLIENT_ID`s, conforme abaixo.

## Habilitar OAuth de verdade

> É necessário um **backend** para trocar o `code` por um **access token** (fluxo *Authorization Code*). O front-end deste projeto apenas **redireciona** para o provedor e recebe o `code` em `callback.html`.

### Google
1. Crie um projeto no **Google Cloud Console** e habilite *OAuth consent screen*.
2. Crie uma credencial **OAuth 2.0 Client ID** (tipo *Web application*).
3. Configure **Authorized redirect URIs** (ex.: `http://localhost:5500/callback.html`).
4. Copie o `client_id` e cole na seção de configurações da página.
5. Desmarque *Modo simulação* e clique em **Continuar com Google**.

### GitHub
1. Em **Settings → Developer settings → OAuth Apps**, crie um **New OAuth App**.
2. Defina **Authorization callback URL** (ex.: `http://localhost:5500/callback.html`).
3. Copie o **Client ID** e cole na seção de configurações da página.
4. Desmarque *Modo simulação* e clique em **Continuar com GitHub**.

### Backend (esboço)
- O provedor redireciona de volta a `callback.html` com `?code=...`.
- Seu backend deve expor rotas, por exemplo:
  - `POST /oauth/google/token` → troca `code` por token no endpoint do Google.
  - `POST /oauth/github/token` → troca `code` por token no endpoint do GitHub.
- O backend valida o token, cria sessão/jwt e retorna ao front-end.

## Relação com o Diagrama de Caso de Uso
- **Efetuar Login**: ação principal do usuário na tela.
- **Autenticar com Login e Senha**: validado no `app.js` com credenciais simuladas.
- **Autenticar com Google / GitHub**: botões que disparam o fluxo OAuth (simulado por padrão; real com CLIENT_ID).
- O feedback visual reflete sucesso/erro conforme o fluxo, exatamente como indicado nos requisitos.

## Licença
MIT
