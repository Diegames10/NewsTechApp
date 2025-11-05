// ---- Seletores do formulário (ajuste os IDs se forem diferentes) ----
const $form        = document.getElementById("form-publicar");
const $titulo      = document.getElementById("titulo");
const $autor       = document.getElementById("autor");
const $conteudo    = document.getElementById("conteudo");
const $imagem      = document.getElementById("imagem");     // <input type="file">
const $preview     = document.getElementById("preview");    // <img id="preview">
const $btnSalvar   = document.getElementById("btn-salvar");
const $status      = document.getElementById("status");     // <div id="status"> opcional

function msg(txt, ok=false){
  if (!$status) return;
  $status.textContent = txt;
  $status.style.color = ok ? "var(--ok, #16a34a)" : "var(--err, #dc2626)";
}

function getId(){
  const id = Number(new URLSearchParams(location.search).get("id"));
  return Number.isFinite(id) && id > 0 ? id : null;
}

function escapeHtml(s=""){
  return s.replace(/[&<>"']/g, c => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
  })[c]);
}

// Pré-visualização da imagem
$imagem?.addEventListener("change", () => {
  const f = $imagem.files?.[0];
  if (!f){ $preview?.setAttribute("style","display:none"); return; }
  const url = URL.createObjectURL(f);
  if ($preview){
    $preview.src = url;
    $preview.style.display = "block";
  }
});

// Carrega dados do post para edição (GET /api/posts/<id>)
async function carregar(){
  const id = getId();
  if (!id){
    // modo criar (sem id) — apenas limpa e segue
    msg("");
    return;
  }
  try{
    msg("Carregando…");
    const r = await fetch(`/api/posts/${id}`, { headers: { Accept: "application/json" }});
    if (!r.ok) throw new Error(`Falha ao carregar (${r.status})`);
    const p = await r.json();

    $titulo.value   = p.titulo || "";
    $autor.value    = p.autor || "";
    $conteudo.value = p.conteudo || "";

    if (p.image_url){
      if ($preview){
        $preview.src = p.image_url;
        $preview.style.display = "block";
      }
      // guarda a URL atual para detectar troca opcionalmente
      $preview.dataset.current = p.image_url;
    } else if ($preview){
      $preview.removeAttribute("src");
      $preview.style.display = "none";
      delete $preview.dataset.current;
    }

    msg("Carregado.", true);
  }catch(e){
    console.error(e);
    msg("Falha ao carregar os dados do post.");
  }
}

// Salva (criar ou atualizar)
async function salvar(e){
  e?.preventDefault?.();
  const id = getId();

  const temImagemNova = $imagem?.files && $imagem.files.length > 0;

  let url  = "/api/posts";
  let met  = "POST";
  if (id){ url = `/api/posts/${id}`; met = "PUT"; }

  try{
    $btnSalvar?.setAttribute("disabled","disabled");
    msg("Salvando…");

    let r;
    if (temImagemNova){
      // Envia multipart se usuário escolheu nova imagem
      const fd = new FormData();
      fd.set("titulo",   $titulo.value.trim());
      fd.set("autor",    $autor.value.trim());
      fd.set("conteudo", $conteudo.value.trim());
      fd.set("imagem",   $imagem.files[0]); // nome do campo que seu backend espera

      r = await fetch(url, { method: met, body: fd });
    } else {
      // Sem nova imagem → JSON (mantém a existente no servidor)
      const payload = {
        titulo:   $titulo.value.trim(),
        autor:    $autor.value.trim(),
        conteudo: $conteudo.value.trim()
      };
      r = await fetch(url, {
        method: met,
        headers: { "Content-Type": "application/json", "Accept":"application/json" },
        body: JSON.stringify(payload)
      });
    }

    if (!r.ok){
      const txt = await r.text().catch(()=> "");
      throw new Error(`Falha ao salvar (${r.status}) ${txt}`);
    }

    msg("Salvo com sucesso!", true);

    // Redireciona para a home após salvar (opcional)
    setTimeout(()=> { location.href = "/"; }, 500);

  } catch(e){
    console.error(e);
    msg("Erro ao salvar. Veja o console para detalhes.");
  } finally {
    $btnSalvar?.removeAttribute("disabled");
  }
}

$form?.addEventListener("submit", salvar);

// Start
carregar();
