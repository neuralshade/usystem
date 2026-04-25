import { cp, mkdir, readdir, rm } from "node:fs/promises";
import path from "node:path";

const icons = [
  "arrow-left",
  "bar-chart-3",
  "book-open",
  "calendar",
  "graduation-cap",
  "link",
  "log-out",
  "message-circle",
  "message-square",
  "paperclip",
  "send",
  "unlink-2",
  "user-plus",
  "users",
  "x"
];

const projectRoot = process.cwd();
const sourceDir = path.join(projectRoot, "node_modules", "lucide-static", "icons");
const outputDir = path.join(projectRoot, "app", "static", "icons");

await mkdir(outputDir, { recursive: true });

const existingEntries = await readdir(outputDir, { withFileTypes: true });
for (const entry of existingEntries) {
  if (entry.isFile() && entry.name.endsWith(".svg")) {
    await rm(path.join(outputDir, entry.name));
  }
}

for (const iconName of icons) {
  await cp(
    path.join(sourceDir, `${iconName}.svg`),
    path.join(outputDir, `${iconName}.svg`)
  );
}

console.log(`Prepared ${icons.length} Lucide icons in app/static/icons`);
