// === Seletores compatíveis com publicar.html atual ===
const $form      = document.getElementById("form-post");   // era form-publicar
const $titulo    = document.getElementById("titulo");
const $conteudo  = document.getElementById("conteudo");
const $image     = document.getElementById("image");       // era imagem
const $preview   = document.getElementById("preview");     // se existir no HTML
const $status    = document.getElementById("status");      // opcional

function msg(txt, ok=false){
  if (!$status) return;
  $status.textContent = txt;
  $status.style.color = ok ? "var(--ok, #16a34a)" : "var(--err, #dc2626)";
}

// Prévia opcional
$image?.addEventListener("change", () => {
  if (!$preview || !$image.files?.length) return;
  const file = $image.files[0];
  const reader = new FileReader();
  reader.onload = e => {
    $preview.src = e.target.result;
    $preview.style.display = "block";
  };
  reader.readAsDataURL(file);
});

async function salvar(ev){
  ev.preventDefault();

  const titulo   = ($titulo?.value || "").trim();
  const conteudo = ($conteudo?.value || "").trim();
  const file     = $image?.files?.[0] || null;

  if (!titulo || !conteudo){
    msg("Preencha título e conteúdo.");
    return;
  }

  try {
    const fd = new FormData();
    fd.set("titulo", titulo);
    fd.set("conteudo", conteudo);
    if (file) fd.set("image", file);      // name="image" no HTML

    const r = await fetch("/api/posts/", {
      method: "POST",
      body: fd
      // cookies de sessão seguem automaticamente (mesmo domínio)
    });

    if (!r.ok){
      const j = await r.json().catch(()=>({}));
      throw new Error(j?.error || `Falha ao salvar (${r.status})`);
    }

    msg("Post publicado com sucesso!", true);
    // redireciona ao portal
    setTimeout(()=> { location.href = "/"; }, 600);

  } catch(e){
    console.error(e);
    msg(e.message || "Erro ao salvar.");
  }
}

$form?.addEventListener("submit", salvar);
