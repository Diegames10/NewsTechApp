// db.js — CRUD completo em SQLite (sql.js + IndexedDB) para "publicacoes.db"
// Usa CDN para sql.js (sem precisar baixar arquivos .wasm)
// Rode via servidor local (Live Server ou python -m http.server) para o WASM carregar.

const SQLITE_JS_CDN   = "https://cdn.jsdelivr.net/npm/sql.js@1.10.2/dist/sql-wasm.js";
const SQLITE_WASM_CDN = "https://cdn.jsdelivr.net/npm/sql.js@1.10.2/dist/sql-wasm.wasm";

const VIRTUAL_DB_FILENAME = "publicacoes.db";     // nome lógico do arquivo no IndexedDB
const IDB_DB_NAME = "sqljs-idb";
const IDB_STORE_NAME = "files";

// ---------- IndexedDB helpers ----------
function idbOpen() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(IDB_DB_NAME, 1);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(IDB_STORE_NAME)) {
        db.createObjectStore(IDB_STORE_NAME);
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function idbGet(key) {
  const db = await idbOpen();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(IDB_STORE_NAME, "readonly");
    const store = tx.objectStore(IDB_STORE_NAME);
    const req = store.get(key);
    req.onsuccess = () => resolve(req.result || null);
    req.onerror = () => reject(req.error);
  });
}

async function idbSet(key, value) {
  const db = await idbOpen();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(IDB_STORE_NAME, "readwrite");
    const store = tx.objectStore(IDB_STORE_NAME);
    const req = store.put(value, key);
    req.onsuccess = () => resolve(true);
    req.onerror = () => reject(req.error);
  });
}

// ---------- Carregar sql.js dinamicamente ----------
function loadSqlJs() {
  return new Promise((resolve, reject) => {
    if (window.initSqlJs) return resolve(window.initSqlJs);
    const s = document.createElement("script");
    s.src = SQLITE_JS_CDN;
    s.async = true;
    s.onload = () => resolve(window.initSqlJs);
    s.onerror = () => reject(new Error("Falha ao carregar sql-wasm.js"));
    document.head.appendChild(s);
  });
}

let SQL = null; // namespace do sql.js
let db  = null; // instância do banco em memória (sql.js)

// ---------- Abrir/Inicializar o banco ----------
async function openDatabase() {
  if (db) return db;

  const initSqlJs = await loadSqlJs();
  SQL = await initSqlJs({
    locateFile: () => SQLITE_WASM_CDN,
  });

  const saved = await idbGet(VIRTUAL_DB_FILENAME);
  if (saved) {
    db = new SQL.Database(new Uint8Array(saved));
  } else {
    db = new SQL.Database();
    db.run(`
      PRAGMA foreign_keys = ON;

      CREATE TABLE IF NOT EXISTS publicacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        autor TEXT NOT NULL,
        conteudo TEXT NOT NULL,
        imagemDataURL TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT
      );

      CREATE INDEX IF NOT EXISTS idx_publicacoes_created_at ON publicacoes(created_at);
      CREATE INDEX IF NOT EXISTS idx_publicacoes_titulo ON publicacoes(titulo);
    `);
    await persistDatabase();
  }
  return db;
}

async function persistDatabase() {
  if (!db) return;
  const data = db.export(); // Uint8Array
  await idbSet(VIRTUAL_DB_FILENAME, data);
}

// ---------- Utilidades ----------
function nowISO() {
  return new Date().toISOString();
}

function bindAndCollectRows(database, sql, params = []) {
  const stmt = database.prepare(sql);
  if (params && params.length) stmt.bind(params);
  const rows = [];
  while (stmt.step()) rows.push(stmt.getAsObject());
  stmt.free();
  return rows;
}

// ---------- CRUD ----------

// C (Create)
export async function dbAddPublicacao({ titulo, autor, conteudo, imagemDataURL }) {
  const database = await openDatabase();
  const created_at = nowISO();
  const stmt = database.prepare(`
    INSERT INTO publicacoes (titulo, autor, conteudo, imagemDataURL, created_at)
    VALUES (?, ?, ?, ?, ?)
  `);
  stmt.run([titulo, autor, conteudo, imagemDataURL || null, created_at]);
  stmt.free();
  await persistDatabase();

  const idRow = database.exec("SELECT last_insert_rowid() AS id;")[0]?.values?.[0]?.[0];
  return { id: idRow, created_at };
}

// R (Read) — listar com busca/ordenação/paginação
export async function dbListPublicacoes({ q = "", order = "recente", limit = 50, offset = 0 } = {}) {
  const database = await openDatabase();
  let sql = "SELECT id, titulo, autor, conteudo, imagemDataURL, created_at, updated_at FROM publicacoes";
  const params = [];

  if (q && q.trim()) {
    sql += " WHERE titulo LIKE ? OR conteudo LIKE ?";
    const like = `%${q.trim()}%`;
    params.push(like, like);
  }

  if (order === "antigo") {
    sql += " ORDER BY datetime(created_at) ASC";
  } else if (order === "titulo-az") {
    sql += " ORDER BY titulo COLLATE NOCASE ASC";
  } else if (order === "titulo-za") {
    sql += " ORDER BY titulo COLLATE NOCASE DESC";
  } else {
    sql += " ORDER BY datetime(created_at) DESC";
  }

  if (Number.isFinite(limit) && Number.isFinite(offset)) {
    sql += " LIMIT ? OFFSET ?";
    params.push(limit, offset);
  }

  return bindAndCollectRows(database, sql, params);
}

// R (Read) — obter 1 por id
export async function dbGetPublicacao(id) {
  const database = await openDatabase();
  const rows = bindAndCollectRows(
    database,
    "SELECT id, titulo, autor, conteudo, imagemDataURL, created_at, updated_at FROM publicacoes WHERE id = ?",
    [id]
  );
  return rows[0] || null;
}

// U (Update) — atualizar campos passados no payload
export async function dbUpdatePublicacao(id, { titulo, autor, conteudo, imagemDataURL }) {
  const database = await openDatabase();

  // Monta dinâmico só com os campos fornecidos
  const sets = [];
  const params = [];
  if (typeof titulo !== "undefined") { sets.push("titulo = ?"); params.push(titulo); }
  if (typeof autor !== "undefined") { sets.push("autor = ?"); params.push(autor); }
  if (typeof conteudo !== "undefined") { sets.push("conteudo = ?"); params.push(conteudo); }
  if (typeof imagemDataURL !== "undefined") { sets.push("imagemDataURL = ?"); params.push(imagemDataURL); }
  sets.push("updated_at = ?"); params.push(nowISO());

  if (sets.length === 1) { // só updated_at
    return { updated: 0 };
  }

  const sql = `UPDATE publicacoes SET ${sets.join(", ")} WHERE id = ?`;
  params.push(id);

  const stmt = database.prepare(sql);
  stmt.run(params);
  stmt.free();
  await persistDatabase();

  // checa quantas linhas foram afetadas
  // (sql.js não traz changes() no prepare; usamos SELECT para conferir existência)
  const row = await dbGetPublicacao(id);
  return { updated: row ? 1 : 0 };
}

// D (Delete)
export async function dbDeletePublicacao(id) {
  const database = await openDatabase();
  const stmt = database.prepare("DELETE FROM publicacoes WHERE id = ?");
  stmt.run([id]);
  stmt.free();
  await persistDatabase();
  return { deleted: 1 }; // assume sucesso; para checar, você pode consultar antes
}

// Count (útil p/ paginação)
export async function dbCountPublicacoes({ q = "" } = {}) {
  const database = await openDatabase();
  let sql = "SELECT COUNT(*) AS total FROM publicacoes";
  const params = [];
  if (q && q.trim()) {
    sql += " WHERE titulo LIKE ? OR conteudo LIKE ?";
    const like = `%${q.trim()}%`;
    params.push(like, like);
  }
  const rows = bindAndCollectRows(database, sql, params);
  return rows[0]?.total ?? 0;
}

// Exporta .db binário p/ download
export async function dbExportBlob() {
  const database = await openDatabase();
  const data = database.export();
  return new Blob([data], { type: "application/octet-stream" });
}

// Importa .db binário (sobrescreve o banco atual)
export async function dbImportBlob(blob) {
  const arr = new Uint8Array(await blob.arrayBuffer());
  const initSqlJs = await loadSqlJs();
  SQL = await initSqlJs({ locateFile: () => SQLITE_WASM_CDN });
  db = new SQL.Database(arr);
  await persistDatabase();
}

// Limpa tudo (DANGER)
export async function dbClearAll() {
  const database = await openDatabase();
  database.run("DELETE FROM publicacoes;");
  await persistDatabase();
}
