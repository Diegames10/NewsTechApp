// publicar.init.js
import { dbAddPublicacao } from "./db.js"; // ajuste o caminho se necessário

// Espera a página carregar para conectar nos elementos
window.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("form-noticia");
  const inputImg = document.getElementById("imagem");

  async function fileToDataURL(file) {
    if (!file) return null;
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = () => reject(reader.error);
      reader.readAsDataURL(file);
    });
  }

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      const titulo = document.getElementById("titulo").value.trim();
      const autor = document.getElementById("autor").value.trim();
      const conteudo = document.getElementById("conteudo").value.trim();
      const img = inputImg?.files?.[0] || null;

      if (!titulo || !autor || !conteudo) {
        alert("Preencha título, autor e conteúdo.");
        return;
      }

      try {
        const imagemDataURL = await fileToDataURL(img);
        const { id } = await dbAddPublicacao({ titulo, autor, conteudo, imagemDataURL });
        alert(`Publicação salva localmente (ID ${id}).`);
        form.reset();
        const preview = document.getElementById("preview-noticia");
        if (preview) preview.remove();
      } catch (err) {
        console.error(err);
        alert("Falha ao salvar no banco local: " + err.message);
      }
    });
  }

  if (inputImg) {
    inputImg.addEventListener("change", () => {
      const file = inputImg.files && inputImg.files[0];
      if (!file) return;
      let preview = document.getElementById("preview-noticia");
      if (!preview) {
        preview = document.createElement("img");
        preview.id = "preview-noticia";
        preview.style.maxWidth = "320px";
        preview.style.display = "block";
        preview.style.marginTop = "8px";
        inputImg.parentElement.appendChild(preview);
      }
      const reader = new FileReader();
      reader.onload = () => (preview.src = reader.result);
      reader.readAsDataURL(file);
    });
  }
});
