// Configuração inicial
const SIMULATION_DEFAULT = true;

// Utilidades
const $ = (id) => document.getElementById(id);
const feedbackEl = $("feedback");
function feedback(type, msg){
  feedbackEl.className = "feedback " + (type === "success" ? "success" : "error");
  feedbackEl.textContent = msg;
  feedbackEl.style.display = "block";
}

// Login local (usuário/senha)
$("local-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const u = $("username").value.trim();
  const p = $("password").value;
  if (u === "teste" && p === "123"){
    feedback("success", "Login bem-sucedido! ✅ (local)");
  } else {
    feedback("error", "Credenciais inválidas. Tente usuário='teste' e senha='123'.");
  }
});

// Controle de simulação e client ids
$("simMode").checked = SIMULATION_DEFAULT;

function getConfig(){
  return {
    simulate: $("simMode").checked,
    googleClientId: $("googleClientId").value.trim(),
    githubClientId: $("githubClientId").value.trim(),
    redirectUri: $("redirectUri").value.trim() || window.location.origin + "/callback.html"
  };
}

// Botões sociais
$("btn-google").addEventListener("click", () => {
  const cfg = getConfig();
  if (cfg.simulate || !cfg.googleClientId){
    feedback("success", "Simulando login com Google... ✅");
    return;
  }
  // Redireciona para o endpoint de autorização do Google (fluxo Authorization Code com PKCE – requer backend)
  const params = new URLSearchParams({
    client_id: cfg.googleClientId,
    redirect_uri: cfg.redirectUri,
    response_type: "code",
    scope: "openid email profile",
    access_type: "offline",
    include_granted_scopes: "true",
    prompt: "consent"
  });
  window.location.href = "https://accounts.google.com/o/oauth2/v2/auth?" + params.toString();
});

$("btn-github").addEventListener("click", () => {
  const cfg = getConfig();
  if (cfg.simulate || !cfg.githubClientId){
    feedback("success", "Simulando login com GitHub... ✅");
    return;
  }
  // Redireciona para o endpoint de autorização do GitHub (Authorization Code – requer backend)
  const params = new URLSearchParams({
    client_id: cfg.githubClientId,
    redirect_uri: cfg.redirectUri,
    scope: "read:user user:email",
    allow_signup: "true"
  });
  window.location.href = "https://github.com/login/oauth/authorize?" + params.toString();
});
