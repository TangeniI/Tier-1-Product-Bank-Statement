// Run the FastAPI engine and the Next.js app together for local dev.
// Usage: pnpm dev:all   (from repo root)
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const engineDir = join(root, "services", "engine");
const venvPython = join(engineDir, ".venv", "bin", "python");

if (!existsSync(venvPython)) {
  console.error(
    "Engine venv not found. Create it:\n" +
      "  cd services/engine && python3 -m venv .venv && " +
      ".venv/bin/pip install -r requirements-dev.txt",
  );
  process.exit(1);
}

const procs = [];

function start(name, cmd, args, opts) {
  const p = spawn(cmd, args, { stdio: "inherit", ...opts });
  p.on("exit", (code) => {
    console.log(`[${name}] exited with ${code}`);
    shutdown();
  });
  procs.push(p);
  return p;
}

function shutdown() {
  for (const p of procs) {
    if (!p.killed) p.kill("SIGTERM");
  }
  process.exit(0);
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);

start("engine", venvPython, ["-m", "uvicorn", "app.main:app", "--port", "8000", "--reload"], {
  cwd: engineDir,
});
start("web", "pnpm", ["--filter", "@tabular/web", "dev"], { cwd: root });

console.log("Engine → http://localhost:8000  ·  Web → http://localhost:3000");
